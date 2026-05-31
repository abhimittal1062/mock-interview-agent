from __future__ import annotations

import re
from typing import Iterable


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "to", "of", "in", "on", "for", "with",
    "your", "you", "how", "what", "why", "when", "where", "explain", "describe",
    "tell", "about", "can", "could", "would", "should", "is", "are", "be",
}


def question_text(question: dict | str | None) -> str:
    if question is None:
        return ""
    if isinstance(question, str):
        return question
    return str(question.get("text") or question.get("title") or "")


def normalized_question_key(text: str) -> str:
    return " ".join(_tokens(text))


def is_similar_question(candidate: str, existing: str, threshold: float = 0.72) -> bool:
    candidate_tokens = set(_tokens(candidate))
    existing_tokens = set(_tokens(existing))
    if not candidate_tokens or not existing_tokens:
        return False
    overlap = len(candidate_tokens & existing_tokens) / max(min(len(candidate_tokens), len(existing_tokens)), 1)
    return overlap >= threshold


def is_duplicate_question(candidate: str, existing_questions: Iterable[str | dict]) -> bool:
    candidate_key = normalized_question_key(candidate)
    for existing in existing_questions:
        existing_text = question_text(existing)
        if not existing_text:
            continue
        if candidate_key == normalized_question_key(existing_text):
            return True
        if is_similar_question(candidate, existing_text):
            return True
    return False


def unique_questions(questions: list[dict], avoid_questions: Iterable[str | dict]) -> list[dict]:
    accepted: list[dict] = []
    blocked = list(avoid_questions)
    for question in questions:
        text = question_text(question)
        if text and not is_duplicate_question(text, [*blocked, *accepted]):
            accepted.append(question)
    return accepted


def _tokens(text: str) -> list[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9+#.\s-]", " ", text.lower())
    return [token for token in re.split(r"\s+", cleaned) if len(token) > 2 and token not in STOP_WORDS]
