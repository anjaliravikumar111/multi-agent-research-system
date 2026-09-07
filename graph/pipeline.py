"""
LangGraph Multi-Agent Pipeline
────────────────────────────────
Nodes  : search_planner → web_searcher → retriever → fact_checker
                        → synthesizer → critic ──┐
                                                  ├── [needs_revision] → synthesizer (once)
                                                  └── [done] → report_writer → END
"""
from __future__ import annotations

from langgraph.graph import StateGraph, END

from graph.state import ResearchState
from agents import (
    search_planner,
    web_searcher,
    retriever,
    fact_checker,
    synthesizer,
    critic,
    report_writer,
)


# ── node wrappers ─────────────────────────────────────────────────────────────

def node_search_planner(state: ResearchState) -> ResearchState:
    return search_planner.run(state)

def node_web_searcher(state: ResearchState) -> ResearchState:
    return web_searcher.run(state)

def node_retriever(state: ResearchState) -> ResearchState:
    return retriever.run(state)

def node_fact_checker(state: ResearchState) -> ResearchState:
    return fact_checker.run(state)

def node_synthesizer(state: ResearchState) -> ResearchState:
    return synthesizer.run(state)

def node_critic(state: ResearchState) -> ResearchState:
    return critic.run(state)

def node_report_writer(state: ResearchState) -> ResearchState:
    return report_writer.run(state)


# ── routing ───────────────────────────────────────────────────────────────────

def route_after_critic(state: ResearchState) -> str:
    """Revise once if critic flags issues, then finalise."""
    if state.get("needs_revision", False):
        return "synthesizer"       # re-generate with critique context
    return "report_writer"


# ── graph construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(ResearchState)

    g.add_node("search_planner", node_search_planner)
    g.add_node("web_searcher",   node_web_searcher)
    g.add_node("retriever",      node_retriever)
    g.add_node("fact_checker",   node_fact_checker)
    g.add_node("synthesizer",    node_synthesizer)
    g.add_node("critic",         node_critic)
    g.add_node("report_writer",  node_report_writer)

    g.set_entry_point("search_planner")

    g.add_edge("search_planner", "web_searcher")
    g.add_edge("web_searcher",   "retriever")
    g.add_edge("retriever",      "fact_checker")
    g.add_edge("fact_checker",   "synthesizer")
    g.add_edge("synthesizer",    "critic")

    g.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "synthesizer":    "synthesizer",
            "report_writer":  "report_writer",
        },
    )

    g.add_edge("report_writer", END)

    return g.compile()


# ── public entry point ────────────────────────────────────────────────────────

def run_pipeline(query: str) -> ResearchState:
    """Execute the full multi-agent pipeline and return the final state."""
    graph = build_graph()
    initial: ResearchState = {
        "query": query,
        "iteration": 0,
        "messages": [],
        "errors": [],
    }
    result = graph.invoke(initial)
    return result
