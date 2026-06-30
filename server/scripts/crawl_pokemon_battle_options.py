#!/usr/bin/env python3
"""Crawl Pokémon Champions battle options for Regulation M-B.

The official Champions roster tells us which Pokémon are legal. PokeAPI provides
Pokémon Champions version-group ability/move metadata. This script joins those
sources and writes reviewable local JSON artifacts shaped like pokemon-options
DynamoDB items.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.error
from pathlib import Path
from typing import Any

from crawl_regulation_mb import (
    CURATED_DIR,
    POKEAPI_BASE,
    REGULATION_SET,
    REJECTED_DIR,
    ROOT,
    RULESET,
    language_name,
    pokeapi,
    pokemon_stats,
    pokemon_types,
)

VERSION_GROUP = "champions"
PARSER_VERSION = "pokemon-battle-options-crawler:v1"
SPECIES_FILE = CURATED_DIR / "pokemon_species_regulation_m_b.jsonl"
OPTIONS_FILE = CURATED_DIR / "pokemon_battle_options_regulation_m_b.json"
REJECTED_FILE = REJECTED_DIR / "pokemon_battle_options_regulation_m_b_rejected.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def titleize_identifier(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split("-"))


def localized_name(payload: dict[str, Any], fallback: str, lang: str) -> str:
    return language_name(payload.get("names", []), lang) or fallback


def ability_option(entry: dict[str, Any]) -> dict[str, Any]:
    ability_id = entry["ability"]["name"]
    detail = pokeapi(entry["ability"]["url"])
    return {
        "abilityId": ability_id,
        "nameEn": localized_name(detail, titleize_identifier(ability_id), "en"),
        "nameKo": localized_name(detail, titleize_identifier(ability_id), "ko"),
        "slot": entry["slot"],
        "hidden": bool(entry["is_hidden"]),
    }


def champions_learn_details(move_entry: dict[str, Any]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for version_detail in move_entry.get("version_group_details", []):
        if version_detail.get("version_group", {}).get("name") != VERSION_GROUP:
            continue
        details.append(
            {
                "learnMethod": version_detail.get("move_learn_method", {}).get("name"),
                "levelLearnedAt": version_detail.get("level_learned_at", 0),
                "versionGroup": VERSION_GROUP,
            }
        )
    return details


def move_option(move_entry: dict[str, Any]) -> dict[str, Any] | None:
    learn_details = champions_learn_details(move_entry)
    if not learn_details:
        return None

    move_id = move_entry["move"]["name"]
    detail = pokeapi(move_entry["move"]["url"])
    effect_chance = detail.get("effect_chance")
    return {
        "moveId": move_id,
        "nameEn": localized_name(detail, titleize_identifier(move_id), "en"),
        "nameKo": localized_name(detail, titleize_identifier(move_id), "ko"),
        "type": detail.get("type", {}).get("name"),
        "damageClass": detail.get("damage_class", {}).get("name"),
        "power": detail.get("power"),
        "accuracy": detail.get("accuracy"),
        "pp": detail.get("pp"),
        "priority": detail.get("priority"),
        "target": detail.get("target", {}).get("name"),
        "effectChance": effect_chance,
        "learnDetails": sorted(
            learn_details,
            key=lambda item: (item["learnMethod"] or "", item["levelLearnedAt"] or 0),
        ),
    }


def pokemon_form_name(pokemon: dict[str, Any], lang: str) -> str | None:
    for form_link in pokemon.get("forms", []):
        form = pokeapi(form_link["url"])
        for name_entry in form.get("names", []):
            if name_entry.get("language", {}).get("name") == lang:
                return name_entry.get("name")
        for name_entry in form.get("form_names", []):
            if name_entry.get("language", {}).get("name") == lang:
                return name_entry.get("name")
    return None


def battle_option_item(
    *,
    species_item: dict[str, Any],
    pokemon: dict[str, Any],
    crawled_at: str,
    form_kind: str,
    mega_parent_pokemon_id: str | None = None,
) -> dict[str, Any]:
    pokemon_id = pokemon["name"]
    move_options = [option for move in pokemon.get("moves", []) if (option := move_option(move)) is not None]
    move_options.sort(key=lambda item: item["moveId"])
    name_en = species_item["nameEn"] if form_kind == "official_roster" else pokemon_form_name(pokemon, "en")
    name_ko = species_item["nameKo"] if form_kind == "official_roster" else pokemon_form_name(pokemon, "ko")
    types = pokemon_types(pokemon)
    base_stats = pokemon_stats(pokemon)
    required_stats = {"hp", "atk", "def", "spa", "spd", "spe"}
    if not types or not required_stats.issubset(base_stats):
        raise ValueError(f"Incomplete Pokémon identity data for {pokemon_id}: types={types}, baseStats={base_stats}")

    item = {
        "pk": f"OPTIONS#{RULESET}#REGULATION#{REGULATION_SET}",
        "sk": f"POKEMON#{pokemon_id}",
        "entityType": "PokemonBattleOptions",
        "ruleset": RULESET,
        "regulationSet": REGULATION_SET,
        "versionGroup": VERSION_GROUP,
        "pokemonId": pokemon_id,
        "speciesId": species_item["speciesId"],
        "nationalDexNumber": species_item["nationalDexNumber"],
        "formKind": form_kind,
        "megaParentPokemonId": mega_parent_pokemon_id,
        "nameEn": name_en or titleize_identifier(pokemon_id),
        "nameKo": name_ko or titleize_identifier(pokemon_id),
        "types": types,
        "baseStats": base_stats,
        "availableAbilities": [ability_option(ability) for ability in pokemon.get("abilities", [])],
        "availableMoves": move_options,
        "source": {
            "name": "official-pokemon-champions-roster+pokeapi-champions-version-group",
            "officialRosterSource": species_item.get("source", {}).get("officialRosterUrlEn"),
            "pokeapiPokemonUrl": f"{POKEAPI_BASE}/pokemon/{pokemon['id']}/",
            "pokeapiVersionGroup": VERSION_GROUP,
            "crawledAt": crawled_at,
            "parserVersion": PARSER_VERSION,
            "confidence": "official_roster_with_pokeapi_champions_moveset_enrichment",
        },
    }
    return item


def mega_varieties_for_species(species_id: str) -> list[dict[str, Any]]:
    species = pokeapi(f"pokemon-species/{species_id}")
    megas: list[dict[str, Any]] = []
    for variety in species.get("varieties", []):
        pokemon_name = variety.get("pokemon", {}).get("name", "")
        if "-mega" not in pokemon_name:
            continue
        megas.append(pokeapi(variety["pokemon"]["url"]))
    return sorted(megas, key=lambda item: item["name"])


def build_records(crawled_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    species_items = load_jsonl(SPECIES_FILE)
    records: dict[str, dict[str, Any]] = {}
    rejected: list[dict[str, Any]] = []

    for species_item in species_items:
        try:
            pokemon = pokeapi(f"pokemon/{species_item['pokemonId']}")
            item = battle_option_item(
                species_item=species_item,
                pokemon=pokemon,
                crawled_at=crawled_at,
                form_kind="official_roster",
            )
            records[item["pokemonId"]] = item
        except (KeyError, RuntimeError, urllib.error.URLError, ValueError) as exc:
            rejected.append(rejected_item(species_item, "official_roster_options_failed", str(exc), crawled_at))
            continue

        for mega_pokemon in mega_varieties_for_species(species_item["speciesId"]):
            try:
                item = battle_option_item(
                    species_item=species_item,
                    pokemon=mega_pokemon,
                    crawled_at=crawled_at,
                    form_kind="mega",
                    mega_parent_pokemon_id=species_item["pokemonId"],
                )
                records[item["pokemonId"]] = item
            except (KeyError, RuntimeError, urllib.error.URLError, ValueError) as exc:
                rejected.append(rejected_item(species_item, "mega_options_failed", str(exc), crawled_at))

    infer_meowstic_female_mega(records, crawled_at)
    return list(records.values()), rejected


def infer_meowstic_female_mega(records: dict[str, dict[str, Any]], crawled_at: str) -> None:
    """Fill a Pokémon Champions data hole with an explicitly marked inference.

    PokeAPI currently exposes `meowstic-female-mega` with Champions move details
    but no type/stat/ability identity. Champions treats it as the female form of
    the same Mega species, so copy the complete male Mega identity and mark the
    record as inferred for auditability.
    """
    if "meowstic-female-mega" in records:
        return
    male_mega = records.get("meowstic-male-mega")
    female = records.get("meowstic-female")
    if male_mega is None or female is None:
        return

    inferred = json.loads(json.dumps(male_mega, ensure_ascii=False))
    inferred.update(
        {
            "sk": "POKEMON#meowstic-female-mega",
            "pokemonId": "meowstic-female-mega",
            "megaParentPokemonId": "meowstic-female",
            "nameEn": "Mega Meowstic Female",
            "nameKo": "메가냐오닉스♀",
            "dataQuality": "inferred",
            "inferredFromPokemonId": "meowstic-male-mega",
        }
    )
    inferred["source"] = {
        **inferred.get("source", {}),
        "crawledAt": crawled_at,
        "confidence": "inferred_from_meowstic_male_mega_due_to_incomplete_pokeapi_female_mega_identity",
        "inferredFromPokemonId": "meowstic-male-mega",
        "inferenceReason": "PokeAPI meowstic-female-mega has moves but empty types/baseStats/abilities.",
    }
    records[inferred["pokemonId"]] = inferred


def rejected_item(species_item: dict[str, Any], reason: str, error: str, crawled_at: str) -> dict[str, Any]:
    return {
        "pk": f"REJECTED#{RULESET}#REGULATION#{REGULATION_SET}",
        "sk": f"{crawled_at}#{species_item.get('pokemonId')}",
        "entityType": "RejectedPokemonBattleOptions",
        "pokemonId": species_item.get("pokemonId"),
        "speciesId": species_item.get("speciesId"),
        "reason": reason,
        "error": error,
        "source": species_item.get("source"),
    }


def write_json(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl Pokémon Champions ability and move options.")
    parser.add_argument("--crawled-at", default=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"))
    parser.add_argument("--fail-on-rejected", action="store_true", help="Exit non-zero when any record is rejected.")
    args = parser.parse_args()

    records, rejected = build_records(args.crawled_at)
    records.sort(key=lambda item: (item["nationalDexNumber"], item["formKind"] != "official_roster", item["pokemonId"]))
    write_json(OPTIONS_FILE, records)
    write_jsonl(REJECTED_FILE, rejected)

    official_count = sum(1 for item in records if item["formKind"] == "official_roster")
    mega_count = sum(1 for item in records if item["formKind"] == "mega")
    move_count = sum(len(item["availableMoves"]) for item in records)
    ability_count = sum(len(item["availableAbilities"]) for item in records)
    print(f"records={len(records)} official={official_count} mega={mega_count} {OPTIONS_FILE.relative_to(ROOT)}")
    print(f"abilities={ability_count} moves={move_count} versionGroup={VERSION_GROUP}")
    print(f"rejected={len(rejected)} {REJECTED_FILE.relative_to(ROOT)}")
    if rejected and args.fail_on_rejected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
