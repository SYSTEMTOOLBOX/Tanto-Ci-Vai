-- Requester-defined maximum delivery deadline
alter table public.consegne
  add column if not exists consegna_entro timestamptz;

-- A runner cannot newly accept a request whose requester deadline has already expired.
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
    and cliente_id <> auth.uid()
    and (consegna_entro is null or consegna_entro > now());

  get diagnostics n = row_count;
  return n = 1;
end;
$$;

revoke all on function public.accetta_consegna(uuid) from public;
grant execute on function public.accetta_consegna(uuid) to authenticated;

-- Pickup confirmation keeps the runner ETA inside the requester's deadline while the deadline is still achievable.
create or replace function public.segna_ritiro_con_eta(
  p_consegna_id uuid,
  p_consegna_prevista timestamptz
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  n integer;
begin
  if auth.uid() is null or p_consegna_prevista is null or p_consegna_prevista <= now() then
    return false;
  end if;

  update public.consegne
  set
    stato = 'ritirata',
    consegna_prevista = p_consegna_prevista,
    updated_at = now()
  where
    id = p_consegna_id
    and rider_id = auth.uid()
    and stato = 'accettata'
    and (
      consegna_entro is null
      or consegna_entro <= now()
      or p_consegna_prevista <= consegna_entro
    );

  get diagnostics n = row_count;
  return n = 1;
end;
$$;

revoke all on function public.segna_ritiro_con_eta(uuid,timestamptz) from public;
grant execute on function public.segna_ritiro_con_eta(uuid,timestamptz) to authenticated;
