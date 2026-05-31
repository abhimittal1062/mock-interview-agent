import uuid


# In-memory session store. This is fine for local/demo mode; persistent storage
# should replace it before multi-user production deployment.
SESSIONS = {}


DEFAULT_CONFIG = {
    "interview_type": "mixed",
    "difficulty": "junior",
    "question_count": 5,
    "language": "cpp",
    "answer_mode": "voice",
}


def create_session(resume_json, jd_json):
    """
    Creates a new interview session with resume + job description parsed data.
    Stores full interview state in memory.
    """
    session_id = str(uuid.uuid4())

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
    }

    return session_id


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
    current["question_count"] = int(current.get("question_count") or 5)
    session["config"] = current
    return session
