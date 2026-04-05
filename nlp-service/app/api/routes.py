import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.transcriber import transcribe
from app.core.summarizer import summarize
from app.core.task_extractor import extract_tasks
from app.core.config import settings

MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100 MB
AUDIO_EXTS = {"mp3", "mp4", "wav", "m4a", "ogg", "flac", "webm"}

router = APIRouter(prefix="/api/v1/nlp", tags=["meeting"])


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
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 100MB")
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, transcribe, content, file.filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize")
async def summarize_endpoint(body: TranscriptInput):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")
    try:
        loop = asyncio.get_running_loop()
        return {"summary": await loop.run_in_executor(None, summarize, body.transcript)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks")
async def tasks_endpoint(body: TranscriptInput):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")
    try:
        loop = asyncio.get_running_loop()
        return {"tasks": await loop.run_in_executor(None, extract_tasks, body.transcript)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_endpoint(body: TranscriptInput):
    if not body.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty")
    try:
        loop = asyncio.get_running_loop()
        summary = await loop.run_in_executor(None, summarize, body.transcript)
        tasks = await loop.run_in_executor(None, extract_tasks, body.transcript)
        return {
            "transcript": body.transcript,
            "summary": summary,
            "tasks": tasks,
            "word_count": len(body.transcript.split()),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
def models():
    return {
        "whisper_model": settings.WHISPER_MODEL,
        "summarizer_model": settings.SUMMARIZER_MODEL,
        "llm_model": settings.OLLAMA_MODEL,
    }
