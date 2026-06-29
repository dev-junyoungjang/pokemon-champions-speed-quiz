from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.models.domain import PokemonMoveOption, PokemonSpecies


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "curated" / "pokemon_species_regulation_m_b.jsonl"
MOVE_OPTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "curated" / "pokemon_move_options_sample.json"


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
def load_move_options() -> dict[str, list[PokemonMoveOption]]:
    if not MOVE_OPTIONS_PATH.exists():
        return {}

    raw_catalog = json.loads(MOVE_OPTIONS_PATH.read_text(encoding="utf-8"))
    return {
        normalize_species_query(pokemon_id): [PokemonMoveOption.model_validate(move) for move in moves]
        for pokemon_id, moves in raw_catalog.items()
    }


@lru_cache(maxsize=1)
def load_regulation_species() -> tuple[PokemonSpecies, ...]:
    move_catalog = load_move_options()
    species: list[PokemonSpecies] = []
    with DATA_PATH.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            item = PokemonSpecies.model_validate(json.loads(line))
            species.append(item.model_copy(update={"available_moves": move_catalog.get(item.pokemon_id, [])}))
    return tuple(species)


@lru_cache(maxsize=1)
def species_index() -> dict[str, PokemonSpecies]:
    index: dict[str, PokemonSpecies] = {}
    for species in load_regulation_species():
        for alias in _species_aliases(species):
            index.setdefault(alias, species)
    return index


def get_species_by_query(query: str) -> PokemonSpecies | None:
    return species_index().get(normalize_species_query(query))


def list_species() -> list[PokemonSpecies]:
    return list(load_regulation_species())
