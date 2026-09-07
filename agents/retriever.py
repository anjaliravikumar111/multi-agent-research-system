"""
Retriever / Analyst Agent
──────────────────────────
Reads the raw search results and extracts key facts, data points,
and structured information relevant to the research query.
"""
from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ResearchState
from utils import get_llm, logger, cache

SYSTEM = """You are a research analyst. You receive web search results and a research
question. Extract the most important facts, statistics, quotes, and insights.

Return ONLY a valid JSON object with this structure (no markdown fences):
{
  "facts": ["fact 1", "fact 2", ...],
  "key_entities": ["entity 1", ...],
  "data_points": ["stat or number 1", ...],
  "gaps": ["what information is missing or unclear"]
}

Be precise. Each fact should be a complete, standalone sentence with source context.
"""


def run(state: ResearchState) -> ResearchState:
    logger.section("Retriever / Analyst Agent", color="yellow")
    query = state["query"]
    raw_results = state.get("raw_search_results", [])

    cache_key = query + str(len(raw_results))
    cached = cache.get("retriever", cache_key)
    if cached:
        logger.agent_log("Retriever", "Using cached extraction", color="green")
        state["extracted_facts"] = cached.get("facts", [])
        return state

    # Condense results to fit context window
    condensed = []
    for item in raw_results:
        q = item["query"]
        for r in item["results"][:3]:
            condensed.append(
                f"[Source: {r['url']}]\nTitle: {r['title']}\n{r['content'][:600]}"
            )

    content_block = "\n\n---\n\n".join(condensed[:12])  # cap at 12 snippets

    llm = get_llm(temperature=0.0)
    resp = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=(
            f"Research Question: {query}\n\n"
            f"Search Results:\n{content_block}"
        )),
    ])

    raw = resp.content.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = raw[:-3].strip()

    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {"facts": [raw], "key_entities": [], "data_points": [], "gaps": []}

    facts = parsed.get("facts", [])
    logger.agent_log("Retriever", f"Extracted {len(facts)} facts")
    for f in facts[:5]:
        logger.step_log("  →", f[:120])

    cache.set("retriever", cache_key, parsed)
    state["extracted_facts"] = facts
    return state
