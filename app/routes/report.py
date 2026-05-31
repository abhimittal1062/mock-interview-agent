from fastapi import APIRouter, Form

from app.graph.report_graph import build_report_with_graph
from app.services.session_manager import SESSIONS

router = APIRouter()


@router.post("/final-report")
async def final_report(session_id: str = Form(...)):
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "Invalid session_id"}
    return {"report": await build_report_with_graph(session)}


@router.post("/end-interview")
async def end_interview(session_id: str = Form(...)):
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "Invalid session_id"}
    return {"report": await build_report_with_graph(session, reason="candidate_ended_early")}
