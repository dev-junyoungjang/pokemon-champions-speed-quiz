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


def get_held_items_by_query(query: str | None = None) -> list[dict[str, Any]]:
    items = list_held_items()
    if not query:
        return items

    normalized = normalize_query(query)
    return [
        item for item in items
        if normalized in normalize_query(item.get("itemId", ""))
        or normalized in normalize_query(item.get("nameEn", ""))
        or normalized in normalize_query(item.get("nameKo", ""))
    ]
