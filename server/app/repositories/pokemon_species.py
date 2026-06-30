from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.settings import get_settings
from app.models.domain import PokemonBattleOptions, PokemonMoveOption, PokemonSpecies


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "curated" / "pokemon_species_regulation_m_b.jsonl"
MOVE_OPTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "curated" / "pokemon_move_options_sample.json"
BATTLE_OPTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "curated" / "pokemon_battle_options_regulation_m_b.json"
REGULATION_SPECIES_PK = "SPECIES#pokemon_champions#REGULATION#M-B"
REGULATION_OPTIONS_PK = "OPTIONS#pokemon_champions#REGULATION#M-B"

MEGA_STONE_ITEM_EXCEPTIONS = {
    "abomasnow": "abomasite",
    "alakazam": "alakazite",
    "altaria": "altarianite",
    "audino": "audinite",
    "blastoise": "blastoisinite",
    "diancie": "diancite",
    "gallade": "galladite",
    "glalie": "glalitite",
    "heracross": "heracronite",
    "houndoom": "houndoominite",
    "kyogre": "blue-orb",
    "latias": "latiasite",
    "latios": "latiosite",
    "lopunny": "lopunnite",
    "lucario": "lucarionite",
    "manectric": "manectite",
    "meowstic-female": "meowsticite",
    "meowstic-male": "meowsticite",
    "rayquaza": None,
    "sableye": "sablenite",
    "sharpedo": "sharpedonite",
    "slowbro": "slowbronite",
}


def mega_stone_item_id_for_pokemon_id(pokemon_id: str) -> str | None:
    if "-mega" not in pokemon_id:
        return None

    parent_id = pokemon_id.split("-mega", 1)[0]
    suffix = pokemon_id.split("-mega", 1)[1].strip("-")
    if parent_id in MEGA_STONE_ITEM_EXCEPTIONS:
        base_item_id = MEGA_STONE_ITEM_EXCEPTIONS[parent_id]
    elif parent_id.endswith("e"):
        base_item_id = f"{parent_id[:-1]}ite"
    else:
        base_item_id = f"{parent_id}ite"

    if base_item_id is None:
        return None
    return f"{base_item_id}-{suffix}" if suffix else base_item_id


class PokemonSpeciesDataSourceError(RuntimeError):
    pass


def normalize_species_query(value: str) -> str:
    return re.sub(r"[\s._]+", "-", value.strip().lower())


def _species_aliases(species: PokemonSpecies) -> set[str]:
    return {
        normalize_species_query(species.pokemon_id),
        normalize_species_query(species.name_en),
        normalize_species_query(species.name_ko),
        normalize_species_query(species.species_id),
        normalize_species_query(species.species_name_en),
        normalize_species_query(species.species_name_ko),
        str(species.national_dex_number),
        f"{species.national_dex_number:03d}",
        normalize_species_query(species.pokemon_champions_code),
    }


@lru_cache(maxsize=1)
def load_legacy_move_options() -> dict[str, list[PokemonMoveOption]]:
    if not MOVE_OPTIONS_PATH.exists():
        return {}

    raw_catalog = json.loads(MOVE_OPTIONS_PATH.read_text(encoding="utf-8"))
    return {
        normalize_species_query(pokemon_id): [PokemonMoveOption.model_validate(move) for move in moves]
        for pokemon_id, moves in raw_catalog.items()
    }


@lru_cache(maxsize=1)
def load_local_battle_options() -> dict[str, PokemonBattleOptions]:
    if not BATTLE_OPTIONS_PATH.exists():
        return {
            pokemon_id: PokemonBattleOptions(pokemonId=pokemon_id, availableMoves=moves)
            for pokemon_id, moves in load_legacy_move_options().items()
        }

    raw_options = json.loads(BATTLE_OPTIONS_PATH.read_text(encoding="utf-8"))
    if isinstance(raw_options, dict):
        iterable = raw_options.values()
    else:
        iterable = raw_options
    return {
        normalize_species_query(option.pokemon_id): option
        for option in (PokemonBattleOptions.model_validate(item) for item in iterable)
    }


def _merge_battle_options(species: PokemonSpecies, options: PokemonBattleOptions | None) -> PokemonSpecies:
    if options is None:
        return _with_mega_stone_item(species)
    return _with_mega_stone_item(species.model_copy(
        update={
            "available_abilities": options.available_abilities,
            "available_moves": options.available_moves,
        }
    ))


def _with_mega_stone_item(species: PokemonSpecies) -> PokemonSpecies:
    if species.mega_stone_item_id:
        return species
    mega_stone_item_id = mega_stone_item_id_for_pokemon_id(species.pokemon_id)
    if mega_stone_item_id is None:
        return species
    return species.model_copy(update={"mega_stone_item_id": mega_stone_item_id})


