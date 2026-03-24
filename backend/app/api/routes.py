from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.core.service import transcribe_audio, summarize, extract_tasks, process, get_models
import httpx

router = APIRouter(prefix="/api/v1", tags=["meeting"])


class TranscriptInput(BaseModel):
    transcript: str


def _handle(e: Exception):
    if isinstance(e, httpx.ConnectError):
        raise HTTPException(status_code=503, detail="NLP service unavailable")
    if isinstance(e, httpx.HTTPStatusError):
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return await transcribe_audio(file.filename, content, file.content_type or "audio/mpeg")
    except Exception as e:
        _handle(e)


@router.post("/summarize")
async def summarize_endpoint(body: TranscriptInput):
    try:
        return await summarize(body.transcript)
    except Exception as e:
        _handle(e)


@router.post("/tasks")
async def tasks_endpoint(body: TranscriptInput):
    try:
        return await extract_tasks(body.transcript)
    except Exception as e:
        _handle(e)


@router.post("/process")
async def process_endpoint(body: TranscriptInput):
    try:
        return await process(body.transcript)
    except Exception as e:
        _handle(e)


@router.get("/models")
async def models():
    try:
        return await get_models()
    except Exception as e:
        _handle(e)
