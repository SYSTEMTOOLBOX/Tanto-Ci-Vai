-- Tanto Ci Vai - beta backend helpers

create or replace function public.crea_profilo()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, nome, telefono)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'nome', ''),
    nullif(new.raw_user_meta_data ->> 'telefono', '')
  )
  on conflict (id) do update
    set nome = coalesce(nullif(excluded.nome, ''), public.profiles.nome),
        telefono = coalesce(excluded.telefono, public.profiles.telefono);

  return new;
end;
$$;

create or replace function public.aggiorna_stato_consegna(
  p_consegna_id uuid,
  p_stato text
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

  if p_stato not in ('ritirata', 'in_consegna', 'consegnata', 'annullata') then
    return false;
  end if;

  if p_stato = 'annullata' then
    update public.consegne
    set stato = 'annullata', updated_at = now()
    where id = p_consegna_id
      and cliente_id = auth.uid()
      and stato in ('disponibile', 'accettata');
  else
    update public.consegne
    set stato = p_stato, updated_at = now()
    where id = p_consegna_id
      and rider_id = auth.uid()
      and stato in ('accettata', 'ritirata', 'in_consegna');
  end if;

  get diagnostics n = row_count;
  return n = 1;
end;
$$;

revoke all on function public.aggiorna_stato_consegna(uuid, text) from public;
grant execute on function public.aggiorna_stato_consegna(uuid, text) to authenticated;

-- Add consegne to Supabase Realtime once, if it is not already present.
do $$
begin
  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'consegne'
  ) then
    alter publication supabase_realtime add table public.consegne;
  end if;
end;
$$;
