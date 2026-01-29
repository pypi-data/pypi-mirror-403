from typing import Optional, Union

import numpy as np
import pandas as pd
import torch
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError
from pyannote.audio import Pipeline

from murmurai.audio import SAMPLE_RATE, load_audio
from murmurai.log_utils import get_logger
from murmurai.schema import AlignedTranscriptionResult, TranscriptionResult

logger = get_logger(__name__)

# Model URLs for helpful error messages
MODEL_URLS = {
    "pyannote/speaker-diarization-3.1": "https://huggingface.co/pyannote/speaker-diarization-3.1",
    "pyannote/segmentation-3.0": "https://huggingface.co/pyannote/segmentation-3.0",
    "pyannote/speaker-diarization-community-1": "https://huggingface.co/pyannote/speaker-diarization-community-1",
}
HF_TOKEN_URL = "https://huggingface.co/settings/tokens"


class DiarizationAuthError(Exception):
    """Raised when there's an authentication error loading diarization models."""

    pass


def _get_auth_error_message(model_name: str, status_code: int) -> str:
    """Generate a user-friendly error message for HuggingFace auth errors."""
    model_url = MODEL_URLS.get(model_name, f"https://huggingface.co/{model_name}")

    if status_code == 401:
        return (
            f"Invalid or missing HuggingFace token.\n"
            f"Please provide a valid token via --hf_token or HF_TOKEN env var.\n"
            f"Create a token at: {HF_TOKEN_URL}"
        )
    elif status_code == 403:
        extra_models = ""
        if model_name == "pyannote/speaker-diarization-3.1":
            extra_models = f"\n  - {MODEL_URLS['pyannote/segmentation-3.0']} (required dependency)"
        return (
            f"Access denied to model '{model_name}'.\n"
            f"You need to accept the license agreement(s) at:\n"
            f"  - {model_url}{extra_models}"
        )
    else:
        return f"Failed to load model '{model_name}'.\nModel URL: {model_url}\nToken URL: {HF_TOKEN_URL}"


class DiarizationPipeline:
    def __init__(
        self,
        model_name=None,
        use_auth_token=None,
        device: Optional[Union[str, torch.device]] = "cpu",
    ):
        if isinstance(device, str):
            device = torch.device(device)
        model_config = model_name or "pyannote/speaker-diarization-community-1"
        logger.info(f"Loading diarization model: {model_config}")
        try:
            self.model = Pipeline.from_pretrained(model_config, use_auth_token=use_auth_token).to(
                device
            )
        except (HfHubHTTPError, RepositoryNotFoundError) as e:
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            if status_code in (401, 403):
                error_msg = _get_auth_error_message(model_config, status_code)
                logger.error(error_msg)
                raise DiarizationAuthError(error_msg) from e
            raise

    def __call__(
        self,
        audio: Union[str, np.ndarray],
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        return_embeddings: bool = False,
    ) -> Union[tuple[pd.DataFrame, Optional[dict[str, list[float]]]], pd.DataFrame]:
        """
        Perform speaker diarization on audio.

        Args:
            audio: Path to audio file or audio array
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers to detect
            max_speakers: Maximum number of speakers to detect
            return_embeddings: Whether to return speaker embeddings

        Returns:
            If return_embeddings is True:
                Tuple of (diarization dataframe, speaker embeddings dictionary)
            Otherwise:
                Just the diarization dataframe
        """
        if isinstance(audio, str):
            audio = load_audio(audio)
        audio_data = {"waveform": torch.from_numpy(audio[None, :]), "sample_rate": SAMPLE_RATE}

        if return_embeddings:
            diarization, embeddings = self.model(
                audio_data,
                num_speakers=num_speakers,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
                return_embeddings=True,
            )
        else:
            diarization = self.model(
                audio_data,
                num_speakers=num_speakers,
                min_speakers=min_speakers,
                max_speakers=max_speakers,
            )
            embeddings = None

        diarization_annotation = diarization
        if hasattr(diarization, "speaker_diarization"):
            diarization_annotation = diarization.speaker_diarization
            if embeddings is None and getattr(diarization, "speaker_embeddings", None) is not None:
                embeddings = diarization.speaker_embeddings

        diarize_df = pd.DataFrame(
            diarization_annotation.itertracks(yield_label=True),
            columns=["segment", "label", "speaker"],
        )
        diarize_df["start"] = diarize_df["segment"].apply(lambda x: x.start)
        diarize_df["end"] = diarize_df["segment"].apply(lambda x: x.end)

        if return_embeddings and embeddings is not None:
            speaker_embeddings = {
                speaker: embeddings[s].tolist()
                for s, speaker in enumerate(diarization_annotation.labels())
            }
            return diarize_df, speaker_embeddings

        # For backwards compatibility
        if return_embeddings:
            return diarize_df, None
        else:
            return diarize_df


def assign_word_speakers(
    diarize_df: pd.DataFrame,
    transcript_result: Union[AlignedTranscriptionResult, TranscriptionResult],
    speaker_embeddings: Optional[dict[str, list[float]]] = None,
    fill_nearest: bool = False,
) -> Union[AlignedTranscriptionResult, TranscriptionResult]:
    """
    Assign speakers to words and segments in the transcript.

    Args:
        diarize_df: Diarization dataframe from DiarizationPipeline
        transcript_result: Transcription result to augment with speaker labels
        speaker_embeddings: Optional dictionary mapping speaker IDs to embedding vectors
        fill_nearest: If True, assign speakers even when there's no direct time overlap

    Returns:
        Updated transcript_result with speaker assignments and optionally embeddings
    """
    transcript_segments = transcript_result["segments"]
    for seg in transcript_segments:
        # assign speaker to segment (if any)
        diarize_df["intersection"] = np.minimum(diarize_df["end"], seg["end"]) - np.maximum(
            diarize_df["start"], seg["start"]
        )
        diarize_df["union"] = np.maximum(diarize_df["end"], seg["end"]) - np.minimum(
            diarize_df["start"], seg["start"]
        )
        # remove no hit, otherwise we look for closest (even negative intersection...)
        if not fill_nearest:
            dia_tmp = diarize_df[diarize_df["intersection"] > 0]
        else:
            dia_tmp = diarize_df
        if len(dia_tmp) > 0:
            # sum over speakers
            speaker = (
                dia_tmp.groupby("speaker")["intersection"]
                .sum()
                .sort_values(ascending=False)
                .index[0]
            )
            seg["speaker"] = speaker

        # assign speaker to words
        if "words" in seg:
            for word in seg["words"]:
                if "start" in word:
                    diarize_df["intersection"] = np.minimum(
                        diarize_df["end"], word["end"]
                    ) - np.maximum(diarize_df["start"], word["start"])
                    diarize_df["union"] = np.maximum(diarize_df["end"], word["end"]) - np.minimum(
                        diarize_df["start"], word["start"]
                    )
                    # remove no hit
                    if not fill_nearest:
                        dia_tmp = diarize_df[diarize_df["intersection"] > 0]
                    else:
                        dia_tmp = diarize_df
                    if len(dia_tmp) > 0:
                        # sum over speakers
                        speaker = (
                            dia_tmp.groupby("speaker")["intersection"]
                            .sum()
                            .sort_values(ascending=False)
                            .index[0]
                        )
                        word["speaker"] = speaker

    # Add speaker embeddings to the result if provided
    if speaker_embeddings is not None:
        transcript_result["speaker_embeddings"] = speaker_embeddings

    return transcript_result


class Segment:
    def __init__(self, start: int, end: int, speaker: Optional[str] = None):
        self.start = start
        self.end = end
        self.speaker = speaker
