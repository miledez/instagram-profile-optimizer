-- 0001_initial_schema.sql
-- Pipeline core: prospects, scores, suppression, A/B variants, touches, outcomes.

create table if not exists prospects (
  id uuid primary key default gen_random_uuid(),
  cnpj text unique,
  business_name text not null,
  segment text not null check (segment in
    ('estetica','odonto','salao','restaurante','pet','fitness','outro')),
  city text, uf text, city_tier smallint,           -- 1 capital, 2 interior grande, 3 interior
  phone_e164 text,                                   -- from Places/CNPJ, WhatsApp target
  website text,
  places_id text,
  ig_handle text unique,
  ig_resolution_method text,                         -- website_scrape | search | manual | null
  created_at timestamptz default now()
);

create table if not exists prospect_scores (
  id uuid primary key default gen_random_uuid(),
  prospect_id uuid references prospects(id) on delete cascade,
  ig_handle text not null unique,
  followers int,
  segment text,
  s1 int, s2 int, s3 int, s4 int, s5 int, s6 int, s7 int,
  auto_score int generated always as
    (coalesce(s1,0)+coalesce(s2,0)+coalesce(s3,0)+coalesce(s4,0)+coalesce(s5,0)) stored,
  final_score int,
  er numeric,
  posts_90d int,
  dominant_colors jsonb,                             -- P2 output, seeds Frame brand kit
  evidence jsonb,                                    -- PT-BR strings for pitch injection
  llm_raw jsonb,                                     -- P1/P2 raw outputs (calibration week)
  before_screenshot_url text,
  status text not null default 'pending' check (status in
    ('pending','auto_scored','in_review','qualified','disqualified',
     'unscoreable_personal','llm_error','suppressed')),
  scored_at timestamptz default now()
);

create table if not exists suppression_list (
  id uuid primary key default gen_random_uuid(),
  ig_handle text,
  phone_e164 text,
  cnpj text,
  reason text not null,                              -- opt_out | bounced | client | manual
  created_at timestamptz default now()
);
create index on suppression_list (ig_handle);
create index on suppression_list (phone_e164);

create table if not exists variants (
  id text primary key,                               -- e.g. 'pitch-weakness-v1', 'price-B'
  dimension text not null check (dimension in
    ('pitch_copy','mockup_style','price_point','channel')),
  description text,
  payload jsonb,                                     -- template text, price values, etc.
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists touches (
  id uuid primary key default gen_random_uuid(),
  prospect_id uuid references prospects(id) on delete cascade,
  channel text not null check (channel in ('whatsapp','ig_dm')),
  pitch_variant text references variants(id),
  mockup_variant text references variants(id),
  price_variant text references variants(id),
  sent_at timestamptz,
  delivered boolean,
  replied_at timestamptz,
  meeting_at timestamptz,
  notes text
);

create table if not exists outcomes (
  id uuid primary key default gen_random_uuid(),
  prospect_id uuid references prospects(id) on delete cascade,
  status text not null check (status in
    ('open','replied','meeting','closed_won','closed_lost','opted_out')),
  setup_fee_brl numeric,
  monthly_brl numeric,
  closed_at timestamptz,
  updated_at timestamptz default now()
);

-- Weekly A/B rollup
create or replace view v_variant_performance as
select
  t.pitch_variant,
  t.price_variant,
  t.channel,
  count(*)                                       as sends,
  count(*) filter (where t.delivered)            as delivered,
  count(*) filter (where t.replied_at is not null) as replies,
  count(*) filter (where t.meeting_at is not null) as meetings,
  count(o.id) filter (where o.status = 'closed_won') as closes,
  round(100.0 * count(*) filter (where t.replied_at is not null)
        / nullif(count(*) filter (where t.delivered), 0), 1) as reply_rate_pct
from touches t
left join outcomes o on o.prospect_id = t.prospect_id
group by 1, 2, 3;
