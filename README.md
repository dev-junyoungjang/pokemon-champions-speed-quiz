# Pokémon Champions Speed Quiz

A mobile-first yes/no swipe quiz app for comparing a user's six-Pokémon team against current Pokémon Champions meta samples.

- `server/`: FastAPI backend, deterministic speed rules, quiz generation, repository layer for DynamoDB-compatible data.
- `front/`: React + Vite + TypeScript frontend, Emotion styled UI, swipe quiz interaction.

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
