# PRD — instagram-profile-optimizer

> Living document. Rules: feature IDs are permanent (never renumber — mark
> `cut` instead) · every change appends a row to §9 and, if strategic, a
> D-entry in `docs/decisions.md` · status values: `planned` `building`
> `done` `cut` `changed` · priority: `P0` (launch-blocking) `P1` (pre-scale)
> `P2` (later).

**Version:** 1.3 · **Updated:** 2026-07-05 · **Owner:** Simon / mil&dez

---

## 1. Summary

Productized Instagram makeover for Brazilian local-service SMBs (500–20k
followers, visibly weak profiles). Maximally automated pipeline finds weak
profiles, generates a personalized before/after mockup, proves value with a
live DM-automation demo, and pitches via WhatsApp/DM with human-in-loop
sends. Revenue: setup fee + monthly subscription (template kit + DM
automation).

## 2. Goals & success metrics

| Metric | Target | Measured by |
|---|---|---|
| Delivery rate | >95% | `touches.delivered` |
| Reply rate | ≥15% | `v_variant_performance` |
| Reply → meeting | ≥40% | `touches.meeting_at` |
| Meeting → close | ≥25% (≈3% of contacted) | `outcomes.closed_won` |
| Scoring throughput | ≥100 profiles/day | n8n `01-scorer-daily` |
| Human time per qualified prospect | ≤2 min (review + send taps) | operator log |
| Lock criteria | reply ≥15% AND close ≥3% → freeze variants, scale volume | weekly report |

## 3. Users

| User | Needs |
|---|---|
| Operator (Simon) | Zero-friction queues: review 30s/profile, tap-to-send pitches, weekly variant report |
| Prospect (SMB owner) | PT-BR, WhatsApp-first, concrete proof (their own profile made over), instant demo |

## 4. Features

### E1 — Prospecting & scoring

| ID | Feature | Pri | Status | Acceptance criteria |
|---|---|---|---|---|
| F-101 | Handle resolver (`resolve_handles.py`) | P0 | building | ≥70% of prospects auto-resolved; method logged; invalid handles never written |
| F-110 | Places prospecting CLI (`scripts/prospect.py`) | P0 | done | 6 segments; idempotent re-runs (dedupe on `places_id`); valid rows (E.164 phone, UF, city tier); D-007 |
| F-102 | Business Discovery fetcher (n8n) | P0 | planned | 1 call/prospect; 25s spacing; error 110 → `unscoreable_personal` |
| F-103 | Deterministic signals S1/S2/S4 | P0 | planned | Matches spec §2 tables; likes-hidden fallback works |
| F-104 | P1 bio classifier | P0 | planned | JSON parse rate >98%; raw output logged to `llm_raw` |
| F-105 | P2 grid vision + palette | P0 | planned | 9 imgs @512px same-run fetch; `dominant_colors` persisted always |
| F-106 | Review queue (dashboard) | P0 | planned | S6/S7 checklist + screenshot upload; ≤30s per profile |
| F-107 | Evidence generator (PT-BR) | P0 | planned | Top-3 weakness strings stored in `evidence` jsonb |
| F-108 | Suppression enforcement | P0 | planned | Checked at scoring AND before every send; opt-outs land here same day |
| F-109 | Benchmark calibration | P1 | planned | After 200 scored: segment medians replace defaults; 25–35% qualify |

### E2 — Mockup generation (lives in Frame repo; tracked here)

| ID | Feature | Pri | Status | Acceptance criteria |
|---|---|---|---|---|
| F-201 | Brand kit from `dominant_colors` + logo | P0 | planned | Palette + type auto-applied to Frame templates |
| F-202 | Bio rewrite (oferta + CTA + link) | P0 | planned | ≤150 chars, PT-BR, segment-specific CTA |
| F-203 | Branded highlight covers (5) | P0 | planned | Rendered via `renderToCanvas` |
| F-204 | 9-post grid preview | P0 | planned | Mix foto/arte per segment; branded |
| F-205 | Before/after composite export | P0 | planned | Single shareable image + PDF; before = review screenshot |
| F-206 | Mockup style variants (clean/colorido) | P1 | planned | Selectable per A/B assignment |

### E3 — Value hook (demo)

| ID | Feature | Pri | Status | Acceptance criteria |
|---|---|---|---|---|
| F-301 | Private Replies workflow (comment PREÇO → DM) | P0 | planned | <10s response on mil&dez account; official API only |
| F-302 | DM → wa.me handoff with price list | P0 | planned | Prefilled message; touch logged |

### E4 — Pitch & outreach

