create table if not exists public.satispay_payments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  satispay_payment_id text not null unique,
  order_ref text not null,
  amount_unit integer not null check (amount_unit > 0),
  currency text not null default 'EUR',
  status text not null default 'PENDING',
  sandbox boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  accepted_at timestamptz,
  cancelled_at timestamptz
);

alter table public.satispay_payments enable row level security;

drop policy if exists satispay_payments_select_own on public.satispay_payments;
create policy satispay_payments_select_own on public.satispay_payments
for select to authenticated
using (user_id = auth.uid());

revoke insert, update, delete on table public.satispay_payments from anon, authenticated;
grant select on table public.satispay_payments to authenticated;
grant select, insert, update, delete on table public.satispay_payments to service_role;

create index if not exists satispay_payments_user_created_idx on public.satispay_payments(user_id, created_at desc);
create index if not exists satispay_payments_status_idx on public.satispay_payments(status, updated_at desc);
