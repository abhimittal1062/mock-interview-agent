from app.services.evaluator_model import (
    generate_ideal_answer,
    compute_semantic_similarity,
    compute_bert_f1
)
from app.services.llm_client import call_json_llm


async def evaluate_answer(question_text: str, user_answer: str):
    
    ideal_answer = await generate_ideal_answer(question_text)


    if not ideal_answer or len(ideal_answer.strip()) < 3:
        ideal_answer = "The ideal answer was unavailable due to LLM error."

    semantic_score = compute_semantic_similarity(user_answer, ideal_answer)
    bert_f1 = compute_bert_f1(user_answer, ideal_answer)

    combined_score = round((semantic_score + bert_f1) / 2, 4)

    system_msg = (
        "You are an interview evaluator. "
        "Provide constructive feedback in VALID JSON only. "
        "No markdown, no backticks."
    )

    user_prompt = f"""
Evaluate this interview answer.

QUESTION:
{question_text}

IDEAL ANSWER:
{ideal_answer}

USER ANSWER:
{user_answer}

Return a JSON object with exactly these keys:
- strengths: list of strings
- weaknesses: list of strings
- missing_keywords: list of important terms that were not mentioned
- concise_feedback: a short paragraph (2–3 sentences)
"""

    qualitative = await call_json_llm(
        system_msg,
        user_prompt,
        {
            "strengths": [],
            "weaknesses": ["Evaluation failed. Model returned invalid JSON."],
            "missing_keywords": [],
            "concise_feedback": "Evaluation failed. Model returned invalid JSON.",
        },
    )


    evaluation = {
        "ideal_answer": ideal_answer,
        "semantic_score": semantic_score,
        "bert_f1": bert_f1,
        "combined_score": combined_score,
        **qualitative
    }

    return evaluation