| ID | Feature | Pri | Status | Acceptance criteria |
|---|---|---|---|---|
| F-401 | Pitch templates PT-BR + evidence injection | P0 | planned | 2–3 weaknesses cited with real numbers; opt-out line mandatory |
| F-402 | WhatsApp queue (wa.me tap-to-send) | P0 | planned | 50–80/day cap enforced; number warm-up schedule |
| F-403 | IG DM manual queue | P1 | planned | Copy-paste queue in dashboard; logged as channel=ig_dm |
| F-404 | Touch logging (sent/delivered/replied/meeting) | P0 | planned | One tap per state change from dashboard |

### E5 — Pricing

| ID | Feature | Pri | Status | Acceptance criteria |
|---|---|---|---|---|
| F-501 | Price variants A/B/C in `variants` table | P0 | planned | A: 497+247 · B: 797+397 · C: 1297+597 (BRL) |
| F-502 | Auto-assignment by segment × city tier | P1 | planned | C→estética/odonto tier-1; A→pet/restaurante tier-3; B default |

### E6 — Feedback loop

| ID | Feature | Pri | Status | Acceptance criteria |
|---|---|---|---|---|
| F-601 | Variant performance view | P0 | done | `v_variant_performance` in migration 0001 |
| F-602 | Weekly A/B report (n8n `04-metrics-rollup`) | P1 | planned | Min 100 sends/variant before comparison; 1 variable/week |
| F-603 | Lock & scale switch | P1 | planned | On lock criteria met: freeze variants, raise daily volume |

## 5. Non-goals

| Excluded | Reason |
|---|---|
| Content management / posting for clients | Product is makeover + kit + automation, not gestão |
| Instagram scraping, cold Cloud API sends, automated cold DMs | Compliance (D-001) |
| Paid traffic services | Out of product scope |
| Multi-tenant SaaS for other agencies | Maybe post-lock; not now |
| Consumer (B2C) profiles | B2B only, LGPD basis is legítimo interesse |

## 6. Constraints

| Area | Rule |
|---|---|
| Meta | Official APIs only; human-in-loop for all outbound |
| LGPD | Public business data; opt-out honored same day; suppression list |
| Language | Prospect-facing = PT-BR; internal = English |
| Brand (dashboard/mockups) | Inter · #6b0f1a <5% · white bg · 1px borders · no shadows |
| Stack | Supabase · n8n · Claude API (haiku-4-5 classify) · Next.js 14 · Python resolver |

## 7. Milestones

| Week | Deliverable | Features |
|---|---|---|
| 1 | Scorer live, 100 profiles scored | F-101→F-105, F-107, F-108 |
| 2 | Review dashboard + mockup pipeline + demo | F-106, F-201→F-205, F-301, F-302 |
| 3 | First cohort: 100 sends, variant B | F-401, F-402, F-404, F-501 |
| 4+ | Weekly A/B iteration → lock → scale | F-109, F-206, F-403, F-502, F-602, F-603 |

## 8. Open questions

| # | Question | Blocking |
|---|---|---|
| Q1 | Meta app review needed for `instagram_manage_insights` at our usage level? | F-102 |
| Q2 | Dedicated WhatsApp number: new chip vs existing business line? | F-402 |
| Q3 | Mockup delivered as image in first message vs after reply (A/B)? | F-401 |
| Q4 | Demo post format on mil&dez profile (reel vs carousel) | F-301 |

## 9. Change log

| Date | Ver | Change | Ref |
|---|---|---|---|
| 2026-07-05 | 1.0 | Initial PRD from pipeline design + scorer spec | D-001→D-006 |
| 2026-07-05 | 1.1 | F-101 implementation complete (scrape + aggregator follow + Places fallback + suppression/dedupe); stays `building` until ≥70% AC verified on first real batch. Supabase project live (`ejxoageyamogdgwwycvp`, sa-east-1), migration 0001 applied — F-601 view deployed. | F-101, F-601 |
| 2026-07-05 | 1.2 | Added F-110: prospecting (stage 1a) moved into this repo as `scripts/prospect.py`, `done`. First resolver batch on 79 off-ICP pilot rows: 40% auto-resolve — not an AC verdict (B2B clinics, no Places key at the time); fixes shipped (escaped-URL regex, platform-account blocklist, SSL retry). On-segment micro-sample: 3/3 with-website resolved. | F-110, F-101, D-007 |
| 2026-07-05 | 1.3 | First on-segment AC batch (128 prospects, 6 segments): 47% overall, 64% of with-website — 26% of prospects have no website, the structural gap. Added Custom Search JSON API step to F-101 `search` method (official API; zero-overlap picks rejected); activates when `GOOGLE_CSE_ID` is set. AC re-measure pending CSE credentials. | F-101 |
