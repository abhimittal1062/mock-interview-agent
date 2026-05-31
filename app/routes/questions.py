from fastapi import APIRouter, Form
from urllib.parse import quote
from app.services.session_manager import SESSIONS

router = APIRouter()


@router.post("/get-question")
async def get_question(session_id: str = Form(...)):
    """
    Returns:
        - Pending follow-up (with audio_url)
        - Next main question (with audio_url)
        - Done message
    """

    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "Invalid session_id"}

    # ---------------------- 1️⃣ FOLLOW-UP QUESTION HANDLING ----------------------
    followup_text = session.get("followup_pending")
    if followup_text:
        encoded_text = quote(followup_text)
        audio_url = f"/api/question-audio?text={encoded_text}"

        return {
            "type": "followup",
            "followup_count": session.get("followup_count", 0),
            "question": {
                "id": f"followup_{session['followup_count']}",
                "category": "followup",
                "text": followup_text,
                "audio_url": audio_url,
            },
        }

    # ---------------------- 2️⃣ MAIN QUESTION HANDLING ----------------------
    current_index = session.get("current", 0)
    questions = session.get("questions", [])

    # No more questions → interview done
    if current_index >= len(questions):
        return {
            "type": "done",
            "message": "Interview completed. No more questions."
        }

    # Safe extraction
    q = questions[current_index]
    q_text = q.get("text") or q.get("title") or "No question text provided (fallback)."

    encoded_text = quote(q_text)
    audio_url = f"/api/question-audio?text={encoded_text}"

    # Attach audio_url to the question
    return {
        "type": "main",
        "index": current_index,
        "remaining": len(questions) - current_index - 1,
        "question": {
            **q,
            "text": q_text,   # ensure existence
            "audio_url": audio_url,
        },
    }
