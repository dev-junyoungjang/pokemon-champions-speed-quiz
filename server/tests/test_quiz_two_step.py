import pytest
from fastapi.testclient import TestClient

from app.main import app, quiz_service
from app.services.ai_question_client import OpenAiResponsesClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def _deterministic_quiz(monkeypatch):
    # These tests assert deterministic template prose against the static meta
    # pool; keep them off live OpenAI and the species-backed opponent provider.
    monkeypatch.setattr(OpenAiResponsesClient, "enabled_for_candidates", lambda self: False)
    monkeypatch.setattr(OpenAiResponsesClient, "enabled_for_rendering", lambda self: False)
    monkeypatch.setattr(quiz_service, "meta_provider", None)


def save_quiz_team() -> None:
    response = client.put(
        "/api/v1/teams/me",
        json={
            "teamName": "main",
            "format": "pokemon_champions",
            "members": [
                {
                    "slot": 1,
                    "pokemonId": "garchomp",
                    "pokemonName": "한카리아스",
                    "nationalDexNumber": 445,
                    "baseStatsSnapshot": {"hp": 108, "atk": 130, "def": 95, "spa": 80, "spd": 85, "spe": 102},
                    "speciesTypes": ["dragon", "ground"],
                    "moves": [],
                    "level": 50,
                    "nature": "Jolly",
                    "ability": "rough-skin",
                    "item": "Choice Scarf",
                    "evs": {},
                    "statPoints": {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0},
                    "ivs": {"hp": 31, "atk": 31, "def": 31, "spa": 31, "spd": 31, "spe": 31},
                }
            ],
        },
    )
    assert response.status_code == 200


def test_question_candidate_validate_render_two_step_flow():
    save_quiz_team()
    candidate_response = client.post(
        "/api/v1/quiz/question-candidates",
        json={"difficulty": "hard", "count": 1, "teamName": "main"},
    )
    assert candidate_response.status_code == 200
    candidates = candidate_response.json()["candidates"]
    assert len(candidates) == 1
    candidate = candidates[0]
    assert "statement" not in candidate
    assert "correctAnswer" not in candidate
    assert "explanation" not in candidate

    validate_response = client.post("/api/v1/quiz/questions/validate", json=candidate)
    assert validate_response.status_code == 200
    validated = validate_response.json()
    assert validated["candidateId"] == candidate["id"]
    assert validated["correctAnswer"] is False
    assert validated["subject"]["speed"]["effectiveSpeed"] == 201
    assert validated["opponent"]["speed"]["effectiveSpeed"] == 205
    assert validated["validation"]["status"] == "valid"

    render_response = client.post("/api/v1/quiz/questions/render", json={"question": validated, "locale": "ko"})
    assert render_response.status_code == 200
    rendered = render_response.json()["question"]
    assert rendered["validatedQuestionId"] == validated["id"]
    assert rendered["correctAnswer"] == validated["correctAnswer"]
    assert "보다 빠르다" in rendered["statement"]
    assert "정답은 아니오입니다" in rendered["explanation"]


def test_legacy_generate_questions_uses_validated_rendered_questions():
    save_quiz_team()
    response = client.post("/api/v1/quiz/questions", json={"difficulty": "hard", "count": 1, "teamName": "main"})
    assert response.status_code == 200
    payload = response.json()
    question = payload["questions"][0]
    assert payload["sessionId"]
    assert question["validatedQuestionId"]
    assert question["correctAnswer"] is False
    assert question["subject"]["speed"]["effectiveSpeed"] == 201
    assert question["opponent"]["speed"]["effectiveSpeed"] == 205

    answer_response = client.post(
        "/api/v1/quiz/answers",
        json={"questionId": question["id"], "answer": False, "sessionId": payload["sessionId"]},
    )
    assert answer_response.status_code == 200
    history_response = client.get("/api/v1/quiz/history")
    assert history_response.status_code == 200
    sessions = history_response.json()["sessions"]
    assert any(session["sessionId"] == payload["sessionId"] for session in sessions)
