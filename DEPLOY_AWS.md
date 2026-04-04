# AWS Deployment Guide — Project 15 Meeting Transcript → Summary → Task Generator

---

## AWS Services for Meeting Transcription & Summarization

### 1. Ready-to-Use AI (No Model Needed)

| Service                    | What it does                                                                 | When to use                                        |
|----------------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| **Amazon Transcribe**      | Speech-to-text for audio meetings — replace Whisper                         | Replace your OpenAI Whisper pipeline               |
| **Amazon Bedrock**         | Claude/Titan for summarization and task extraction — replace BART + Ollama  | Replace your BART + Ollama pipeline                |
| **Amazon Comprehend**      | Key phrase and event extraction from transcripts                             | Lightweight task extraction without LLM            |

> **Amazon Transcribe + Bedrock** replace your Whisper + BART + Ollama pipeline entirely. Transcribe handles audio → text, Bedrock handles summarization and task extraction.

### 2. Host Your Own Model (Keep Current Stack)

| Service                    | What it does                                                        | When to use                                           |
|----------------------------|---------------------------------------------------------------------|-------------------------------------------------------|
| **AWS App Runner**         | Run backend container — simplest, no VPC or cluster needed          | Quickest path to production                           |
| **Amazon ECS Fargate**     | Run backend + nlp-service containers in a private VPC               | Best match for your current microservice architecture |
| **Amazon ECR**             | Store your Docker images                                            | Used with App Runner, ECS, or EKS                     |

### 3. Supporting Services

| Service                  | Purpose                                                                   |
|--------------------------|---------------------------------------------------------------------------|
| **Amazon S3**            | Store uploaded audio files and generated transcripts/summaries            |
| **AWS Secrets Manager**  | Store API keys and connection strings instead of .env files               |
| **Amazon CloudWatch**    | Track transcription latency, summarization quality, request volume        |

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  S3 + CloudFront — React Frontend                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  AWS App Runner / ECS Fargate — Backend (FastAPI :8000)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ Internal
        ┌──────────────┴──────────────┐
        │ Option A                    │ Option B
        ▼                             ▼
┌───────────────────┐    ┌────────────────────────────────────┐
│ ECS Fargate       │    │ Amazon Transcribe                  │
│ NLP Service :8001 │    │ + Amazon Bedrock (Claude)          │
│ Whisper+BART      │    │ No GPU / model download needed     │
│ + Ollama          │    │                                    │
└───────────────────┘    └────────────────────────────────────┘
```

---

## Prerequisites

```bash
aws configure
AWS_REGION=eu-west-2
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
```

---

## Step 1 — Create ECR and Push Images

```bash
aws ecr create-repository --repository-name meetingsumm/nlp-service --region $AWS_REGION
aws ecr create-repository --repository-name meetingsumm/backend --region $AWS_REGION
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR
docker build -f docker/Dockerfile.nlp-service -t $ECR/meetingsumm/nlp-service:latest ./nlp-service
docker push $ECR/meetingsumm/nlp-service:latest
docker build -f docker/Dockerfile.backend -t $ECR/meetingsumm/backend:latest ./backend
docker push $ECR/meetingsumm/backend:latest
```

---

## Step 2 — Create S3 Bucket for Audio Files

```bash
aws s3 mb s3://meeting-audio-$AWS_ACCOUNT --region $AWS_REGION
```

---

## Step 3 — Deploy with App Runner

```bash
aws apprunner create-service \
  --service-name meetingsumm-backend \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR'/meetingsumm/backend:latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "NLP_SERVICE_URL": "http://nlp-service:8001"
        }
      }
    }
  }' \
  --instance-configuration '{"Cpu": "2 vCPU", "Memory": "4 GB"}' \
  --region $AWS_REGION
```

---

## Option B — Use Amazon Transcribe + Bedrock

```python
import boto3, json, time

transcribe = boto3.client("transcribe", region_name="eu-west-2")
bedrock = boto3.client("bedrock-runtime", region_name="eu-west-2")

def transcribe_audio(s3_uri: str, job_name: str) -> str:
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": s3_uri},
        MediaFormat="mp3",
        LanguageCode="en-US"
    )
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
            break
        time.sleep(5)
    transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
    import urllib.request
    with urllib.request.urlopen(transcript_uri) as f:
        return json.loads(f.read())["results"]["transcripts"][0]["transcript"]

def summarize_and_extract_tasks(transcript: str) -> dict:
    prompt = f"Summarize this meeting transcript and extract action items as JSON.\nTranscript: {transcript[:8000]}\nReturn: {{summary, tasks: [{{task, owner, deadline, priority}}]}}"
    response = bedrock.invoke_model(
        modelId="anthropic.claude-v2",
        body=json.dumps({"prompt": prompt, "max_tokens_to_sample": 1000}),
        contentType="application/json"
    )
    return json.loads(json.loads(response["body"].read())["completion"])
```

---

## Estimated Monthly Cost

| Service                    | Tier              | Est. Cost          |
|----------------------------|-------------------|--------------------|
| App Runner (backend)       | 2 vCPU / 4 GB     | ~$30–40/month      |
| App Runner (nlp-service)   | 2 vCPU / 4 GB     | ~$30–40/month      |
| ECR + S3 + CloudFront      | Standard          | ~$3–7/month        |
| Amazon Transcribe          | Pay per minute    | ~$2–5/month        |
| Amazon Bedrock (Claude)    | Pay per token     | ~$5–15/month       |
| **Total (Option A)**       |                   | **~$63–87/month**  |
| **Total (Option B)**       |                   | **~$40–67/month**  |

For exact estimates → https://calculator.aws

---

## Teardown

```bash
aws ecr delete-repository --repository-name meetingsumm/backend --force
aws ecr delete-repository --repository-name meetingsumm/nlp-service --force
aws s3 rm s3://meeting-audio-$AWS_ACCOUNT --recursive
aws s3 rb s3://meeting-audio-$AWS_ACCOUNT
```
