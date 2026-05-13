from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.extractors.asr_faster_whisper import FasterWhisperASR
from app.models.schemas import Transcript


def transcribe_audio(audio_path: Path, settings: Settings) -> Transcript:
    if settings.asr_provider != "faster_whisper":
        return Transcript(warnings=[f"ASR provider '{settings.asr_provider}' is not implemented in the MVP."])
    return FasterWhisperASR(settings.asr_model).transcribe(audio_path)

