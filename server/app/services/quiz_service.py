from __future__ import annotations

from itertools import cycle

from app.core.speed import base_speed_of, calculate_effective_speed
from app.models.domain import (
    Difficulty,
    GenerateQuizRequest,
    PokemonBuild,
    QuizPokemonCase,
    QuizQuestion,
)
from app.repositories.in_memory import InMemoryRepository


class QuizService:
    def __init__(self, repository: InMemoryRepository) -> None:
        self.repository = repository
        self._questions: dict[str, QuizQuestion] = {}

    def generate_questions(self, request: GenerateQuizRequest) -> list[QuizQuestion]:
        team = self.repository.get_team(request.team_name)
        meta_samples = self.repository.list_active_meta_samples()
        if not team.members or not meta_samples:
            return []

        questions: list[QuizQuestion] = []
        pairs = zip(cycle(team.members), cycle(meta_samples), strict=False)
        for subject, opponent in pairs:
            if len(questions) >= request.count:
                break
            question = self._build_question(request.difficulty, subject, opponent)
            self._questions[question.id] = question
            questions.append(question)
        return questions

    def get_question(self, question_id: str) -> QuizQuestion | None:
        return self._questions.get(question_id)

    def _build_question(
        self,
        difficulty: Difficulty,
        subject: PokemonBuild,
        opponent: PokemonBuild,
    ) -> QuizQuestion:
        include_modifiers = difficulty not in {Difficulty.easy, Difficulty.normal}

        if difficulty == Difficulty.easy:
            subject_speed = base_speed_of(subject)
            opponent_speed = base_speed_of(opponent)
            neutral_speed_context = {"speed_stage": 0, "item": None, "weather": None, "status": None}
            subject_case = subject.model_copy(update=neutral_speed_context)
            opponent_case = opponent.model_copy(update=neutral_speed_context)
            subject_computation = calculate_effective_speed(subject_case, include_modifiers=False).model_copy(
                update={
                    "raw_speed": subject_speed,
                    "effective_speed": subject_speed,
                    "modifiers": [f"base speed={subject_speed}"],
                }
            )
            opponent_computation = calculate_effective_speed(opponent_case, include_modifiers=False).model_copy(
                update={
                    "raw_speed": opponent_speed,
                    "effective_speed": opponent_speed,
                    "modifiers": [f"base speed={opponent_speed}"],
                }
            )
            statement = f"{subject.pokemon_name}의 기본 Speed는 {opponent.pokemon_name}보다 높다."
        else:
            subject_case = subject
            opponent_case = opponent
            subject_computation = calculate_effective_speed(subject_case, include_modifiers=include_modifiers)
            opponent_computation = calculate_effective_speed(opponent_case, include_modifiers=include_modifiers)
            statement = f"{self._label(subject_case)}는 {self._label(opponent_case)}보다 빠르다."

        correct = subject_computation.effective_speed > opponent_computation.effective_speed
        explanation = (
            f"{subject.pokemon_name}: {subject_computation.effective_speed}, "
            f"{opponent.pokemon_name}: {opponent_computation.effective_speed}. "
            f"따라서 문장은 {'맞습니다' if correct else '틀립니다'}."
        )
        return QuizQuestion(
            difficulty=difficulty,
            statement=statement,
            correctAnswer=correct,
            subject=QuizPokemonCase(build=subject_case, speed=subject_computation),
            opponent=QuizPokemonCase(build=opponent_case, speed=opponent_computation),
            explanation=explanation,
        )

    def _label(self, build: PokemonBuild) -> str:
        parts = [build.nature, f"{build.evs.spe} Spe", build.pokemon_name]
        if build.item:
            parts.append(f"@ {build.item}")
        if build.speed_stage:
            parts.append(f"Speed stage {build.speed_stage:+d}")
        if build.weather:
            parts.append(f"in {build.weather}")
        if build.status:
            parts.append(f"status {build.status}")
        return " ".join(parts)
