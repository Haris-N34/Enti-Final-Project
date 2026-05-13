from __future__ import annotations

from pathlib import Path
from typing import Any

from app.extractors.qwen_vl_client import QwenVLClient


class QwenOmniClient(QwenVLClient):
    async def analyze_audio_video_context(self, prompt: str, frame_paths: list[Path]) -> tuple[dict[str, Any] | None, str | None]:
        if not self.configured:
            return None, "Qwen3-Omni is not configured; synchronized audio/video reasoning was skipped."
        return await self.complete_json(prompt, frame_paths)

