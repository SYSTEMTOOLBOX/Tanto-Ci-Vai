create sequence if not exists public.tcv_order_number_seq
  as bigint
  increment by 1
  minvalue 0
  start with 0
  no cycle;

alter table public.consegne
  add column if not exists numero_ordine bigint;

create unique index if not exists consegne_numero_ordine_unique
  on public.consegne (numero_ordine)
  where numero_ordine is not null;

create or replace function private.tcv_assign_order_number()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if tg_op = 'INSERT' then
    new.numero_ordine := nextval('public.tcv_order_number_seq'::regclass);
  elsif new.numero_ordine is distinct from old.numero_ordine then
    new.numero_ordine := old.numero_ordine;
  end if;
  return new;
end;
$$;

revoke all on function private.tcv_assign_order_number() from public, anon, authenticated;

drop trigger if exists tcv_assign_order_number on public.consegne;
create trigger tcv_assign_order_number
before insert or update of numero_ordine on public.consegne
for each row
execute function private.tcv_assign_order_number();

comment on column public.consegne.numero_ordine is
  'Numero ordine progressivo assegnato dal database. I dati beta precedenti restano senza numero; il primo nuovo ordine parte da 0000.';
