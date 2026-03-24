"""
Task extractor using Ollama LLM.
Extracts structured action items: task, owner, deadline from transcript.
Falls back to regex-based extraction if Ollama is unavailable.
"""
import re
import json
from langchain_community.llms import Ollama
from app.core.config import settings


_PROMPT = """You are an assistant that extracts action items from meeting transcripts.
Extract all action items, tasks, and follow-ups from the transcript below.
Return ONLY a valid JSON array. Each item must have these fields:
  - "task": what needs to be done (string)
  - "owner": who is responsible (string, use "Unassigned" if not mentioned)
  - "deadline": when it is due (string, use "Not specified" if not mentioned)
  - "priority": "High", "Medium", or "Low"

Transcript:
{transcript}

JSON array of action items:"""


def _extract_with_llm(transcript: str) -> list[dict]:
    llm = Ollama(model=settings.OLLAMA_MODEL, base_url=settings.OLLAMA_BASE_URL)
    prompt = _PROMPT.format(transcript=transcript[:3000])  # limit context
    response = llm.invoke(prompt)

    # Extract JSON array from response
    match = re.search(r"\[.*\]", response, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return []


def _extract_with_regex(transcript: str) -> list[dict]:
    """Fallback: simple regex patterns for common task phrases."""
    patterns = [
        r"(?:action item|todo|task|follow.?up|will|should|need to|must)[:\s]+([^.\n]+)",
        r"([A-Z][a-z]+)\s+(?:will|should|needs? to|is going to)\s+([^.\n]+)",
    ]
    tasks = []
    for pattern in patterns:
        for m in re.finditer(pattern, transcript, re.I):
            text = m.group(0).strip()
            if len(text) > 10:
                tasks.append({
                    "task": text,
                    "owner": "Unassigned",
                    "deadline": "Not specified",
                    "priority": "Medium",
                })
    return tasks[:10]


def extract_tasks(transcript: str) -> list[dict]:
    try:
        tasks = _extract_with_llm(transcript)
        if tasks:
            return tasks
    except Exception:
        pass
    return _extract_with_regex(transcript)
