# CLAUDE.md — instagram-profile-optimizer

Stable operating manual. Volatile state lives in `STATUS.md`. Decisions are
append-only in `docs/decisions.md`. Do not duplicate state here.

## Purpose

Productized Instagram makeover service for Brazilian local-service SMBs
(estética, odonto, salão, restaurante, pet, fitness — 500–20k followers).
Automated pipeline: prospect → score → mockup → hook → pitch → track.
Business model: one-time makeover setup fee + monthly subscription
(template kit + DM automation). Operated by mil&dez.

## Pipeline stages & where they live

| Stage | Lives in | Notes |
|---|---|---|
| 1a. Prospecting (Places + CNPJ) | existing `run.py` CLI (separate repo) | outputs to `prospects` table |
| 1b. Handle resolution + scoring | this repo: `scripts/`, `n8n/`, `prompts/` | spec: `docs/scorer-spec.md` |
| 2. Mockup generation | Frame repo (`~/instagram-admin`) | consumes `dominant_colors` from scores |
| 3. DM demo (Private Replies) | this repo: `n8n/` | runs on mil&dez IG account |
| 4. Pitch queue | this repo: `n8n/` + `dashboard/` | human tap-to-send, wa.me links |
| 5–6. Pricing variants + feedback loop | this repo: Supabase + `dashboard/` | A/B tracking tables |

## Stack

- Supabase (Postgres + Storage) — single source of truth, migrations in `supabase/migrations/`
- n8n (self-hosted, srv1318470.hstgr.cloud) — orchestration; export workflow JSON to `n8n/`
- Claude API — `claude-haiku-4-5` for classification (P1/P2 prompts in `prompts/`)
- Meta Graph API v23.0 — Business Discovery + Private Replies (official only)
- Next.js 14 + TypeScript + Tailwind — review dashboard (`dashboard/`, week 2)
- Python 3 — handle resolver script (`scripts/`)

## Hard constraints

1. **Meta compliance**: official APIs only. No profile scraping, no cold sends
   via WhatsApp Cloud API, no automated cold IG DMs. Human-in-loop for all
   outbound (wa.me prefilled links, manual DM queue).
2. **LGPD**: public business data only; legítimo interesse; opt-out line in
   every pitch; suppression list enforced before any send.
3. **Language**: all prospect-facing text PT-BR. Internal docs/code English.

## Conventions

- Brand: Inter, burgundy `#6b0f1a` (<5% surface), white bg, 1px borders,
  no shadows — applies to dashboard UI.
- Supabase migrations: sequential `NNNN_description.sql`, never edit applied ones.
- n8n workflows: `NN-name.json`, inventory table in `n8n/README.md`.
- Prompts: one file per prompt, versioned in place, JSON-only outputs, temp 0.
- Env vars: see `.env.example`; secrets never committed.

## Engineering principles

1. Think before coding — restate the goal, identify the smallest change.
2. Simplicity first — no speculative abstraction; n8n Code node beats a microservice.
3. Surgical changes — touch only what the task requires.
4. Goal-driven execution — every task maps to a pipeline stage and a metric
   (delivery >95%, reply ≥15%, close ≥3%).

## Key references

- `docs/scorer-spec.md` — rubric, API calls, prompts, schema, edge cases
- `docs/decisions.md` — why things are the way they are
- `STATUS.md` — current phase, next actions, blockers
