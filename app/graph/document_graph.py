from __future__ import annotations

from typing import Any, TypedDict

from app.services.parser_service import parse_jd, parse_resume
from app.services.session_manager import create_session

try:
    from langgraph.graph import END, StateGraph
except Exception:
    END = None
    StateGraph = None


class DocumentState(TypedDict, total=False):
    resume_text: str
    jd_text: str
    resume: dict[str, Any]
    jd: dict[str, Any]
    session_id: str


async def _parse_resume_node(state: DocumentState) -> DocumentState:
    state["resume"] = await parse_resume(state["resume_text"])
    return state


async def _parse_jd_node(state: DocumentState) -> DocumentState:
    state["jd"] = await parse_jd(state["jd_text"])
    return state


async def _create_session_node(state: DocumentState) -> DocumentState:
    state["session_id"] = create_session(state["resume"], state["jd"])
    return state


def _build_document_graph():
    if StateGraph is None:
        return None
    graph = StateGraph(DocumentState)
    graph.add_node("parse_resume", _parse_resume_node)
    graph.add_node("parse_jd", _parse_jd_node)
    graph.add_node("create_session", _create_session_node)
    graph.set_entry_point("parse_resume")
    graph.add_edge("parse_resume", "parse_jd")
    graph.add_edge("parse_jd", "create_session")
    graph.add_edge("create_session", END)
    return graph.compile()


_DOCUMENT_GRAPH = _build_document_graph()


async def ingest_documents(resume_text: str, jd_text: str) -> DocumentState:
    state: DocumentState = {"resume_text": resume_text, "jd_text": jd_text}
    if _DOCUMENT_GRAPH is not None:
        return await _DOCUMENT_GRAPH.ainvoke(state)

    state = await _parse_resume_node(state)
    state = await _parse_jd_node(state)
    return await _create_session_node(state)
