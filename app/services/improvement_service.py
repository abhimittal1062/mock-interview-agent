# app/services/improvement_service.py
import json

from .llm_client import call_json_llm

# load prompt
with open("app/prompts/improvement_plan.txt", "r", encoding="utf-8") as f:
    IMPROVEMENT_PROMPT = f.read()

async def generate_improvement_plan(session_summary: dict):
    """
    session_summary: dict with keys:
      - resume (parsed resume)
      - jd (parsed jd)
      - answers (list of {question_text, transcript, evaluation})
    Returns parsed JSON or fallback dict.
    """
    system_prompt = (
        "You are a concise career coach who outputs ONLY valid JSON following the schema in the prompt."
    )

    # Fill template
    user_prompt = IMPROVEMENT_PROMPT.replace("{{SESSION_SUMMARY}}", json.dumps(session_summary))

    return await call_json_llm(system_prompt, user_prompt, {"error": "Invalid JSON from model", "raw": ""})
