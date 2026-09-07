"""
Shared state object that flows through the LangGraph pipeline.
Every agent reads from and writes to this TypedDict.
"""
from __future__ import annotations

from typing import Annotated, Any, List, Optional
from typing_extensions import TypedDict
import operator


class ResearchState(TypedDict, total=False):
    # ── input ──────────────────────────────────────────────────────────────
    query: str                          # original user question

    # ── search agent outputs ───────────────────────────────────────────────
    search_queries: List[str]           # sub-queries generated
    raw_search_results: List[dict]      # [{query, results}]

    # ── retrieval / analysis agent ─────────────────────────────────────────
    extracted_facts: List[str]          # key facts pulled from results
    source_urls: List[str]              # cited sources

    # ── fact-check agent ──────────────────────────────────────────────────
    verified_facts: List[str]
    disputed_facts: List[str]
    fact_check_notes: str

    # ── synthesis agent ───────────────────────────────────────────────────
    draft_report: str

    # ── critic agent ──────────────────────────────────────────────────────
    critique: str
    needs_revision: bool

    # ── final output ──────────────────────────────────────────────────────
    final_report: str
    report_path: str

    # ── pipeline metadata ─────────────────────────────────────────────────
    iteration: int
    messages: Annotated[List[Any], operator.add]   # agent message log
    errors: List[str]
