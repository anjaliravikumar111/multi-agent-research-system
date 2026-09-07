"""
Tavily-powered web search with Redis caching.
Exposed as a LangChain tool so any agent can use it.
"""
from __future__ import annotations

import os
from typing import List

from langchain.tools import tool
from tavily import TavilyClient

from utils import cache, logger

_tavily: TavilyClient | None = None


def _client() -> TavilyClient:
    global _tavily
    if _tavily is None:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            raise EnvironmentError("TAVILY_API_KEY is not set.")
        _tavily = TavilyClient(api_key=api_key)
    return _tavily


@tool
def web_search(query: str) -> str:
    """
    Search the web for current information using Tavily.
    Returns a JSON-serialisable list of {title, url, content} dicts.
    Results are cached in Redis to avoid duplicate API calls.
    """
    cached = cache.get("search", query)
    if cached:
        logger.agent_log("SearchTool", f"Cache HIT — '{query}'", color="green")
        return _format(cached)

    logger.agent_log("SearchTool", f"Searching: '{query}'", color="magenta")
    try:
        max_r = int(os.getenv("MAX_SEARCH_RESULTS", 5))
        resp = _client().search(
            query=query,
            search_depth="advanced",
            max_results=max_r,
        )
        results: List[dict] = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
            }
            for r in resp.get("results", [])
        ]
        cache.set("search", query, results)
        logger.success(f"Retrieved {len(results)} results for '{query}'")
        return _format(results)
    except Exception as exc:
        logger.error(f"Search failed: {exc}")
        return f"Search error: {exc}"


def _format(results: list) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}\n    URL: {r['url']}\n    {r['content'][:400]}...")
    return "\n\n".join(lines) if lines else "No results found."
