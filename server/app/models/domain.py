from __future__ import annotations

from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

StatKey = Literal["hp", "atk", "def", "spa", "spd", "spe"]


class Difficulty(str, Enum):
    easy = "easy"
    normal = "normal"
    hard = "hard"
    expert = "expert"
    master = "master"


class BaseStats(BaseModel):
    hp: int = Field(ge=1)
    atk: int = Field(ge=1)
    def_: int = Field(alias="def", ge=1)
    spa: int = Field(ge=1)
    spd: int = Field(ge=1)
    spe: int = Field(ge=1)

    model_config = {"populate_by_name": True}


class StatSpread(BaseModel):
    hp: int = Field(default=0, ge=0, le=252)
    atk: int = Field(default=0, ge=0, le=252)
    def_: int = Field(default=0, alias="def", ge=0, le=252)
    spa: int = Field(default=0, ge=0, le=252)
    spd: int = Field(default=0, ge=0, le=252)
    spe: int = Field(default=0, ge=0, le=252)

    model_config = {"populate_by_name": True}


class IvSpread(BaseModel):
    hp: int = Field(default=31, ge=0, le=31)
    atk: int = Field(default=31, ge=0, le=31)
    def_: int = Field(default=31, alias="def", ge=0, le=31)
    spa: int = Field(default=31, ge=0, le=31)
    spd: int = Field(default=31, ge=0, le=31)
    spe: int = Field(default=31, ge=0, le=31)

    model_config = {"populate_by_name": True}


class PokemonBuild(BaseModel):
    pokemon_id: str = Field(alias="pokemonId")
    pokemon_name: str = Field(alias="pokemonName")
    base_stats_snapshot: BaseStats = Field(alias="baseStatsSnapshot")
    level: int = Field(default=50, ge=1, le=100)
    nature: str = "Neutral"
    ability: str | None = None
    item: str | None = None
    evs: StatSpread = Field(default_factory=StatSpread)
    ivs: IvSpread = Field(default_factory=IvSpread)
    speed_stage: int = Field(default=0, alias="speedStage", ge=-6, le=6)
    weather: str | None = None
    status: str | None = None

    model_config = {"populate_by_name": True}


class TeamMember(PokemonBuild):
    slot: int = Field(ge=1, le=6)


class UserTeam(BaseModel):
    team_name: str = Field(default="main", alias="teamName")
    format: str = "pokemon_champions"
    members: list[TeamMember] = Field(min_length=1, max_length=6)

    model_config = {"populate_by_name": True}


class MetaSample(PokemonBuild):
    sample_id: str = Field(default_factory=lambda: str(uuid4()), alias="sampleId")
    usage_rank: int = Field(default=999, alias="usageRank")
    active: bool = True

    model_config = {"populate_by_name": True}


class SpeedComputation(BaseModel):
    raw_speed: int = Field(alias="rawSpeed")
    effective_speed: int = Field(alias="effectiveSpeed")
    modifiers: list[str]

    model_config = {"populate_by_name": True}


class QuizPokemonCase(BaseModel):
    build: PokemonBuild
    speed: SpeedComputation


class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    difficulty: Difficulty
    mode: Literal["IS_FASTER"] = "IS_FASTER"
    statement: str
    answer_type: Literal["YES_NO"] = Field(default="YES_NO", alias="answerType")
    correct_answer: bool = Field(alias="correctAnswer")
    subject: QuizPokemonCase
    opponent: QuizPokemonCase
    explanation: str
    ruleset_version: str = Field(default="pokemon_champions:v0-mainline-speed", alias="rulesetVersion")

    model_config = {"populate_by_name": True}


class GenerateQuizRequest(BaseModel):
    difficulty: Difficulty
    count: int = Field(default=5, ge=1, le=20)
    team_name: str = Field(default="main", alias="teamName")

    model_config = {"populate_by_name": True}


class AnswerRequest(BaseModel):
    question_id: str = Field(alias="questionId")
    answer: bool

    model_config = {"populate_by_name": True}


class AnswerResult(BaseModel):
    correct: bool
    correct_answer: bool = Field(alias="correctAnswer")
    explanation: str
    subject_speed: int = Field(alias="subjectSpeed")
    opponent_speed: int = Field(alias="opponentSpeed")

    model_config = {"populate_by_name": True}
