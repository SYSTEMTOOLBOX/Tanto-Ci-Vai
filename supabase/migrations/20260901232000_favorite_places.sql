-- Tanto Ci Vai - luoghi preferiti utente
create table if not exists public.luoghi_preferiti (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  tipo text not null default 'farmacia',
  osm_type text,
  osm_id bigint,
  nome text not null,
  indirizzo text,
  lat double precision not null,
  lng double precision not null,
  created_at timestamptz not null default now(),
  constraint luoghi_preferiti_tipo_check check (tipo in ('farmacia')),
  constraint luoghi_preferiti_user_osm_unique unique (user_id, tipo, osm_type, osm_id)
);

alter table public.luoghi_preferiti enable row level security;

drop policy if exists "luoghi preferiti propri select" on public.luoghi_preferiti;
create policy "luoghi preferiti propri select"
on public.luoghi_preferiti for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "luoghi preferiti propri insert" on public.luoghi_preferiti;
create policy "luoghi preferiti propri insert"
on public.luoghi_preferiti for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "luoghi preferiti propri delete" on public.luoghi_preferiti;
create policy "luoghi preferiti propri delete"
on public.luoghi_preferiti for delete
to authenticated
using (auth.uid() = user_id);
