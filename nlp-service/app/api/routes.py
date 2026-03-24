from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.transcriber import transcribe
from app.core.summarizer import summarize
from app.core.task_extractor import extract_tasks
from app.core.config import settings

router = APIRouter(prefix="/api/v1/nlp", tags=["meeting"])

AUDIO_EXTS = {"mp3", "mp4", "wav", "m4a", "ogg", "flac", "webm"}


class TranscriptInput(BaseModel):
    transcript: str


@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in AUDIO_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: .{ext}")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    return transcribe(content, file.filename)


@router.post("/summarize")
def summarize_endpoint(body: TranscriptInput):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")
    return {"summary": summarize(body.transcript)}


@router.post("/tasks")
def tasks_endpoint(body: TranscriptInput):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")
    return {"tasks": extract_tasks(body.transcript)}


@router.post("/process")
def process_endpoint(body: TranscriptInput):
    """Full pipeline: transcript → summary + tasks in one call."""
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")
    summary = summarize(body.transcript)
    tasks = extract_tasks(body.transcript)
    return {
        "transcript": body.transcript,
        "summary": summary,
        "tasks": tasks,
        "word_count": len(body.transcript.split()),
    }


@router.get("/models")
def models():
    return {
        "whisper_model": settings.WHISPER_MODEL,
        "summarizer_model": settings.SUMMARIZER_MODEL,
        "llm_model": settings.OLLAMA_MODEL,
    }
