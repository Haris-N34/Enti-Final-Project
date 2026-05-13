from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.api.deps import get_job_store, get_object_store
from app.config import get_settings
from app.models.schemas import AnalyzeResponse, StatusResponse
from app.pipelines.analysis_pipeline import run_analysis

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze/{job_id}", response_model=AnalyzeResponse)
async def analyze_job(job_id: str, background_tasks: BackgroundTasks) -> AnalyzeResponse:
    jobs = get_job_store()
    try:
        job = jobs.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc
    if job["status"] in {"preprocessing", "transcribing", "extracting_slides", "reasoning", "scoring"}:
        return AnalyzeResponse(job_id=job_id, status=job["status"], message="Analysis is already running.")
    settings = get_settings()
    objects = get_object_store()
    background_tasks.add_task(run_analysis, job_id, settings, objects, jobs)
    return AnalyzeResponse(job_id=job_id, status=job["status"], message="Analysis queued.")


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    jobs = get_job_store()
    try:
        job = jobs.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc
    return StatusResponse(**job)

