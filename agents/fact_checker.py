"""
Fact Checker Agent
───────────────────
Cross-verifies extracted facts against all search results.
Marks each fact as verified, disputed, or unverifiable.
This is the core accuracy layer that differentiates the pipeline.
"""
from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ResearchState
from utils import get_llm, logger, cache

SYSTEM = """You are a rigorous fact-checker. You receive:
1. A list of extracted facts
2. The original search results used as evidence

Your job:
- VERIFY facts that are clearly supported by multiple sources
- DISPUTE facts that contradict or are unsupported by the evidence
- FLAG facts that appear in only one source (single-source bias)

Return ONLY a valid JSON object (no markdown):
{
  "verified": ["fully supported fact 1", ...],
  "disputed": ["fact that seems wrong or contradicted: reason"],
  "single_source": ["fact only found in one source"],
  "notes": "Overall assessment of source quality and reliability (2-3 sentences)"
}
"""


def run(state: ResearchState) -> ResearchState:
    logger.section("Fact Checker Agent", color="red")
    facts = state.get("extracted_facts", [])
    raw_results = state.get("raw_search_results", [])

    if not facts:
        logger.warn("No facts to verify.")
        state["verified_facts"] = []
        state["disputed_facts"] = []
        state["fact_check_notes"] = "No facts were available for verification."
        return state

    cache_key = "".join(facts[:5])
    cached = cache.get("factcheck", cache_key)
    if cached:
        logger.agent_log("FactChecker", "Using cached verification", color="green")
        state.update(_unpack(cached))
        return state

    # Build evidence block
    evidence = []
    for item in raw_results:
        for r in item["results"][:2]:
            evidence.append(f"[{r['url']}] {r['content'][:400]}")
    evidence_block = "\n\n".join(evidence[:10])

    facts_block = "\n".join(f"{i+1}. {f}" for i, f in enumerate(facts))

    llm = get_llm(temperature=0.0)
    resp = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=(
            f"Facts to check:\n{facts_block}\n\n"
            f"Evidence from sources:\n{evidence_block}"
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
        parsed = {"verified": facts, "disputed": [], "single_source": [], "notes": "Parse error."}

    logger.agent_log("FactChecker",
        f"Verified={len(parsed.get('verified', []))}  "
        f"Disputed={len(parsed.get('disputed', []))}  "
        f"Single-source={len(parsed.get('single_source', []))}"
    )

    cache.set("factcheck", cache_key, parsed)
    state.update(_unpack(parsed))
    return state


def _unpack(parsed: dict) -> dict:
    return {
        "verified_facts": parsed.get("verified", []),
        "disputed_facts": parsed.get("disputed", []),
        "fact_check_notes": parsed.get("notes", ""),
    }
