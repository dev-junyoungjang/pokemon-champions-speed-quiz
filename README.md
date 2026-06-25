# Pokémon Champions Speed Quiz

A mobile-first yes/no swipe quiz app for comparing a user's six-Pokémon team against current Pokémon Champions meta samples.

- `server/`: FastAPI backend, deterministic speed rules, quiz generation, repository layer for DynamoDB-compatible data.
- `front/`: React + Vite + TypeScript frontend, Emotion styled UI, swipe quiz interaction.

## Data policy

The first commit uses in-memory development fixtures so the app can be exercised locally. Real crawler data must follow `docs/crawler-source-policy.md`: only Pokémon Champions-specific sources may create meta samples, and every sample must pass the local `PokemonSpecies` availability allowlist before insertion.

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
