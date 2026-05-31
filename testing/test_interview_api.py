from __future__ import annotations


def test_interview_api_happy_path(client, seeded_session):
    configure_response = client.post(
        "/api/configure-interview",
        data={
            "session_id": seeded_session,
            "interview_type": "technical",
            "difficulty": "mid",
            "question_count": 2,
            "language": "python",
            "answer_mode": "text",
        },
    )
    assert configure_response.status_code == 200
    assert configure_response.json()["config"] == {
        "interview_type": "technical",
        "difficulty": "mid",
        "question_count": 2,
        "language": "python",
        "answer_mode": "text",
    }

    start_response = client.post(
        "/api/start-interview",
        data={"session_id": seeded_session, "question_count": 2},
    )
    assert start_response.status_code == 200
    start_payload = start_response.json()
    assert start_payload["message"] == "Interview started"
    assert start_payload["total_questions"] == 2
    assert start_payload["first_question"]["text"] == "Mock interview question 1?"
    assert start_payload["ats_score"] == {"score": 82}

    question_response = client.post(
        "/api/get-question",
        data={"session_id": seeded_session},
    )
    assert question_response.status_code == 200
    question_payload = question_response.json()
    assert question_payload["type"] == "main"
    assert question_payload["index"] == 0
    assert question_payload["question"]["audio_url"].startswith("/api/question-audio?text=")

    answer_response = client.post(
        "/api/submit-answer",
        data={
            "session_id": seeded_session,
            "transcript": "I would clarify requirements, then discuss API and data tradeoffs.",
            "audio_filename": "answer-1.webm",
        },
    )
    assert answer_response.status_code == 200
    answer_payload = answer_response.json()
    assert answer_payload["type"] == "next_main_question"
    assert answer_payload["evaluation"]["combined_score"] == 0.89
    assert answer_payload["next_question"]["id"] == "question_2"

    audio_response = client.post(
        "/api/submit-answer-audio",
        data={"session_id": seeded_session, "audio_filename": "answer-2.webm"},
        files={"file": ("answer.webm", b"fake webm bytes", "audio/webm")},
    )
    assert audio_response.status_code == 200
    audio_payload = audio_response.json()
    assert audio_payload["type"] == "finished"

    report_response = client.post(
        "/api/final-report",
        data={"session_id": seeded_session},
    )
    assert report_response.status_code == 200
    report = report_response.json()["report"]
    assert report["session_id"] == seeded_session
    assert report["overall_score"] == 0.89
    assert report["ats"] == {"score": 82}
    assert len(report["questions"]) == 2
    assert report["questions"][1]["transcript"] == "Audio answer transcribed by fixture"


def test_invalid_session_errors(client):
    endpoints = [
        "/api/configure-interview",
        "/api/start-interview",
        "/api/get-question",
        "/api/submit-answer",
        "/api/final-report",
    ]

    for endpoint in endpoints:
        data = {"session_id": "missing"}
        if endpoint == "/api/submit-answer":
            data["transcript"] = "Answer"

        response = client.post(endpoint, data=data)
        assert response.status_code == 200
        assert response.json()["error"] == "Invalid session_id"


def test_invalid_interview_type_is_rejected(client, seeded_session):
    response = client.post(
        "/api/configure-interview",
        data={
            "session_id": seeded_session,
            "interview_type": "panel",
        },
    )

    assert response.status_code == 200
    assert response.json()["error"].startswith("Invalid interview_type")


def test_get_question_returns_done_after_last_answer(client, seeded_session):
    client.post(
        "/api/configure-interview",
        data={"session_id": seeded_session, "question_count": 1},
    )
    client.post(
        "/api/start-interview",
        data={"session_id": seeded_session, "question_count": 1},
    )
    client.post(
        "/api/submit-answer",
        data={"session_id": seeded_session, "transcript": "Concise answer."},
    )

    response = client.post("/api/get-question", data={"session_id": seeded_session})

    assert response.status_code == 200
    assert response.json() == {
        "type": "done",
        "message": "Interview completed. No more questions.",
    }


def test_dsa_configuration_accepts_code_submission(client, seeded_session):
    client.post(
        "/api/configure-interview",
        data={
            "session_id": seeded_session,
            "interview_type": "dsa",
            "language": "python",
            "question_count": 1,
        },
    )
    start_response = client.post(
        "/api/start-interview",
        data={"session_id": seeded_session, "question_count": 1},
    )
    assert start_response.json()["first_question"]["category"] == "dsa"

    run_response = client.post(
        "/api/run-code-samples",
        data={
            "session_id": seeded_session,
            "code": "int main(){return 0;}",
            "time_complexity": "O(n)",
            "space_complexity": "O(n)",
        },
    )
    assert run_response.status_code == 200
    run_payload = run_response.json()["run"]
    assert run_payload["result"]["ok"] is True
    assert run_payload["time_complexity"] == "O(n)"

    answer_response = client.post(
        "/api/submit-answer",
        data={
            "session_id": seeded_session,
            "transcript": "I would use a hash map for complements.",
            "code_submission": "def two_sum(nums, target): return []",
            "complexity_claim": "Time: O(n); Space: O(n)",
        },
    )

    payload = answer_response.json()
    assert payload["type"] == "followup"
    assert "followup" in payload
    assert payload["evaluation"]["code_evaluation"]["code_score"] == 0.84

    report = client.post("/api/final-report", data={"session_id": seeded_session}).json()["report"]
    assert report["coding_summary"]["total_sample_runs"] == 1
    assert report["coding_summary"]["passed_sample_runs"] == 1
    assert report["questions"][0]["code_attempts"] == 1
    assert report["questions"][0]["complexity_claim"] == "Time: O(n); Space: O(n)"
