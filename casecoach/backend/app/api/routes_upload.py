from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import get_job_store, get_object_store
from app.config import get_settings
from app.models.schemas import UploadResponse
from app.pipelines.ingest import safe_upload_name, validate_slide_filename, validate_video_filename

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_presentation(
    video_file: UploadFile = File(...),
    slide_deck: UploadFile | None = File(default=None),
    case_prompt: str = Form(default=""),
    rubric: str = Form(default=""),
    team_members: str = Form(default=""),
    presentation_length_limit_minutes: int | None = Form(default=None),
    qa_included: bool = Form(default=False),
    analysis_mode: str = Form(default="fast"),
) -> UploadResponse:
    settings = get_settings()
    jobs = get_job_store()
    objects = get_object_store()
    warnings: list[str] = []

    try:
        validate_video_filename(video_file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job_id = str(uuid4())
    job_dir = objects.job_dir(job_id)
    original_video = job_dir / "uploads" / safe_upload_name(video_file.filename or "", "presentation.mp4")
    try:
        objects.copy_stream_limited(video_file.file, original_video, settings.max_upload_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    paths = {"original_video": str(original_video)}
    if slide_deck and slide_deck.filename:
        try:
            validate_slide_filename(slide_deck.filename)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        deck_path = job_dir / "uploads" / safe_upload_name(slide_deck.filename, "slides.pdf")
        try:
            objects.copy_stream_limited(slide_deck.file, deck_path, settings.max_upload_bytes)
        except ValueError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        paths["slide_deck"] = str(deck_path)

    members = _parse_team_members(team_members)
    metadata = {
        "case_prompt": case_prompt,
        "rubric": rubric,
        "team_members": members,
        "presentation_length_limit_minutes": presentation_length_limit_minutes,
        "qa_included": qa_included,
        "analysis_mode": analysis_mode,
    }
    (job_dir / "artifacts" / "upload_context.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    jobs.create_job(job_id, metadata, paths)
    return UploadResponse(job_id=job_id, status="uploaded", warnings=warnings)


def _parse_team_members(value: str) -> list[str]:
    if not value.strip():
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in value.split(",") if item.strip()]
