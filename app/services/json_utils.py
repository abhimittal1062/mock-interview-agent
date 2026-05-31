import json
import re
from typing import Any


def clean_json_text(text: str) -> str:
    text = re.sub(r"```json", "", text or "", flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()


def parse_json_object(text: str, fallback: Any) -> Any:
    cleaned = clean_json_text(text)
    try:
        return json.loads(cleaned)
    except Exception:
        return fallback


def keyword_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        raw = re.split(r"[,;/\n]| and ", value, flags=re.IGNORECASE)
    elif isinstance(value, dict):
        raw = []
        for item in value.values():
            raw.extend(keyword_set(item))
    elif isinstance(value, (list, tuple, set)):
        raw = []
        for item in value:
            raw.extend(keyword_set(item))
    else:
        raw = [str(value)]

    keywords: set[str] = set()
    for item in raw:
        token = str(item).strip().lower()
        token = re.sub(r"[^a-z0-9+#.\s-]", "", token)
        token = re.sub(r"\s+", " ", token).strip()
        if len(token) >= 2:
            keywords.add(token)
    return keywords
