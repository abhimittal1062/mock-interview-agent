import hashlib
import json
import uuid

from app.settings import SETTINGS
from app.services.question_history import question_text

# In-memory session store. This is fine for local/demo mode; persistent storage
# should replace it before multi-user production deployment.
SESSIONS = {}
QUESTION_HISTORY_BY_PROFILE = {}


DEFAULT_CONFIG = {
    "interview_type": SETTINGS.default_interview_type,
    "difficulty": SETTINGS.default_difficulty,
    "question_count": SETTINGS.default_question_count,
    "language": SETTINGS.default_language,
    "answer_mode": "voice",
}


def create_session(resume_json, jd_json):
    """
    Creates a new interview session with resume + job description parsed data.
    Stores full interview state in memory.
    """
    session_id = str(uuid.uuid4())
    profile_key = _profile_key(resume_json, jd_json)

    SESSIONS[session_id] = {
        "session_id": session_id,
        "resume": resume_json,
        "jd": jd_json,
        "config": DEFAULT_CONFIG.copy(),
        "ats_score": None,
        "questions": [],
        "current": 0,
        "followup_pending": None,
        "followup_count": 0,
        "answers": [],
        "code_runs": [],
        "final_plan": None,
        "final_report": None,
        "status": "created",
        "ended_reason": None,
        "ended_at": None,
        "profile_key": profile_key,
        "question_history": QUESTION_HISTORY_BY_PROFILE.get(profile_key, []).copy(),
        "mastered_questions": [],
    }

    return session_id


def remember_questions(session: dict, questions: list[dict]):
    profile_key = session.get("profile_key")
    if not profile_key:
        return
    history = QUESTION_HISTORY_BY_PROFILE.setdefault(profile_key, [])
    for question in questions:
        text = question_text(question)
        if text and text not in history:
            history.append(text)
    session["question_history"] = history.copy()


def remember_mastered_question(session: dict, question: dict | str | None):
    text = question_text(question)
    if not text:
        return
    mastered = session.setdefault("mastered_questions", [])
    if text not in mastered:
        mastered.append(text)
    remember_questions(session, [{"text": text}])


def avoided_questions(session: dict) -> list[str]:
    current_questions = [question_text(question) for question in session.get("questions", [])]
    answered_questions = [question_text(answer.get("question_text")) for answer in session.get("answers", [])]
    return list(dict.fromkeys(
        item for item in [
            *session.get("question_history", []),
            *session.get("mastered_questions", []),
            *current_questions,
            *answered_questions,
        ] if item
    ))


def get_session(session_id: str):
    return SESSIONS.get(session_id)


def update_session(session_id: str, data: dict):
    if session_id in SESSIONS:
        SESSIONS[session_id].update(data)
        return True
    return False


def configure_session(session_id: str, config: dict):
    session = get_session(session_id)
    if not session:
        return None

    current = session.get("config", DEFAULT_CONFIG.copy()).copy()
    current.update({key: value for key, value in config.items() if value is not None})
    current["question_count"] = int(current.get("question_count") or SETTINGS.default_question_count)
    session["config"] = current
    return session


def _profile_key(resume_json, jd_json) -> str:
    payload = json.dumps({"resume": resume_json, "jd": jd_json}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
