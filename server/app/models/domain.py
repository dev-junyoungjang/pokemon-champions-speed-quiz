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


class StatPointSpread(BaseModel):
    hp: int = Field(default=0, ge=0, le=32)
    atk: int = Field(default=0, ge=0, le=32)
    def_: int = Field(default=0, alias="def", ge=0, le=32)
    spa: int = Field(default=0, ge=0, le=32)
    spd: int = Field(default=0, ge=0, le=32)
    spe: int = Field(default=0, ge=0, le=32)

    model_config = {"populate_by_name": True}


class IvSpread(BaseModel):
    hp: int = Field(default=31, ge=0, le=31)
    atk: int = Field(default=31, ge=0, le=31)
    def_: int = Field(default=31, alias="def", ge=0, le=31)
    spa: int = Field(default=31, ge=0, le=31)
    spd: int = Field(default=31, ge=0, le=31)
    spe: int = Field(default=31, ge=0, le=31)

    model_config = {"populate_by_name": True}


class PokemonImageAssets(BaseModel):
    primary_artwork_url: str | None = Field(default=None, alias="primaryArtworkUrl")
    fallback_artwork_url: str | None = Field(default=None, alias="fallbackArtworkUrl")
    sprite_url: str | None = Field(default=None, alias="spriteUrl")
    source_name: str = Field(default="pokemon-official+pokedex-pokeapi", alias="sourceName")
    hotlink_policy: str = Field(default="unknown", alias="hotlinkPolicy")

    model_config = {"populate_by_name": True}


class PokemonSpecies(BaseModel):
    pokemon_id: str = Field(alias="pokemonId")
    name_en: str = Field(alias="nameEn")
    name_ko: str = Field(alias="nameKo")
    species_id: str = Field(alias="speciesId")
    species_name_en: str = Field(alias="speciesNameEn")
    species_name_ko: str = Field(alias="speciesNameKo")
    national_dex_number: int = Field(alias="nationalDexNumber")
    pokemon_champions_code: str = Field(alias="pokemonChampionsCode")
    base_stats: BaseStats = Field(alias="baseStats")
    image_assets: PokemonImageAssets = Field(alias="imageAssets")
    types: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class PokemonBuild(BaseModel):
    pokemon_id: str = Field(alias="pokemonId")
    pokemon_name: str = Field(alias="pokemonName")
    national_dex_number: int | None = Field(default=None, alias="nationalDexNumber")
    image_assets: PokemonImageAssets | None = Field(default=None, alias="imageAssets")
    base_stats_snapshot: BaseStats = Field(alias="baseStatsSnapshot")
    level: int = Field(default=50, ge=1, le=100)
    nature: str = "Neutral"
    ability: str | None = None
    item: str | None = None
    evs: StatSpread = Field(default_factory=StatSpread)
    stat_points: StatPointSpread = Field(default_factory=StatPointSpread, alias="statPoints")
    ivs: IvSpread = Field(default_factory=IvSpread)
    speed_stage: int = Field(default=0, alias="speedStage", ge=-6, le=6)
    weather: str | None = None
    status: str | None = None
    tailwind: bool = False
    item_consumed: bool = Field(default=False, alias="itemConsumed")

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


class QuizQuestionCandidate(BaseModel):
    """AI- or server-generated structured question candidate.

    Candidates intentionally contain no trusted answer, speed value, statement,
    or explanation. The server validates and computes those from the rules engine.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    difficulty: Difficulty
    mode: Literal["IS_FASTER"] = "IS_FASTER"
    subject: PokemonBuild
    opponent: PokemonBuild
    ruleset_version: str = Field(default="pokemon_champions:speed:v1", alias="rulesetVersion")

    model_config = {"populate_by_name": True}


class ValidatedQuizQuestion(BaseModel):
    """Rules-engine result for a candidate, still independent from prose."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    candidate_id: str = Field(alias="candidateId")
    difficulty: Difficulty
    mode: Literal["IS_FASTER"] = "IS_FASTER"
    answer_type: Literal["YES_NO"] = Field(default="YES_NO", alias="answerType")
    correct_answer: bool = Field(alias="correctAnswer")
    subject: QuizPokemonCase
    opponent: QuizPokemonCase
    validation: dict[str, object]
    ruleset_version: str = Field(default="pokemon_champions:speed:v1", alias="rulesetVersion")

    model_config = {"populate_by_name": True}


class RenderQuestionRequest(BaseModel):
    question: ValidatedQuizQuestion
    locale: Literal["ko", "en"] = "ko"


class QuizQuestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    validated_question_id: str | None = Field(default=None, alias="validatedQuestionId")
    difficulty: Difficulty
    mode: Literal["IS_FASTER"] = "IS_FASTER"
    statement: str
    answer_type: Literal["YES_NO"] = Field(default="YES_NO", alias="answerType")
    correct_answer: bool = Field(alias="correctAnswer")
    subject: QuizPokemonCase
    opponent: QuizPokemonCase
    explanation: str
    ruleset_version: str = Field(default="pokemon_champions:speed:v1", alias="rulesetVersion")

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
