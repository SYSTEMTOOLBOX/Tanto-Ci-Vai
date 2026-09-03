create table if not exists public.ride_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  from_label text not null,
  from_lat double precision,
  from_lng double precision,
  to_label text not null,
  to_lat double precision,
  to_lng double precision,
  departure_at timestamptz not null,
  flex_minutes integer not null default 30 check (flex_minutes between 0 and 180),
  passengers integer not null default 1 check (passengers between 1 and 6),
  note text not null default '',
  status text not null default 'open' check (status in ('open','matched','cancelled','completed')),
  driver_id uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

alter table public.ride_requests enable row level security;

drop policy if exists ride_requests_select on public.ride_requests;
create policy ride_requests_select on public.ride_requests
for select to authenticated
using (status = 'open' or user_id = auth.uid() or driver_id = auth.uid());

drop policy if exists ride_requests_insert on public.ride_requests;
create policy ride_requests_insert on public.ride_requests
for insert to authenticated
with check (user_id = auth.uid());

drop policy if exists ride_requests_update on public.ride_requests;
create policy ride_requests_update on public.ride_requests
for update to authenticated
using (user_id = auth.uid() or driver_id = auth.uid())
with check (user_id = auth.uid() or driver_id = auth.uid());

drop policy if exists ride_requests_delete on public.ride_requests;
create policy ride_requests_delete on public.ride_requests
for delete to authenticated
using (user_id = auth.uid());

create index if not exists ride_requests_open_departure_idx on public.ride_requests(status, departure_at);
create index if not exists ride_requests_user_idx on public.ride_requests(user_id, created_at desc);
