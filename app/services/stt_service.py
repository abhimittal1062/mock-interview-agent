import os
import tempfile

import whisper

try:
    from imageio_ffmpeg import get_ffmpeg_exe

    ffmpeg_dir = os.path.dirname(get_ffmpeg_exe())
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
except Exception as exc:
    print("FFmpeg auto-detection failed. Install imageio-ffmpeg or add ffmpeg to PATH:", exc)


model = None


def get_whisper_model():
    global model
    if model is None:
        model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))
    return model


async def speech_to_text(file):
    """
    Converts uploaded audio to text using Whisper local model.
    The temporary backend file is deleted immediately after transcription.
    """
    audio_bytes = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = get_whisper_model().transcribe(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return result["text"]
