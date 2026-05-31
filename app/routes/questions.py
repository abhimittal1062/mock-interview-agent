from urllib.parse import quote

from fastapi import APIRouter, Form

from app.settings import SETTINGS
from app.services.session_manager import SESSIONS

router = APIRouter()


@router.post("/get-question")
async def get_question(session_id: str = Form(...)):
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "Invalid session_id"}
    if session.get("status") == "ended":
        return {"type": "done", "message": "Interview ended by candidate."}

    followup_text = session.get("followup_pending")
    if followup_text:
        return {
            "type": "followup",
            "followup_count": session.get("followup_count", 0),
            "question": {
                "id": f"followup_{session['followup_count']}",
                "category": "followup",
                "text": followup_text,
                "audio_url": _question_audio_url(followup_text),
            },
        }

    current_index = session.get("current", 0)
    questions = session.get("questions", [])
    if current_index >= len(questions):
        session["status"] = "completed"
        return {"type": "done", "message": "Interview completed. No more questions."}

    question = questions[current_index]
    question_text = question.get("text") or question.get("title") or SETTINGS.fallback_question_text
    return {
        "type": "main",
        "index": current_index,
        "remaining": len(questions) - current_index - 1,
        "question": {
            **question,
            "text": question_text,
            "audio_url": _question_audio_url(question_text),
        },
    }


def _question_audio_url(text: str) -> str:
    return f"/api/question-audio?text={quote(text)}"
