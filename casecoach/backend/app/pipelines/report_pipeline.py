from __future__ import annotations

from app.models.schemas import (
    AnalysisResult,
    DeliveryMetrics,
    SlideResult,
    TimestampedEvidence,
    Transcript,
    VideoMetadata,
)
from app.scoring.content_scores import score_content
from app.scoring.qa_scores import empty_qa_scores
from app.scoring.slide_scores import summarize_slide_metrics
from app.scoring.team_scores import compute_speaker_stats


def build_report(
    job_id: str,
    video_metadata: VideoMetadata,
    transcript: Transcript,
    slides: list[SlideResult],
    timeline,
    delivery_metrics: DeliveryMetrics,
    rubric_text: str,
    qa_included: bool,
    warnings: list[str],
) -> AnalysisResult:
    content_scores = score_content(transcript, rubric_text)
    slide_metrics = summarize_slide_metrics(slides)
    speakers = compute_speaker_stats(transcript)
    timestamped_evidence = _evidence_from_metrics(delivery_metrics, transcript)
    overall = _overall_score(content_scores, delivery_metrics, slide_metrics)
    return AnalysisResult(
        job_id=job_id,
        video_metadata=video_metadata,
        transcript=transcript,
        speakers=speakers,
        slides=slides,
        timeline=timeline,
        delivery_metrics=delivery_metrics,
        slide_metrics=slide_metrics,
        content_scores=content_scores,
        team_scores={"speaker_count": len(speakers), "speakers": [speaker.model_dump() for speaker in speakers]},
        qa_scores=empty_qa_scores(qa_included),
        overall_score=overall,
        top_strengths=_top_strengths(content_scores, delivery_metrics, slides),
        top_issues=_top_issues(content_scores, delivery_metrics, slides),
        recommended_drills=_recommended_drills(delivery_metrics, slides),
        timestamped_evidence=timestamped_evidence,
        warnings=warnings + transcript.warnings,
    )


def _overall_score(content_scores, delivery_metrics: DeliveryMetrics, slide_metrics: dict[str, object]) -> float:
    content_average = sum(score.score for score in content_scores.values()) / len(content_scores) if content_scores else 55.0
    delivery_score = 80.0
    if delivery_metrics.average_wpm > 185 or (0 < delivery_metrics.average_wpm < 110):
        delivery_score -= 10
    if delivery_metrics.filler_words_per_minute > 5:
        delivery_score -= 10
    slide_score = slide_metrics.get("average_readability_score") or 65.0
    return round(content_average * 0.55 + delivery_score * 0.25 + float(slide_score) * 0.20, 2)


def _top_strengths(content_scores, delivery_metrics: DeliveryMetrics, slides: list[SlideResult]) -> list[str]:
    strengths = []
    if delivery_metrics.average_wpm and 110 <= delivery_metrics.average_wpm <= 165:
        strengths.append("Observable delivery pace is within a typical presentation range.")
    if slides:
        strengths.append("Uploaded slides were processed into slide-level artifacts.")
    best = max(content_scores.values(), key=lambda item: item.score, default=None)
    if best:
        strengths.append(f"Strongest rubric signal: {best.dimension}.")
    return strengths or ["The backend generated a complete evidence structure for review."]


def _top_issues(content_scores, delivery_metrics: DeliveryMetrics, slides: list[SlideResult]) -> list[str]:
    issues = []
    if delivery_metrics.average_wpm > 185:
        issues.append("Observable transcript pace is above the recommended range.")
    if delivery_metrics.filler_words_per_minute > 5:
        issues.append("Filler frequency is high enough to distract from the answer.")
    if not slides:
        issues.append("No uploaded slide deck was available for slide audit.")
    weak = [score.dimension for score in content_scores.values() if score.issues]
    if weak:
        issues.append(f"Rubric dimensions needing clearer evidence: {', '.join(weak[:3])}.")
    return issues or ["No major deterministic issue was detected; review timestamped evidence for nuance."]


def _recommended_drills(delivery_metrics: DeliveryMetrics, slides: list[SlideResult]) -> list[str]:
    drills = [
        "Practice a 30-second answer-first opening for the recommendation.",
        "Pair each major claim with one metric, assumption, or source.",
    ]
    if delivery_metrics.average_wpm > 185:
        drills.append("Repeat the highest-pressure section with a deliberate pause after each key number.")
    if not slides:
        drills.append("Upload a PDF/PPTX deck to unlock slide-by-slide coaching.")
    return drills


def _evidence_from_metrics(delivery_metrics: DeliveryMetrics, transcript: Transcript) -> list[TimestampedEvidence]:
    evidence = []
    for pause in delivery_metrics.long_pauses[:5]:
        evidence.append(
            TimestampedEvidence(
                start=pause["start"],
                end=pause["end"],
                type="delivery_metric",
                severity="medium",
                summary=f"Long pause detected for {pause['duration']} seconds.",
                evidence={"pause_duration_sec": pause["duration"]},
                fix="Practice the transition sentence immediately before this pause.",
            )
        )
    if delivery_metrics.average_wpm > 185 and transcript.segments:
        first = transcript.segments[0]
        evidence.append(
            TimestampedEvidence(
                start=first.start,
                end=first.end,
                type="delivery_metric",
                severity="medium",
                summary=f"Average transcript pace is {delivery_metrics.average_wpm} WPM.",
                evidence={"average_wpm": delivery_metrics.average_wpm},
                fix="Use shorter sentences and insert a one-beat pause before financial or risk claims.",
            )
        )
    return evidence

