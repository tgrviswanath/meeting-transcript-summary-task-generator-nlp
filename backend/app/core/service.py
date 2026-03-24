import httpx
from app.core.config import settings

NLP_URL = settings.NLP_SERVICE_URL


async def transcribe_audio(filename: str, content: bytes, content_type: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{NLP_URL}/api/v1/nlp/transcribe",
            files={"file": (filename, content, content_type)},
            timeout=300.0,
        )
        r.raise_for_status()
        return r.json()


async def summarize(transcript: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{NLP_URL}/api/v1/nlp/summarize",
            json={"transcript": transcript},
            timeout=120.0,
        )
        r.raise_for_status()
        return r.json()


async def extract_tasks(transcript: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{NLP_URL}/api/v1/nlp/tasks",
            json={"transcript": transcript},
            timeout=120.0,
        )
        r.raise_for_status()
        return r.json()


async def process(transcript: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{NLP_URL}/api/v1/nlp/process",
            json={"transcript": transcript},
            timeout=180.0,
        )
        r.raise_for_status()
        return r.json()


async def get_models() -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{NLP_URL}/api/v1/nlp/models", timeout=10.0)
        r.raise_for_status()
        return r.json()
