from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.models.domain import PokemonSpecies


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "curated" / "pokemon_species_regulation_m_b.jsonl"


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
def load_regulation_species() -> tuple[PokemonSpecies, ...]:
    with DATA_PATH.open(encoding="utf-8") as file:
        return tuple(PokemonSpecies.model_validate(json.loads(line)) for line in file if line.strip())


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
