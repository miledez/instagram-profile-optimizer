# Decisions log (append-only)

Format: `D-NNN · date · decision · context`. Never edit past entries; supersede
with a new one.

---

**D-001 · 2026-07-05 · Compliance routes locked**
Profile data via Graph API Business Discovery only (no scraping). Cold
WhatsApp via Business app + wa.me prefilled links, human tap-to-send,
50–80/day per warmed number (Cloud API cold sends violate Meta policy).
IG DM demo via Private Replies on the mil&dez account (comment PREÇO → DM);
cold DMs manual from queue.

**D-002 · 2026-07-05 · Scoring thresholds**
Weakness points 0–100, higher = weaker. Auto signals max 80. auto ≥50 →
human 30s review (S6/S7 + screenshot). final ≥60 → enters funnel. Calibrate
after 200 scored (target 25–35% qualification rate).

**D-003 · 2026-07-05 · Model choice**
`claude-haiku-4-5` for both P1 (bio) and P2 (grid vision), temp 0, JSON-only.
Images downscaled to 512px. Sonnet reserved for pitch drafting if needed.

**D-004 · 2026-07-05 · Pricing test variants**
A: R$497 setup + R$247/mo (volume, interior/pet/restaurante).
B: R$797 + R$397 (default). C: R$1.297 + R$597 (estética/odonto capitais).
Anchored on 2026 market: PME packages R$800–2.500/mo; nearest comparable
product R$490 setup + R$450/mo.

**D-005 · 2026-07-05 · Repo scope**
This repo: scorer (n8n + prompts + scripts), Private Replies demo workflow,
pitch queue, dashboard, Supabase migrations, A/B tracking. Mockup generation
stays in Frame (`~/instagram-admin`) — it consumes `dominant_colors` from
`prospect_scores`. Prospecting CLI (`run.py`) stays in its own repo and
writes into the shared `prospects` table.

**D-006 · 2026-07-05 · Success metrics / lock criteria**
Delivery >95% · reply ≥15% · reply→meeting ≥40% · meeting→close ≥25%
(≈3% close of contacted). One A/B variable per week, min 100 sends/variant.
Lock winning combo when reply ≥15% and close ≥3%, then scale volume.

**D-007 · 2026-07-05 · Prospecting localized (supersedes D-005 in part)**
Stage 1a moved into this repo as `scripts/prospect.py` — self-contained
Places prospecting for the six IG segments, deduping against the shared
`prospects` table (no local cache; Supabase is the single source of truth).
The external `run.py` (miledez-main) keeps only its original four Sheets
verticals for the other product line; its IG additions were reverted the
same day to avoid two pipelines writing one table.
