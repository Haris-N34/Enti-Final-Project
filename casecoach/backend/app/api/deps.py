from __future__ import annotations

from app.config import get_settings
from app.storage.db import JobStore
from app.storage.object_store import ObjectStore


def get_job_store() -> JobStore:
    settings = get_settings()
    return JobStore(settings.sqlite_path)


def get_object_store() -> ObjectStore:
    settings = get_settings()
    return ObjectStore(settings.data_dir)

