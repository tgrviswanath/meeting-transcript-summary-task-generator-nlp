"""
Whisper-based audio transcriber.
Supports: mp3, mp4, wav, m4a, ogg, flac, webm
"""
import whisper
import tempfile
import os
from app.core.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model(settings.WHISPER_MODEL)
    return _model


def transcribe(audio_bytes: bytes, filename: str) -> dict:
    model = _get_model()
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "wav"

    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = model.transcribe(tmp_path, fp16=False)
        segments = [
            {
                "start": round(s["start"], 1),
                "end": round(s["end"], 1),
                "text": s["text"].strip(),
            }
            for s in result.get("segments", [])
        ]
        return {
            "transcript": result["text"].strip(),
            "language": result.get("language", "en"),
            "segments": segments,
        }
    finally:
        os.unlink(tmp_path)
