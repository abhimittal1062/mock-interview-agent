from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class InterviewSettings:
    default_model: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.85"))
    llm_top_p: float = float(os.getenv("LLM_TOP_P", "0.92"))
    followup_score_threshold: float = float(os.getenv("FOLLOWUP_SCORE_THRESHOLD", "0.55"))
    max_followups_per_question: int = int(os.getenv("MAX_FOLLOWUPS_PER_QUESTION", "3"))
    default_question_count: int = int(os.getenv("DEFAULT_QUESTION_COUNT", "5"))
    default_language: str = os.getenv("DEFAULT_CODING_LANGUAGE", "cpp")
    default_difficulty: str = os.getenv("DEFAULT_INTERVIEW_DIFFICULTY", "junior")
    default_interview_type: str = os.getenv("DEFAULT_INTERVIEW_TYPE", "mixed")
    fallback_question_text: str = "Question unavailable from the model. Ask the candidate to explain a relevant project and trade-offs."
    recording_policy: str = (
        "Recordings are downloaded by the browser for the user. Backend audio is temporary and deleted after transcription."
    )
    resource_links: dict[str, dict[str, str]] = field(
        default_factory=lambda: {
            "star": {"title": "STAR method practice", "url": "https://www.themuse.com/advice/star-interview-method"},
            "system_design": {
                "title": "System design primer",
                "url": "https://github.com/donnemartin/system-design-primer",
            },
            "dsa": {"title": "NeetCode practice roadmap", "url": "https://neetcode.io/roadmap"},
            "resume_keywords": {
                "title": "Resume keyword alignment guide",
                "url": "https://www.indeed.com/career-advice/resumes-cover-letters/resume-keywords",
            },
        }
    )


SETTINGS = InterviewSettings()
