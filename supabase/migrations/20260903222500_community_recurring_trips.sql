create table if not exists public.community_trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  driver_name text not null default '',
  from_label text not null,
  from_lat double precision not null,
  from_lng double precision not null,
  to_label text not null,
  to_lat double precision not null,
  to_lng double precision not null,
  distance_km numeric(8,2) not null check (distance_km >= 0),
  price_per_km numeric(5,2) not null default 0.35 check (price_per_km > 0),
  seats smallint not null default 3 check (seats between 1 and 7),
  schedule jsonb not null default '{}'::jsonb,
  route_coords jsonb not null default '[]'::jsonb,
  active boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.community_trips enable row level security;

drop policy if exists community_trips_select on public.community_trips;
create policy community_trips_select on public.community_trips
for select to authenticated
using (active = true or user_id = auth.uid());

drop policy if exists community_trips_insert on public.community_trips;
create policy community_trips_insert on public.community_trips
for insert to authenticated
with check (user_id = auth.uid());

drop policy if exists community_trips_update on public.community_trips;
create policy community_trips_update on public.community_trips
for update to authenticated
using (user_id = auth.uid())
with check (user_id = auth.uid());

drop policy if exists community_trips_delete on public.community_trips;
create policy community_trips_delete on public.community_trips
for delete to authenticated
using (user_id = auth.uid());

grant select, insert, update, delete on public.community_trips to authenticated;

create index if not exists community_trips_active_idx on public.community_trips(active, updated_at desc);
create index if not exists community_trips_user_idx on public.community_trips(user_id, updated_at desc);
