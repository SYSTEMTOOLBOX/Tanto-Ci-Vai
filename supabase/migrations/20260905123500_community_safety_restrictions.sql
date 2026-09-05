create table if not exists public.community_safety_restrictions (
  user_id uuid primary key references auth.users(id) on delete cascade,
  suspended_until timestamptz not null,
  reason text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint community_safety_restrictions_reason_len check (char_length(reason) <= 500)
);

alter table public.community_safety_restrictions enable row level security;
revoke all on table public.community_safety_restrictions from anon, authenticated;
grant select, insert, update, delete on table public.community_safety_restrictions to service_role;

comment on table public.community_safety_restrictions is 'Internal safety-feature suspensions for abusive or false Community SOS/hazard reporting. Not exposed to app clients.';
