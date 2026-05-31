from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from app.services.report_service import build_final_report

try:
    from langgraph.graph import END, StateGraph
except Exception:
    END = None
    StateGraph = None


class ReportState(TypedDict, total=False):
    session: dict[str, Any]
    reason: str
    report: dict[str, Any]


async def _mark_ended_node(state: ReportState) -> ReportState:
    session = state["session"]
    if state.get("reason"):
        session["status"] = "ended"
        session["ended_reason"] = state["reason"]
        session["ended_at"] = datetime.utcnow().isoformat() + "Z"
        session["followup_pending"] = None
    return state


async def _report_node(state: ReportState) -> ReportState:
    state["report"] = build_final_report(state["session"])
    return state


def _build_report_graph():
    if StateGraph is None:
        return None
    graph = StateGraph(ReportState)
    graph.add_node("mark_ended", _mark_ended_node)
    graph.add_node("report", _report_node)
    graph.set_entry_point("mark_ended")
    graph.add_edge("mark_ended", "report")
    graph.add_edge("report", END)
    return graph.compile()


_REPORT_GRAPH = _build_report_graph()


async def build_report_with_graph(session: dict, reason: str | None = None) -> dict:
    state: ReportState = {"session": session, "reason": reason or ""}
    if _REPORT_GRAPH is not None:
        state = await _REPORT_GRAPH.ainvoke(state)
    else:
        state = await _mark_ended_node(state)
        state = await _report_node(state)
    return state["report"]
