from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.extractors.qwen_omni_client import QwenOmniClient
from app.extractors.qwen_vl_client import QwenVLClient
from app.models.schemas import AnalysisResult, TimestampedEvidence, VideoMetadata
from app.pipelines.audio_pipeline import transcribe_audio
from app.pipelines.fusion_pipeline import build_timeline
from app.pipelines.preprocess import preprocess_video
from app.pipelines.report_pipeline import build_report
from app.pipelines.slide_pipeline import process_slide_deck
from app.scoring.delivery_scores import compute_delivery_metrics
from app.storage.db import JobStore
from app.storage.object_store import ObjectStore


async def run_analysis(job_id: str, settings: Settings, store: ObjectStore, jobs: JobStore) -> None:
    try:
        job = jobs.get_job(job_id)
        metadata = job["metadata"]
        paths = job["paths"]
        job_dir = store.job_dir(job_id)

        jobs.update_status(job_id, "preprocessing")
        video_metadata, preprocess_paths = preprocess_video(Path(paths["original_video"]), job_dir)
        jobs.update_paths(job_id, preprocess_paths)

        jobs.update_status(job_id, "transcribing")
        transcript = transcribe_audio(Path(preprocess_paths["audio_wav"]), settings)
        transcript_path = job_dir / "artifacts" / "transcript.json"
        store.write_json(transcript_path, transcript.model_dump())

        jobs.update_status(job_id, "extracting_slides")
        slide_path = Path(paths["slide_deck"]) if paths.get("slide_deck") else None
        slides, slide_warnings = process_slide_deck(slide_path, job_dir / "slides")
        slides_path = job_dir / "artifacts" / "slides.json"
        store.write_json(slides_path, [slide.model_dump() for slide in slides])

        jobs.update_status(job_id, "reasoning")
        reasoning_warnings, model_reasoning = await _run_reasoning(settings, job_dir, preprocess_paths, transcript.model_dump(), slides)

        jobs.update_status(job_id, "scoring")
        delivery_metrics = compute_delivery_metrics(transcript)
        timeline = build_timeline(transcript, slides, delivery_metrics)
        result = build_report(
            job_id=job_id,
            video_metadata=video_metadata,
            transcript=transcript,
            slides=slides,
            timeline=timeline,
            delivery_metrics=delivery_metrics,
            rubric_text=metadata.get("rubric", ""),
            qa_included=bool(metadata.get("qa_included", False)),
            warnings=slide_warnings + reasoning_warnings,
        )
        _merge_reasoning_into_result(result, model_reasoning)
        _assert_safe_report(result)
        report_path = job_dir / "artifacts" / "report.json"
        timeline_path = job_dir / "artifacts" / "timeline.json"
        store.write_json(report_path, result.model_dump())
        store.write_json(timeline_path, [event.model_dump() for event in timeline])
        jobs.update_paths(
            job_id,
            {
                "transcript_json": str(transcript_path),
                "slides_json": str(slides_path),
                "timeline_json": str(timeline_path),
                "report_json": str(report_path),
            },
        )
        jobs.update_metadata(job_id, {"video_metadata": video_metadata.model_dump()})
        jobs.update_status(job_id, "completed")
    except Exception as exc:
        jobs.fail_job(job_id, str(exc))
        raise


async def _run_reasoning(
    settings: Settings, job_dir: Path, preprocess_paths: dict[str, object], transcript, slides
) -> tuple[list[str], dict[str, object]]:
    warnings: list[str] = []
    merged_reasoning: dict[str, object] = {}
    frame_paths = [Path(path) for path in (preprocess_paths.get("sampled_frames") or [])[:6]]
    slide_images = [Path(slide.image_path) for slide in slides[:6] if slide.image_path]
    prompt = _reasoning_prompt(transcript, len(slides))
    qwen = QwenVLClient(settings.qwen_vl_base_url, settings.qwen_vl_api_key, settings.qwen_vl_model)
    response, warning = await qwen.complete_json(prompt, frame_paths + slide_images)
    if warning:
        warnings.append(warning)
    if response:
        (job_dir / "artifacts" / "qwen_vl_reasoning.json").write_text(json.dumps(response, indent=2), encoding="utf-8")
        merged_reasoning["qwen_vl"] = response

    if settings.qwen_omni_base_url:
        omni = QwenOmniClient(settings.qwen_omni_base_url, settings.qwen_omni_api_key, settings.qwen_omni_model)
        omni_response, omni_warning = await omni.analyze_audio_video_context(prompt, frame_paths)
        if omni_warning:
            warnings.append(omni_warning)
        if omni_response:
            (job_dir / "artifacts" / "qwen_omni_reasoning.json").write_text(json.dumps(omni_response, indent=2), encoding="utf-8")
            merged_reasoning["qwen_omni"] = omni_response
    return warnings, merged_reasoning


def _reasoning_prompt(transcript, slide_count: int) -> str:
    return (
        "Evaluate this case competition presentation evidence. Use observable behavior only. "
        "Return JSON with strengths, issues, timestamped_observations, and suggested_fixes. "
        f"Slide count: {slide_count}. Transcript JSON: {json.dumps(transcript)[:12000]}"
    )


def _assert_safe_report(result: AnalysisResult) -> None:
    banned = ["you looked nervous", "personality", "protected trait", "winner", "will win"]
    text = json.dumps(result.model_dump()).lower()
    for phrase in banned:
        if phrase in text:
            raise ValueError(f"Unsafe report language detected: {phrase}")


def _merge_reasoning_into_result(result: AnalysisResult, model_reasoning: dict[str, object]) -> None:
    for response in model_reasoning.values():
        if not isinstance(response, dict):
            continue
        result.top_strengths.extend(_string_list(response.get("strengths"))[:3])
        result.top_issues.extend(_string_list(response.get("issues"))[:3])
        for observation in _observation_list(response.get("timestamped_observations")):
            result.timestamped_evidence.append(observation)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _observation_list(value: object) -> list[TimestampedEvidence]:
    if not isinstance(value, list):
        return []
    observations: list[TimestampedEvidence] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        try:
            observations.append(
                TimestampedEvidence(
                    start=float(item.get("start", item.get("timestamp", 0.0)) or 0.0),
                    end=float(item.get("end", item.get("timestamp", 0.0)) or 0.0),
                    type=str(item.get("type", "model_observation")),
                    severity=str(item.get("severity", "medium")) if item.get("severity") in {"low", "medium", "high"} else "medium",
                    speaker=item.get("speaker"),
                    slide_id=item.get("slide_id"),
                    summary=str(item.get("summary", item.get("observation", ""))),
                    evidence=item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                    fix=str(item.get("fix", "")),
                )
            )
        except (TypeError, ValueError):
            continue
    return observations
