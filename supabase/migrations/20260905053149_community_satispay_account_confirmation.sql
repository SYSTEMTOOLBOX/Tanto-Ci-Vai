alter table public.community_public_profiles
  add column if not exists account_confirmed boolean not null default false,
  add column if not exists account_confirmed_at timestamptz;

create table if not exists public.community_satispay_accounts (
  user_id uuid primary key references auth.users(id) on delete cascade,
  authorization_id text unique,
  consumer_uid text,
  status text not null default 'PENDING' check (status in ('PENDING','ACCEPTED','CANCELED')),
  sandbox boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  confirmed_at timestamptz
);

alter table public.community_satispay_accounts enable row level security;
revoke all on table public.community_satispay_accounts from anon, authenticated;
grant select on table public.community_satispay_accounts to authenticated;

drop policy if exists community_satispay_accounts_select_own on public.community_satispay_accounts;
create policy community_satispay_accounts_select_own
on public.community_satispay_accounts
for select
to authenticated
using ((select auth.uid()) = user_id);

create or replace function public.tcv_guard_account_confirmed()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_confirmed_at timestamptz;
begin
  select confirmed_at into v_confirmed_at
  from public.community_satispay_accounts
  where user_id = new.user_id and status = 'ACCEPTED'
  limit 1;

  new.account_confirmed := (v_confirmed_at is not null);
  new.account_confirmed_at := v_confirmed_at;
  return new;
end;
$$;

revoke all on function public.tcv_guard_account_confirmed() from public, anon, authenticated;

drop trigger if exists tcv_guard_account_confirmed on public.community_public_profiles;
create trigger tcv_guard_account_confirmed
before insert or update of account_confirmed, account_confirmed_at on public.community_public_profiles
for each row execute function public.tcv_guard_account_confirmed();
