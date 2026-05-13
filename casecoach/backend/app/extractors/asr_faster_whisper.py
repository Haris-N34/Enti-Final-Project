from __future__ import annotations

from pathlib import Path

from app.models.schemas import Transcript, TranscriptSegment, WordTimestamp


class FasterWhisperASR:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name

    def transcribe(self, audio_path: Path) -> Transcript:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return Transcript(
                warnings=[
                    "faster-whisper is not installed; transcript is unavailable. Install the asr extra or configure a remote ASR provider."
                ]
            )

        model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
        segments, _info = model.transcribe(str(audio_path), word_timestamps=True)
        output: list[TranscriptSegment] = []
        for segment in segments:
            words = [
                WordTimestamp(
                    word=item.word.strip(),
                    start=float(item.start or segment.start),
                    end=float(item.end or segment.end),
                    confidence=getattr(item, "probability", None),
                )
                for item in (segment.words or [])
                if item.word.strip()
            ]
            output.append(
                TranscriptSegment(
                    start=float(segment.start),
                    end=float(segment.end),
                    speaker="SPEAKER_00",
                    text=segment.text.strip(),
                    words=words,
                )
            )
        return Transcript(segments=output)

