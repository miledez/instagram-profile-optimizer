# SPEC — Instagram Weakness Scorer (v1)

Pipeline stage 1b. Input: prospect row (from `run.py`) + resolved IG handle.
Output: `weakness_score` 0–100 + evidence strings (PT-BR) for pitch injection.
Funnel entry: **final_score ≥ 60**. Higher = weaker profile.

---

## 1. Data acquisition — Business Discovery (Graph API)

Single call per prospect, from the mil&dez IG business account:

```
GET https://graph.facebook.com/v23.0/{MILEDEZ_IG_USER_ID}
  ?fields=business_discovery.username({handle}){
    username,name,biography,website,followers_count,media_count,
    profile_picture_url,
    media.limit(12){id,caption,media_type,media_url,thumbnail_url,
                    like_count,comments_count,timestamp,permalink}
  }
  &access_token={LONG_LIVED_TOKEN}
```

Prereqs: mil&dez IG professional account linked to FB Page; app with
`instagram_basic`, `instagram_manage_insights`; long-lived token in n8n creds.

Constraints:
- Target must be **business/creator** account. Error code 110 / "cannot be
  found" → set `status = unscoreable_personal`, route to manual queue (still
  a prospect — personal account is itself a weakness signal for the pitch).
- Rate limit: ~200 calls/hr (BUC). n8n: batch 150/hr, 25s spacing.
- `like_count` may be null/0 when owner hides likes → see S2 fallback.

Pre-filters (drop before scoring): `followers_count` < 500 or > 20 000;
`media_count` = 0; handle already in suppression list.

---

## 2. Rubric — signals, weights, computation

| # | Signal | Pts | Method |
|---|--------|-----|--------|
| S1 | Posting frequency | 20 | deterministic |
| S2 | Engagement vs benchmark | 20 | deterministic |
| S3 | Bio without offer/CTA | 15 | Claude (P1) |
| S4 | No link-in-bio | 10 | deterministic |
| S5 | Grid inconsistency | 15 | Claude vision (P2) |
| S6 | Highlights unbranded/absent | 10 | human review |
| S7 | Unanswered comments / no WA button | 10 | human review |

Auto max = 80. If `auto_score ≥ 50` → human review queue (30 s: S6 + S7 +
"antes" screenshot capture). `final_score = auto + S6 + S7`.

### S1 — Posting frequency (20)
`posts_90d` = count of media with `timestamp ≥ now − 90d` (from the 12
returned; if all 12 are within 90d, cap rate at 1+/wk → 0 pts, no extra call).
`weekly_rate = posts_90d / 12.86`

| weekly_rate | Pts |
|---|---|
| < 0.25 | 20 |
| 0.25–0.49 | 15 |
| 0.5–0.99 | 10 |
| ≥ 1 | 0 |

### S2 — Engagement vs segment benchmark (20)
`ER = mean((like_count + comments_count) / followers_count)` over last 12
posts, excluding the single highest outlier (viral skew).

Fallback when likes hidden (≥ 6 posts with null/0 likes but comments > 0):
`ER_c = mean(comments_count / followers_count)`; use comment benchmark column.

| ER vs benchmark | Pts |
|---|---|
| < 40% | 20 |
| 40–69% | 12 |
| 70–99% | 6 |
| ≥ 100% | 0 |

Initial benchmarks (500–20k local BR accounts — **calibrate after first 200
scored**, replace with observed segment medians):

| Segment | ER bench | Comments-only bench |
|---|---|---|
| Clínica estética | 3.5% | 0.20% |
| Odontologia | 2.5% | 0.12% |
| Salão/barbearia | 3.0% | 0.15% |
| Restaurante | 2.0% | 0.10% |
| Pet shop/vet | 4.0% | 0.25% |
| Fitness/studio | 3.0% | 0.15% |

### S4 — Link-in-bio (10)
0 pts if `website` non-empty **or** biography matches
`/(wa\.me|api\.whatsapp|linktr\.ee|bit\.ly|beacons|linkin\.bio|https?:\/\/)/i`.
Else 10.

---

## 3. Claude classification prompts

Model: `claude-haiku-4-5` for both (P2 with images). Temperature 0,
max_tokens 500. Wrap in try/catch; on parse failure retry once, then
`status = llm_error`. Strip ```json fences before `JSON.parse`.

### P1 — Bio offer/CTA (S3)

```
Você é um classificador. Analise a bio de Instagram de um negócio local
brasileiro e responda APENAS com JSON válido, sem markdown, sem texto extra.

Definições:
- "oferta": a bio comunica claramente o que o negócio vende/faz e para quem
  (serviço + diferencial ou benefício). Apenas nome/cidade/emoji não conta.
- "cta": instrução explícita de ação ("agende", "chame no WhatsApp",
  "clique no link", "peça pelo link", "reserve").

Bio:
"""
{biography}
"""
Segmento provável (do cadastro): {segment}

