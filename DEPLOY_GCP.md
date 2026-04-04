# GCP Deployment Guide — Project 15 Meeting Transcript → Summary → Task Generator

---

## GCP Services for Meeting Transcription & Summarization

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Speech-to-Text API**               | Speech recognition for audio meetings with speaker diarization — replace Whisper | Replace your OpenAI Whisper pipeline           |
| **Vertex AI Gemini**                 | Gemini Pro for summarization and task extraction — replace BART + Ollama    | Replace your BART + Ollama pipeline                |
| **Cloud Natural Language API**       | Key phrase and event extraction from transcripts                             | Lightweight task extraction without LLM            |

> **Speech-to-Text API + Vertex AI Gemini** replace your Whisper + BART + Ollama pipeline. Speech-to-Text handles audio → text with speaker labels, Gemini handles summarization and task extraction.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Cloud Run**              | Run backend + nlp-service containers — serverless, scales to zero   | Best match for your current microservice architecture |
| **Artifact Registry**      | Store your Docker images                                            | Used with Cloud Run or GKE                            |

### 3. Supporting Services

| Service                        | Purpose                                                                   |
|--------------------------------|---------------------------------------------------------------------------|
| **Cloud Storage**              | Store uploaded audio files and generated transcripts/summaries            |
| **Secret Manager**             | Store API keys and connection strings instead of .env files               |
| **Cloud Monitoring + Logging** | Track transcription latency, summarization quality, request volume        |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Firebase Hosting — React Frontend                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Cloud Run — Backend (FastAPI :8000)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal HTTPS
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Cloud Run         │    │ Speech-to-Text API                 │
│ NLP Service :8001 │    │ + Vertex AI Gemini                 │
│ Whisper+BART      │    │ No GPU / model download needed     │
│ + Ollama          │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
gcloud auth login
gcloud projects create meetingsumm-project --name="Meeting Summarizer"
gcloud config set project meetingsumm-project
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com speech.googleapis.com \
  aiplatform.googleapis.com language.googleapis.com \
  storage.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Create Artifact Registry and Push Images

```bash
GCP_REGION=europe-west2
gcloud artifacts repositories create meetingsumm-repo \
  --repository-format=docker --location=$GCP_REGION
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev
AR=$GCP_REGION-docker.pkg.dev/meetingsumm-project/meetingsumm-repo
docker build -f docker/Dockerfile.nlp-service -t $AR/nlp-service:latest ./nlp-service
docker push $AR/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $AR/backend:latest ./backend
docker push $AR/backend:latest
```

---

## Step 2 — Create Cloud Storage for Audio Files

```bash
gsutil mb -l $GCP_REGION gs://meeting-audio-meetingsumm-project
```

---

## Step 3 — Deploy to Cloud Run

```bash
gcloud run deploy nlp-service \
  --image $AR/nlp-service:latest --region $GCP_REGION \
  --port 8001 --no-allow-unauthenticated \
  --min-instances 1 --max-instances 3 --memory 4Gi --cpu 2

NLP_URL=$(gcloud run services describe nlp-service --region $GCP_REGION --format "value(status.url)")

gcloud run deploy backend \
  --image $AR/backend:latest --region $GCP_REGION \
  --port 8000 --allow-unauthenticated \
  --min-instances 1 --max-instances 5 --memory 1Gi --cpu 1 \
  --set-env-vars NLP_SERVICE_URL=$NLP_URL
```

---

## Option B — Use Speech-to-Text API + Vertex AI Gemini

```python
from google.cloud import speech_v1
import vertexai
from vertexai.generative_models import GenerativeModel
import json

speech_client = speech_v1.SpeechClient()
vertexai.init(project="meetingsumm-project", location="europe-west2")
gemini = GenerativeModel("gemini-pro")

def transcribe_audio(gcs_uri: str) -> str:
    audio = speech_v1.RecognitionAudio(uri=gcs_uri)
    config = speech_v1.RecognitionConfig(
        encoding=speech_v1.RecognitionConfig.AudioEncoding.MP3,
        language_code="en-US",
        enable_speaker_diarization=True,
        diarization_speaker_count=4
    )
    operation = speech_client.long_running_recognize(config=config, audio=audio)
    result = operation.result(timeout=300)
    return " ".join([r.alternatives[0].transcript for r in result.results])

def summarize_and_extract_tasks(transcript: str) -> dict:
    response = gemini.generate_content(
        f"Summarize this meeting and extract action items as JSON.\nTranscript: {transcript[:8000]}\nReturn: {{summary, tasks: [{{task, owner, deadline, priority}}]}}"
    )
    return json.loads(response.text)
```

---

## Estimated Monthly Cost

| Service                    | Tier                  | Est. Cost          |
|----------------------------|-----------------------|--------------------|
| Cloud Run (backend)        | 1 vCPU / 1 GB         | ~$10–15/month      |
| Cloud Run (nlp-service)    | 2 vCPU / 4 GB         | ~$20–30/month      |
| Artifact Registry          | Storage               | ~$1–2/month        |
| Firebase Hosting           | Free tier             | $0                 |
| Speech-to-Text API         | Pay per minute        | ~$2–5/month        |
| Vertex AI Gemini           | Pay per token         | ~$5–15/month       |
| **Total (Option A)**       |                       | **~$32–48/month**  |
| **Total (Option B)**       |                       | **~$18–37/month**  |

For exact estimates → https://cloud.google.com/products/calculator

---

## Teardown

```bash
gcloud run services delete backend --region $GCP_REGION --quiet
gcloud run services delete nlp-service --region $GCP_REGION --quiet
gcloud artifacts repositories delete meetingsumm-repo --location=$GCP_REGION --quiet
gsutil rm -r gs://meeting-audio-meetingsumm-project
gcloud projects delete meetingsumm-project
```
