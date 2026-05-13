from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_analysis import router as analysis_router
from app.api.routes_report import router as report_router
from app.api.routes_upload import router as upload_router
from app.config import get_settings
from app.storage.db import JobStore


def create_app() -> FastAPI:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    JobStore(settings.sqlite_path)
    app = FastAPI(
        title="CaseCoach Backend",
        version="0.1.0",
        description="Backend MVP for Case Mirror video-model presentation analysis.",
    )
    app.include_router(upload_router)
    app.include_router(analysis_router)
    app.include_router(report_router)

    @app.get("/health")
    async def health():
        return {"ok": True}

    return app


app = create_app()

