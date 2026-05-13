from __future__ import annotations

import re

from app.models.schemas import DeliveryMetrics, Transcript, TranscriptSegment

FILLER_PATTERNS = [
    "um",
    "uh",
    "like",
    "you know",
    "basically",
    "so",
    "right",
    "sort of",
    "kind of",
]


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text))


def count_fillers(text: str) -> int:
    lower = f" {text.lower()} "
    total = 0
    for filler in FILLER_PATTERNS:
        pattern = r"\b" + re.escape(filler).replace(r"\ ", r"\s+") + r"\b"
        total += len(re.findall(pattern, lower))
    return total


def compute_delivery_metrics(transcript: Transcript, long_pause_threshold: float = 1.5) -> DeliveryMetrics:
    text = " ".join(segment.text for segment in transcript.segments)
    words = word_count(text)
    filler_count = count_fillers(text)
    duration = _speaking_duration(transcript.segments)
    wpm = (words / duration * 60) if duration > 0 else 0.0
    pauses = _long_pauses(transcript.segments, long_pause_threshold)
    filler_per_min = (filler_count / duration * 60) if duration > 0 else 0.0
    return DeliveryMetrics(
        word_count=words,
        speaking_duration_sec=round(duration, 2),
        average_wpm=round(wpm, 2),
        filler_word_count=filler_count,
        filler_words_per_minute=round(filler_per_min, 2),
        long_pause_count=len(pauses),
        long_pauses=pauses,
    )


def _speaking_duration(segments: list[TranscriptSegment]) -> float:
    return round(sum(max(0.0, segment.end - segment.start) for segment in segments), 3)


def _long_pauses(segments: list[TranscriptSegment], threshold: float) -> list[dict[str, float]]:
    ordered = sorted(segments, key=lambda item: item.start)
    pauses: list[dict[str, float]] = []
    for previous, current in zip(ordered, ordered[1:]):
        gap = current.start - previous.end
        if gap >= threshold:
            pauses.append({"start": round(previous.end, 2), "end": round(current.start, 2), "duration": round(gap, 2)})
    return pauses

