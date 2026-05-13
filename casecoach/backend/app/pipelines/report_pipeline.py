from __future__ import annotations

from app.models.schemas import (
    AnalysisResult,
    BodyMetrics,
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
    body_metrics: BodyMetrics,
    rubric_text: str,
    qa_included: bool,
    warnings: list[str],
) -> AnalysisResult:
    content_scores = score_content(transcript, rubric_text)
    slide_metrics = summarize_slide_metrics(slides)
    speakers = compute_speaker_stats(transcript)
    timestamped_evidence = _evidence_from_metrics(delivery_metrics, body_metrics, transcript)
    overall = _overall_score(content_scores, delivery_metrics, body_metrics, slide_metrics)
    return AnalysisResult(
        job_id=job_id,
        video_metadata=video_metadata,
        transcript=transcript,
        speakers=speakers,
        slides=slides,
        timeline=timeline,
        delivery_metrics=delivery_metrics,
        body_metrics=body_metrics,
        slide_metrics=slide_metrics,
        content_scores=content_scores,
        team_scores={"speaker_count": len(speakers), "speakers": [speaker.model_dump() for speaker in speakers]},
        qa_scores=empty_qa_scores(qa_included),
        overall_score=overall,
        top_strengths=_top_strengths(content_scores, delivery_metrics, body_metrics, slides),
        top_issues=_top_issues(content_scores, delivery_metrics, body_metrics, slides),
        recommended_drills=_recommended_drills(delivery_metrics, body_metrics, slides),
        timestamped_evidence=timestamped_evidence,
        warnings=warnings + transcript.warnings,
    )


def _overall_score(
    content_scores, delivery_metrics: DeliveryMetrics, body_metrics: BodyMetrics, slide_metrics: dict[str, object]
) -> float:
    content_average = sum(score.score for score in content_scores.values()) / len(content_scores) if content_scores else 55.0
    delivery_score = 80.0
    if delivery_metrics.average_wpm > 185 or (0 < delivery_metrics.average_wpm < 110):
        delivery_score -= 10
    if delivery_metrics.filler_words_per_minute > 5:
        delivery_score -= 10
    if body_metrics.posture_stability is not None and body_metrics.posture_stability < 0.55:
        delivery_score -= 6
    if body_metrics.avg_torso_lean_deg is not None and body_metrics.avg_torso_lean_deg > 16:
        delivery_score -= 4
    if body_metrics.gesture_rate_per_min is not None and body_metrics.gesture_rate_per_min > 45:
        delivery_score -= 4
    slide_score = slide_metrics.get("average_readability_score") or 65.0
    return round(content_average * 0.55 + delivery_score * 0.25 + float(slide_score) * 0.20, 2)


def _top_strengths(
    content_scores, delivery_metrics: DeliveryMetrics, body_metrics: BodyMetrics, slides: list[SlideResult]
) -> list[str]:
    strengths = []
    if delivery_metrics.average_wpm and 110 <= delivery_metrics.average_wpm <= 165:
        strengths.append("Observable delivery pace is within a typical presentation range.")
    if body_metrics.posture_stability is not None and body_metrics.posture_stability >= 0.7:
        strengths.append("Sampled posture landmarks show stable shoulder/torso positioning.")
    if body_metrics.hands_visible_pct is not None and body_metrics.hands_visible_pct >= 65:
        strengths.append("Hands were visible in most sampled frames, which helps gesture coaching quality.")
    if slides:
        strengths.append("Uploaded slides were processed into slide-level artifacts.")
    best = max(content_scores.values(), key=lambda item: item.score, default=None)
    if best:
        strengths.append(f"Strongest rubric signal: {best.dimension}.")
    return strengths or ["The backend generated a complete evidence structure for review."]


def _top_issues(content_scores, delivery_metrics: DeliveryMetrics, body_metrics: BodyMetrics, slides: list[SlideResult]) -> list[str]:
    issues = []
    if delivery_metrics.average_wpm > 185:
        issues.append("Observable transcript pace is above the recommended range.")
    if delivery_metrics.filler_words_per_minute > 5:
        issues.append("Filler frequency is high enough to distract from the answer.")
    if body_metrics.pose_visible_pct == 0:
        issues.append("No presenter body pose was detected in sampled frames, so posture coaching is limited.")
    elif body_metrics.pose_visible_pct is not None and body_metrics.pose_visible_pct < 35:
        issues.append("Presenter body pose was visible in too few sampled frames for reliable posture coaching.")
    if body_metrics.posture_stability is not None and body_metrics.posture_stability < 0.55:
        issues.append("Shoulder-center movement was high across sampled frames; practice a steadier stance.")
    if body_metrics.avg_shoulder_tilt_deg is not None and body_metrics.avg_shoulder_tilt_deg > 10:
        issues.append("Average shoulder tilt was elevated in sampled frames; check camera angle and stance alignment.")
    if body_metrics.gesture_rate_per_min is not None and body_metrics.gesture_rate_per_min > 45:
        issues.append("Hand movement frequency was high in sampled frames; anchor gestures around key points.")
    if not slides:
        issues.append("No uploaded slide deck was available for slide audit.")
    weak = [score.dimension for score in content_scores.values() if score.issues]
    if weak:
        issues.append(f"Rubric dimensions needing clearer evidence: {', '.join(weak[:3])}.")
    return issues or ["No major deterministic issue was detected; review timestamped evidence for nuance."]


def _recommended_drills(delivery_metrics: DeliveryMetrics, body_metrics: BodyMetrics, slides: list[SlideResult]) -> list[str]:
    drills = [
        "Practice a 30-second answer-first opening for the recommendation.",
        "Pair each major claim with one metric, assumption, or source.",
    ]
    if delivery_metrics.average_wpm > 185:
        drills.append("Repeat the highest-pressure section with a deliberate pause after each key number.")
    if body_metrics.posture_stability is not None and body_metrics.posture_stability < 0.55:
        drills.append("Practice one answer with feet planted and shoulders square; review whether shoulder-center movement drops.")
    if body_metrics.gesture_rate_per_min is not None and body_metrics.gesture_rate_per_min > 45:
        drills.append("Use one intentional gesture per claim, then return hands to a neutral position.")
    if not slides:
        drills.append("Upload a PDF/PPTX deck to unlock slide-by-slide coaching.")
    return drills


def _evidence_from_metrics(
    delivery_metrics: DeliveryMetrics, body_metrics: BodyMetrics, transcript: Transcript
) -> list[TimestampedEvidence]:
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
    if body_metrics.posture_stability is not None and body_metrics.posture_stability < 0.55:
        evidence.append(
            TimestampedEvidence(
                start=0.0,
                end=0.0,
                type="body_metric",
                severity="medium",
                summary=f"Posture stability proxy is {body_metrics.posture_stability}.",
                evidence={
                    "posture_stability": body_metrics.posture_stability,
                    "motion_level": body_metrics.motion_level,
                    "sampled_frame_count": body_metrics.sampled_frame_count,
                },
                fix="Practice the recommendation answer with a planted stance and controlled upper-body movement.",
            )
        )
    if body_metrics.avg_torso_lean_deg is not None and body_metrics.avg_torso_lean_deg > 16:
        evidence.append(
            TimestampedEvidence(
                start=0.0,
                end=0.0,
                type="body_metric",
                severity="low",
                summary=f"Average torso lean proxy is {body_metrics.avg_torso_lean_deg} degrees.",
                evidence={"avg_torso_lean_deg": body_metrics.avg_torso_lean_deg},
                fix="Check camera placement and practice keeping shoulders over hips during key claims.",
            )
        )
    return evidence
