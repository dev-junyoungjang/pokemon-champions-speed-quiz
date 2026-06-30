# Pokémon Champions data exports

This directory stores reviewable JSONL exports before any DynamoDB import.

## Current export

- Regulation: `M-B`
- Ruleset: `pokemon_champions`
- Official eligible roster source:
  - English: <https://web-view.app.pokemonchampions.jp/battle/pages/events/rs178066986988lmoqpm/en/pokemon.html>
  - Korean: <https://web-view.app.pokemonchampions.jp/battle/pages/events/rs178066986988lmoqpm/ko/pokemon.html>
- Species enrichment source: PokeAPI Pokémon and Pokémon Species endpoints for base stats, types, species names, and image URLs.
- Battle-option enrichment source: PokeAPI Pokémon Champions version group (`champions`) for ability and move options.
- `meowstic-female-mega` is included as an explicit inferred record copied from `meowstic-male-mega`, because PokeAPI currently has empty identity data for that form.

## Files

- `raw/champions/regulation_m_b_official_roster.jsonl`
  - One line per official eligible Pokémon entry.
  - Contains official Pokémon Champions code, English name, Korean name, source URLs, and crawl timestamp.
- `curated/pokemon_species_regulation_m_b.jsonl`
  - DynamoDB-shaped species items.
  - Contains official Regulation M-B roster Pokémon plus Mega form records derived from eligible species.
  - Includes `pk`, `sk`, `pokemonId`, `nameEn`, `nameKo`, `types`, `baseStats`, `availability`, and `source`.
- `rejected/pokemon_species_regulation_m_b_rejected.jsonl`
  - Failed/mismatched records. The current export has zero rejected records.
- `curated/pokemon_battle_options_regulation_m_b.json`
  - DynamoDB-shaped `pokemon-options` items for all official Regulation M-B Pokémon plus Mega forms for eligible species.
  - Includes `availableAbilities`, `availableMoves`, move metadata, learn details, types, base stats, and source metadata.
- `rejected/pokemon_battle_options_regulation_m_b_rejected.jsonl`
  - Failed battle-option enrichment records. The current export has zero rejected records.
- `rules/regulation_m_b_rules.json`
  - Machine-readable official Regulation M-B battle rules and source links.
- `rules/speed_formula_v1.json`
  - Machine-readable speed formula contract used by tests and explanation validation.
- `rules/rule_sources.jsonl`
  - One line per source used to build or cross-check the rules data.

## Regenerate

```bash
python server/scripts/crawl_regulation_mb.py
python server/scripts/crawl_pokemon_battle_options.py
python server/scripts/add_mega_species_records.py
```

The scripts write JSON/JSONL locally and do not write to DynamoDB. Import reviewed battle options with:

```bash
python server/scripts/import_pokemon_options_to_dynamodb.py --dry-run
python server/scripts/import_pokemon_options_to_dynamodb.py \
  --table-name pokemon-options \
  --region ap-northeast-2
```
