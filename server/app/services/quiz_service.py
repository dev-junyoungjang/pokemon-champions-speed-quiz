from __future__ import annotations

from itertools import cycle
from typing import Any, Sequence

from app.core.settings import get_settings
from app.core.speed import base_speed_of, calculate_effective_speed
from app.models.domain import (
    Difficulty,
    GenerateQuizRequest,
    PokemonBuild,
    QuizPokemonCase,
    QuizQuestion,
    QuizQuestionCandidate,
    RenderQuestionRequest,
    ValidatedQuizQuestion,
)
from app.repositories.in_memory import InMemoryRepository
from app.services.ai_question_client import AiQuestionError, OpenAiResponsesClient

RULESET_VERSION = "pokemon_champions:speed:v1"


class QuizService:
    def __init__(self, repository: InMemoryRepository, ai_client: OpenAiResponsesClient | None = None) -> None:
        self.repository = repository
        self.settings = get_settings()
        self.ai_client = ai_client or OpenAiResponsesClient(self.settings)
        self._questions: dict[str, QuizQuestion] = {}
        self._validated_questions: dict[str, ValidatedQuizQuestion] = {}

    def generate_questions(self, request: GenerateQuizRequest) -> list[QuizQuestion]:
        """Generate playable questions through candidate -> validate -> render.

        This preserves the old API response while enforcing the new two-step
        invariant: structured candidates never carry trusted answer/prose, and
        every rendered question is backed by a validated rules-engine result.
        """
        candidates = self.generate_candidates(request)
        questions: list[QuizQuestion] = []
        for candidate in candidates:
            validated = self.validate_candidate(candidate)
            question = self.render_question(RenderQuestionRequest(question=validated))
            self._questions[question.id] = question
            questions.append(question)
        return questions

    def generate_candidates(self, request: GenerateQuizRequest) -> list[QuizQuestionCandidate]:
        team = self.repository.get_team(request.team_name)
        meta_samples = self.repository.list_active_meta_samples()
        if not team.members or not meta_samples:
            return []

        if self.ai_client.enabled_for_candidates():
            ai_candidates = self._generate_ai_candidates(request, team.members, meta_samples)
            if ai_candidates:
                return ai_candidates[:request.count]

        return self._generate_deterministic_candidates(request, team.members, meta_samples)

    def _generate_deterministic_candidates(
        self,
        request: GenerateQuizRequest,
        team_members: Sequence[PokemonBuild],
        meta_samples: Sequence[PokemonBuild],
    ) -> list[QuizQuestionCandidate]:
        candidates: list[QuizQuestionCandidate] = []
        pairs = zip(cycle(team_members), cycle(meta_samples), strict=False)
        for subject, opponent in pairs:
            if len(candidates) >= request.count:
                break
            candidates.append(
                QuizQuestionCandidate(
                    difficulty=request.difficulty,
                    subject=self._candidate_build(request.difficulty, subject),
                    opponent=self._candidate_build(request.difficulty, opponent),
                    rulesetVersion=RULESET_VERSION,
                )
            )
        return candidates

    def _generate_ai_candidates(
        self,
        request: GenerateQuizRequest,
        team_members: Sequence[PokemonBuild],
        meta_samples: Sequence[PokemonBuild],
    ) -> list[QuizQuestionCandidate]:
        candidates: list[QuizQuestionCandidate] = []
        attempts = 0
        while len(candidates) < request.count and attempts < self.settings.ai_max_generation_attempts:
            attempts += 1
            batch_size = max(request.count - len(candidates), request.count * self.settings.ai_candidate_batch_multiplier)
            try:
                payload = self.ai_client.create_json(
                    model=self.settings.openai_candidate_model,
                    instructions=(
                        "You generate Pokémon Champions speed quiz pair selections. "
                        "Return only JSON. Do not compute answers, speeds, statements, or explanations. "
                        "Choose varied pairs from the provided team and meta pools."
                    ),
                    input_payload={
                        "difficulty": request.difficulty.value,
                        "count": batch_size,
                        "team": [self._build_summary(index, member) for index, member in enumerate(team_members)],
                        "meta": [self._build_summary(index, sample) for index, sample in enumerate(meta_samples)],
                        "requiredShape": {"pairs": [{"teamIndex": 0, "metaIndex": 0}]},
                    },
                )
            except AiQuestionError:
                break

            for pair in payload.get("pairs", []):
                if len(candidates) >= request.count:
                    break
                if not isinstance(pair, dict):
                    continue
                try:
                    subject = team_members[int(pair["teamIndex"])]
                    opponent = meta_samples[int(pair["metaIndex"])]
                except (KeyError, TypeError, ValueError, IndexError):
                    continue
                candidates.append(
                    QuizQuestionCandidate(
                        difficulty=request.difficulty,
                        subject=self._candidate_build(request.difficulty, subject),
                        opponent=self._candidate_build(request.difficulty, opponent),
                        rulesetVersion=RULESET_VERSION,
                    )
                )

        if len(candidates) < request.count:
            deterministic = self._generate_deterministic_candidates(request, team_members, meta_samples)
            candidates.extend(deterministic[: request.count - len(candidates)])
        return candidates

    def validate_candidate(self, candidate: QuizQuestionCandidate) -> ValidatedQuizQuestion:
        subject_case, opponent_case = self._compute_cases(candidate)
        correct = subject_case.speed.effective_speed > opponent_case.speed.effective_speed
        validated = ValidatedQuizQuestion(
            candidateId=candidate.id,
            difficulty=candidate.difficulty,
            mode=candidate.mode,
            correctAnswer=correct,
            subject=subject_case,
            opponent=opponent_case,
            validation={
                "status": "valid",
                "engine": "server/app/core/speed.py",
                "candidateHadTrustedAnswer": False,
                "candidateHadTrustedText": False,
            },
            rulesetVersion=RULESET_VERSION,
        )
        self._validated_questions[validated.id] = validated
        return validated

    def render_question(self, request: RenderQuestionRequest) -> QuizQuestion:
        validated = request.question
        statement = self._statement(validated, locale=request.locale)
        explanation = self._explanation(validated, locale=request.locale)
        if self.ai_client.enabled_for_rendering():
            ai_rendered = self._render_ai_text(validated, locale=request.locale)
            if ai_rendered is not None:
                statement, explanation = ai_rendered
        question = QuizQuestion(
            validatedQuestionId=validated.id,
            difficulty=validated.difficulty,
            mode=validated.mode,
            statement=statement,
            correctAnswer=validated.correct_answer,
            subject=validated.subject,
            opponent=validated.opponent,
            explanation=explanation,
            rulesetVersion=validated.ruleset_version,
        )
        self._questions[question.id] = question
        return question

    def get_question(self, question_id: str) -> QuizQuestion | None:
        return self._questions.get(question_id)

    def _compute_cases(self, candidate: QuizQuestionCandidate) -> tuple[QuizPokemonCase, QuizPokemonCase]:
        if candidate.difficulty == Difficulty.easy:
            subject_speed = base_speed_of(candidate.subject)
            opponent_speed = base_speed_of(candidate.opponent)
            subject_computation = calculate_effective_speed(candidate.subject, include_modifiers=False).model_copy(
                update={
                    "raw_speed": subject_speed,
                    "effective_speed": subject_speed,
                    "modifiers": [f"base speed={subject_speed}"],
                }
            )
            opponent_computation = calculate_effective_speed(candidate.opponent, include_modifiers=False).model_copy(
                update={
                    "raw_speed": opponent_speed,
                    "effective_speed": opponent_speed,
                    "modifiers": [f"base speed={opponent_speed}"],
                }
            )
        else:
            include_modifiers = candidate.difficulty not in {Difficulty.normal}
            subject_computation = calculate_effective_speed(candidate.subject, include_modifiers=include_modifiers)
            opponent_computation = calculate_effective_speed(candidate.opponent, include_modifiers=include_modifiers)

        return (
            QuizPokemonCase(build=candidate.subject, speed=subject_computation),
            QuizPokemonCase(build=candidate.opponent, speed=opponent_computation),
        )

    def _build_summary(self, index: int, build: PokemonBuild) -> dict[str, Any]:
        return {
            "index": index,
            "pokemonId": build.pokemon_id,
            "pokemonName": build.pokemon_name,
            "baseSpeed": build.base_stats_snapshot.spe,
            "nature": build.nature,
            "item": build.item,
            "ability": build.ability,
            "speedStage": build.speed_stage,
            "tailwind": build.tailwind,
            "weather": build.weather,
            "status": build.status,
            "statPointsSpe": build.stat_points.spe,
            "evSpe": build.evs.spe,
            "ivSpe": build.ivs.spe,
        }

    def _render_ai_text(self, validated: ValidatedQuizQuestion, locale: str = "ko") -> tuple[str, str] | None:
        try:
            payload = self.ai_client.create_json(
                model=self.settings.openai_render_model,
                instructions=(
                    "Render a Pokémon Champions speed quiz question from validated JSON. "
                    "Return only JSON with string fields statement and explanation. "
                    "Never change the answer, Pokémon names, or speed numbers. "
                    "For Korean, use concise natural Korean and include the computed speeds in the explanation."
                ),
                input_payload={
                    "locale": locale,
                    "validatedQuestion": validated.model_dump(by_alias=True),
                    "requiredShape": {"statement": "string", "explanation": "string"},
                },
            )
        except AiQuestionError:
            return None

        statement = payload.get("statement")
        explanation = payload.get("explanation")
        if not isinstance(statement, str) or not isinstance(explanation, str):
            return None
        if not statement.strip() or not explanation.strip():
            return None
        subject_speed = str(validated.subject.speed.effective_speed)
        opponent_speed = str(validated.opponent.speed.effective_speed)
        if subject_speed not in explanation or opponent_speed not in explanation:
            return None
        return statement.strip(), explanation.strip()

    def _candidate_build(self, difficulty: Difficulty, build: PokemonBuild) -> PokemonBuild:
        if difficulty == Difficulty.easy:
            return build.model_copy(
                update={
                    "speed_stage": 0,
                    "item": None,
                    "weather": None,
                    "status": None,
                    "tailwind": False,
                    "item_consumed": False,
                }
            )
        if difficulty == Difficulty.normal:
            return build.model_copy(
                update={
                    "speed_stage": 0,
                    "item": None,
                    "weather": None,
                    "status": None,
                    "tailwind": False,
                    "item_consumed": False,
                }
            )
        return build

    def _statement(self, validated: ValidatedQuizQuestion, locale: str = "ko") -> str:
        subject = validated.subject.build.pokemon_name
        opponent = validated.opponent.build.pokemon_name
        if validated.difficulty == Difficulty.easy:
            return f"{subject}의 기본 Speed는 {opponent}보다 높다."
        if locale == "en":
            return f"Is {self._label(validated.subject.build)} faster than {self._label(validated.opponent.build)}?"
        return f"{self._label(validated.subject.build)}는 {self._label(validated.opponent.build)}보다 빠르다."

    def _explanation(self, validated: ValidatedQuizQuestion, locale: str = "ko") -> str:
        subject = validated.subject
        opponent = validated.opponent
        comparison = ">" if subject.speed.effective_speed > opponent.speed.effective_speed else "<="
        if locale == "en":
            return (
                f"{subject.build.pokemon_name}: {subject.speed.effective_speed} "
                f"({'; '.join(subject.speed.modifiers)}), "
                f"{opponent.build.pokemon_name}: {opponent.speed.effective_speed} "
                f"({'; '.join(opponent.speed.modifiers)}). "
                f"Because {subject.speed.effective_speed} {comparison} {opponent.speed.effective_speed}, "
                f"the answer is {'yes' if validated.correct_answer else 'no'}."
            )
        return (
            f"{subject.build.pokemon_name}: {subject.speed.effective_speed} "
            f"({'; '.join(subject.speed.modifiers)}), "
            f"{opponent.build.pokemon_name}: {opponent.speed.effective_speed} "
            f"({'; '.join(opponent.speed.modifiers)}). "
            f"{subject.speed.effective_speed} {comparison} {opponent.speed.effective_speed} 이므로 "
            f"정답은 {'예' if validated.correct_answer else '아니오'}입니다."
        )

    def _label(self, build: PokemonBuild) -> str:
        speed_points = build.stat_points.spe or build.evs.spe
        speed_unit = "SP" if build.stat_points.spe else "Spe"
        parts = [build.nature, f"{speed_points} {speed_unit}", build.pokemon_name]
        if build.item:
            parts.append(f"@ {build.item}")
        if build.speed_stage:
            parts.append(f"Speed stage {build.speed_stage:+d}")
        if build.tailwind:
            parts.append("Tailwind")
        if build.weather:
            parts.append(f"in {build.weather}")
        if build.status:
            parts.append(f"status {build.status}")
        return " ".join(parts)
