from __future__ import annotations

from app.models.schemas import DeliveryMetrics, SlideResult, TimelineEvent, Transcript


def build_timeline(transcript: Transcript, slides: list[SlideResult], metrics: DeliveryMetrics) -> list[TimelineEvent]:
    slide_by_time = slides[0].slide_id if slides else None
    events: list[TimelineEvent] = []
    for segment in transcript.segments:
        tags = _content_tags(segment.text)
        issues = []
        if metrics.average_wpm > 185:
            issues.append("pace_above_target_range")
        events.append(
            TimelineEvent(
                start=segment.start,
                end=segment.end,
                speaker=segment.speaker,
                slide=slide_by_time,
                transcript=segment.text,
                delivery_metrics={"average_wpm": metrics.average_wpm, "filler_words_per_minute": metrics.filler_words_per_minute},
                content_tags=tags,
                issues=issues,
            )
        )
    return events


def _content_tags(text: str) -> list[str]:
    lower = text.lower()
    tags = []
    for keyword, tag in [
        ("recommend", "recommendation"),
        ("risk", "risk"),
        ("metric", "metrics"),
        ("revenue", "financials"),
        ("cost", "financials"),
        ("implement", "implementation"),
        ("timeline", "implementation"),
    ]:
        if keyword in lower and tag not in tags:
            tags.append(tag)
    return tags

