from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import app

client = TestClient(app)


def test_ai_config_does_not_expose_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    monkeypatch.setenv("OPENAI_CANDIDATE_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_RENDER_MODEL", "gpt-5.4-mini")
    get_settings.cache_clear()
    try:
        response = client.get("/api/v1/ai/config")
        assert response.status_code == 200
        payload = response.json()
        assert payload["openaiConfigured"] is True
        assert payload["candidateModel"] == "gpt-5.4-mini"
        assert payload["renderModel"] == "gpt-5.4-mini"
        assert "apiKey" not in payload
        assert "sk-test-secret" not in response.text
    finally:
        get_settings.cache_clear()
