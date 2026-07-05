# P2 — Grid visual consistency (S5, 15 pts, vision)

Model: `claude-haiku-4-5` · temp 0 · max_tokens 500 · up to 9 images
(`media_url`, fallback `thumbnail_url` for VIDEO) downscaled to 512px,
fetched in the same n8n run (CDN URLs expire).

Placeholder: `{segment}`.

Scoring: consistency 1–2 → 15 · 3 → 8 · 4–5 → 0.
Persist `dominant_colors_hex` to `prospect_scores.dominant_colors` even when
the profile does not qualify — it seeds the Frame brand kit (stage 2).

---

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
