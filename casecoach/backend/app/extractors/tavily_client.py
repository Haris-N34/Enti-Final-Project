from __future__ import annotations

from typing import Any


class TavilyClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, max_results: int = 5) -> tuple[list[dict[str, str]], str | None]:
        if not self.configured:
            return [], "TAVILY_API_KEY is not configured; used assumption-based market context."
        try:
            import httpx
        except ImportError:
            return [], "httpx is not installed; market search was skipped."

        payload: dict[str, Any] = {
            "query": query,
            "topic": "general",
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post("https://api.tavily.com/search", json=payload, headers=headers)
                response.raise_for_status()
            body = response.json()
            results = []
            for item in body.get("results", [])[:max_results]:
                results.append(
                    {
                        "title": str(item.get("title", "")),
                        "url": str(item.get("url", "")),
                        "content": str(item.get("content", "")),
                    }
                )
            return results, None
        except httpx.HTTPStatusError as exc:
            return [], f"Tavily search failed with HTTP {exc.response.status_code}; used fallback context."
        except (httpx.RequestError, ValueError, TypeError) as exc:
            return [], f"Tavily search failed; used fallback context. {exc}"

