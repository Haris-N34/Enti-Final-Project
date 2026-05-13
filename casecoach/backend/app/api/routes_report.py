from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import get_job_store, get_object_store

router = APIRouter(prefix="/api", tags=["report"])


@router.get("/report/{job_id}")
async def get_report(job_id: str):
    return _read_artifact(job_id, "report_json")


@router.get("/timeline/{job_id}")
async def get_timeline(job_id: str):
    return _read_artifact(job_id, "timeline_json")


@router.get("/slides/{job_id}")
async def get_slides(job_id: str):
    return _read_artifact(job_id, "slides_json")


@router.get("/transcript/{job_id}")
async def get_transcript(job_id: str):
    return _read_artifact(job_id, "transcript_json")


@router.get("/body-metrics/{job_id}")
async def get_body_metrics(job_id: str):
    return _read_artifact(job_id, "body_metrics_json")


@router.get("/export/json/{job_id}")
async def export_json(job_id: str):
    return _read_artifact(job_id, "report_json")


def _read_artifact(job_id: str, key: str):
    jobs = get_job_store()
    objects = get_object_store()
    try:
        job = jobs.get_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found.") from exc
    path_value = job["paths"].get(key)
    if not path_value:
        if job["status"] == "failed":
            raise HTTPException(status_code=409, detail=job["error"] or "Analysis failed.")
        raise HTTPException(status_code=404, detail=f"Artifact '{key}' is not ready.")
    path = objects.resolve(path_value)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact '{key}' is missing on disk.")
    return objects.read_json(path)
