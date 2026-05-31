from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


class _Scalar:
    def __init__(self, value: float):
        self.value = value

    def item(self) -> float:
        return self.value


class _Vector:
    def __init__(self, value: float):
        self.value = value

    def __getitem__(self, index: int) -> _Scalar:
        return _Scalar(self.value)


def _install_ai_dependency_fakes() -> None:
    """Install import-time fakes for optional/heavy AI packages."""

    groq = types.ModuleType("groq")

    class FakeGroq:
        def __init__(self, *args, **kwargs):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=self._create)
            )

        def _create(self, *args, **kwargs):
            message = types.SimpleNamespace(content='{"ok": true}')
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])

    groq.Groq = FakeGroq
    sys.modules.setdefault("groq", groq)

    whisper = types.ModuleType("whisper")

    class FakeWhisperModel:
        def transcribe(self, path: str) -> dict[str, str]:
            return {"text": "transcribed answer from fake whisper"}

    whisper.load_model = lambda *args, **kwargs: FakeWhisperModel()
    sys.modules.setdefault("whisper", whisper)

    sentence_transformers = types.ModuleType("sentence_transformers")

    class FakeSentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass

        def encode(self, text: str, convert_to_tensor: bool = False):
            return text

    sentence_transformers.SentenceTransformer = FakeSentenceTransformer
    sentence_transformers.util = types.SimpleNamespace(
        cos_sim=lambda left, right: _Scalar(0.88)
    )
    sys.modules.setdefault("sentence_transformers", sentence_transformers)

    bert_score = types.ModuleType("bert_score")
    bert_score.score = lambda *args, **kwargs: (None, None, _Vector(0.86))
    sys.modules.setdefault("bert_score", bert_score)

    torch = types.ModuleType("torch")
    sys.modules.setdefault("torch", torch)

    gtts = types.ModuleType("gtts")

    class FakeGTTS:
        def __init__(self, text: str, lang: str = "en"):
            self.text = text
            self.lang = lang

        def save(self, file_path: str) -> None:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            Path(file_path).write_bytes(b"fake mp3")

    gtts.gTTS = FakeGTTS
    sys.modules.setdefault("gtts", gtts)

    imageio_ffmpeg = types.ModuleType("imageio_ffmpeg")
    imageio_ffmpeg.get_ffmpeg_exe = lambda: str(PROJECT_ROOT / "testing" / "ffmpeg")
    sys.modules.setdefault("imageio_ffmpeg", imageio_ffmpeg)


_install_ai_dependency_fakes()


@pytest.fixture(autouse=True)
def reset_sessions():
    from app.services.session_manager import SESSIONS

    SESSIONS.clear()
    yield
    SESSIONS.clear()


@pytest.fixture
def app(monkeypatch):
    from app.graph import interview_graph
    from app.routes import answer_audio, coding
    from app.main import app as fastapi_app

    async def fake_generate_questions(
        resume_json: dict,
        jd_json: dict,
        count: int = 5,
        *args,
        **kwargs,
    ):
        return [
            {
                "id": f"question_{index}",
                "category": "technical",
                "text": f"Mock interview question {index}?",
                "expected_points": ["clarity", "tradeoffs"],
                "audio_url": None,
            }
            for index in range(1, count + 1)
        ]

    async def fake_generate_coding_problem(resume_json, jd_json, difficulty, language):
        return {
            "id": "coding_1",
            "category": "dsa",
            "title": "Two Sum",
            "text": f"Solve Two Sum in {language}.",
            "expected_points": ["hash map", "complexity"],
        }

    async def fake_evaluate_answer(question_text: str, user_answer: str):
        return {
            "ideal_answer": "A structured answer that covers tradeoffs.",
            "semantic_score": 0.9,
            "bert_f1": 0.88,
            "combined_score": 0.89,
            "strengths": ["Clear structure"],
            "weaknesses": ["Add more metrics"],
            "missing_keywords": ["latency"],
            "concise_feedback": "Good structure. Add concrete constraints and metrics.",
        }

    async def fake_generate_followup(question_text: str, transcript: str):
        return {"followup": "What tradeoff would you make first?"}

    async def fake_evaluate_code_answer(
        problem,
        code_submission,
        transcript,
        complexity_claim=None,
        sample_runs=None,
    ):
        return {
            "code_score": 0.84,
            "correctness_notes": ["Uses an efficient lookup"],
            "followup_topics": ["edge cases"],
            "complexity_questions": ["What are the time and space complexities, and why?"],
            "concise_feedback": "Covers the main algorithm; discuss edge cases.",
            "complexity": "O(n) time and O(n) space",
        }

    def fake_run_sample_tests(problem, code):
        return {
            "ok": True,
            "status": "passed",
            "message": "2/2 sample tests passed.",
            "tests": [
                {
                    "index": 1,
                    "ok": True,
                    "stdin": "4\n2 7 11 15\n9\n",
                    "expected_stdout": "0 1",
                    "actual_stdout": "0 1",
                    "stderr": "",
                    "returncode": 0,
                    "elapsed_ms": 12,
                }
            ],
            "passed": 2,
            "total": 2,
            "elapsed_ms": 30,
        }

    async def fake_speech_to_text(file):
        await file.read()
        return "Audio answer transcribed by fixture"

    monkeypatch.setattr(interview_graph, "score_resume_against_jd", lambda *_: {"score": 82})
    monkeypatch.setattr(interview_graph, "generate_questions", fake_generate_questions)
    monkeypatch.setattr(interview_graph, "generate_coding_problem", fake_generate_coding_problem)
    monkeypatch.setattr(interview_graph, "evaluate_answer", fake_evaluate_answer)
    monkeypatch.setattr(interview_graph, "generate_followup", fake_generate_followup)
    monkeypatch.setattr(interview_graph, "evaluate_code_answer", fake_evaluate_code_answer)
    monkeypatch.setattr(answer_audio, "speech_to_text", fake_speech_to_text)
    monkeypatch.setattr(coding, "run_sample_tests", fake_run_sample_tests)

    return fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def sample_resume() -> dict:
    return {
        "name": "Ada Candidate",
        "skills": ["Python", "FastAPI", "System Design"],
        "experience": [{"title": "Backend Engineer", "years": 3}],
    }


@pytest.fixture
def sample_jd() -> dict:
    return {
        "title": "Backend Engineer",
        "required_skills": ["Python", "APIs", "Databases"],
        "seniority": "mid",
    }


@pytest.fixture
def seeded_session(sample_resume, sample_jd) -> str:
    from app.services.session_manager import create_session

    return create_session(sample_resume, sample_jd)
