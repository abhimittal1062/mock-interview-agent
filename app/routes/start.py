from fastapi import APIRouter, Form

from app.graph.interview_graph import initialize_interview
from app.services.session_manager import SESSIONS

router = APIRouter()


@router.post("/start-interview")
async def start_interview(
    session_id: str = Form(...),
    question_count: int = Form(5),
):
    session = SESSIONS.get(session_id)

    if not session:
        return {"error": "Invalid session_id"}

    config = session.get("config", {}).copy()
    config["question_count"] = question_count or config.get("question_count", 5)
    session = await initialize_interview(session, config)
    questions = session["questions"]

    return {
        "message": "Interview started",
        "total_questions": len(questions),
        "first_question": questions[0] if questions else None,
        "ats_score": session.get("ats_score"),
        "config": session.get("config"),
    }
