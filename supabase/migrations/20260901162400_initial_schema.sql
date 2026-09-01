-- Tanto Ci Vai - initial Supabase schema

-- 1. Profili utenti
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nome text,
  telefono text,
  disponibile boolean not null default false,
  created_at timestamptz not null default now()
);

-- 2. Consegne
create table if not exists public.consegne (
  id uuid primary key default gen_random_uuid(),

  cliente_id uuid not null
    references public.profiles(id) on delete cascade,

  rider_id uuid
    references public.profiles(id) on delete set null,

  titolo text not null,
  descrizione text,

  ritiro_indirizzo text not null,
  ritiro_lat double precision,
  ritiro_lng double precision,

  consegna_indirizzo text not null,
  consegna_lat double precision,
  consegna_lng double precision,

  compenso_rider numeric(8,2) not null default 0,
  commissione_app numeric(8,2) not null default 0.50,

  stato text not null default 'disponibile'
    check (
      stato in (
        'disponibile',
        'accettata',
        'ritirata',
        'in_consegna',
        'consegnata',
        'annullata'
      )
    ),

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- 3. Row Level Security
alter table public.profiles enable row level security;
alter table public.consegne enable row level security;

-- 4. Rimuove eventuali policy precedenti prima di ricrearle
drop policy if exists prof_select_own on public.profiles;
drop policy if exists prof_insert_own on public.profiles;
drop policy if exists prof_update_own on public.profiles;

drop policy if exists "profilo personale lettura" on public.profiles;
drop policy if exists "profilo personale creazione" on public.profiles;
drop policy if exists "profilo personale modifica" on public.profiles;

drop policy if exists consegne_select_visible on public.consegne;
drop policy if exists consegne_insert_own on public.consegne;

drop policy if exists "consegne visibili" on public.consegne;
drop policy if exists "creazione consegna" on public.consegne;
drop policy if exists "modifica consegna" on public.consegne;

-- 5. Policy profili
create policy prof_select_own
on public.profiles
for select
to authenticated
using (
  auth.uid() = id
);

create policy prof_insert_own
on public.profiles
for insert
to authenticated
with check (
  auth.uid() = id
);

create policy prof_update_own
on public.profiles
for update
to authenticated
using (
  auth.uid() = id
)
with check (
  auth.uid() = id
);

-- 6. Policy consegne
create policy consegne_select_visible
on public.consegne
for select
to authenticated
using (
  stato = 'disponibile'
  or cliente_id = auth.uid()
  or rider_id = auth.uid()
);

create policy consegne_insert_own
on public.consegne
for insert
to authenticated
with check (
  cliente_id = auth.uid()
  and rider_id is null
  and stato = 'disponibile'
);

-- 7. Permessi API
grant usage on schema public to authenticated;

grant select, insert
on public.profiles
to authenticated;

grant update (nome, telefono, disponibile)
on public.profiles
to authenticated;

grant select, insert
on public.consegne
to authenticated;

-- 8. Il rider prende una consegna disponibile in modo atomico
create or replace function public.accetta_consegna(
  p_consegna_id uuid
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  n integer;
begin

  if auth.uid() is null then
    return false;
  end if;

  update public.consegne
  set
    rider_id = auth.uid(),
    stato = 'accettata',
    updated_at = now()
  where
    id = p_consegna_id
    and stato = 'disponibile'
    and rider_id is null
    and cliente_id <> auth.uid();

  get diagnostics n = row_count;

  return n = 1;

end;
$$;

revoke all
on function public.accetta_consegna(uuid)
from public;

grant execute
on function public.accetta_consegna(uuid)
to authenticated;

-- 9. Crea automaticamente il profilo quando nasce un utente Auth
create or replace function public.crea_profilo()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin

  insert into public.profiles (
    id,
    nome
  )
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'nome', '')
  )
  on conflict (id) do nothing;

  return new;

end;
$$;

drop trigger if exists nuovo_utente_profilo
on auth.users;

create trigger nuovo_utente_profilo
after insert on auth.users
for each row
execute function public.crea_profilo();
