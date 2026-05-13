from __future__ import annotations

from pathlib import Path


ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
ALLOWED_SLIDE_EXTENSIONS = {".pdf", ".pptx"}


def validate_video_filename(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_VIDEO_EXTENSIONS))
        raise ValueError(f"Unsupported video type '{suffix or 'unknown'}'. Allowed: {allowed}.")
    return suffix


def validate_slide_filename(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_SLIDE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_SLIDE_EXTENSIONS))
        raise ValueError(f"Unsupported slide deck type '{suffix or 'unknown'}'. Allowed: {allowed}.")
    return suffix


def safe_upload_name(filename: str, fallback: str) -> str:
    name = Path(filename or fallback).name.replace("/", "_").replace("\\", "_")
    return name or fallback

