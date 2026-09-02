create table if not exists public.help_alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  message text not null default '',
  lat double precision,
  lng double precision,
  location_label text,
  created_at timestamptz not null default now()
);

alter table public.help_alerts enable row level security;

create index if not exists help_alerts_user_created_idx
  on public.help_alerts(user_id, created_at desc);

revoke all on table public.help_alerts from anon, authenticated;
