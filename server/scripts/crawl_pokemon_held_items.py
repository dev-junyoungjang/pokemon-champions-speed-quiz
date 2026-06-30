#!/usr/bin/env python3
"""Crawl Pokémon Champions held-item options into reviewable JSONL.

The Regulation M-B news page links an official held-item page, but as of the
current crawl that page exposes no explicit allow/ban arrays. To keep the data
usable and auditable, this exporter records the official page as the rules
source and enriches battle-relevant held-item categories from PokeAPI.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

REGULATION_SET = "M-B"
RULESET = "pokemon_champions"
PARSER_VERSION = "regulation-m-b-held-item-crawler:v1"
OFFICIAL_EVENT_ID = "rs178066986988lmoqpm"
OFFICIAL_ITEM_URL_TEMPLATE = (
    "https://web-view.app.pokemonchampions.jp/battle/pages/events/"
    f"{OFFICIAL_EVENT_ID}" + "/{lang}/item.html"
)
POKEAPI_BASE = "https://pokeapi.co/api/v2"
USER_AGENT = "pokemon-champions-speed-quiz-crawler/1.0 (+local-jsonl-export)"
ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "server" / "data" / "cache" / "pokeapi"
CURATED_FILE = ROOT / "server" / "data" / "curated" / "pokemon_held_items_regulation_m_b.jsonl"
REJECTED_FILE = ROOT / "server" / "data" / "rejected" / "pokemon_held_items_regulation_m_b_rejected.jsonl"

# PokeAPI categories that represent items intended to be held in battle.
# Excludes generational mechanics that Pokémon Champions does not currently use
# as held-item rules data here (Z-Crystals, Memories, Tera Shards, etc.).
HELD_ITEM_CATEGORIES = [
    "held-items",
    "choice",
    "bad-held-items",
    "plates",
    "species-specific",
    "type-enhancement",
    "mega-stones",
]


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_") + ".json"


def fetch_text(url: str, *, use_cache: bool = True) -> str:
    cache_path = CACHE_DIR / "http" / safe_filename(url)
    if use_cache and cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8")
    if use_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")
    return text


def fetch_json(url: str, *, use_cache: bool = True) -> dict[str, Any]:
    cache_path = CACHE_DIR / "http" / safe_filename(url)
    if use_cache and cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    if use_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(0.05)
    return data


def pokeapi(path_or_url: str) -> dict[str, Any]:
    url = path_or_url if path_or_url.startswith("http") else f"{POKEAPI_BASE}/{path_or_url.lstrip('/')}"
    return fetch_json(url)


def language_name(names: list[dict[str, Any]], lang: str) -> str | None:
    for entry in names:
        if entry.get("language", {}).get("name") == lang:
            return entry.get("name")
    return None


def official_item_url(lang: str) -> str:
    return OFFICIAL_ITEM_URL_TEMPLATE.format(lang=lang)


def official_page_has_explicit_item_data(lang: str) -> bool:
    html = fetch_text(official_item_url(lang))
    return "const items" in html or "const canItems" in html or "const cannotItems" in html


def category_item_links() -> dict[str, set[str]]:
    by_item: dict[str, set[str]] = {}
    for category_id in HELD_ITEM_CATEGORIES:
        category = pokeapi(f"item-category/{category_id}")
        for item in category.get("items", []):
            by_item.setdefault(item["name"], set()).add(category_id)
    return by_item


def item_record(item_id: str, categories: set[str], crawled_at: str) -> dict[str, Any]:
    item = pokeapi(f"item/{item_id}")
    name_en = language_name(item.get("names", []), "en") or item.get("name", item_id).replace("-", " ").title()
    name_ko = language_name(item.get("names", []), "ko") or name_en
    effect_en = language_name(item.get("effect_entries", []), "en")
    flavor_en = language_name(item.get("flavor_text_entries", []), "en")
    attributes = [entry["name"] for entry in item.get("attributes", [])]
    return {
        "pk": f"RULESET#{RULESET}#REGULATION#{REGULATION_SET}#HELD_ITEM",
        "sk": f"ITEM#{item_id}",
        "entityType": "PokemonHeldItemOption",
        "ruleset": RULESET,
        "regulationSet": REGULATION_SET,
        "itemId": item_id,
        "nameEn": name_en,
        "nameKo": name_ko,
        "eligible": True,
        "categories": sorted(categories),
        "cost": item.get("cost"),
        "flingPower": item.get("fling_power"),
        "flingEffect": item.get("fling_effect", {}).get("name") if item.get("fling_effect") else None,
        "attributes": attributes,
        "spriteUrl": item.get("sprites", {}).get("default"),
        "effectEn": effect_en,
        "flavorTextEn": flavor_en,
        "source": {
            "name": "official-pokemon-champions-regulation+pokeapi-held-item-enrichment",
            "officialItemUrlEn": official_item_url("en"),
            "officialItemUrlKo": official_item_url("ko"),
            "pokeapiItemUrl": f"{POKEAPI_BASE}/item/{item_id}",
            "pokeapiCategories": sorted(categories),
            "crawledAt": crawled_at,
            "parserVersion": PARSER_VERSION,
            "confidence": "official_page_present_no_explicit_item_arrays_pokeapi_battle_held_item_categories",
        },
    }


def build_records(crawled_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    explicit_pages = [lang for lang in ("en", "ko") if official_page_has_explicit_item_data(lang)]
    if explicit_pages:
        raise RuntimeError("Official item pages now expose explicit arrays; update crawler to parse them before exporting.")

    records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item_id, categories in sorted(category_item_links().items()):
        try:
            records.append(item_record(item_id, categories, crawled_at))
        except Exception as exc:  # noqa: BLE001 - export rejected rows for review
            rejected.append({
                "pk": f"REJECTED#{RULESET}#REGULATION#{REGULATION_SET}#HELD_ITEM",
                "sk": f"{crawled_at}#{item_id}",
                "entityType": "RejectedPokemonHeldItemOption",
                "itemId": item_id,
                "categories": sorted(categories),
                "reason": "held_item_enrichment_failed",
                "error": str(exc),
            })
    return records, rejected


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl Pokémon Champions held-item options.")
    parser.add_argument("--crawled-at", default=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    parser.add_argument("--fail-on-rejected", action="store_true")
    args = parser.parse_args()

    records, rejected = build_records(args.crawled_at)
    records.sort(key=lambda record: record["nameEn"])
    write_jsonl(CURATED_FILE, records)
    write_jsonl(REJECTED_FILE, rejected)

    print(f"records={len(records)} {CURATED_FILE.relative_to(ROOT)}")
    print(f"rejected={len(rejected)} {REJECTED_FILE.relative_to(ROOT)}")
    if rejected and args.fail_on_rejected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
