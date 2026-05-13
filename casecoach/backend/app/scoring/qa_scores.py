from __future__ import annotations


def empty_qa_scores(qa_included: bool) -> dict[str, object]:
    return {
        "qa_included": qa_included,
        "status": "not_analyzed" if not qa_included else "pending_dedicated_qa_detection",
        "note": "Dedicated judge Q&A segmentation is planned after the first video-analysis milestone.",
    }

