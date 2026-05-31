from fastapi import APIRouter, Form

from app.services.session_manager import configure_session

router = APIRouter()


@router.post("/configure-interview")
async def configure_interview(
    session_id: str = Form(...),
    interview_type: str = Form("mixed"),
    difficulty: str = Form("junior"),
    question_count: int = Form(5),
    language: str = Form("cpp"),
    answer_mode: str = Form("voice"),
):
    allowed_types = {"hr", "technical", "system_design", "dsa", "mixed"}
    if interview_type not in allowed_types:
        return {"error": f"Invalid interview_type. Use one of: {sorted(allowed_types)}"}

    session = configure_session(
        session_id,
        {
            "interview_type": interview_type,
            "difficulty": difficulty,
            "question_count": question_count,
            "language": language,
            "answer_mode": answer_mode,
        },
    )
    if not session:
        return {"error": "Invalid session_id"}
    return {"message": "Interview configured", "config": session["config"]}
