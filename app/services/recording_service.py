from __future__ import annotations

import re
from datetime import datetime


def safe_filename(value: str | None, default: str) -> str:
    raw = value or default
    raw = re.sub(r"[^a-zA-Z0-9_.-]", "_", raw)
    raw = re.sub(r"_+", "_", raw).strip("._")
    return raw or default


def make_recording_filename(session_id: str, question_id: str, kind: str = "main", ext: str = "webm") -> str:
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    short_session = safe_filename(session_id, "session")[:8]
    safe_question = safe_filename(question_id, "question")[:32]
    safe_kind = safe_filename(kind, "main")
    return f"mock_interview_{short_session}_{stamp}_{safe_question}_{safe_kind}.{ext.lstrip('.')}"
