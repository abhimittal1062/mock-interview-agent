import json
import re
import uuid
from .llm_client import call_llm

# Load prompt template
with open("app/prompts/question_gen.txt", "r", encoding="utf-8") as f:
    QUESTION_PROMPT = f.read()


def clean_json(text: str):
    """
    Remove markdown fences (```json ... ```).
    """
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()


async def generate_questions(
    resume_json: dict,
    jd_json: dict,
    count: int = 5,
    interview_type: str = "mixed",
    difficulty: str = "junior",
):
    """
    Generate EXACTLY N questions using LLM.
    Ensures every question has:
      - id
      - category
      - text
      - expected_points
      - audio_url (default None)
    And guarantees safe fallback for malformed or partial JSON.
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
        "Return ONLY valid JSON. No markdown, no code fences."
    )

    user_prompt = (
        QUESTION_PROMPT
            .replace("{{RESUME_JSON}}", json.dumps(resume_json))
            .replace("{{JD_JSON}}", json.dumps(jd_json))
            .replace("{{COUNT}}", str(count))
            + f"\n\nMode guidance: {mode_guidance}\nDifficulty: {difficulty}\n"
    )

    # 🔹 Call LLM
    response = await call_llm(system_prompt, user_prompt)
    cleaned = clean_json(response)

    try:
        data = json.loads(cleaned)
    except Exception as e:
        print("❌ LLM returned invalid JSON for question generation:", e)
        # Fallback: produce all placeholder questions
        return [
            {
                "id": str(uuid.uuid4()),
                "category": interview_type,
                "text": "Placeholder question (LLM JSON parse failed).",
                "expected_points": [],
                "audio_url": None
            }
            for _ in range(count)
        ]

    # 🔹 Ensure list
    if isinstance(data, dict):
        data = [data]

    # 🔹 Validate each question object
    validated = []
    for q in data:
        validated.append({
            "id": q.get("id") or str(uuid.uuid4()),
            "category": q.get("category", interview_type),
            "text": q.get("text") or "Placeholder question (missing text from LLM).",
            "expected_points": q.get("expected_points", []),
            "audio_url": None
        })

    # 🔹 Pad with placeholders if fewer than count
    if len(validated) < count:
        print(f"⚠ WARNING: LLM returned only {len(validated)} questions, expected {count}. Filling with placeholders.")
        while len(validated) < count:
            validated.append({
                "id": str(uuid.uuid4()),
                "category": interview_type,
                "text": "Placeholder question (LLM rate-limited).",
                "expected_points": [],
                "audio_url": None
            })

    # 🔹 Trim if more than required
    if len(validated) > count:
        validated = validated[:count]

    return validated