def _with_local_battle_options(species: PokemonSpecies) -> PokemonSpecies:
    return _merge_battle_options(species, load_local_battle_options().get(species.pokemon_id))


@lru_cache(maxsize=1)
def load_local_regulation_species() -> tuple[PokemonSpecies, ...]:
    species: list[PokemonSpecies] = []
    with DATA_PATH.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            item = PokemonSpecies.model_validate(json.loads(line))
            species.append(_with_local_battle_options(item))
    return tuple(species)


@lru_cache(maxsize=8)
def load_dynamodb_battle_options(table_name: str, region_name: str) -> dict[str, PokemonBattleOptions]:
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=region_name,
            config=Config(connect_timeout=1, read_timeout=2, retries={"max_attempts": 1}),
        )
        table = cast(Any, dynamodb).Table(table_name)
        items: list[dict[str, Any]] = []
        query_kwargs: dict[str, Any] = {"KeyConditionExpression": Key("pk").eq(REGULATION_OPTIONS_PK)}
        while True:
            response = table.query(**query_kwargs)
            items.extend(response.get("Items", []))
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
            query_kwargs["ExclusiveStartKey"] = last_evaluated_key
    except (BotoCoreError, ClientError, TimeoutError) as exc:
        raise PokemonSpeciesDataSourceError(
            f"Failed to load Pokémon battle options from DynamoDB table {table_name!r}: {exc}"
        ) from exc

    return {
        normalize_species_query(option.pokemon_id): option
        for option in (PokemonBattleOptions.model_validate(item) for item in items)
    }


@lru_cache(maxsize=8)
def load_dynamodb_regulation_species(table_name: str, region_name: str, options_table_name: str | None = None) -> tuple[PokemonSpecies, ...]:
    try:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=region_name,
            config=Config(connect_timeout=1, read_timeout=2, retries={"max_attempts": 1}),
        )
        table = cast(Any, dynamodb).Table(table_name)
        items: list[dict[str, Any]] = []
        query_kwargs: dict[str, Any] = {"KeyConditionExpression": Key("pk").eq(REGULATION_SPECIES_PK)}
        while True:
            response = table.query(**query_kwargs)
            items.extend(response.get("Items", []))
            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
            query_kwargs["ExclusiveStartKey"] = last_evaluated_key
    except (BotoCoreError, ClientError, TimeoutError) as exc:
        raise PokemonSpeciesDataSourceError(
            f"Failed to load Pokémon species from DynamoDB table {table_name!r}: {exc}"
        ) from exc

    options = load_local_battle_options()
    if options_table_name:
        try:
            options = {**options, **load_dynamodb_battle_options(options_table_name, region_name)}
        except PokemonSpeciesDataSourceError:
            pass

    species = tuple(
        _merge_battle_options(PokemonSpecies.model_validate(item), options.get(normalize_species_query(item.get("pokemonId", ""))))
        for item in items
    )
    if not species:
        raise PokemonSpeciesDataSourceError(f"DynamoDB table {table_name!r} returned no Pokémon species items")
    return species


@lru_cache(maxsize=8)
def load_regulation_species(
    source: str | None = None,
    table_name: str | None = None,
    region_name: str | None = None,
    options_table_name: str | None = None,
) -> tuple[PokemonSpecies, ...]:
    settings = get_settings()
    source = source or settings.pokemon_species_source
    table_name = table_name or settings.pokemon_species_table_name
    region_name = region_name or settings.aws_region
    options_table_name = options_table_name or settings.pokemon_options_table_name

    if source == "local":
        return load_local_regulation_species()

    try:
        return load_dynamodb_regulation_species(table_name, region_name, options_table_name)
    except PokemonSpeciesDataSourceError:
        # Local JSONL is kept as a reviewed fallback so local development and tests
        # still work when AWS credentials are not present.
        return load_local_regulation_species()


@lru_cache(maxsize=8)
def species_index(
    source: str | None = None,
    table_name: str | None = None,
    region_name: str | None = None,
    options_table_name: str | None = None,
) -> dict[str, PokemonSpecies]:
    index: dict[str, PokemonSpecies] = {}
    for species in load_regulation_species(source, table_name, region_name, options_table_name):
        for alias in _species_aliases(species):
            index.setdefault(alias, species)
    return index


def get_species_by_query(query: str) -> PokemonSpecies | None:
    return species_index().get(normalize_species_query(query))


def list_species() -> list[PokemonSpecies]:
    return list(load_regulation_species())
