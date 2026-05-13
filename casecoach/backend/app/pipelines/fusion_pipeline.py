from __future__ import annotations

from app.models.schemas import BodyMetrics, DeliveryMetrics, SlideResult, TimelineEvent, Transcript


def build_timeline(
    transcript: Transcript, slides: list[SlideResult], metrics: DeliveryMetrics, body_metrics: BodyMetrics | None = None
) -> list[TimelineEvent]:
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
                delivery_metrics={
                    "average_wpm": metrics.average_wpm,
                    "filler_words_per_minute": metrics.filler_words_per_minute,
                    **_body_summary(body_metrics),
                },
                content_tags=tags,
                issues=issues,
            )
        )
    return events


def _body_summary(body_metrics: BodyMetrics | None) -> dict[str, float | None]:
    if body_metrics is None:
        return {}
    return {
        "pose_visible_pct": body_metrics.pose_visible_pct,
        "posture_stability": body_metrics.posture_stability,
        "gesture_rate_per_min": body_metrics.gesture_rate_per_min,
    }


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
