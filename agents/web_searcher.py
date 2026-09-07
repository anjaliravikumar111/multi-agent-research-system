"""
Web Searcher Agent
──────────────────
Executes each sub-query via Tavily (with Redis caching) and
accumulates raw results into the pipeline state.
"""
from __future__ import annotations

import os
from typing import List

from tavily import TavilyClient

from graph.state import ResearchState
from utils import cache, logger

_client: TavilyClient | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        key = os.getenv("TAVILY_API_KEY", "")
        if not key:
            raise EnvironmentError("TAVILY_API_KEY not set.")
        _client = TavilyClient(api_key=key)
    return _client


def _search(query: str) -> List[dict]:
    cached = cache.get("search", query)
    if cached:
        logger.agent_log("WebSearcher", f"Cache HIT: '{query}'", color="green")
        return cached

    logger.agent_log("WebSearcher", f"Fetching: '{query}'", color="magenta")
    max_r = int(os.getenv("MAX_SEARCH_RESULTS", 5))
    resp = _get_client().search(
        query=query,
        search_depth="advanced",
        max_results=max_r,
    )
    results = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        }
        for r in resp.get("results", [])
    ]
    cache.set("search", query, results)
    logger.success(f"  {len(results)} results")
    return results


def run(state: ResearchState) -> ResearchState:
    logger.section("Web Searcher Agent", color="magenta")
    sub_queries = state.get("search_queries", [state["query"]])
    all_results = []
    source_urls: List[str] = []

    for q in sub_queries:
        results = _search(q)
        all_results.append({"query": q, "results": results})
        for r in results:
            url = r.get("url", "")
            if url and url not in source_urls:
                source_urls.append(url)

    state["raw_search_results"] = all_results
    state["source_urls"] = source_urls
    logger.success(f"Total sources collected: {len(source_urls)}")
    return state
