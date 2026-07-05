# n8n workflows

Export JSON here after every meaningful change (`NN-name.json`).
Instance: n8n.srv1318470.hstgr.cloud

| # | Workflow | Trigger | Status |
|---|---|---|---|
| 01 | scorer-daily | cron 07:00 daily | built, untested live — blocked on Meta app creds |
| 02 | private-replies-demo | IG comment webhook (PREÇO) | planned |
| 03 | pitch-queue-builder | score status → qualified | planned |
| 04 | metrics-rollup | cron weekly | planned |

Conventions: 25s spacing on Graph API loops · all secrets via n8n
credentials, never inline · every workflow upserts, never inserts blind.

## 01-scorer-daily setup (after import)

1. Credentials to create (names must match the JSON):
   - `Supabase service (custom auth)` — Custom Auth, JSON:
     `{"headers": {"apikey": "<service_role_key>", "Authorization": "Bearer <service_role_key>"}}`
   - `Meta Graph token (query auth)` — Query Auth, name `access_token`,
     value = long-lived token
   - `Anthropic x-api-key (header auth)` — Header Auth, name `x-api-key`,
     value = Anthropic API key
2. In the **Business Discovery** node URL, replace
   `REPLACE_MILEDEZ_IG_USER_ID` with the mil&dez IG user id.
3. Flow: fetch `v_prospects_to_score` (suppression enforced in the view,
   F-108) → loop 25s → Business Discovery → error 110 → `unscoreable_personal`
   · prefilters → `disqualified` · other errors → skipped, retried next run
   → S1/S2/S4 Code node → Claude P1 (bio) → P2 (≤9 grid images, URL source)
   → S3/S5 + evidence PT-BR → upsert `prospect_scores` (`on_conflict=ig_handle`);
   `auto ≥ 50` → status `in_review`, else `auto_scored`. P1/P2 raw always
   logged to `llm_raw`; `dominant_colors` persisted even off-funnel.
4. Known deviation from spec §3: grid images go to Claude as URLs
   (`source.type=url`) at original size, not downscaled to 512px — n8n has
   no image lib by default. Revisit if vision cost becomes material.
5. Code-node logic is fixture-tested outside n8n:
   scratchpad `test_workflow_js.js` (25 checks vs spec §2/§5/§8 tables).
