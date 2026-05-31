from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

# Import API routes
from app.routes.parse import router as parse_router
from app.routes.start import router as start_router
from app.routes.questions import router as questions_router
from app.routes.answer import router as answer_router
from app.routes.improvement import router as improvement_router
from app.routes.upload import router as upload_router
from app.routes.tts import router as tts_router
from app.routes.stt import router as stt_router
from app.routes.answer_audio import router as answer_audio_router
from app.routes.config import router as config_router
from app.routes.report import router as report_router
from app.routes.coding import router as coding_router

app = FastAPI(title="Mock Interview MVP")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API ROUTES (MUST BE REGISTERED BEFORE STATICFILES)
app.include_router(parse_router,        prefix="/api")
app.include_router(start_router,        prefix="/api")
app.include_router(questions_router,    prefix="/api")
app.include_router(answer_router,       prefix="/api")
app.include_router(improvement_router,  prefix="/api")
app.include_router(upload_router,       prefix="/api")
app.include_router(tts_router,          prefix="/api")
app.include_router(stt_router,          prefix="/api")
app.include_router(answer_audio_router, prefix="/api")
app.include_router(config_router,       prefix="/api")
app.include_router(report_router,       prefix="/api")
app.include_router(coding_router,       prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "running", "app": "Mock Interview MVP"}


# 🚨 StaticFiles MUST come LAST
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
