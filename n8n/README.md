# n8n workflows

Export JSON here after every meaningful change (`NN-name.json`).
Instance: n8n.srv1318470.hstgr.cloud

| # | Workflow | Trigger | Status |
|---|---|---|---|
| 01 | scorer-daily | cron 1x/day | planned — spec §7 |
| 02 | private-replies-demo | IG comment webhook (PREÇO) | planned |
| 03 | pitch-queue-builder | score status → qualified | planned |
| 04 | metrics-rollup | cron weekly | planned |

Conventions: 25s spacing on Graph API loops · all secrets via n8n
credentials, never inline · every workflow upserts, never inserts blind.
