"""
Critic Agent
─────────────
Reviews the draft report for completeness, accuracy, clarity,
and logical structure. Outputs a critique and a revision flag.
"""
from __future__ import annotations

import json
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ResearchState
from utils import get_llm, logger

SYSTEM = """You are a senior editor reviewing a research report. Evaluate:

1. Completeness — Does it answer the original question fully?
2. Accuracy — Are claims grounded? Any unsupported assertions?
3. Clarity — Is the writing clear and well-organised?
4. Balance — Are limitations and caveats included?

Return ONLY valid JSON (no markdown fences):
{
  "score": 1-10,
  "strengths": ["strength 1", ...],
  "weaknesses": ["weakness 1", ...],
  "suggestions": ["concrete improvement 1", ...],
  "needs_revision": true/false
}

Set needs_revision=true only if score < 7 AND this is the first review.
"""


def run(state: ResearchState) -> ResearchState:
    logger.section("Critic Agent", color="bright_red")
    draft = state.get("draft_report", "")
    query = state["query"]
    iteration = state.get("iteration", 0)

    llm = get_llm(temperature=0.1)
    resp = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=(
            f"Original question: {query}\n\n"
            f"Draft report:\n{draft}\n\n"
            f"Review iteration: {iteration}"
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
        parsed = {"score": 8, "needs_revision": False, "suggestions": [], "strengths": [], "weaknesses": []}

    score = parsed.get("score", 8)
    needs_rev = parsed.get("needs_revision", False) and iteration < 1  # max 1 revision

    logger.agent_log("Critic", f"Score: {score}/10  |  Needs revision: {needs_rev}")
    for w in parsed.get("weaknesses", []):
        logger.warn(f"  {w}")
    for s in parsed.get("suggestions", []):
        logger.step_log("  Suggestion:", s[:100])

    critique_text = (
        f"Score: {score}/10\n"
        f"Strengths: {', '.join(parsed.get('strengths', []))}\n"
        f"Weaknesses: {', '.join(parsed.get('weaknesses', []))}\n"
        f"Suggestions: {', '.join(parsed.get('suggestions', []))}"
    )

    state["critique"] = critique_text
    state["needs_revision"] = needs_rev
    state["iteration"] = iteration + 1
    return state
