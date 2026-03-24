# Project 15 - Meeting Transcript → Summary → Task Generator

Microservice NLP system that transcribes audio meetings, generates summaries, and extracts structured action items.

## Architecture

```
Frontend :3000  →  Backend :8000  →  NLP Service :8001
  React/MUI        FastAPI/httpx      Whisper + BART + Ollama
```

## What's Different from Projects 1-4

| Project | Input | NLP | Output |
|---------|-------|-----|--------|
| 1 | Text | NLTK + LogReg | Sentiment |
| 2 | Text | spaCy + SVM | Category |
| 3 | File (PDF) | spaCy NER | Structured JSON |
| 4 | Text | NLTK + NaiveBayes | Spam/Ham |
| **15** | **Audio / Text** | **Whisper + BART + Ollama** | **Summary + Action Items** |

## NLP Service - Pipeline

| Step | Tool | What it does |
|------|------|-------------|
| Transcription | OpenAI Whisper | Audio → text with timestamps |
| Summarization | facebook/bart-large-cnn | Long transcript → concise summary |
| Task Extraction | Ollama (llama3.2) | Transcript → structured action items |
| Fallback | regex | If Ollama unavailable, regex extracts tasks |

## Local Run

```bash
# Prerequisites - install Ollama for task extraction (optional)
# Download from https://ollama.ai
ollama pull llama3.2

# Terminal 1 - NLP Service
cd nlp-service && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Backend
cd backend && python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 3 - Frontend
cd frontend && npm install && npm start
```

- NLP Service: http://localhost:8001/docs
- Backend API: http://localhost:8000/docs
- Frontend UI: http://localhost:3000

## UI Features

- Drag & drop audio upload (MP3, WAV, MP4, M4A, OGG, FLAC, WEBM)
- Paste transcript directly for testing without audio
- Sample transcript pre-loaded for instant demo
- Meeting summary with copy button
- Action items table: Task / Owner / Deadline / Priority

## Notes

- Whisper `base` model (~140MB) downloads automatically on first run
- BART model (~1.6GB) downloads automatically on first run
- Ollama is optional — regex fallback works without it
- 16GB RAM recommended for BART + Whisper together
