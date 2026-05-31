import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from groq import Groq
from langchain_core.runnables import RunnableLambda

from app.settings import SETTINGS
from app.services.json_utils import clean_json_text, parse_json_object

load_dotenv()

DEFAULT_MODEL = SETTINGS.default_model


def _get_client() -> Groq:
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


@lru_cache(maxsize=8)
def build_llm_chain(model: str = DEFAULT_MODEL):
    async def groq_chat(payload: dict[str, Any]):
        messages = [
            {"role": "system", "content": str(payload.get("system_prompt", ""))},
            {"role": "user", "content": str(payload.get("user_prompt", ""))},
        ]
        response = _get_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=SETTINGS.llm_temperature,
            top_p=SETTINGS.llm_top_p,
        )
        return response.choices[0].message.content or ""

    return RunnableLambda(groq_chat)


def build_json_chain(fallback: Any, model: str = DEFAULT_MODEL):
    return build_llm_chain(model) | RunnableLambda(
        lambda raw: parse_json_object(clean_json_text(raw), fallback)
    )


async def call_llm(system_prompt, user_prompt, model=DEFAULT_MODEL):
    try:
        return await build_llm_chain(model).ainvoke(
            {"system_prompt": system_prompt, "user_prompt": user_prompt}
        )
    except Exception as e:
        print("Groq Error:", e)
        return "{}"


async def call_json_llm(system_prompt: str, user_prompt: str, fallback: Any, model=DEFAULT_MODEL) -> Any:
    try:
        return await build_json_chain(fallback, model).ainvoke(
            {"system_prompt": system_prompt, "user_prompt": user_prompt}
        )
    except Exception as e:
        print("Groq JSON chain error:", e)
        return fallback
