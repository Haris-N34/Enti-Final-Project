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
        image_paths = image_paths or []
        content: str | list[dict[str, Any]]
        if image_paths:
            content = [{"type": "text", "text": prompt}]
        else:
            content = prompt
        for path in image_paths or []:
            assert isinstance(content, list)
            content.append({"type": "image_url", "image_url": {"url": _image_data_url(path)}})
        payload = {
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
        if "dashscope" in self.base_url and self.model.startswith("qwen3.6"):
            payload["enable_thinking"] = False
        return payload

    async def complete_json(self, prompt: str, image_paths: list[Path] | None = None) -> tuple[dict[str, Any] | None, str | None]:
        if not self.configured:
            return None, "QWEN_VL_BASE_URL or QWEN_VL_API_KEY is not configured; skipped Qwen3-VL reasoning."
        try:
            import httpx
        except ImportError:
            return None, "httpx is not installed; skipped Qwen3-VL reasoning."

        if _is_dashscope_app_call(self.base_url, self.model, image_paths):
            return await self._complete_dashscope_app(httpx, prompt)

        payload = self.build_multimodal_payload(prompt, image_paths)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(_chat_url(self.base_url), headers=headers, json=payload)
                response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            return _parse_json_content(content), None
        except httpx.HTTPStatusError as exc:
            return None, _http_warning(exc, "Qwen OpenAI-compatible request failed")
        except (httpx.RequestError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return None, f"Qwen OpenAI-compatible request failed; used fallback. {exc}"

    async def _complete_dashscope_app(self, httpx: Any, prompt: str) -> tuple[dict[str, Any] | None, str | None]:
        url = _dashscope_app_url(self.base_url, self.model)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"input": {"prompt": prompt}, "parameters": {}, "debug": {}}
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            body = response.json()
            content = body.get("output", {}).get("text", "")
            return _parse_json_content(content), None
        except httpx.HTTPStatusError as exc:
            return None, _http_warning(exc, "DashScope application request failed")
        except (httpx.RequestError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return None, f"DashScope application request failed; used fallback. {exc}"


def _chat_url(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def _is_dashscope_app_call(base_url: str, model: str, image_paths: list[Path] | None) -> bool:
    if image_paths:
        return False
    return "dashscope" in base_url and model.isdigit()


def _dashscope_app_url(base_url: str, app_id: str) -> str:
    if "dashscope-intl.aliyuncs.com" in base_url:
        return f"https://dashscope-intl.aliyuncs.com/api/v1/apps/{app_id}/completion"
    return f"https://dashscope.aliyuncs.com/api/v1/apps/{app_id}/completion"


def _parse_json_content(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    text = str(content).strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise TypeError("model response JSON is not an object")
    return parsed


def _http_warning(exc: Any, prefix: str) -> str:
    body = exc.response.text[:500] if exc.response is not None else ""
    return f"{prefix} with HTTP {exc.response.status_code}; used fallback. {body}"


def _image_data_url(path: Path) -> str:
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"
