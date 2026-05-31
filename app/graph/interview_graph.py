from __future__ import annotations

from app.graph.state import InterviewState
from app.services.ats_service import score_resume_against_jd
from app.services.coding_service import evaluate_code_answer, generate_coding_problem
from app.services.evaluator_service import evaluate_answer
from app.services.followup_service import generate_followup
from app.services.question_service import generate_questions

try:
    from langgraph.graph import END, StateGraph
except Exception:
    END = None
    StateGraph = None


FOLLOWUP_SCORE_THRESHOLD = 0.55


async def _ats_node(state: InterviewState) -> InterviewState:
    state["ats_score"] = score_resume_against_jd(state["resume"], state["jd"])
    return state


async def _plan_node(state: InterviewState) -> InterviewState:
    config = state["config"]
    interview_type = config.get("interview_type", "mixed")
    count = int(config.get("question_count", 5))
    difficulty = config.get("difficulty", "junior")
    language = config.get("language", "cpp")

    if interview_type == "dsa":
        problems = []
        for _ in range(count):
            problems.append(await generate_coding_problem(state["resume"], state["jd"], difficulty, language))
        state["questions"] = problems
        return state

    questions = await generate_questions(state["resume"], state["jd"], count, interview_type, difficulty)
    for question in questions:
        question["interview_type"] = interview_type
        if interview_type == "system_design":
            question["category"] = "system_design"
        elif interview_type == "hr":
            question["category"] = "hr"
    state["questions"] = questions
    return state


def _build_setup_graph():
    if StateGraph is None:
        return None
    graph = StateGraph(InterviewState)
    graph.add_node("ats", _ats_node)
    graph.add_node("plan", _plan_node)
    graph.set_entry_point("ats")
    graph.add_edge("ats", "plan")
    graph.add_edge("plan", END)
    return graph.compile()


_SETUP_GRAPH = _build_setup_graph()


async def initialize_interview(session: dict, config: dict) -> dict:
    state: InterviewState = {
        "session": session,
        "session_id": session["session_id"],
        "resume": session["resume"],
        "jd": session["jd"],
        "config": config,
    }
    if _SETUP_GRAPH is not None:
        state = await _SETUP_GRAPH.ainvoke(state)
    else:
        state = await _ats_node(state)
        state = await _plan_node(state)

    session["config"] = config
    session["ats_score"] = state["ats_score"]
    session["questions"] = state["questions"]
    session["current"] = 0
    session["answers"] = []
    session["followup_pending"] = None
    session["followup_count"] = 0
    return session


async def _evaluate_node(state: InterviewState) -> InterviewState:
    evaluation = await evaluate_answer(state["question_text"], state["transcript"])
    if state.get("code_submission"):
        problem = state.get("current_question") or {"text": state["question_text"]}
        sample_runs = _current_question_code_runs(state["session"], state["question_id"])
        evaluation["code_evaluation"] = await evaluate_code_answer(
            problem,
            state["code_submission"] or "",
            state["transcript"],
            state.get("complexity_claim"),
            sample_runs,
        )
    state["evaluation"] = evaluation
    return state


def _needs_followup(state: InterviewState) -> str:
    session = state["session"]
    evaluation = state.get("evaluation", {})
    combined_score = evaluation.get("combined_score", 0.0)
    code_score = (evaluation.get("code_evaluation") or {}).get("code_score")
    code_eval = evaluation.get("code_evaluation") or {}
    if code_score is not None:
        combined_score = min(float(combined_score or 0.0), float(code_score))
    missing_keywords = evaluation.get("missing_keywords", []) or []
    current_qid = state.get("question_id")
    sample_runs = _current_question_code_runs(session, current_qid)
    has_failed_sample_run = any(not ((run.get("result") or {}).get("ok")) for run in sample_runs)

    if session.get("followup_count", 0) >= 3:
        return "advance"
    if state.get("code_submission") and not state.get("complexity_claim"):
        return "followup"
    if has_failed_sample_run:
        return "followup"
    if code_eval.get("complexity_questions") or code_eval.get("followup_topics"):
        return "followup"
    if combined_score < FOLLOWUP_SCORE_THRESHOLD:
        return "followup"
    if len(missing_keywords) >= 2:
        return "followup"
    return "advance"


