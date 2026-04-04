# Azure Deployment Guide — Project 15 Meeting Transcript → Summary → Task Generator

---

## Azure Services for Meeting Transcription & Summarization

### 1. Ready-to-Use AI (No Model Needed)

| Service                              | What it does                                                                 | When to use                                        |
|--------------------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Azure AI Speech**                  | Speech-to-text for audio meetings with speaker diarization — replace Whisper | Replace your OpenAI Whisper pipeline               |
| **Azure OpenAI Service**             | GPT-4 for summarization and task extraction — replace BART + Ollama          | Replace your BART + Ollama pipeline                |
| **Azure AI Language**                | Key phrase and event extraction from transcripts                             | Lightweight task extraction without LLM            |

> **Azure AI Speech + Azure OpenAI** replace your Whisper + BART + Ollama pipeline. Azure AI Speech handles audio → text with speaker labels, Azure OpenAI handles summarization and task extraction.

### 2. Host Your Own Model (Keep Current Stack)

| Service                        | What it does                                                        | When to use                                           |
|--------------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **Azure Container Apps**       | Run your 3 Docker containers (frontend, backend, nlp-service)       | Best match for your current microservice architecture |
| **Azure Container Registry**   | Store your Docker images                                            | Used with Container Apps or AKS                       |

### 3. Supporting Services

| Service                       | Purpose                                                                  |
|-------------------------------|--------------------------------------------------------------------------|
| **Azure Blob Storage**        | Store uploaded audio files and generated transcripts/summaries           |
| **Azure Key Vault**           | Store API keys and connection strings instead of .env files              |
| **Azure Monitor + App Insights** | Track transcription latency, summarization quality, request volume   |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Azure Static Web Apps — React Frontend                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  Azure Container Apps — Backend (FastAPI :8000)             │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ Container Apps    │    │ Azure AI Speech                    │
│ NLP Service :8001 │    │ + Azure OpenAI (GPT-4)             │
│ Whisper+BART      │    │ No GPU / model download needed     │
│ + Ollama          │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
az login
az group create --name rg-meeting-summ --location uksouth
az extension add --name containerapp --upgrade
```

---

## Step 1 — Create Container Registry and Push Images

```bash
az acr create --resource-group rg-meeting-summ --name meetingsummacr --sku Basic --admin-enabled true
az acr login --name meetingsummacr
ACR=meetingsummacr.azurecr.io
docker build -f docker/Dockerfile.nlp-service -t $ACR/nlp-service:latest ./nlp-service
docker push $ACR/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $ACR/backend:latest ./backend
docker push $ACR/backend:latest
```

---

## Step 2 — Create Blob Storage for Audio Files

```bash
az storage account create --name meetingaudio --resource-group rg-meeting-summ --sku Standard_LRS
az storage container create --name audio --account-name meetingaudio
az storage container create --name transcripts --account-name meetingaudio
```

---

## Step 3 — Deploy Container Apps

```bash
az containerapp env create --name meetingsumm-env --resource-group rg-meeting-summ --location uksouth

az containerapp create \
  --name nlp-service --resource-group rg-meeting-summ \
  --environment meetingsumm-env --image $ACR/nlp-service:latest \
  --registry-server $ACR --target-port 8001 --ingress internal \
  --min-replicas 1 --max-replicas 3 --cpu 2 --memory 4.0Gi

az containerapp create \
  --name backend --resource-group rg-meeting-summ \
  --environment meetingsumm-env --image $ACR/backend:latest \
  --registry-server $ACR --target-port 8000 --ingress external \
  --min-replicas 1 --max-replicas 5 --cpu 0.5 --memory 1.0Gi \
  --env-vars NLP_SERVICE_URL=http://nlp-service:8001
```

---

## Option B — Use Azure AI Speech + Azure OpenAI

```python
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
import json

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_SPEECH_KEY"),
    region=os.getenv("AZURE_SPEECH_REGION")
)
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01"
)

def transcribe_audio(audio_file_path: str) -> str:
    audio_config = speechsdk.AudioConfig(filename=audio_file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result = recognizer.recognize_once()
    return result.text

def summarize_and_extract_tasks(transcript: str) -> dict:
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": f"Summarize this meeting and extract action items as JSON.\nTranscript: {transcript[:8000]}\nReturn: {{summary, tasks: [{{task, owner, deadline, priority}}]}}"}]
    )
    return json.loads(response.choices[0].message.content)
```

Add to requirements.txt: `azure-cognitiveservices-speech>=1.35.0 openai>=1.12.0`

---

## Estimated Monthly Cost

| Service                  | Tier      | Est. Cost          |
|--------------------------|-----------|--------------------|
| Container Apps (backend) | 0.5 vCPU  | ~$10–15/month      |
| Container Apps (nlp-svc) | 2 vCPU    | ~$25–35/month      |
| Container Registry       | Basic     | ~$5/month          |
| Static Web Apps          | Free      | $0                 |
| Azure AI Speech          | Pay per hour | ~$2–5/month     |
| Azure OpenAI (GPT-4)     | Pay per token | ~$10–25/month  |
| **Total (Option A)**     |           | **~$40–55/month**  |
| **Total (Option B)**     |           | **~$27–50/month**  |

For exact estimates → https://calculator.azure.com

---

## Teardown

```bash
az group delete --name rg-meeting-summ --yes --no-wait
```
