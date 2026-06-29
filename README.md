# Pokémon Champions Speed Quiz

A mobile-first yes/no swipe quiz app for comparing a user's six-Pokémon team against current Pokémon Champions meta samples.

- `server/`: FastAPI backend, deterministic speed rules, quiz generation, repository layer for DynamoDB-compatible data.
- `front/`: React + Vite + TypeScript frontend, Emotion styled UI, swipe quiz interaction.

## Data policy

The first commit uses in-memory development fixtures so the app can be exercised locally. Real crawler data must follow `docs/crawler-source-policy.md`: only Pokémon Champions-specific sources may create meta samples, and every sample must pass the local `PokemonSpecies` availability allowlist before insertion.

Reviewable Regulation M-B roster exports live under `server/data/`:

- `server/data/raw/champions/regulation_m_b_official_roster.jsonl`
- `server/data/curated/pokemon_species_regulation_m_b.jsonl`
- `server/data/rejected/pokemon_species_regulation_m_b_rejected.jsonl`

Machine-readable rules and source records live under `server/data/rules/`:

- `server/data/rules/regulation_m_b_rules.json`
- `server/data/rules/speed_formula_v1.json`
- `server/data/rules/rule_sources.jsonl`

Regenerate roster exports with:

```bash
python server/scripts/crawl_regulation_mb.py
```

### AI configuration

For local GPT/OpenAI-compatible calls, copy the example env file and put your token in `.env`:

```bash
cd server
cp .env.example .env
# edit OPENAI_API_KEY in .env
```

Recommended defaults for this app:

- `OPENAI_CANDIDATE_MODEL=gpt-5.4-mini` for structured candidate JSON generation.
- `OPENAI_RENDER_MODEL=gpt-5.4-mini` for Korean question/explanation rendering.
- If cost becomes more important than phrasing quality, use a smaller mini/nano-class model for rendering only.
- If candidate validity is poor, upgrade only `OPENAI_CANDIDATE_MODEL` to a stronger non-mini model and keep rendering on mini.

The frontend should still call only `POST /api/v1/quiz/questions`. Model calls, validation, retry, and rendering stay server-side.

### Question generation pipeline

The server supports a two-step question pipeline so AI can assist without deciding trusted answers:

1. `POST /api/v1/quiz/question-candidates` creates structured candidate JSON with Pokémon/build inputs only.
2. `POST /api/v1/quiz/questions/validate` recomputes speeds and `correctAnswer` with the server rules engine.
3. `POST /api/v1/quiz/questions/render` converts validated JSON into user-facing statement/explanation text.

`POST /api/v1/quiz/questions` remains as a compatibility endpoint that performs all three steps internally and returns rendered questions.

## Local development

### Server

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd front
npm install
npm run dev
```
