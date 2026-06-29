from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_question_candidate_validate_render_two_step_flow():
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
    assert validated["correctAnswer"] is True
    assert validated["subject"]["speed"]["effectiveSpeed"] == 253
    assert validated["opponent"]["speed"]["effectiveSpeed"] == 205
    assert validated["validation"]["status"] == "valid"

    render_response = client.post("/api/v1/quiz/questions/render", json={"question": validated, "locale": "ko"})
    assert render_response.status_code == 200
    rendered = render_response.json()["question"]
    assert rendered["validatedQuestionId"] == validated["id"]
    assert rendered["correctAnswer"] == validated["correctAnswer"]
    assert "보다 빠르다" in rendered["statement"]
    assert "정답은 예입니다" in rendered["explanation"]


def test_legacy_generate_questions_uses_validated_rendered_questions():
    response = client.post("/api/v1/quiz/questions", json={"difficulty": "hard", "count": 1, "teamName": "main"})
    assert response.status_code == 200
    question = response.json()["questions"][0]
    assert question["validatedQuestionId"]
    assert question["correctAnswer"] is True
    assert question["subject"]["speed"]["effectiveSpeed"] == 253
    assert question["opponent"]["speed"]["effectiveSpeed"] == 205
