from .llm_client import call_json_llm

# Load prompts
with open("app/prompts/resume_parser.txt", "r", encoding="utf-8") as f:
    RESUME_PROMPT = f.read()

with open("app/prompts/jd_parser.txt", "r", encoding="utf-8") as f:
    JD_PROMPT = f.read()

async def parse_resume(text: str):
    system_prompt = (
        "You are a strict resume parser. "
        "Return ONLY valid JSON. "
        "DO NOT wrap in ```json fences. "
        "No explanation text."
    )

    user_prompt = RESUME_PROMPT.replace("{{RESUME_TEXT}}", text)
    return await call_json_llm(system_prompt, user_prompt, {"error": "Invalid JSON", "raw": ""})


async def parse_jd(text: str):
    system_prompt = (
        "You are a strict job description parser. "
        "Return ONLY valid JSON with no code fences."
    )

    user_prompt = JD_PROMPT.replace("{{JD_TEXT}}", text)
    return await call_json_llm(system_prompt, user_prompt, {"error": "Invalid JSON", "raw": ""})
