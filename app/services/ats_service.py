from __future__ import annotations

import re
from typing import Any

from app.services.json_utils import keyword_set


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_flatten_text(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_text(v) for v in value)
    return str(value)


def _extract_resume_skills(resume: dict) -> set[str]:
    likely_keys = ("skills", "technical_skills", "tools", "technologies", "languages")
    values = []
    for key, value in resume.items():
        if any(part in key.lower() for part in likely_keys):
            values.append(value)
    values.append(_flatten_text(resume))
    return keyword_set(values)


def _extract_jd_keywords(jd: dict) -> set[str]:
    likely_keys = (
        "skills",
        "requirements",
        "responsibilities",
        "qualifications",
        "must_have",
        "preferred",
        "technologies",
    )
    values = []
    for key, value in jd.items():
        if any(part in key.lower() for part in likely_keys):
            values.append(value)
    values.append(_flatten_text(jd))
    return keyword_set(values)


def _has_metric(text: str) -> bool:
    return bool(re.search(r"\b(\d+%|\d+x|\d+\+|\d+\s*(users|requests|ms|sec|seconds|hrs|hours|months|years))\b", text, re.I))


def score_resume_against_jd(resume: dict, jd: dict) -> dict:
    resume_text = _flatten_text(resume).lower()
    jd_text = _flatten_text(jd).lower()
    resume_skills = _extract_resume_skills(resume)
    jd_keywords = _extract_jd_keywords(jd)

    stop = {
        "and", "the", "for", "with", "you", "are", "will", "can", "our", "from",
        "this", "that", "have", "has", "job", "role", "team", "work", "good",
    }
    jd_keywords = {k for k in jd_keywords if k not in stop and len(k) > 2}

    matched = sorted(k for k in jd_keywords if k in resume_text or k in resume_skills)
    missing = sorted(k for k in jd_keywords if k not in matched)

    coverage = len(matched) / max(len(jd_keywords), 1)
    skill_score = round(min(30, coverage * 30), 1)
    keyword_score = round(min(20, coverage * 20), 1)

    project_terms = ("project", "built", "developed", "implemented", "designed", "deployed")
    project_score = 20 if any(term in resume_text for term in project_terms) else 10
    role_score = 10 if any(token in resume_text for token in jd_text.split()[:80] if len(token) > 5) else 5
    impact_score = 10 if _has_metric(resume_text) else 4
    formatting_score = 10 if len(resume_text) > 600 and len(resume_text.splitlines()) < 140 else 6

    total = round(skill_score + keyword_score + project_score + role_score + impact_score + formatting_score)
    total = max(0, min(100, total))

    suggestions = []
    if missing[:8]:
        suggestions.append("Add truthful evidence for missing JD keywords: " + ", ".join(missing[:8]))
    if impact_score < 10:
        suggestions.append("Rewrite project bullets with measurable impact, scale, latency, accuracy, or business outcome.")
    if project_score < 20:
        suggestions.append("Add stronger project descriptions tied to the target role requirements.")
    if formatting_score < 10:
        suggestions.append("Keep resume sections concise and ATS-readable with clear headings and simple formatting.")

    return {
        "score": total,
        "rubric": {
            "skills_match": skill_score,
            "jd_keyword_coverage": keyword_score,
            "experience_project_relevance": project_score,
            "role_alignment": role_score,
            "measurable_impact": impact_score,
            "formatting_readability": formatting_score,
        },
        "matched_keywords": matched[:30],
        "missing_keywords": missing[:30],
        "suggestions": suggestions,
        "note": "This is an interview-prep ATS approximation, not a guarantee from any specific ATS product.",
    }
