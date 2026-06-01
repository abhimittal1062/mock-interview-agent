from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parent
DATASETS = ROOT / "datasets"


def read_csv(name: str) -> list[dict]:
    path = DATASETS / name
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def to_bool(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed", "relevant", "good"}


def label_from_score(score: float, threshold: float = 0.60) -> str:
    return "good" if score >= threshold else "weak"


def answer_eval_metrics() -> dict:
    rows = read_csv("answer_eval.csv")
    rows = [r for r in rows if r.get("human_label") and r.get("app_score")]

    if not rows:
        return {"status": "no_data"}

    correct = 0
    abs_errors = []

    for r in rows:
        human_label = str(r["human_label"]).strip().lower()
        human_score = to_float(r.get("human_score", ""))
        app_score = to_float(r["app_score"])
        app_label = label_from_score(app_score)

        if human_label == app_label:
            correct += 1

        if r.get("human_score"):
            abs_errors.append(abs(human_score - app_score))

    result = {
        "sample_size": len(rows),
        "agreement_accuracy": round(correct / len(rows), 4),
        "agreement_percent": round((correct / len(rows)) * 100, 2),
        "threshold_used": 0.60,
    }

    if abs_errors:
        result["mae"] = round(mean(abs_errors), 4)

    return result


def question_relevance_metrics() -> dict:
    rows = read_csv("question_relevance.csv")
    rows = [r for r in rows if r.get("relevance_score")]

    if not rows:
        return {"status": "no_data"}

    scores = [to_float(r["relevance_score"]) for r in rows]
    relevant = [s for s in scores if s >= 4.0]

    return {
        "sample_size": len(rows),
        "average_relevance_1_to_5": round(mean(scores), 3),
        "highly_relevant_rate_percent": round((len(relevant) / len(scores)) * 100, 2),
        "rubric": "1=irrelevant, 3=somewhat relevant, 5=highly relevant",
    }


def followup_metrics() -> dict:
    rows = read_csv("followup_eval.csv")
    rows = [r for r in rows if r.get("followup_relevant")]

    if not rows:
        return {"status": "no_data"}

    relevant = sum(1 for r in rows if to_bool(r["followup_relevant"]))

    return {
        "sample_size": len(rows),
        "followup_relevance_percent": round((relevant / len(rows)) * 100, 2),
    }


def word_distance(reference_words: list[str], predicted_words: list[str]) -> int:
    n = len(reference_words)
    m = len(predicted_words)

    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(n + 1):
        dp[i][0] = i

    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if reference_words[i - 1] == predicted_words[j - 1]:
                cost = 0
            else:
                cost = 1

            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )

    return dp[n][m]


def normalize_words(text: str) -> list[str]:
    cleaned = (
        text.lower()
        .replace(",", "")
        .replace(".", "")
        .replace("?", "")
        .replace("!", "")
        .replace(":", "")
        .replace(";", "")
    )
    return [w for w in cleaned.split() if w.strip()]


def stt_metrics() -> dict:
    rows = read_csv("stt_eval.csv")
    rows = [r for r in rows if r.get("reference_transcript") and r.get("whisper_transcript")]

    if not rows:
        return {"status": "no_data"}

    wers = []

    for r in rows:
        ref_words = normalize_words(r["reference_transcript"])
        hyp_words = normalize_words(r["whisper_transcript"])

        if not ref_words:
            continue

        dist = word_distance(ref_words, hyp_words)
        wer = dist / len(ref_words)
        wers.append(wer)

    if not wers:
        return {"status": "no_valid_rows"}

    return {
        "sample_size": len(wers),
        "average_wer": round(mean(wers), 4),
        "average_wer_percent": round(mean(wers) * 100, 2),
        "note": "Lower WER is better",
    }


def code_runner_metrics() -> dict:
    rows = read_csv("code_runner_eval.csv")
    rows = [r for r in rows if r.get("expected_pass") and r.get("actual_pass")]

    if not rows:
        return {"status": "no_data"}

    correct = 0

    for r in rows:
        expected = to_bool(r["expected_pass"])
        actual = to_bool(r["actual_pass"])

        if expected == actual:
            correct += 1

    return {
        "sample_size": len(rows),
        "pass_fail_accuracy_percent": round((correct / len(rows)) * 100, 2),
    }


def main():
    results = {
        "answer_evaluation": answer_eval_metrics(),
        "question_relevance": question_relevance_metrics(),
        "followup_quality": followup_metrics(),
        "stt_transcription": stt_metrics(),
        "code_runner": code_runner_metrics(),
    }

    print(json.dumps(results, indent=2))

    print("\nResume-safe summary:")
    answer = results["answer_evaluation"]
    question = results["question_relevance"]
    followup = results["followup_quality"]
    stt = results["stt_transcription"]
    code = results["code_runner"]

    if answer.get("agreement_percent"):
        print(
            f"- Validated answer evaluation on {answer['sample_size']} labeled responses, "
            f"achieving {answer['agreement_percent']}% good/weak agreement"
            + (f" and {answer['mae']} MAE." if answer.get("mae") is not None else ".")
        )

    if question.get("average_relevance_1_to_5"):
        print(
            f"- Evaluated question generation across {question['sample_size']} generated questions, "
            f"achieving {question['average_relevance_1_to_5']}/5 average resume/JD relevance."
        )

    if followup.get("followup_relevance_percent"):
        print(
            f"- Measured adaptive follow-up quality on {followup['sample_size']} weak-answer cases, "
            f"achieving {followup['followup_relevance_percent']}% relevance."
        )

    if stt.get("average_wer_percent"):
        print(
            f"- Measured Whisper STT quality on {stt['sample_size']} audio samples, "
            f"achieving {stt['average_wer_percent']}% average WER."
        )

    if code.get("pass_fail_accuracy_percent"):
        print(
            f"- Validated C++ sample-test runner on {code['sample_size']} known submissions, "
            f"achieving {code['pass_fail_accuracy_percent']}% pass/fail classification accuracy."
        )


if __name__ == "__main__":
    main()
