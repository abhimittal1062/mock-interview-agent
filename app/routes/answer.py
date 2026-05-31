from typing import Optional

from fastapi import APIRouter, Form

from app.graph.interview_graph import process_answer
from app.services.session_manager import SESSIONS

router = APIRouter()


@router.post("/submit-answer")
async def submit_answer(
    session_id: str = Form(...),
    transcript: str = Form(...),
    audio_filename: Optional[str] = Form(None),
    code_submission: Optional[str] = Form(None),
    complexity_claim: Optional[str] = Form(None),
):
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "Invalid session_id"}

    return await process_answer(
        session=session,
        transcript=transcript,
        audio_filename=audio_filename,
        code_submission=code_submission,
        complexity_claim=complexity_claim,
    )
