from __future__ import annotations

from typing import Any, TypedDict


class InterviewState(TypedDict, total=False):
    session: dict[str, Any]
    config: dict[str, Any]
    session_id: str
    resume: dict[str, Any]
    jd: dict[str, Any]
    questions: list[dict[str, Any]]
    ats_score: dict[str, Any]
    current_question: dict[str, Any]
    question_text: str
    question_id: str
    transcript: str
    code_submission: str | None
    complexity_claim: str | None
    audio_filename: str | None
    is_followup: bool
    evaluation: dict[str, Any]
    result: dict[str, Any]
