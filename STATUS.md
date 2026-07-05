# STATUS — instagram-profile-optimizer

> Volatile. Update every working session. History belongs in git, not here.

**Phase:** Week 1 — scorer build (PRD milestone 1: F-101→F-105, F-107, F-108)
**Last updated:** 2026-07-05

## Done

- [x] Pipeline architecture + compliance routes defined (D-001)
- [x] Scorer spec complete (`docs/scorer-spec.md`)
- [x] PRD v1.2 (`docs/PRD.md`) — source of truth for scope
- [x] Repo scaffold, on GitHub (`miledez/instagram-profile-optimizer`)
- [x] Supabase project live: `instagram-profile-optimizer`
      (ref `ejxoageyamogdgwwycvp`, sa-east-1, free tier)
- [x] Migration 0001 applied — 6 tables + `v_variant_performance` (F-601)
- [x] F-110 prospecting CLI local (`scripts/prospect.py`, D-007) — 6 segments,
      dedupe vs `prospects` table, smoke-tested live (5 salao + 3 pet in DB)
- [x] F-101 resolver code complete; first batch run on 79 off-ICP pilot rows
      (medicina do trabalho, from old run.py cache, segment `outro`):
      40% auto-resolve. Fixes shipped from failure analysis: escaped-URL
      regex (linktree/Wix), platform-account blocklist, SSL retry.
      On-segment micro-sample: 3/3 with-website resolved.
- [x] `.env` complete: Supabase URL/key + Places key, all verified live
- [x] P1/P2 prompts drafted (`prompts/`)

## In progress

- [ ] F-101 AC "≥70% auto-resolved" — needs a real on-segment batch;
      40% on off-ICP B2B pilot is not the verdict (those sites rarely
      link IG; no-website rows are the main manual driver)

## Next actions (Week 1, in order)

- [ ] Create Meta app: `instagram_basic` + `instagram_manage_insights`,
      long-lived token — resolves Q1, unblocks F-102
- [ ] First on-segment batch: `python3 scripts/prospect.py --all --limit 20`
      (~120 prospects), then `resolve_handles.py --dry-run --limit 100` →
      judge F-101 AC → live run → mark done in PRD
- [ ] Decide RLS: migration 0002 enabling RLS (no policies; service role
      bypasses) — Supabase advisor flags all 6 tables, prospect PII/LGPD
- [ ] F-102: n8n `01-scorer-daily` Business Discovery fetch (25s spacing,
      error 110 → `unscoreable_personal`)
- [ ] F-103: deterministic signals S1/S2/S4 per spec §2 (likes-hidden fallback)
- [ ] F-104/F-105: wire P1/P2 Claude calls in n8n, log raw to `llm_raw`,
      persist `dominant_colors` always
- [ ] F-107: evidence generator — top-3 weakness strings PT-BR → `evidence` jsonb
- [ ] F-108: suppression enforcement at scoring time (send-time check comes
      with outreach in week 3)
- [ ] Week 2 preview: F-106 dashboard review queue, F-201→F-205 mockups,
      F-301/F-302 demo

## Blockers

- Meta app credentials not yet created (blocks F-102 Business Discovery calls)
- Open questions Q1–Q4 in PRD §8; only Q1 (app review need) blocks week 1

## Housekeeping

- Rotate Supabase service_role key (was printed during debug session)
- Delete leftover broken `.venv/` dir in repo root
- Decide fate of 79 `outro` pilot rows in `prospects` (keep as resolver
  test data vs delete before scoring starts)

## Current metrics

- Prospects in DB: 87 (79 outro pilot · 5 salao · 3 pet) · Scored: 0 ·
  Qualified (≥60): 0 · Sends: 0
- Week-1 exit criteria: scorer live, 100 profiles scored
