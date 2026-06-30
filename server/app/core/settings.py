from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables.

    Secrets must be provided through `.env` or the deployment environment and
    must never be committed to the repository.
    """

    openai_api_key: str | None
    openai_base_url: str
    openai_candidate_model: str
    openai_render_model: str
    ai_question_generation_enabled: bool
    ai_question_rendering_enabled: bool
    ai_timeout_seconds: float
    ai_candidate_batch_multiplier: int
    ai_max_generation_attempts: int
    aws_region: str
    pokemon_species_source: str
    pokemon_species_table_name: str
    pokemon_options_table_name: str

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_candidate_model=os.getenv("OPENAI_CANDIDATE_MODEL", "gpt-5.4-mini"),
        openai_render_model=os.getenv("OPENAI_RENDER_MODEL", "gpt-5.4-mini"),
        ai_question_generation_enabled=_bool_env("AI_QUESTION_GENERATION_ENABLED", False),
        ai_question_rendering_enabled=_bool_env("AI_QUESTION_RENDERING_ENABLED", False),
        ai_timeout_seconds=_float_env("AI_TIMEOUT_SECONDS", 30.0),
        ai_candidate_batch_multiplier=max(1, _int_env("AI_CANDIDATE_BATCH_MULTIPLIER", 2)),
        ai_max_generation_attempts=max(1, _int_env("AI_MAX_GENERATION_ATTEMPTS", 3)),
        aws_region=os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "ap-northeast-2")),
        pokemon_species_source=os.getenv("POKEMON_SPECIES_SOURCE", "dynamodb").strip().lower(),
        pokemon_species_table_name=os.getenv("POKEMON_SPECIES_TABLE_NAME", "pokemon-species"),
        pokemon_options_table_name=os.getenv("POKEMON_OPTIONS_TABLE_NAME", "pokemon-options"),
    )
