create table if not exists public.runner_wallet_entries (
  id uuid primary key default gen_random_uuid(),
  rider_id uuid not null references auth.users(id) on delete cascade,
  consegna_id uuid not null references public.consegne(id) on delete restrict,
  amount numeric(10,2) not null check (amount >= 0),
  title text not null,
  category text,
  earned_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (consegna_id)
);

create index if not exists runner_wallet_entries_rider_earned_idx
  on public.runner_wallet_entries (rider_id, earned_at desc);

alter table public.runner_wallet_entries enable row level security;
revoke all on public.runner_wallet_entries from anon;
revoke insert, update, delete on public.runner_wallet_entries from authenticated;
grant select on public.runner_wallet_entries to authenticated;

drop policy if exists "runner_wallet_entries_select_own" on public.runner_wallet_entries;
create policy "runner_wallet_entries_select_own"
on public.runner_wallet_entries
for select to authenticated
using ((select auth.uid()) = rider_id);

create table if not exists public.runner_wallet_years (
  user_id uuid not null references auth.users(id) on delete cascade,
  year integer not null check (year between 2020 and 2100),
  external_gross numeric(10,2) not null default 0 check (external_gross >= 0),
  updated_at timestamptz not null default now(),
  primary key (user_id, year)
);

alter table public.runner_wallet_years enable row level security;
revoke all on public.runner_wallet_years from anon;
grant select, insert, update on public.runner_wallet_years to authenticated;
revoke delete on public.runner_wallet_years from authenticated;

drop policy if exists "runner_wallet_years_select_own" on public.runner_wallet_years;
create policy "runner_wallet_years_select_own"
on public.runner_wallet_years
for select to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "runner_wallet_years_insert_own" on public.runner_wallet_years;
create policy "runner_wallet_years_insert_own"
on public.runner_wallet_years
for insert to authenticated
with check ((select auth.uid()) = user_id);

drop policy if exists "runner_wallet_years_update_own" on public.runner_wallet_years;
create policy "runner_wallet_years_update_own"
on public.runner_wallet_years
for update to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create or replace function private.tcv_record_runner_wallet_entry()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.stato = 'consegnata'
     and old.stato is distinct from 'consegnata'
     and new.rider_id is not null then
    insert into public.runner_wallet_entries(
      rider_id, consegna_id, amount, title, category, earned_at
    ) values (
      new.rider_id,
      new.id,
      new.compenso_rider,
      new.titolo,
      new.categoria,
      coalesce(new.updated_at, now())
    )
    on conflict (consegna_id) do nothing;
  end if;
  return new;
end;
$$;

revoke all on function private.tcv_record_runner_wallet_entry() from public, anon, authenticated;

drop trigger if exists tcv_runner_wallet_on_delivery on public.consegne;
create trigger tcv_runner_wallet_on_delivery
after update of stato on public.consegne
for each row
execute function private.tcv_record_runner_wallet_entry();

insert into public.runner_wallet_entries(
  rider_id, consegna_id, amount, title, category, earned_at
)
select
  c.rider_id,
  c.id,
  c.compenso_rider,
  c.titolo,
  c.categoria,
  coalesce(c.updated_at, c.created_at, now())
from public.consegne c
where c.stato = 'consegnata'
  and c.rider_id is not null
on conflict (consegna_id) do nothing;
