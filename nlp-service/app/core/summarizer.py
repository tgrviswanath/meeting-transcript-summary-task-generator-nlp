"""
BART-based abstractive summarizer.
Handles long transcripts by chunking into ~1000-word pieces.
"""
from transformers import pipeline
from app.core.config import settings

_summarizer = None


def _get_summarizer():
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline(
            "summarization",
            model=settings.SUMMARIZER_MODEL,
            device=-1,   # CPU; set to 0 for GPU
        )
    return _summarizer


def _chunk_text(text: str, max_words: int = 900) -> list[str]:
    words = text.split()
    return [
        " ".join(words[i: i + max_words])
        for i in range(0, len(words), max_words)
    ]


def summarize(transcript: str) -> str:
    if not transcript.strip():
        return ""
    summarizer = _get_summarizer()
    chunks = _chunk_text(transcript)
    chunk_summaries = []
    for chunk in chunks:
        if len(chunk.split()) < 30:
            chunk_summaries.append(chunk)
            continue
        out = summarizer(
            chunk,
            max_length=settings.SUMMARY_MAX_LENGTH,
            min_length=settings.SUMMARY_MIN_LENGTH,
            do_sample=False,
        )
        chunk_summaries.append(out[0]["summary_text"])

    combined = " ".join(chunk_summaries)
    # If multiple chunks, do a final summarization pass
    if len(chunks) > 1 and len(combined.split()) > 100:
        out = summarizer(
            combined,
            max_length=settings.SUMMARY_MAX_LENGTH,
            min_length=settings.SUMMARY_MIN_LENGTH,
            do_sample=False,
        )
        return out[0]["summary_text"]
    return combined
