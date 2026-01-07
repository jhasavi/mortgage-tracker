-- Migration: Mortgage Rates schema, RLS, and public view
-- Safety: No public access to raw snapshots; anon can read view only

begin;

-- Tables
create table if not exists public.sources (
  id bigserial primary key,
  name text not null unique,
  org_type text,
  homepage_url text,
  rate_url text,
  method text not null,
  enabled boolean not null default true,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_sources_enabled on public.sources(enabled);

create table if not exists public.runs (
  id bigserial primary key,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null check (status in ('started','success','partial','failed')),
  stats_json jsonb not null default '{}'::jsonb,
  error_text text,
  created_at timestamptz not null default now()
);

create index if not exists idx_runs_started_at on public.runs(started_at desc);
create index if not exists idx_runs_status on public.runs(status);

create table if not exists public.rate_snapshots (
  id bigserial primary key,
  run_id bigint not null references public.runs(id) on delete cascade,
  source_id bigint not null references public.sources(id) on delete cascade,
  fetched_at timestamptz not null default now(),
  http_status integer,
  raw_text text,
  raw_json jsonb,
  parse_status text check (parse_status in ('parsed','failed','skipped')),
  parse_error text,
  created_at timestamptz not null default now()
);

create index if not exists idx_rate_snapshots_run on public.rate_snapshots(run_id);
create index if not exists idx_rate_snapshots_source on public.rate_snapshots(source_id);
create index if not exists idx_rate_snapshots_fetched_at on public.rate_snapshots(fetched_at desc);

create table if not exists public.offers_normalized (
  id bigserial primary key,
  run_id bigint not null references public.runs(id) on delete cascade,
  source_id bigint not null references public.sources(id) on delete cascade,
  lender_name text not null,
  category text not null check (category in ('30Y fixed','15Y fixed','5/6 ARM','FHA 30Y','VA 30Y')),
  rate numeric,
  apr numeric,
  points numeric,
  lender_fees numeric,
  loan_amount numeric,
  ltv numeric,
  fico integer,
  state text,
  term_months integer,
  lock_days integer,
  updated_at timestamptz not null default now(),
  details_json jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_offers_category_updated on public.offers_normalized(category, updated_at desc);
create index if not exists idx_offers_source on public.offers_normalized(source_id);
create index if not exists idx_offers_run on public.offers_normalized(run_id);

create table if not exists public.lenders (
  id bigserial primary key,
  lender_name text not null unique,
  is_favorite boolean not null default false,
  is_excluded boolean not null default false,
  notes text,
  created_at timestamptz not null default now()
);

-- RLS: enable on all tables; no public policies
alter table public.sources enable row level security;
alter table public.runs enable row level security;
alter table public.rate_snapshots enable row level security;
alter table public.offers_normalized enable row level security;
alter table public.lenders enable row level security;

-- No policies are created here intentionally; service role bypasses RLS for writes.

-- View: latest results from most recent successful/partial run
create or replace view public.latest_rates_view as
with last_run as (
  select r.id
  from public.runs r
  where r.status in ('success','partial')
  order by r.started_at desc
  limit 1
)
select 
  o.lender_name,
  o.category,
  o.rate,
  o.apr,
  o.points,
  o.lender_fees,
  o.state,
  o.loan_amount,
  o.ltv,
  o.fico,
  o.lock_days,
  o.updated_at,
  o.source_id
from public.offers_normalized o
join last_run lr on o.run_id = lr.id;

-- RLS policies to allow anon read of the latest run only
drop policy if exists anon_select_latest_run on public.runs;
create policy anon_select_latest_run on public.runs
  for select to anon
  using (
    status in ('success','partial')
    and id = (
      select r2.id from public.runs r2
      where r2.status in ('success','partial')
      order by r2.started_at desc
      limit 1
    )
  );

drop policy if exists anon_select_latest_offers on public.offers_normalized;
create policy anon_select_latest_offers on public.offers_normalized
  for select to anon
  using (
    run_id = (
      select r2.id from public.runs r2
      where r2.status in ('success','partial')
      order by r2.started_at desc
      limit 1
    )
  );

-- Allow anonymous read on the view only
grant usage on schema public to anon;
grant select on public.latest_rates_view to anon;

-- Ensure anon has no direct access to raw tables
revoke select on public.rate_snapshots from anon;
revoke select on public.runs from anon;
revoke select on public.sources from anon;
revoke select on public.offers_normalized from anon;
revoke select on public.lenders from anon;

commit;
