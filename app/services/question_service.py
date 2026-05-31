import json
import uuid
from itertools import islice, repeat

from app.services.question_history import unique_questions

from .llm_client import call_json_llm


with open("app/prompts/question_gen.txt", "r", encoding="utf-8") as f:
    QUESTION_PROMPT = f.read()


async def generate_questions(
    resume_json: dict,
    jd_json: dict,
    count: int = 5,
    interview_type: str = "mixed",
    difficulty: str = "junior",
    avoid_questions: list[str] | None = None,
):
    """
    Generate a batch of interview questions through the LangChain LLM chain.
    Batch generation keeps the planning node graph-driven instead of manually
    looping over individual question calls.
    """
    mode_guidance = {
        "hr": "Ask HR and behavioral questions using the resume and JD. Prefer STAR-format, motivation, teamwork, conflict, ownership, and culture-fit questions.",
        "technical": "Ask technical resume-based questions from projects, skills, internships, and JD requirements.",
        "system_design": "Ask system design questions connected to the candidate projects and JD. Cover APIs, storage, scale, caching, observability, tradeoffs, and failure modes.",
        "mixed": "Ask a balanced mix of HR, technical, resume-based, and JD-aligned questions.",
    }.get(interview_type, "Ask a balanced mix of interview questions.")

    system_prompt = (
        "You are an expert interviewer. "
        f"Interview type: {interview_type}. Difficulty: {difficulty}. "
        f"{mode_guidance} "
        "Prioritize questions that teach or reveal a new competency. "
        "Do not repeat, paraphrase, or lightly reword already asked or mastered questions. "
        "Return ONLY valid JSON. No markdown, no code fences."
    )

    avoid_block = "\n".join(f"- {item}" for item in (avoid_questions or [])[-30:]) or "- None"
    user_prompt = (
        QUESTION_PROMPT
        .replace("{{RESUME_JSON}}", json.dumps(resume_json))
        .replace("{{JD_JSON}}", json.dumps(jd_json))
        .replace("{{COUNT}}", str(count))
        + f"""

Mode guidance: {mode_guidance}
Difficulty: {difficulty}

Already asked or mastered questions to avoid:
{avoid_block}

Diversity requirements:
- Do not ask two questions that test the same exact skill or project detail.
- Prefer fresh angles: implementation detail, debugging, trade-off, scale, failure mode, metrics, ownership, and JD-specific validation.
- If a previous answer was satisfactory, move to a new competency instead of asking the same topic again.
"""
    )

    data = await call_json_llm(system_prompt, user_prompt, [])
    return normalize_question_batch(data, count, interview_type, avoid_questions or [])


def normalize_question_batch(data, count: int, interview_type: str, avoid_questions: list[str] | None = None) -> list[dict]:
    rows = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
    normalized = list(map(lambda question: normalize_question(question, interview_type), rows))
    unique = unique_questions(normalized, avoid_questions or [])
    placeholders_needed = max(count - len(unique), 0)
    placeholders = list(islice(repeat(None), placeholders_needed))
    return (unique + list(map(lambda _: placeholder_question(interview_type), placeholders)))[:count]


def normalize_question(question: dict, interview_type: str) -> dict:
    return {
        "id": question.get("id") or str(uuid.uuid4()),
        "category": question.get("category", interview_type),
        "text": question.get("text") or "Placeholder question (missing text from LLM).",
        "expected_points": question.get("expected_points", []),
        "audio_url": None,
    }


def placeholder_question(interview_type: str) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "category": interview_type,
        "text": "Placeholder question (LLM returned fewer questions than requested).",
        "expected_points": [],
        "audio_url": None,
    }