Responda:
{
  "has_offer": boolean,
  "has_cta": boolean,
  "detected_segment": "estetica|odonto|salao|restaurante|pet|fitness|outro",
  "segment_conflict": boolean,
  "notes_ptbr": "máx 15 palavras, fraqueza principal da bio"
}
```

Scoring: `!has_offer && !has_cta` → 15 · one missing → 8 · both present → 0.
`segment_conflict = true` → flag row (mis-tagged prospect, wrong benchmark).

### P2 — Grid visual consistency (S5)

Input: up to 9 images (`media_url`, fallback `thumbnail_url` for VIDEO),
downscaled to 512px before sending (cost + speed).

```
Você é um auditor de identidade visual. Estas são as últimas publicações do
feed de Instagram de um negócio local brasileiro ({segment}). Avalie a
consistência visual do grid como um todo. Responda APENAS com JSON válido.

Critérios:
- Paleta de cores recorrente e proposital
- Tipografia/templates consistentes entre artes
- Proporção equilibrada entre foto real e arte gráfica
- Aparência amadora: prints, imagens esticadas, textos ilegíveis,
  artes genéricas de banco/IA sem marca

Responda:
{
  "consistency_1_5": 1-5,
  "dominant_colors_hex": ["#...", "#...", "#..."],
  "has_visible_branding": boolean,
  "amateur_signals_ptbr": ["máx 3 itens, 8 palavras cada"],
  "grid_summary_ptbr": "1 frase, tom neutro"
}
```

Scoring: 1–2 → 15 · 3 → 8 · 4–5 → 0.
Side effect: `dominant_colors_hex` seeds the Frame brand kit (stage 2) —
persist it even for profiles that don't enter the funnel.

---

## 4. Human review (S6 + S7) — 30 s checklist

Dashboard card per prospect (`auto_score ≥ 50` only), open profile link:

| Check | Pts if weak |
|---|---|
| Highlights: absent, or covers unbranded/mismatched | 10 |
| ≥ 3 unanswered customer comments (last 12 posts) **ou** sem botão WhatsApp/contato | 10 |
| Capture screenshot "antes" (upload to Supabase storage) | — |
| Override: profile actually fine → mark `disqualified` | — |

---

## 5. Evidence strings (feeds stage 4 pitch)

Deterministic PT-BR templates, generated at scoring time, stored in
`evidence` jsonb, ordered by points desc — pitch takes top 2–3:

| Signal | Template |
|---|---|
| S1 | `só {posts_90d} publicações nos últimos 3 meses` |
| S2 | `engajamento de {er:.1%} — a média do setor é {bench:.1%}` |
| S3 | `a bio não diz o que vocês oferecem nem como agendar` |
| S4 | `sem link de agendamento ou WhatsApp na bio` |
| S5 | `{grid_summary_ptbr}` (from P2) |
| S6 | `destaques sem capas com a identidade da marca` |
| S7 | `comentários de clientes sem resposta` |

---

## 6. Storage — Supabase `prospect_scores`

```sql
create table prospect_scores (
  id uuid primary key default gen_random_uuid(),
  prospect_id uuid references prospects(id),
  ig_handle text not null,
  followers int,
  segment text,
  s1 int, s2 int, s3 int, s4 int, s5 int, s6 int, s7 int,
  auto_score int generated always as
    (coalesce(s1,0)+coalesce(s2,0)+coalesce(s3,0)+coalesce(s4,0)+coalesce(s5,0)) stored,
  final_score int,
  er numeric, posts_90d int,
  dominant_colors jsonb,
  evidence jsonb,
  before_screenshot_url text,
  status text default 'pending',
    -- pending | auto_scored | in_review | qualified | disqualified
    -- | unscoreable_personal | llm_error | suppressed
  scored_at timestamptz default now(),
  unique (ig_handle)
);
```

---

## 7. n8n flow (stage 1b)

1. Cron 1×/dia → rows in `prospects` with handle e sem score
2. Loop 25 s spacing → Business Discovery call
3. Error 110 → `unscoreable_personal`, next
4. Pre-filters → drop/`disqualified`
5. Compute S1/S2/S4 (Code node)
6. Claude P1 (bio) → Claude P2 (9 imagens, 512px)
7. Upsert `prospect_scores` + evidence
8. `auto_score ≥ 50` → status `in_review` → notifica dashboard

## 8. Edge cases

| Case | Handling |
|---|---|
| < 12 posts total | Score with available; if < 4 posts, S2 = null → S2 pts = 12 (thin data ≈ weak) |
| Likes hidden | Comments-only fallback (S2) |
| Carousel/Reels | `like_count`/`comments_count` work normally; Reels views not available — ignore |
| Handle typo (resolver) | 110 error → back to resolver retry queue, 1 retry |
| Duplicate CNPJ, 2 handles | Score both, keep higher final_score |
| Media_url expired (CDN TTL) | Fetch images immediately after API call, same n8n run |

## 9. Calibration (semana 4)

After 200 scored: replace benchmark table with observed per-segment medians;
tune threshold so ~25–35% of scored profiles qualify (≥60). Log P1/P2 raw
outputs for 1 week to spot-check drift.
