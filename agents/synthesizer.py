"""
Synthesizer Agent
──────────────────
Combines verified facts, source URLs, and fact-check notes
into a structured, well-cited research report (Markdown).
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ResearchState
from utils import get_llm, logger

SYSTEM = """You are an expert research writer. Generate a comprehensive, well-structured
research report in Markdown format.

Structure:
# [Title]

## Executive Summary
(2-3 sentence overview)

## Key Findings
(bullet points of the most important verified facts)

## Detailed Analysis
(3-5 paragraphs expanding on the findings with context)

## Data & Statistics
(table or bullets of key numbers/metrics if available)

## Limitations & Caveats
(disputed facts, knowledge gaps, single-source claims)

## Sources
(numbered list of URLs)

Rules:
- Use ONLY the verified facts provided — do not hallucinate
- Cite sources inline as [1], [2] etc. matching the Sources list
- Be objective, precise, and professional
- Minimum 600 words
"""


def run(state: ResearchState) -> ResearchState:
    logger.section("Synthesizer Agent", color="blue")

    verified = state.get("verified_facts", [])
    disputed = state.get("disputed_facts", [])
    notes = state.get("fact_check_notes", "")
    urls = state.get("source_urls", [])
    query = state["query"]

    facts_block = "\n".join(f"- {f}" for f in verified)
    disputed_block = "\n".join(f"- {d}" for d in disputed) if disputed else "None"
    sources_block = "\n".join(f"[{i+1}] {u}" for i, u in enumerate(urls[:15]))

    llm = get_llm(temperature=0.3)
    resp = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=(
            f"Research Question: {query}\n\n"
            f"VERIFIED FACTS:\n{facts_block}\n\n"
            f"DISPUTED / UNCERTAIN:\n{disputed_block}\n\n"
            f"FACT-CHECK NOTES:\n{notes}\n\n"
            f"SOURCES:\n{sources_block}"
        )),
    ])

    draft = resp.content.strip()
    logger.agent_log("Synthesizer", f"Draft generated ({len(draft)} chars)")
    state["draft_report"] = draft
    return state
