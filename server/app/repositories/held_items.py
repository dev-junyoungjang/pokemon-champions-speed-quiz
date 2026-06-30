from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_HELD_ITEMS_FILE = ROOT / "server" / "data" / "curated" / "pokemon_held_items_regulation_m_b.jsonl"


def normalize_query(value: str) -> str:
    return value.casefold().replace("-", " ").strip()


@lru_cache(maxsize=1)
def list_held_items() -> list[dict[str, Any]]:
    if not DEFAULT_HELD_ITEMS_FILE.exists():
        return []
    items: list[dict[str, Any]] = []
    for line in DEFAULT_HELD_ITEMS_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(json.loads(line))
    return items


def mega_stone_name_en(pokemon_name_en: str, item_id: str) -> str:
    normalized = pokemon_name_en.replace("Mega ", "").replace(" Mega", "").strip()
    suffix = item_id.rsplit("-", 1)[-1].upper() if item_id.endswith(("-x", "-y", "-z")) else ""
    base = normalized.replace(" X", "").replace(" Y", "").replace(" Z", "").strip()
    return f"{base}ite {suffix}".strip()


def mega_stone_name_ko(pokemon_name_ko: str, item_id: str) -> str:
    suffix = item_id.rsplit("-", 1)[-1].upper() if item_id.endswith(("-x", "-y", "-z")) else ""
    if pokemon_name_ko.startswith("메가"):
        base = pokemon_name_ko.removeprefix("메가").removesuffix("X").removesuffix("Y").removesuffix("Z")
        return f"{base}나이트{suffix}"
    return mega_stone_name_en(pokemon_name_ko, item_id)


def inferred_mega_stone_items(existing_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from app.repositories.pokemon_species import list_species

    existing_ids = {item["itemId"] for item in existing_items}
    inferred: list[dict[str, Any]] = []
    for species in list_species():
        item_id = species.mega_stone_item_id
        if not item_id or item_id in existing_ids:
            continue
        inferred.append({
            "pk": "RULESET#pokemon_champions#REGULATION#M-B#HELD_ITEM",
            "sk": f"ITEM#{item_id}",
            "entityType": "PokemonHeldItemOption",
            "ruleset": "pokemon_champions",
            "regulationSet": "M-B",
            "itemId": item_id,
            "nameEn": mega_stone_name_en(species.name_en, item_id),
            "nameKo": mega_stone_name_ko(species.name_ko, item_id),
            "eligible": True,
            "categories": ["mega-stones", "inferred-champions-mega-stones"],
            "spriteUrl": None,
            "source": {
                "name": "pokemon-champions-mega-species-derived-held-item",
                "pokemonId": species.pokemon_id,
                "confidence": "inferred_from_champions_mega_form_when_pokeapi_item_is_unavailable",
            },
        })
        existing_ids.add(item_id)
    return sorted(inferred, key=lambda item: item["nameEn"])


@lru_cache(maxsize=1)
def list_held_items_with_inferred() -> list[dict[str, Any]]:
    items = list_held_items()
    return items + inferred_mega_stone_items(items)


def get_held_items_by_query(query: str | None = None) -> list[dict[str, Any]]:
    items = list_held_items_with_inferred()
    if not query:
        return items

    normalized = normalize_query(query)
    return [
        item for item in items
        if normalized in normalize_query(item.get("itemId", ""))
        or normalized in normalize_query(item.get("nameEn", ""))
        or normalized in normalize_query(item.get("nameKo", ""))
    ]
