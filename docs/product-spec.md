# Pokémon Champions Speed Quiz Product Spec

## Goal

Build a Pokémon Champions rules-based speed comparison quiz web app. The first playable version focuses on yes/no speed questions using a user's saved six-Pokémon team versus active meta Pokémon samples.

## Requirements

- Users can enter and save a six-Pokémon team.
- Home page contains team entry and quiz start flow.
- Quiz start opens difficulty selection.
- After difficulty selection, the UI shows a loading/waiting state while questions are generated.
- Quiz questions are yes/no only.
- Swipe right means yes/true; swipe left means no/false.
- Server computes the authoritative answer using a deterministic speed rules engine.
- Model-generated text may be added later, but must not override server-computed answers.
- AI-generated question candidates must be structured JSON only; the server validates candidates with the rules engine before rendering text.
- Text rendering is a separate step from candidate validation so statements/explanations can be regenerated without changing the trusted answer.
- Meta samples and user team records include `baseStatsSnapshot` for reproducible speed calculations.
- Tailwind must not be used.

## Constraints

- Frontend: React Vite TypeScript deployable to Vercel.
- Styling: Emotion styled components with readable named components and local design tokens.
- Backend: FastAPI.
- Persistence target: DynamoDB. MVP includes an in-memory repository with DynamoDB-shaped models so APIs are usable before AWS setup.
- Pokémon Champions official formula differences must be versioned and testable.

## Acceptance criteria

- `server` has passing tests for base speed and level 50 speed calculations.
- `server` exposes health, team save/get, difficulty list, candidate generation, candidate validation, question rendering, legacy question generation, and answer submission APIs.
- `front` builds successfully with Vite.
- UI includes home, team editor, difficulty selection, generation waiting state, and swipe quiz card.
- No Tailwind dependency or utility-heavy class markup is used.

## Context

Game8's party/team registration UI pattern is approximated as a compact six-slot party editor: visible party slots, each with Pokémon details and item/ability/nature/EV fields. The implementation should not copy Game8 assets or protected styling directly.
