# STATUS — instagram-profile-optimizer

> Volatile. Update every working session. History belongs in git, not here.

**Phase:** Week 1 — scorer build (PRD milestone 1: F-101→F-105, F-107, F-108)
**Last updated:** 2026-07-05

## Done

- [x] Pipeline architecture + compliance routes defined (see decisions D-001)
- [x] Scorer spec complete (`docs/scorer-spec.md`)
- [x] PRD v1.0 (`docs/PRD.md`) — source of truth for scope
- [x] Repo scaffold + initial Supabase schema (`0001_initial_schema.sql`)
- [x] F-601 variant performance view (`v_variant_performance` in migration 0001)
- [x] P1/P2 prompts drafted (`prompts/`)
- [x] Repo on GitHub (`miledez/instagram-profile-optimizer`, HTTPS remote)

## In progress

- [ ] F-101 handle resolver — code complete (website scrape, aggregator
      one-level follow, Places details fallback, suppression + dedupe,
      --limit/--dry-run); AC "≥70% auto-resolved" pending first real batch
      (needs Supabase creds + prospects loaded) before PRD flips to done

## Next actions (Week 1, in order)

- [ ] Create Meta app: `instagram_basic` + `instagram_manage_insights`,
      long-lived token — resolves Q1, unblocks F-102
- [ ] Apply migration 0001 to Supabase project
- [ ] F-101: run first batch (`--dry-run` then live) once migration applied
      and prospects imported; verify ≥70% auto-resolve → mark done in PRD
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

## Current metrics

- Prospects scored: 0 / target ≥100/day · Qualified (≥60): 0 · Sends: 0
- Week-1 exit criteria: scorer live, 100 profiles scored
