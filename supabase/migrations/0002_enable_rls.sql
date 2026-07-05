-- 0002_enable_rls.sql
-- Enable RLS with no policies: anon key fully locked out, service role
-- (scripts, n8n, dashboard server routes) bypasses RLS by design.
-- Prospect rows are PII under LGPD — advisor flagged all tables critical.

alter table prospects enable row level security;
alter table prospect_scores enable row level security;
alter table suppression_list enable row level security;
alter table variants enable row level security;
alter table touches enable row level security;
alter table outcomes enable row level security;
