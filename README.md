# Mock Interview Agent

AI-powered interview preparation app with resume/JD-aware questions, voice answers, adaptive follow-ups, coding interview support, ATS-style resume scoring, and a final improvement report.

## What It Does

This project helps a candidate practice interviews against a target job description.

Core flow:

1. Upload resume and job description.
2. Choose interview type and difficulty.
3. Start an adaptive interview.
4. Answer by voice or text.
5. For DSA mode, write C++ code in the browser editor.
6. Get follow-up questions based on weak answers.
7. Generate a final report with transcripts, scores, recording filenames, weak points, strong points, resources, and ATS-style resume/JD feedback.

## Features

- Resume and job description upload: PDF, DOCX, TXT
- Resume/JD parsing using Groq LLM
- Interview modes:
  - HR / behavioral
  - Technical resume-based
  - System design
  - DSA / coding
  - Mixed interview
- Adaptive workflow using a LangGraph-style state graph
- LeetCode-style sample test runner for C++17 code
- Voice questions using gTTS
- Voice answers using local Whisper STT
- Text-answer fallback
- C++ coding workspace for DSA interviews
- Sample test run history and pass/fail tracking
- AI code review and follow-up questions
- Hybrid answer evaluation:
  - LLM feedback
  - semantic similarity
  - BERTScore
  - missing keyword analysis
- ATS-style resume/JD score
- Final report with:
  - each question
  - transcript
  - audio filename
  - code submission
  - score
  - feedback
  - strengths
  - weaknesses
  - resources

## Tech Stack

Backend:

- Python 3.11
- FastAPI
- LangGraph
- LangChain
- Groq API
- PyMuPDF
- python-docx
- Whisper
- gTTS
- SentenceTransformers
- BERTScore

Frontend:

- HTML
- CSS
- JavaScript
- Browser audio recording
- C++ code editor textarea

Testing:

- pytest
- FastAPI TestClient
- optional Playwright smoke test

## Project Structure

```text
mock-interview-agent/
  app/
    graph/
      interview_graph.py
      state.py
    prompts/
    routes/
      answer.py
      answer_audio.py
      config.py
      parse.py
      questions.py
      report.py
      start.py
      stt.py
      tts.py
      upload.py
    services/
      ats_service.py
      coding_service.py
      evaluator_model.py
      evaluator_service.py
      file_reader.py
      followup_service.py
      improvement_service.py
      json_utils.py
      llm_client.py
      question_service.py
      recording_service.py
      report_service.py
      session_manager.py
      stt_service.py
      tts_service.py
    main.py
  frontend/
    index.html
    upload.html
    configure.html
    interview.html
    report.html
    improvement.html
    style.css
  testing/
  requirements.txt
  runtime.txt
  Dockerfile
  .env.example
  SETUP_PYTHON_311.md
```

## Python Version

Use Python 3.11.

Verified version:

```text
Python 3.11.9
```

Do not use Python 3.14 for this project right now. Some dependencies such as LangGraph and Playwright may not have compatible wheels for Python 3.14.

## Setup

Recommended: create the virtual environment outside OneDrive to avoid Windows/OneDrive file-lock issues during large dependency installs.

```powershell
cd "C:\Users\dellc\OneDrive\Desktop\PROJECTS\mock-interview-agent"
py -3.11 -m venv C:\tmp\mock-interview-agent-venv311
C:\tmp\mock-interview-agent-venv311\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
WHISPER_MODEL=base
CXX_COMPILER=C:\path\to\g++.exe
```

Use `.env.example` as the template.

`CXX_COMPILER` is optional if `g++` is already available on `PATH`.

## C++ Sample Test Runner

DSA mode includes a `Run Sample Tests` button, similar to coding platforms.

The backend compiles and runs the submitted C++17 program against executable sample tests. It records:

- how many times samples were run
- how many runs passed
- elapsed runtime for sample runs
- latest pass/fail status
- claimed time complexity
- claimed space complexity

Requirements:

- Install `g++` locally, for example through MinGW or MSYS2.
- Make sure `g++` is available on `PATH`, or set `CXX_COMPILER` in `.env`.

The runner uses a temporary directory and timeout-bound execution. Do not expose arbitrary code execution publicly without a real sandbox such as Judge0, Docker isolation, or another hosted judge service.

## Run Locally

Activate the Python 3.11 environment:

```powershell
C:\tmp\mock-interview-agent-venv311\Scripts\Activate.ps1
```

Start the backend:

```powershell
cd "C:\Users\dellc\OneDrive\Desktop\PROJECTS\mock-interview-agent"
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

If port 8000 is busy:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

Then open:

```text
http://127.0.0.1:8001
```

## App Flow

1. Open `/`.
2. Go to Upload.
3. Upload resume and JD.
4. Configure interview:
   - HR
   - technical
   - system design
   - DSA
   - mixed
5. Start the interview.
6. Answer questions by voice or text.
7. Use the C++ coding workspace in DSA mode.
8. Open the report page after the interview.

## Recording Behavior

The backend does not permanently save user recordings.

Voice answer flow:

1. Browser records audio.
2. Browser downloads the recording locally using a generated filename.
3. Backend receives the audio only for transcription.
4. Backend writes a temporary file for Whisper.
5. Temporary file is deleted after transcription.
6. Final report stores the recording filename, transcript, and evaluation.

## API Endpoints

```text
GET  /api/health
POST /api/upload-docs
POST /api/create-session
POST /api/configure-interview
POST /api/start-interview
POST /api/get-question
POST /api/submit-answer
POST /api/submit-answer-audio
POST /api/run-code-samples
GET  /api/question-audio
POST /api/speech-to-text
POST /api/generate-improvement
POST /api/final-report
```

## Testing

Run tests with the Python 3.11 environment:

```powershell
C:\tmp\mock-interview-agent-venv311\Scripts\Activate.ps1
pytest testing
```

Current expected result:

```text
5 passed, 1 skipped
```

The skipped test is the optional Playwright browser smoke test. To run it:

```powershell
playwright install chromium
$env:MOCK_INTERVIEW_BASE_URL = "http://127.0.0.1:8000"
pytest testing/test_frontend_smoke.py
```

## Deployment Notes

This project includes:

- `Dockerfile`
- `runtime.txt`
- `.env.example`
- `ARCHITECTURE.md`

For hosting:

- Use Python 3.11.
- Set `GROQ_API_KEY` in the hosting provider environment variables.
- Expect first model use to be slower because Whisper/SentenceTransformer models may need to initialize or download.
- Free-tier hosting may struggle with Torch, Whisper, SentenceTransformers, and BERTScore memory usage.

For platform-scale design notes, see `ARCHITECTURE.md`.

## Current Limitations

- DSA sample tests can run locally with `g++`, but this is not a production sandbox.
- For public hosted compile/run support, integrate Judge0 or another sandboxed execution service.
- Sessions are stored in memory, so restarting the server clears active sessions.
- For production, replace in-memory sessions with SQLite/Postgres/Redis.
- ATS score is an interview-prep approximation, not a guarantee from a real ATS vendor.

## Resume Bullet Example

Built and deployed an AI mock interview preparation platform using FastAPI, LangGraph, Groq LLMs, Whisper STT, semantic answer evaluation, ATS-style resume scoring, adaptive follow-up generation, and a final personalized improvement report.
