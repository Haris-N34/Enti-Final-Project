from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any


class QwenVLClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def build_multimodal_payload(
        self,
        prompt: str,
        image_paths: list[Path] | None = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for path in image_paths or []:
            content.append({"type": "image_url", "image_url": {"url": _image_data_url(path)}})
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict but helpful case competition presentation coach. Return JSON only.",
                },
                {"role": "user", "content": content},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

    async def complete_json(self, prompt: str, image_paths: list[Path] | None = None) -> tuple[dict[str, Any] | None, str | None]:
        if not self.configured:
            return None, "QWEN_VL_BASE_URL or QWEN_VL_API_KEY is not configured; skipped Qwen3-VL reasoning."
        try:
            import httpx
        except ImportError:
            return None, "httpx is not installed; skipped Qwen3-VL reasoning."

        payload = self.build_multimodal_payload(prompt, image_paths)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(_chat_url(self.base_url), headers=headers, json=payload)
            response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if isinstance(content, dict):
            return content, None
        return json.loads(content), None


def _chat_url(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def _image_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"

