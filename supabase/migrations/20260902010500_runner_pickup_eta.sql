-- Runner pickup confirmation + expected delivery time
alter table public.consegne
  add column if not exists consegna_prevista timestamptz;

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
    and stato = 'accettata';

  get diagnostics n = row_count;
  return n = 1;
end;
$$;

revoke all on function public.segna_ritiro_con_eta(uuid,timestamptz) from public;
grant execute on function public.segna_ritiro_con_eta(uuid,timestamptz) to authenticated;
