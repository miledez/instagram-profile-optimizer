# P1 — Bio offer/CTA classifier (S3, 15 pts)

Model: `claude-haiku-4-5` · temp 0 · max_tokens 500 · strip ```json fences
before parse · 1 retry on parse failure → `llm_error`.

Placeholders: `{biography}`, `{segment}`.

Scoring: `!has_offer && !has_cta` → 15 · exactly one missing → 8 · both → 0.
`segment_conflict = true` → flag prospect row (wrong benchmark applied).

---

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
