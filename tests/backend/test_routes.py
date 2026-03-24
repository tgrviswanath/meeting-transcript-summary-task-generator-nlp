from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)

MOCK_PROCESS = {
    "transcript": "John will finish docs by Friday.",
    "summary": "John will complete documentation by Friday.",
    "tasks": [{"task": "Finish API docs", "owner": "John", "deadline": "Friday", "priority": "High"}],
    "word_count": 7,
}
MOCK_SUMMARY = {"summary": "John will complete documentation by Friday."}
MOCK_TASKS = {"tasks": [{"task": "Finish API docs", "owner": "John", "deadline": "Friday", "priority": "High"}]}
MOCK_MODELS = {"whisper_model": "base", "summarizer_model": "facebook/bart-large-cnn", "llm_model": "llama3.2"}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


@patch("app.core.service.process", new_callable=AsyncMock, return_value=MOCK_PROCESS)
def test_process_endpoint(mock_proc):
    r = client.post("/api/v1/process", json={"transcript": "John will finish docs by Friday."})
    assert r.status_code == 200
    assert "summary" in r.json()
    assert "tasks" in r.json()


@patch("app.core.service.summarize", new_callable=AsyncMock, return_value=MOCK_SUMMARY)
def test_summarize_endpoint(mock_sum):
    r = client.post("/api/v1/summarize", json={"transcript": "John will finish docs by Friday."})
    assert r.status_code == 200
    assert r.json()["summary"] == MOCK_SUMMARY["summary"]


@patch("app.core.service.extract_tasks", new_callable=AsyncMock, return_value=MOCK_TASKS)
def test_tasks_endpoint(mock_tasks):
    r = client.post("/api/v1/tasks", json={"transcript": "John will finish docs by Friday."})
    assert r.status_code == 200
    assert len(r.json()["tasks"]) == 1


@patch("app.core.service.get_models", new_callable=AsyncMock, return_value=MOCK_MODELS)
def test_models_endpoint(mock_models):
    r = client.get("/api/v1/models")
    assert r.status_code == 200
    assert r.json()["whisper_model"] == "base"
