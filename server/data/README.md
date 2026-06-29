# Pokémon Champions data exports

This directory stores reviewable JSONL exports before any DynamoDB import.

## Current export

- Regulation: `M-B`
- Ruleset: `pokemon_champions`
- Official eligible roster source:
  - English: <https://web-view.app.pokemonchampions.jp/battle/pages/events/rs178066986988lmoqpm/en/pokemon.html>
  - Korean: <https://web-view.app.pokemonchampions.jp/battle/pages/events/rs178066986988lmoqpm/ko/pokemon.html>
- Enrichment source: PokeAPI Pokémon and Pokémon Species endpoints for base stats, types, species names, and image URLs.

## Files

- `raw/champions/regulation_m_b_official_roster.jsonl`
  - One line per official eligible Pokémon entry.
  - Contains official Pokémon Champions code, English name, Korean name, source URLs, and crawl timestamp.
- `curated/pokemon_species_regulation_m_b.jsonl`
  - DynamoDB-shaped species items.
  - Contains only Pokémon present in the official Regulation M-B eligible roster.
  - Includes `pk`, `sk`, `pokemonId`, `nameEn`, `nameKo`, `types`, `baseStats`, `availability`, and `source`.
- `rejected/pokemon_species_regulation_m_b_rejected.jsonl`
  - Failed/mismatched records. The current export has zero rejected records.

## Regenerate

```bash
python server/scripts/crawl_regulation_mb.py
```

The script writes JSONL locally and does not write to DynamoDB. The curated JSONL can later be imported with a separate reviewed batch writer/import tool.
