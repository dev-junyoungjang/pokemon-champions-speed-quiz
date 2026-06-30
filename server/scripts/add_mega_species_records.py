#!/usr/bin/env python3
"""Add Mega form records to the curated Regulation M-B species JSONL.

The official Regulation M-B roster lists eligible species/forms, while Pokémon
Champions battle data also exposes Mega forms for eligible species. This script
keeps the original official roster records and appends synthetic species records
for those Mega forms so `pokemon-species` and `pokemon-options` share the same
`pokemonId` lookup keys.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPECIES_FILE = ROOT / "data" / "curated" / "pokemon_species_regulation_m_b.jsonl"
DEFAULT_OPTIONS_FILE = ROOT / "data" / "curated" / "pokemon_battle_options_regulation_m_b.json"
PARSER_VERSION = "mega-species-augmenter:v1"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def pokeapi_id_from_url(url: str | None) -> int | None:
    if not url:
        return None
    match = re.search(r"/pokemon/(\d+)/?$", url)
    return int(match.group(1)) if match else None


def image_assets_for_mega(pokeapi_pokemon_id: int | None, national_dex_number: int) -> dict[str, str | None]:
    sprite_id = pokeapi_pokemon_id or national_dex_number
    return {
        "primaryArtworkUrl": None,
        "fallbackArtworkUrl": (
            "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/"
            f"other/official-artwork/{sprite_id}.png"
        ),
        "spriteUrl": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{sprite_id}.png",
        "sourceName": "pokeapi-mega-form-sprites",
        "hotlinkPolicy": "unknown",
    }


def mega_species_record(option: dict[str, Any], parent: dict[str, Any]) -> dict[str, Any]:
    source = option.get("source", {})
    pokeapi_pokemon_id = pokeapi_id_from_url(source.get("pokeapiPokemonUrl"))
    parent_code = parent.get("pokemonChampionsCode", f"{option['nationalDexNumber']:04d}-000")
    parent_source = parent.get("source", {})
    record = {
        "pk": parent["pk"],
        "sk": f"POKEMON#{option['pokemonId']}",
        "entityType": "PokemonSpecies",
        "ruleset": option.get("ruleset", parent.get("ruleset")),
        "regulationSet": option.get("regulationSet", parent.get("regulationSet")),
        "pokemonChampionsCode": f"{parent_code}#MEGA#{option['pokemonId']}",
        "eligibleOrder": parent.get("eligibleOrder"),
        "pokemonId": option["pokemonId"],
        "speciesId": option["speciesId"],
        "formId": option["pokemonId"],
        "formKind": "mega",
        "megaParentPokemonId": option.get("megaParentPokemonId") or parent["pokemonId"],
        "nationalDexNumber": option["nationalDexNumber"],
        "nameEn": option["nameEn"],
        "nameKo": option["nameKo"],
        "speciesNameEn": parent.get("speciesNameEn", parent.get("nameEn")),
        "speciesNameKo": parent.get("speciesNameKo", parent.get("nameKo")),
        "types": option["types"],
        "baseStats": option["baseStats"],
        "imageAssets": image_assets_for_mega(pokeapi_pokemon_id, option["nationalDexNumber"]),
        "availability": {
            "status": "available_via_mega_evolution",
            "sourceUrl": parent.get("availability", {}).get("sourceUrl") or parent_source.get("officialRosterUrlEn"),
            "sourceUrlKo": parent.get("availability", {}).get("sourceUrlKo") or parent_source.get("officialRosterUrlKo"),
            "regulationSet": option.get("regulationSet", parent.get("regulationSet")),
            "parentPokemonId": option.get("megaParentPokemonId") or parent["pokemonId"],
        },
        "source": {
            "name": "official-pokemon-champions-roster+pokeapi-mega-form-enrichment",
            "officialRosterUrlEn": parent_source.get("officialRosterUrlEn") or parent.get("availability", {}).get("sourceUrl"),
            "officialRosterUrlKo": parent_source.get("officialRosterUrlKo") or parent.get("availability", {}).get("sourceUrlKo"),
            "pokeapiPokemonUrl": source.get("pokeapiPokemonUrl"),
            "pokeapiVersionGroup": source.get("pokeapiVersionGroup"),
            "crawledAt": source.get("crawledAt"),
            "parserVersion": PARSER_VERSION,
            "confidence": "mega_form_from_pokeapi_for_regulation_eligible_species",
        },
    }
    if "dataQuality" in option:
        record["dataQuality"] = option["dataQuality"]
    if "inferredFromPokemonId" in option:
        record["inferredFromPokemonId"] = option["inferredFromPokemonId"]
        record["source"] = {
            **record["source"],
            "confidence": option.get("source", {}).get("confidence", record["source"]["confidence"]),
            "inferredFromPokemonId": option["inferredFromPokemonId"],
            "inferenceReason": option.get("source", {}).get("inferenceReason"),
        }
    return record


def has_complete_battle_identity(option: dict[str, Any]) -> bool:
    required_stats = {"hp", "atk", "def", "spa", "spd", "spe"}
    base_stats = option.get("baseStats")
    return isinstance(base_stats, dict) and required_stats.issubset(base_stats) and bool(option.get("types"))


def build_augmented_species(species_rows: list[dict[str, Any]], option_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    non_mega_species = [row for row in species_rows if row.get("formKind") != "mega" and "-mega" not in row.get("pokemonId", "")]
    by_pokemon_id = {row["pokemonId"]: row for row in non_mega_species}
    by_species_id = {row["speciesId"]: row for row in non_mega_species}
    existing_ids = {row["pokemonId"] for row in non_mega_species}

    mega_records: list[dict[str, Any]] = []
    skipped = 0
    for option in option_rows:
        if option.get("formKind") != "mega":
            continue
        if option["pokemonId"] in existing_ids or not has_complete_battle_identity(option):
            skipped += 1
            continue
        parent_id = option.get("megaParentPokemonId")
        parent = by_pokemon_id.get(parent_id) or by_species_id.get(option["speciesId"])
        if parent is None:
            skipped += 1
            continue
        mega_records.append(mega_species_record(option, parent))
        existing_ids.add(option["pokemonId"])

    mega_records.sort(key=lambda row: (row["nationalDexNumber"], row["pokemonId"]))
    return non_mega_species + mega_records, len(mega_records), skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Append Mega form records to the curated species JSONL.")
    parser.add_argument("--species-file", type=Path, default=DEFAULT_SPECIES_FILE)
    parser.add_argument("--options-file", type=Path, default=DEFAULT_OPTIONS_FILE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    species_rows = read_jsonl(args.species_file)
    option_rows = json.loads(args.options_file.read_text(encoding="utf-8"))
    augmented_rows, added, skipped = build_augmented_species(species_rows, option_rows)

    print(f"input_species={len(species_rows)} output_species={len(augmented_rows)} added_mega={added} skipped={skipped}")
    if args.dry_run:
        print("dry-run only: no file writes performed")
        return
    write_jsonl(args.species_file, augmented_rows)
    print(f"wrote {args.species_file}")


if __name__ == "__main__":
    main()
