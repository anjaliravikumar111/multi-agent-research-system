"""
Search Planner Agent
────────────────────
Breaks the user query into 3-5 targeted sub-queries that together
cover the topic from multiple angles.
"""
from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ResearchState
from utils import get_llm, logger, cache

SYSTEM = """You are a research strategist. Given a research question, decompose it
into 3-5 focused, distinct web-search queries that together will give comprehensive
coverage. Return ONLY a valid JSON array of strings — no commentary, no markdown.

Example output:
["query one", "query two", "query three"]
"""


def run(state: ResearchState) -> ResearchState:
    query = state["query"]
    logger.section("Search Planner Agent", color="cyan")

    cached = cache.get("plan", query)
    if cached:
        logger.agent_log("SearchPlanner", "Using cached sub-queries", color="green")
        state["search_queries"] = cached
        return state

    llm = get_llm(temperature=0.2)
    resp = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"Research question: {query}"),
    ])

    raw = resp.content.strip()
    # strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        sub_queries = json.loads(raw)
        if not isinstance(sub_queries, list):
            raise ValueError("Expected a list")
    except Exception:
        sub_queries = [query]   # fallback to original query

    logger.agent_log("SearchPlanner", f"Generated {len(sub_queries)} sub-queries")
    for q in sub_queries:
        logger.step_log(f"  • {q}")

    cache.set("plan", query, sub_queries)
    state["search_queries"] = sub_queries
    return state
