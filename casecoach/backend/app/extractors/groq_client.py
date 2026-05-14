from __future__ import annotations

import json
from typing import Any


class GroqClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    async def complete_json(self, prompt: str, system_prompt: str) -> tuple[dict[str, Any] | None, str | None]:
        if not self.configured:
            return None, "GROQ_API_KEY or GROQ_MODEL is not configured; Groq report generation was skipped."
        try:
            import httpx
        except ImportError:
            return None, "httpx is not installed; Groq report generation was skipped."

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/chat/completions" if not self.base_url.endswith("/chat/completions") else self.base_url
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            if isinstance(content, dict):
                return content, None
            parsed = json.loads(str(content).strip())
            if not isinstance(parsed, dict):
                raise TypeError("Groq response JSON is not an object.")
            return parsed, None
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500] if exc.response is not None else ""
            return None, f"Groq request failed with HTTP {exc.response.status_code}; used fallback. {body}"
        except (httpx.RequestError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return None, f"Groq request failed; used fallback. {exc}"
