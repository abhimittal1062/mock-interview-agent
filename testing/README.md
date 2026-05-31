# Testing Scaffold

This folder contains a pytest scaffold for the FastAPI mock interview app. It is intentionally isolated from the existing `tests/` folder and does not require real Groq, Whisper, sentence-transformers, BERTScore, gTTS, or torch models.

## What Is Covered

- `POST /api/configure-interview`
- `POST /api/start-interview`
- `POST /api/get-question`
- `POST /api/submit-answer`
- `POST /api/submit-answer-audio`
- `POST /api/final-report`
- Optional browser smoke check against `GET /api/health`

The API tests seed sessions directly through `app.services.session_manager.create_session`, then exercise the public endpoints. Heavy AI dependencies are faked before `app.main` is imported in `conftest.py`, and route-level services are monkeypatched with deterministic fixtures.

## Run API Tests

From the repository root:

```powershell
pytest testing
```

The Playwright smoke test is skipped by default because it expects a running app.

## Run Browser Smoke Test

Install Playwright browsers once if needed:

```powershell
playwright install chromium
```

Start the app in another terminal:

```powershell
uvicorn app.main:app --reload
```

Run the browser smoke test:

```powershell
$env:MOCK_INTERVIEW_BASE_URL = "http://127.0.0.1:8000"
pytest testing/test_frontend_smoke.py
```

## Fixture Notes

- `client` returns a FastAPI `TestClient` with AI and speech dependencies mocked.
- `seeded_session` creates a valid in-memory interview session.
- `sample_resume` and `sample_jd` provide editable sample input data.
- `reset_sessions` clears the global session store before and after each test.

If endpoint behavior changes, update the deterministic fakes in `conftest.py` first so tests continue to describe API contracts instead of model behavior.
