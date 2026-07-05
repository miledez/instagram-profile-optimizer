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
- [x] **F-101 DONE — AC met at 90%** (116/128 on-segment auto-resolved,
      live run written: 61 website_scrape · 55 search · 12 manual queue).
      Iterations that got there: escaped-URL regex, platform/asset
      blocklists, SSL retry, accent folding + ≥3-char tokens, Brave
      quoted→unquoted fallback gated on distinctive-token match.
- [x] `.env` complete: Supabase URL/key + Places + Brave keys, verified live
- [x] P1/P2 prompts drafted (`prompts/`)
- [x] Migration 0002: RLS enabled all tables (no policies; service role
      bypasses — verified post-apply)
- [x] Migration 0003: `v_prospects_to_score` — scoring-time suppression (F-108)
- [x] n8n `01-scorer-daily.json` built (F-102→F-105, F-107): BD fetch w/
      error-110 routing, prefilters, S1/S2/S4 + evidence Code node, Claude
      P1/P2 HTTP, upsert w/ on_conflict — JS fixture-tested (25 checks)
- [x] 79 `outro` pilot rows deleted — prospects table is 128 on-segment only

## Next actions (Week 1, in order)

- [ ] Create Meta app: `instagram_basic` + `instagram_manage_insights`,
      long-lived token — resolves Q1, unblocks live scorer test
- [ ] Import `n8n/01-scorer-daily.json` into n8n, create the 3 credentials
      + set IG user id (see `n8n/README.md` setup section)
- [ ] Live scorer run on 2–3 handles → verify rows in `prospect_scores`,
      spot-check `llm_raw` → then full queue (116) → F-102→F-105/F-107/F-108
      to done
- [ ] Week 2 preview: F-106 dashboard review queue, F-201→F-205 mockups,
      F-301/F-302 demo

## Blockers

- Meta app credentials not yet created (blocks F-102 Business Discovery calls)
- Open questions Q1–Q4 in PRD §8; only Q1 (app review need) blocks week 1

## Housekeeping

- Spot-check the 55 `ig_resolution_method='search'` handles before scoring —
  lower precision than scrapes; known-suspect examples: GG Cabeleireiros →
  @lourdescabeleireirosmegahair, Cléber Cordeiro → @studiocapitalbeauty,
  Petz Augusta → @augustapetshop (error 110 + follower prefilter + human
  review are the backstops, but a 5-min eyeball is cheap)
- Brave API: attribute Brave Search on project site/about page ($5/mo free
  credit condition)
- Rotate Supabase service_role key (was printed during debug session)
- Delete leftover broken `.venv/` dir in repo root

## Current metrics

- Prospects in DB: 128 (all on-segment) · Handles resolved: 116 (90%) ·
  Manual queue: 12 · Scored: 0 · Qualified: 0 · Sends: 0
- Week-1 exit criteria: scorer live, 100 profiles scored