async def _followup_node(state: InterviewState) -> InterviewState:
    session = state["session"]
    answer_record = _answer_record(state)
    session["answers"].append(answer_record)

    base_question = state["question_text"]
    if state.get("is_followup") and session.get("current", 0) < len(session.get("questions", [])):
        base_question = session["questions"][session["current"]].get("text", base_question)

    followup_answer_context = _build_followup_answer_context(state)
    new_followup = (await generate_followup(base_question, followup_answer_context)).get("followup")
    if new_followup:
        session["followup_pending"] = new_followup
        session["followup_count"] = session.get("followup_count", 0) + 1
        state["result"] = {
            "type": "followup",
            "evaluation": state["evaluation"],
            "followup": new_followup,
            "followup_count": session["followup_count"],
        }
    else:
        state = await _advance_node(state)
    return state


async def _advance_node(state: InterviewState) -> InterviewState:
    session = state["session"]
    session["answers"].append(_answer_record(state))
    session["followup_pending"] = None
    session["followup_count"] = 0
    session["current"] = session.get("current", 0) + 1

    if session["current"] >= len(session.get("questions", [])):
        state["result"] = {"type": "finished", "evaluation": state["evaluation"]}
    else:
        state["result"] = {
            "type": "next_main_question",
            "evaluation": state["evaluation"],
            "next_question": session["questions"][session["current"]],
        }
    return state


def _answer_record(state: InterviewState) -> dict:
    return {
        "question_id": state["question_id"],
        "is_followup": state.get("is_followup", False),
        "question_text": state["question_text"],
        "transcript": state["transcript"],
        "audio_filename": state.get("audio_filename"),
        "code_submission": state.get("code_submission"),
        "complexity_claim": state.get("complexity_claim"),
        "evaluation": state["evaluation"],
    }


def _current_question_code_runs(session: dict, question_id: str | None) -> list[dict]:
    if not question_id:
        return []
    return [
        run for run in session.get("code_runs", [])
        if run.get("question_id") == question_id
    ]


def _build_followup_answer_context(state: InterviewState) -> str:
    parts = [state.get("transcript") or ""]
    if state.get("code_submission"):
        sample_runs = _current_question_code_runs(state["session"], state.get("question_id"))
        code_eval = (state.get("evaluation") or {}).get("code_evaluation") or {}
        parts.append("\nCANDIDATE_CODE:\n" + (state.get("code_submission") or ""))
        parts.append("\nCANDIDATE_COMPLEXITY_CLAIM:\n" + (state.get("complexity_claim") or "Not provided"))
        parts.append("\nSAMPLE_RUN_HISTORY:\n" + str(sample_runs))
        parts.append("\nCODE_EVALUATION:\n" + str(code_eval))
        parts.append(
            "\nFOLLOW-UP REQUIREMENT: Ask about time complexity, space complexity, optimization, hidden edge cases, or failed sample tests. Make it one specific interviewer question."
        )
    return "\n".join(parts)


def _build_answer_graph():
    if StateGraph is None:
        return None
    graph = StateGraph(InterviewState)
    graph.add_node("evaluate", _evaluate_node)
    graph.add_node("followup", _followup_node)
    graph.add_node("advance", _advance_node)
    graph.set_entry_point("evaluate")
    graph.add_conditional_edges("evaluate", _needs_followup, {"followup": "followup", "advance": "advance"})
    graph.add_edge("followup", END)
    graph.add_edge("advance", END)
    return graph.compile()


_ANSWER_GRAPH = _build_answer_graph()


async def process_answer(
    session: dict,
    transcript: str,
    audio_filename: str | None = None,
    code_submission: str | None = None,
    complexity_claim: str | None = None,
) -> dict:
    is_followup = bool(session.get("followup_pending"))
    if is_followup:
        question_text = session["followup_pending"]
        question_id = f"followup_{session.get('followup_count', 0)}"
        question_obj = None
    else:
        idx = session.get("current", 0)
        if idx >= len(session.get("questions", [])):
            return {"type": "finished", "message": "Interview complete."}
        question_obj = session["questions"][idx]
        question_text = question_obj.get("text") or question_obj.get("title") or "Coding problem"
        question_id = question_obj.get("id", f"question_{idx + 1}")

    state: InterviewState = {
        "session": session,
        "current_question": question_obj or {},
        "question_text": question_text,
        "question_id": question_id,
        "transcript": transcript,
        "audio_filename": audio_filename,
        "code_submission": code_submission,
        "complexity_claim": complexity_claim,
        "is_followup": is_followup,
    }

    if _ANSWER_GRAPH is not None:
        state = await _ANSWER_GRAPH.ainvoke(state)
    else:
        state = await _evaluate_node(state)
        if _needs_followup(state) == "followup":
            state = await _followup_node(state)
        else:
            state = await _advance_node(state)
    return state["result"]
