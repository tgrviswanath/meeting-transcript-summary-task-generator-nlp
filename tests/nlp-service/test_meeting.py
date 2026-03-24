from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

SAMPLE_TRANSCRIPT = """John will finish the API docs by Friday.
Sarah needs to review the deployment scripts by Wednesday.
Mike will complete the database migration by Monday."""


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_models():
    r = client.get("/api/v1/nlp/models")
    assert r.status_code == 200
    data = r.json()
    assert "whisper_model" in data
    assert "summarizer_model" in data
    assert "llm_model" in data


def test_summarize():
    with patch("app.core.summarizer._get_summarizer") as mock_sum:
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{"summary_text": "John, Sarah, and Mike discussed tasks."}]
        mock_sum.return_value = mock_pipeline
        r = client.post("/api/v1/nlp/summarize", json={"transcript": SAMPLE_TRANSCRIPT})
        assert r.status_code == 200
        assert "summary" in r.json()


def test_summarize_empty():
    r = client.post("/api/v1/nlp/summarize", json={"transcript": "  "})
    assert r.status_code == 400


def test_tasks_with_regex_fallback():
    with patch("app.core.task_extractor._extract_with_llm", side_effect=Exception("Ollama down")):
        r = client.post("/api/v1/nlp/tasks", json={"transcript": SAMPLE_TRANSCRIPT})
        assert r.status_code == 200
        assert "tasks" in r.json()


def test_tasks_empty():
    r = client.post("/api/v1/nlp/tasks", json={"transcript": "  "})
    assert r.status_code == 400


def test_process():
    with patch("app.core.summarizer._get_summarizer") as mock_sum, \
         patch("app.core.task_extractor._extract_with_llm", side_effect=Exception("no llm")):
        mock_pipeline = MagicMock()
        mock_pipeline.return_value = [{"summary_text": "Team discussed tasks."}]
        mock_sum.return_value = mock_pipeline
        r = client.post("/api/v1/nlp/process", json={"transcript": SAMPLE_TRANSCRIPT})
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data
        assert "tasks" in data
        assert "word_count" in data


def test_transcribe_unsupported():
    r = client.post(
        "/api/v1/nlp/transcribe",
        files={"file": ("meeting.csv", b"a,b,c", "text/csv")},
    )
    assert r.status_code == 400
