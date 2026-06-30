from app.models.domain import GenerateQuizRequest, RenderQuestionRequest, TeamMember, UserTeam
from app.repositories.in_memory import InMemoryRepository
from app.services.quiz_service import QuizService


class FakeAiClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def enabled_for_candidates(self) -> bool:
        return True

    def enabled_for_rendering(self) -> bool:
        return True

    def create_json(self, *, model: str, instructions: str, input_payload: dict[str, object]) -> dict[str, object]:
        self.calls.append({"model": model, "instructions": instructions, "input_payload": input_payload})
        if "validatedQuestion" in input_payload:
            question = input_payload["validatedQuestion"]
            assert isinstance(question, dict)
            subject_speed = question["subject"]["speed"]["effectiveSpeed"]
            opponent_speed = question["opponent"]["speed"]["effectiveSpeed"]
            return {
                "statement": "AI가 만든 한국어 질문입니다.",
                "explanation": f"검증된 속도는 {subject_speed}와 {opponent_speed}입니다.",
            }
        return {"pairs": [{"teamIndex": 0, "metaIndex": 1}]}


def test_quiz_service_uses_ai_for_candidate_pair_selection_and_rendering() -> None:
    repository = InMemoryRepository()
    repository.save_team(UserTeam(
        teamName="main",
        members=[TeamMember.model_validate({
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
        })],
    ))
    fake_ai = FakeAiClient()
    service = QuizService(repository, ai_client=fake_ai)  # type: ignore[arg-type]

    candidates = service.generate_candidates(GenerateQuizRequest.model_validate({"difficulty": "hard", "count": 1, "teamName": "main"}))
    assert candidates[0].opponent.pokemon_id == "chien-pao"

    validated = service.validate_candidate(candidates[0])
    question = service.render_question(RenderQuestionRequest(question=validated, locale="ko"))

    assert question.statement == "AI가 만든 한국어 질문입니다."
    assert "검증된 속도" in question.explanation
    assert len(fake_ai.calls) == 2
