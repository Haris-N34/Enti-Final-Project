from __future__ import annotations

from app.models.schemas import SlideResult


def summarize_slide_metrics(slides: list[SlideResult]) -> dict[str, object]:
    if not slides:
        return {"slide_count": 0, "average_readability_score": None, "warnings": ["No slide deck was processed."]}
    scores = [slide.readability_score for slide in slides if slide.readability_score is not None]
    return {
        "slide_count": len(slides),
        "average_readability_score": round(sum(scores) / len(scores), 2) if scores else None,
        "slides_with_warnings": sum(1 for slide in slides if slide.warnings),
    }

