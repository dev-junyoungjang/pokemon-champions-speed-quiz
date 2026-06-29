#!/usr/bin/env python3
"""Crawl Pokémon Champions Regulation M-B eligible Pokémon into JSONL files.

This script intentionally writes local JSONL artifacts first instead of writing
straight to DynamoDB. The curated output is shaped like DynamoDB items so it can
be batch-written or imported later after review.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REGULATION_SET = "M-B"
RULESET = "pokemon_champions"
PARSER_VERSION = "regulation-m-b-crawler:v1"
OFFICIAL_EVENT_ID = "rs178066986988lmoqpm"
OFFICIAL_ROSTER_URL_TEMPLATE = (
    "https://web-view.app.pokemonchampions.jp/battle/pages/events/"
    f"{OFFICIAL_EVENT_ID}" + "/{lang}/pokemon.html"
)
POKEAPI_BASE = "https://pokeapi.co/api/v2"
USER_AGENT = "pokemon-champions-speed-quiz-crawler/1.0 (+local-jsonl-export)"

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "server" / "data" / "cache" / "pokeapi"
RAW_DIR = ROOT / "server" / "data" / "raw" / "champions"
CURATED_DIR = ROOT / "server" / "data" / "curated"
REJECTED_DIR = ROOT / "server" / "data" / "rejected"


def fetch_text(url: str, *, use_cache: bool = True) -> str:
    cache_path = CACHE_DIR / "http" / safe_filename(url)
    if use_cache and cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        text = body.decode("utf-8")

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
        # Be polite to PokeAPI when filling the cache for the first time.
        time.sleep(0.05)
    return data


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_") + ".json"


def official_roster_url(lang: str) -> str:
    return OFFICIAL_ROSTER_URL_TEMPLATE.format(lang=lang)


def crawl_official_roster(lang: str) -> list[list[Any]]:
    html = fetch_text(official_roster_url(lang))
    match = re.search(r"const pokemons = (\[.*?\]);", html, re.S)
    if not match:
        raise RuntimeError(f"Could not find official pokemons array for lang={lang}")
    return json.loads(match.group(1))


def normalize_name(value: str) -> str:
    value = value.lower().replace("pokémon", "pokemon").replace("é", "e")
    value = value.replace("♀", " f").replace("♂", " m")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def language_name(names: list[dict[str, Any]], lang: str) -> str | None:
    for entry in names:
        if entry.get("language", {}).get("name") == lang:
            return entry.get("name")
    return None


def pokeapi(path_or_url: str) -> dict[str, Any]:
    if path_or_url.startswith("http"):
        url = path_or_url
    else:
        url = f"{POKEAPI_BASE}/{path_or_url.lstrip('/')}"
    return fetch_json(url)


def pokemon_stats(pokemon: dict[str, Any]) -> dict[str, int]:
    key_map = {
        "hp": "hp",
        "attack": "atk",
        "defense": "def",
        "special-attack": "spa",
        "special-defense": "spd",
        "speed": "spe",
    }
    stats: dict[str, int] = {}
    for item in pokemon["stats"]:
        source_name = item["stat"]["name"]
        stats[key_map[source_name]] = item["base_stat"]
    return stats


def pokemon_types(pokemon: dict[str, Any]) -> list[str]:
    return [slot["type"]["name"] for slot in sorted(pokemon["types"], key=lambda entry: entry["slot"])]


def image_assets(national_dex_number: int) -> dict[str, str]:
    padded = f"{national_dex_number:03d}"
    return {
        "primaryArtworkUrl": f"https://assets.pokemon.com/assets/cms2/img/pokedex/full/{padded}.png",
        "fallbackArtworkUrl": (
            "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
            f"other/official-artwork/{national_dex_number}.png"
        ),
        "spriteUrl": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{national_dex_number}.png",
        "sourceName": "pokemon-official+pokedex-pokeapi",
        "hotlinkPolicy": "unknown",
    }


def candidate_names(pokemon: dict[str, Any]) -> list[str]:
    names = [pokemon.get("name", "")]
    for form_link in pokemon.get("forms", []):
        form = pokeapi(form_link["url"])
        names.append(form.get("name", ""))
        names.append(form.get("form_name", ""))
        names.extend(
            entry["name"]
            for entry in form.get("names", [])
            if entry.get("language", {}).get("name") == "en"
        )
    return [name for name in names if name]


def target_aliases(official_name_en: str) -> list[str]:
    """Return normalized names that bridge official/PokeAPI form wording."""
    normalized = normalize_name(official_name_en)
    aliases = [normalized]
    base_name = official_name_en.split("(", 1)[0].strip()
    base_normalized = normalize_name(base_name)
    parenthetical_parts = [normalize_name(part) for part in re.findall(r"\(([^()]*)\)", official_name_en)]
    aliases.extend(part for part in parenthetical_parts if part)

    regional_prefixes = {
        "alolan form": "alolan",
        "galarian form": "galarian",
        "hisuian form": "hisuian",
        "paldean form": "paldean",
    }
    for form_text, prefix in regional_prefixes.items():
        if form_text in normalized:
            aliases.append(f"{prefix} {base_normalized}")
            aliases.append(f"{base_normalized} {prefix}")

    if "paldean form" in normalized:
        for breed in ("combat breed", "blaze breed", "aqua breed"):
            if breed in normalized:
                aliases.append(f"paldean {base_normalized} {breed}")
                aliases.append(f"paldean {breed} {base_normalized}")

    # PokeAPI calls this form "Super Gourgeist" while the official Champions
    # roster calls it "Jumbo Variety".
    if "gourgeist" in normalized and "jumbo" in normalized:
        aliases.append("super gourgeist")

    # Preserve order while deduplicating.
    return list(dict.fromkeys(alias for alias in aliases if alias))


def match_pokeapi_pokemon(national_dex_number: int, official_name_en: str, official_form_code: str) -> dict[str, Any]:
    if official_form_code == "000":
        return pokeapi(f"pokemon/{national_dex_number}")

    species = pokeapi(f"pokemon-species/{national_dex_number}")
    targets = target_aliases(official_name_en)
    best_score = -1.0
    best_pokemon: dict[str, Any] | None = None
    best_name = ""

    for variety in species["varieties"]:
        pokemon = pokeapi(variety["pokemon"]["url"])
        for candidate in candidate_names(pokemon):
            candidate_normalized = normalize_name(candidate)
            score = max(
                1.0 if candidate_normalized == target else
                0.98 if target in candidate_normalized else
                difflib.SequenceMatcher(None, target, candidate_normalized).ratio()
                for target in targets
            )
            if score > best_score:
                best_score = score
                best_pokemon = pokemon
                best_name = candidate

    if best_pokemon is None or best_score < 0.65:
        raise RuntimeError(
            "Could not match official form to PokeAPI variety: "
            f"dex={national_dex_number}, official={official_name_en}, "
            f"best={best_name}, score={best_score:.3f}"
        )
    return best_pokemon


def build_records(crawled_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    english = crawl_official_roster("en")
    korean = crawl_official_roster("ko")
    if len(english) != len(korean):
        raise RuntimeError(f"Official roster length mismatch: en={len(english)} ko={len(korean)}")

    raw_records: list[dict[str, Any]] = []
    curated_records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []

    for eligible_order, (en_entry, ko_entry) in enumerate(zip(english, korean), start=1):
        official_code, allowed_flag, name_en = en_entry
        ko_code, ko_allowed_flag, name_ko = ko_entry
        raw = {
            "regulationSet": REGULATION_SET,
            "ruleset": RULESET,
            "eligibleOrder": eligible_order,
            "pokemonChampionsCode": official_code,
            "allowedFlag": allowed_flag,
            "nameEn": name_en,
            "nameKo": name_ko,
            "source": {
                "name": "official-pokemon-champions-eligible-pokemon",
                "urlEn": official_roster_url("en"),
                "urlKo": official_roster_url("ko"),
                "crawledAt": crawled_at,
                "parserVersion": PARSER_VERSION,
            },
        }
        raw_records.append(raw)

        if official_code != ko_code or allowed_flag != ko_allowed_flag:
            rejected_records.append(
                {
                    "pk": f"REJECTED#{RULESET}#REGULATION#{REGULATION_SET}",
                    "sk": f"{crawled_at}#{official_code}",
                    "entityType": "RejectedPokemonSpecies",
                    "reason": "official_language_roster_mismatch",
                    "rawPayload": {"en": en_entry, "ko": ko_entry},
                    "source": raw["source"],
                }
            )
            continue

        national_dex_number = int(official_code.split("-")[0])
        official_form_code = official_code.split("-")[1]
        try:
            species = pokeapi(f"pokemon-species/{national_dex_number}")
            pokemon = match_pokeapi_pokemon(national_dex_number, name_en, official_form_code)
            pokemon_id = pokemon["name"]
            species_id = species["name"]
            form_id = "base" if official_form_code == "000" else pokemon_id
            species_name_en = language_name(species.get("names", []), "en") or name_en
            species_name_ko = language_name(species.get("names", []), "ko") or name_ko
            item = {
                "pk": f"SPECIES#{RULESET}#REGULATION#{REGULATION_SET}",
                "sk": f"POKEMON#{pokemon_id}",
                "entityType": "PokemonSpecies",
                "ruleset": RULESET,
                "regulationSet": REGULATION_SET,
                "pokemonChampionsCode": official_code,
                "eligibleOrder": eligible_order,
                "pokemonId": pokemon_id,
                "speciesId": species_id,
                "formId": form_id,
                "nationalDexNumber": national_dex_number,
                "nameEn": name_en,
                "nameKo": name_ko,
                "speciesNameEn": species_name_en,
                "speciesNameKo": species_name_ko,
                "types": pokemon_types(pokemon),
                "baseStats": pokemon_stats(pokemon),
                "imageAssets": image_assets(national_dex_number),
                "availability": {
                    "status": "available",
                    "sourceUrl": official_roster_url("en"),
                    "sourceUrlKo": official_roster_url("ko"),
                    "regulationSet": REGULATION_SET,
                },
                "source": {
                    "name": "official-pokemon-champions+pokedex-pokeapi",
                    "officialRosterUrlEn": official_roster_url("en"),
                    "officialRosterUrlKo": official_roster_url("ko"),
                    "pokeapiPokemonUrl": f"{POKEAPI_BASE}/pokemon/{pokemon['id']}/",
                    "pokeapiSpeciesUrl": f"{POKEAPI_BASE}/pokemon-species/{national_dex_number}/",
                    "crawledAt": crawled_at,
                    "parserVersion": PARSER_VERSION,
                    "confidence": "official_roster_with_pokeapi_enrichment",
                },
            }
            curated_records.append(item)
        except (RuntimeError, urllib.error.URLError, KeyError, ValueError) as exc:
            rejected_records.append(
                {
                    "pk": f"REJECTED#{RULESET}#REGULATION#{REGULATION_SET}",
                    "sk": f"{crawled_at}#{official_code}",
                    "entityType": "RejectedPokemonSpecies",
                    "pokemonChampionsCode": official_code,
                    "nameEn": name_en,
                    "nameKo": name_ko,
                    "reason": "pokeapi_enrichment_failed",
                    "error": str(exc),
                    "source": raw["source"],
                }
            )

    return raw_records, curated_records, rejected_records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--crawled-at", default=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    args = parser.parse_args()

    raw, curated, rejected = build_records(args.crawled_at)
    raw_path = RAW_DIR / "regulation_m_b_official_roster.jsonl"
    curated_path = CURATED_DIR / "pokemon_species_regulation_m_b.jsonl"
    rejected_path = REJECTED_DIR / "pokemon_species_regulation_m_b_rejected.jsonl"

    write_jsonl(raw_path, raw)
    write_jsonl(curated_path, curated)
    write_jsonl(rejected_path, rejected)

    print(f"raw={len(raw)} {raw_path.relative_to(ROOT)}")
    print(f"curated={len(curated)} {curated_path.relative_to(ROOT)}")
    print(f"rejected={len(rejected)} {rejected_path.relative_to(ROOT)}")
    if rejected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
