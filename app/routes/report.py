from fastapi import APIRouter, Form

from app.services.report_service import build_final_report
from app.services.session_manager import SESSIONS

router = APIRouter()


@router.post("/final-report")
async def final_report(session_id: str = Form(...)):
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "Invalid session_id"}
    return {"report": build_final_report(session)}
