# Crawler Source Policy

## Goal

Prevent Pokémon Champions quiz data from mixing in Pokémon that are not currently available in Pokémon Champions. The crawler must never treat generic Pokémon/VGC/Showdown meta data as Pokémon Champions meta data.

## Hard rule

A meta sample is valid only if all of the following are true:

1. The species/form exists in the local `PokemonSpecies` table for `ruleset = pokemon_champions`.
2. The species/form has `availability.status = available` or `announced_available`.
3. The meta/build source explicitly says it is for Pokémon Champions.
4. The crawler preserves the source URL, crawl timestamp, parser version, and confidence.

If any rule fails, the sample must be rejected into `RejectedMetaSamples`, not inserted into `PokemonMetaSamples`.

## Source priority

### Tier 0 — Authoritative roster/rules sources

Use these to build and update `PokemonSpecies` and formula/rules metadata.

- Official Pokémon Champions website pages.
- Official Pokémon Champions news posts.
- Official in-game data export/API if one becomes available.
- Official Pokémon HOME / Pokémon official Pokédex data for base stats, but only after the species/form is confirmed available for Pokémon Champions by a Tier 0 roster source.

### Tier 1 — Champions-specific meta/build sources

Use these for `PokemonMetaSamples` only when the page explicitly targets Pokémon Champions.

- Official Pokémon Champions ranked usage/ranking page, if released.
- Game8 Pokémon Champions pages, if the page title/body clearly says Pokémon Champions and not Scarlet/Violet, VGC, Pokémon GO, Unite, or another game.
- Other strategy pages that clearly label the ruleset as Pokémon Champions.

### Tier 2 — Manual curated import

Allowed while public Champions meta sources are incomplete.

- A checked-in JSON file reviewed by us.
- Discord/user-provided team data.
- Manual seed data marked with `source = manual_curated` and `confidence = curated`.

### Forbidden sources for Champions meta

Do not use these as direct `PokemonMetaSamples` sources:

- Generic Pokémon Showdown usage stats unless there is a Champions-specific ladder.
- Scarlet/Violet VGC rankings.
- Smogon tier lists.
- Pikalytics pages for non-Champions formats.
- Any source page that does not explicitly mention Pokémon Champions.

These sources may be used only as human reference material, never as automated Champions meta input.

## Validation pipeline

For every crawled build candidate:

1. Normalize species and form name.
2. Lookup `PokemonSpecies` by `(ruleset, pokemonId, formId)`.
3. Reject if missing from species table.
4. Reject if availability is not `available` or `announced_available`.
5. Verify the page/source is Champions-specific.
6. Normalize nature, item, ability, EVs, IVs, and moves.
7. Attach `baseStatsSnapshot` from `PokemonSpecies`.
8. Compute `sampleHash` from species/form/build/source.
9. Upsert into `PokemonMetaSamples`.
10. After crawl, mark active samples inactive when `lastSeenAt` is older than 10 days.

## Rejection record

Rejected data should be stored for debugging.

```json
{
  "pk": "REJECTED#pokemon_champions",
  "sk": "2026-06-25T00:00:00Z#flutter-mane#hash",
  "pokemonId": "flutter-mane",
  "sourceUrl": "https://...",
  "reason": "species_not_available_in_pokemon_champions",
  "rawPayloadRef": "s3://...",
  "crawlerVersion": "crawler:v1"
}
```

## Prompt for crawler agent

```text
You are crawling data for a Pokémon Champions speed quiz app.

Do not import generic Pokémon meta data.
A Pokémon/build is valid only if the source explicitly targets Pokémon Champions and the species/form already exists in the local PokemonSpecies allowlist for ruleset pokemon_champions.

For each candidate:
1. Capture source URL and crawl timestamp.
2. Extract species, form, nature, ability, item, EVs, IVs, moves, usage/rank if present.
3. Check species/form against PokemonSpecies.
4. If absent or unavailable, reject it with reason species_not_available_in_pokemon_champions.
5. If source is not clearly Pokémon Champions, reject it with reason source_not_champions_specific.
6. Never fill missing availability by guessing from VGC/Showdown/Smogon/Pikalytics.
7. Attach baseStatsSnapshot only from PokemonSpecies, not from the meta page.
8. Output accepted and rejected records separately.
```

## Current project note

The initial in-memory backend seed data is a development fixture, not a trusted Pokémon Champions meta source. Replace it with validated Champions-specific data before treating quiz output as real meta training.
