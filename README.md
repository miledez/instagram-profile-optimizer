# instagram-profile-optimizer

Automated pipeline for mil&dez's productized Instagram makeover service
(Brazilian local-service SMBs). Prospect → score → mockup → demo hook →
pitch → A/B feedback loop.

Start here: `CLAUDE.md` (operating manual) · `STATUS.md` (current state) ·
`docs/scorer-spec.md` (week-1 build spec) · `docs/decisions.md` (why).

| Directory | Contents |
|---|---|
| `docs/` | Specs and append-only decisions log |
| `supabase/migrations/` | Schema (prospects, scores, variants, touches, outcomes) |
| `prompts/` | Claude classification prompts (P1 bio, P2 grid vision) |
| `n8n/` | Exported workflow JSON + inventory |
| `scripts/` | Handle resolver (Python) |
| `dashboard/` | Review queue + pitch queue (Next.js 14, week 2) |

Compliance: official Meta APIs only · human-in-loop outbound · LGPD
(public business data, opt-out honored via suppression list).
