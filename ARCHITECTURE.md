# Platform Architecture Notes

This project is now structured as a mock-interview preparation platform MVP. It has the main product loops in place, but a few backend components must be upgraded before public multi-user hosting.

## Current Architecture

```text
Browser frontend
  -> FastAPI routes
  -> LangGraph interview workflow
  -> Groq LLM services
  -> Whisper STT
  -> gTTS
  -> local C++ sample runner
  -> in-memory session store
```

## Current Platform Capabilities

- Resume/JD upload and parsing
- Interview configuration by type and difficulty
- Adaptive interview state machine
- HR, technical, system design, DSA, and mixed modes
- DSA C++ code editor
- Sample test runner for C++17
- Voice and text answers
- Follow-up questions based on weak answers
- ATS-style resume/JD scoring
- Final report with transcripts, audio filenames, coding attempts, complexity claims, and resources
- pytest API testing scaffold

## Scale Limitations

The current MVP is suitable for local demo and controlled portfolio deployment, but not yet for a public multi-user platform.

Main limitations:

- Sessions are stored in memory.
- No user accounts/authentication.
- No persistent interview history.
- Local C++ execution is not sandboxed enough for public arbitrary code execution.
- LLM/STT calls are synchronous and can block request time.
- No rate limiting or billing controls.
- No background worker queue.
- No object storage for reports/exports.

## Production Platform Target

```text
Frontend
  -> API Gateway / FastAPI
  -> Auth
  -> PostgreSQL sessions/interviews/reports
  -> Redis queue/cache
  -> Worker service for LLM/STT/report jobs
  -> Judge0 or sandbox service for code execution
  -> Object storage for report exports
  -> Observability logs/metrics
```

## Recommended Next Phases

### Phase 1: Persistence

- Replace in-memory `SESSIONS` with a repository interface.
- Add SQLite for local development.
- Add PostgreSQL for deployment.
- Persist:
  - users
  - sessions
  - uploaded document text
  - interview config
  - questions
  - answers
  - code runs
  - final reports

### Phase 2: Safe Code Execution

- Keep local `g++` runner only for local demos.
- Use Judge0 or another sandbox for hosted execution.
- Store sample-run attempts and hidden-test attempts separately.
- Add compile-time and runtime limits per user.

### Phase 3: Background Jobs

- Move slow tasks out of request/response:
  - resume/JD parsing
  - question generation
  - Whisper transcription
  - final report generation
- Use Redis + RQ/Celery/Arq or a managed queue.

### Phase 4: Multi-User Platform

- Add accounts and login.
- Add interview history dashboard.
- Add report download/export.
- Add saved coding submissions.
- Add plan limits/rate limits.

### Phase 5: Observability and Deployment

- Add structured logs.
- Add request IDs.
- Add error tracking.
- Add health checks for:
  - API
  - LLM provider
  - database
  - code runner
- Add Docker Compose for local platform mode.

## Resume Positioning

Good resume framing:

```text
Built an AI interview-preparation platform using FastAPI, LangGraph, Groq LLMs, Whisper, semantic evaluation, ATS-style resume scoring, and a C++ sample-test runner with adaptive DSA follow-ups and final performance reports.
```
