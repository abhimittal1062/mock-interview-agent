from __future__ import annotations

from statistics import mean

from app.settings import SETTINGS


def _score(answer: dict) -> float:
    evaluation = answer.get("evaluation") or {}
    if "combined_score" in evaluation:
        return float(evaluation.get("combined_score") or 0)
    if "code_evaluation" in evaluation:
        return float(evaluation["code_evaluation"].get("code_score") or 0)
    return 0.0


def build_final_report(session: dict) -> dict:
    answers = session.get("answers", [])
    code_runs = session.get("code_runs", [])
    total_questions = len(session.get("questions", []))
    answered_main_questions = len({answer.get("question_id") for answer in answers if not answer.get("is_followup")})
    remaining_questions = max(total_questions - int(session.get("current", 0)), 0)
    scores = [_score(answer) for answer in answers]
    avg_score = round(mean(scores), 4) if scores else 0.0

    weak_points: list[str] = []
    strong_points: list[str] = []
    missing_keywords: list[str] = []

    for answer in answers:
        evaluation = answer.get("evaluation") or {}
        weak_points.extend(evaluation.get("weaknesses") or [])
        strong_points.extend(evaluation.get("strengths") or [])
        missing_keywords.extend(evaluation.get("missing_keywords") or [])
        code_eval = evaluation.get("code_evaluation") or {}
        weak_points.extend(code_eval.get("followup_topics") or [])
        strong_points.extend(code_eval.get("correctness_notes") or [])

    weak_unique = list(dict.fromkeys(str(item) for item in weak_points if item))[:12]
    strong_unique = list(dict.fromkeys(str(item) for item in strong_points if item))[:12]
    missing_unique = list(dict.fromkeys(str(item) for item in missing_keywords if item))[:12]

    resources = _suggest_resources(session, weak_unique, missing_unique)

    question_reports = []
    for index, answer in enumerate(answers, start=1):
        evaluation = answer.get("evaluation") or {}
        question_code_runs = [
            run for run in code_runs
            if run.get("question_id") == answer.get("question_id")
        ]
        question_reports.append({
            "number": index,
            "question_id": answer.get("question_id"),
            "question_type": "followup" if answer.get("is_followup") else "main",
            "question_text": answer.get("question_text"),
            "transcript": answer.get("transcript"),
            "audio_filename": answer.get("audio_filename"),
            "code_submission": answer.get("code_submission"),
            "complexity_claim": answer.get("complexity_claim"),
            "code_runs": question_code_runs,
            "code_attempts": len(question_code_runs),
            "latest_code_run": question_code_runs[-1] if question_code_runs else None,
            "score": _score(answer),
            "feedback": evaluation.get("concise_feedback") or (evaluation.get("code_evaluation") or {}).get("concise_feedback"),
            "evaluated_complexity": (evaluation.get("code_evaluation") or {}).get("complexity"),
            "missing_keywords": evaluation.get("missing_keywords", []),
        })

    coding_summary = summarize_code_runs(code_runs)

    report = {
        "session_id": session.get("session_id"),
        "status": session.get("status", "unknown"),
        "ended_reason": session.get("ended_reason"),
        "ended_at": session.get("ended_at"),
        "progress": {
            "answered_items": len(answers),
            "answered_main_questions": answered_main_questions,
            "total_main_questions": total_questions,
            "remaining_main_questions": remaining_questions,
            "followup_count_current_question": session.get("followup_count", 0),
        },
        "interview_config": session.get("config", {}),
        "overall_score": avg_score,
        "ats": session.get("ats_score"),
        "coding_summary": coding_summary,
        "good_points": strong_unique,
        "weak_points": weak_unique,
        "missing_keywords": missing_unique,
        "resources": resources,
        "questions": question_reports,
        "recording_policy": SETTINGS.recording_policy,
    }
    session["final_report"] = report
    return report


def summarize_code_runs(code_runs: list[dict]) -> dict:
    total = len(code_runs)
    passed = sum(1 for run in code_runs if (run.get("result") or {}).get("ok"))
    elapsed_ms = sum(int((run.get("result") or {}).get("elapsed_ms") or 0) for run in code_runs)
    by_question: dict[str, dict] = {}

    for run in code_runs:
        qid = str(run.get("question_id") or "unknown")
        item = by_question.setdefault(qid, {
            "question_id": qid,
            "runs": 0,
            "passed_runs": 0,
            "last_status": None,
            "time_complexity": None,
            "space_complexity": None,
            "elapsed_ms": 0,
        })
        result = run.get("result") or {}
        item["runs"] += 1
        item["passed_runs"] += 1 if result.get("ok") else 0
        item["last_status"] = result.get("status")
        item["time_complexity"] = run.get("time_complexity") or item["time_complexity"]
        item["space_complexity"] = run.get("space_complexity") or item["space_complexity"]
        item["elapsed_ms"] += int(result.get("elapsed_ms") or 0)

    return {
        "total_sample_runs": total,
        "passed_sample_runs": passed,
        "failed_sample_runs": total - passed,
        "total_elapsed_ms": elapsed_ms,
        "by_question": list(by_question.values()),
    }


def _suggest_resources(session: dict, weak_points: list[str], missing_keywords: list[str]) -> list[dict]:
    config = session.get("config", {})
    interview_type = config.get("interview_type", "mixed")
    resources = [
        SETTINGS.resource_links["star"],
        SETTINGS.resource_links["system_design"],
    ]
    if interview_type in {"dsa", "mixed"} or any("complexity" in item.lower() for item in weak_points):
        resources.append(SETTINGS.resource_links["dsa"])
    if missing_keywords:
        resources.append(SETTINGS.resource_links["resume_keywords"])
    return resources[:6]
