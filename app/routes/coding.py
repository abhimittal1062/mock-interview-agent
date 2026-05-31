from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Form

from app.services.coding_service import run_sample_tests
from app.services.session_manager import SESSIONS

router = APIRouter()


@router.post("/run-code-samples")
async def run_code_samples(
    session_id: str = Form(...),
    code: str = Form(...),
    time_complexity: Optional[str] = Form(None),
    space_complexity: Optional[str] = Form(None),
):
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": "Invalid session_id"}

    current = session.get("current", 0)
    questions = session.get("questions", [])
    if current >= len(questions):
        return {"error": "No active coding question"}

    question = questions[current]
    if question.get("category") != "dsa" and not question.get("sample_tests"):
        return {"error": "Current question is not executable"}

    result = run_sample_tests(question, code)
    run_record = {
        "question_id": question.get("id", f"question_{current + 1}"),
        "question_text": question.get("text") or question.get("title"),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "time_complexity": time_complexity,
        "space_complexity": space_complexity,
        "code": code,
        "result": result,
    }
    session.setdefault("code_runs", []).append(run_record)
    return {"run": run_record}
