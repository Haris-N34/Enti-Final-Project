from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.models.schemas import VideoMetadata


class MissingMediaToolError(RuntimeError):
    pass


def require_media_tools() -> None:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        raise MissingMediaToolError(
            "Missing required media tool(s): "
            + ", ".join(missing)
            + ". Install ffmpeg so the backend can normalize video and extract audio."
        )


def run_command(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{detail}")


def probe_video(video_path: Path) -> VideoMetadata:
    require_media_tools()
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=format_name,duration:stream=codec_type,width,height,r_frame_rate,channels",
            "-of",
            "json",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed.")
    payload: dict[str, Any] = json.loads(result.stdout)
    streams = payload.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), {})
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), {})
    fps = _parse_rate(video_stream.get("r_frame_rate", "0/1"))
    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    return VideoMetadata(
        duration_seconds=float(payload.get("format", {}).get("duration") or 0.0),
        fps=fps,
        width=width,
        height=height,
        audio_channels=int(audio_stream.get("channels") or 0),
        format_name=payload.get("format", {}).get("format_name", ""),
        likely_format=classify_video_format(width, height),
    )


def normalize_video(input_path: Path, output_path: Path) -> None:
    require_media_tools()
    run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            str(output_path),
        ]
    )


def extract_audio(video_path: Path, output_wav: Path) -> None:
    require_media_tools()
    run_command(["ffmpeg", "-y", "-i", str(video_path), "-vn", "-ac", "1", "-ar", "16000", str(output_wav)])


def sample_frames(video_path: Path, frames_dir: Path, fps: int = 1) -> list[Path]:
    require_media_tools()
    frames_dir.mkdir(parents=True, exist_ok=True)
    run_command(["ffmpeg", "-y", "-i", str(video_path), "-vf", f"fps={fps}", str(frames_dir / "frame_%06d.jpg")])
    return sorted(frames_dir.glob("frame_*.jpg"))


def preprocess_video(original_video: Path, job_dir: Path) -> tuple[VideoMetadata, dict[str, str]]:
    preprocessed_dir = job_dir / "preprocessed"
    frames_dir = job_dir / "frames"
    normalized_video = preprocessed_dir / "normalized.mp4"
    audio_wav = preprocessed_dir / "audio_16khz_mono.wav"
    normalize_video(original_video, normalized_video)
    metadata = probe_video(normalized_video)
    extract_audio(normalized_video, audio_wav)
    frame_paths = sample_frames(normalized_video, frames_dir, fps=1)
    return metadata, {
        "normalized_video": str(normalized_video),
        "audio_wav": str(audio_wav),
        "frames_dir": str(frames_dir),
        "sampled_frames": [str(path) for path in frame_paths],
    }


def classify_video_format(width: int, height: int) -> str:
    if width == 0 or height == 0:
        return "unknown"
    ratio = width / height
    if ratio > 1.65:
        return "screen_share_or_landscape"
    if ratio < 0.85:
        return "portrait_webcam"
    return "webcam_or_room_recording"


def _parse_rate(value: str) -> float:
    if "/" not in value:
        return float(value or 0.0)
    numerator, denominator = value.split("/", 1)
    denominator_value = float(denominator or 1)
    return float(numerator or 0) / denominator_value if denominator_value else 0.0

