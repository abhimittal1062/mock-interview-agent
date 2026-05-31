from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile

from app.routes.answer import submit_answer
from app.services.stt_service import speech_to_text

router = APIRouter()


@router.post("/submit-answer-audio")
async def submit_answer_audio(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    audio_filename: Optional[str] = Form(None),
    code_submission: Optional[str] = Form(None),
    complexity_claim: Optional[str] = Form(None),
):
    """
    User speaks the answer -> temporary transcription -> normal answer flow.
    The backend does not retain the uploaded recording after Whisper finishes.
    """
    transcript = await speech_to_text(file)
    return await submit_answer(
        session_id=session_id,
        transcript=transcript,
        audio_filename=audio_filename,
        code_submission=code_submission,
        complexity_claim=complexity_claim,
    )
