# STATUS — instagram-profile-optimizer

> Volatile. Update every working session. History belongs in git, not here.

**Phase:** Week 1 — scorer build
**Last updated:** 2026-07-05

## Done

- [x] Pipeline architecture + compliance routes defined (see decisions D-001)
- [x] Scorer spec complete (`docs/scorer-spec.md`)
- [x] Repo scaffold + initial Supabase schema (`0001_initial_schema.sql`)
- [x] P1/P2 prompts drafted (`prompts/`)

## Next actions

- [ ] Create Meta app: `instagram_basic` + `instagram_manage_insights`, long-lived token
- [ ] Apply migration 0001 to Supabase project
- [ ] Implement `scripts/resolve_handles.py` (website scrape → fallback search)
- [ ] Build n8n workflow `01-scorer-daily` per spec §7
- [ ] Wire P1/P2 Claude calls in n8n, log raw outputs for spot-check
- [ ] Dashboard review queue (week 2)

## Blockers

- Meta app credentials not yet created (blocks Business Discovery calls)

## Current metrics

- Prospects scored: 0 · Qualified (≥60): 0 · Sends: 0
