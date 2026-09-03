alter table public.consegne
  add column if not exists route_km numeric(8,2),
  add column if not exists tariffa_km numeric(8,2) not null default 0.50,
  add column if not exists payment_state text,
  add column if not exists app_fee_status text,
  add column if not exists rider_fund_lock_status text,
  add column if not exists app_fee_payment_id text,
  add column if not exists rider_fund_lock_payment_id text;

update public.consegne
set payment_state = 'LEGACY'
where payment_state is null;

alter table public.consegne
  alter column payment_state set default 'PAYMENT_REQUIRED',
  alter column payment_state set not null,
  alter column commissione_app set default 0.50;

alter table public.satispay_payments
  add column if not exists consegna_id uuid references public.consegne(id) on delete cascade,
  add column if not exists payment_kind text,
  add column if not exists flow text,
  add column if not exists authorized_at timestamptz,
  add column if not exists captured_at timestamptz;

create index if not exists satispay_payments_consegna_idx
  on public.satispay_payments(consegna_id);

create index if not exists consegne_payment_state_idx
  on public.consegne(payment_state);

create or replace function public.accetta_consegna(p_consegna_id uuid)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_phone text;
  v_rider_name text;
  v_delivery public.consegne%rowtype;
begin
  if v_uid is null then
    return false;
  end if;

  select nullif(trim(p.satispay_phone), ''), coalesce(nullif(trim(p.nome), ''), 'Rider')
  into v_phone, v_rider_name
  from public.profiles p
  where p.id = v_uid
    and p.satispay_ready is true;

  if v_phone is null then
    raise exception using errcode='P0001', message='Prima di accettare configura il tuo numero Satispay nel Profilo.';
  end if;

  update public.consegne
  set rider_id=v_uid,
      stato='accettata',
      payment_state=case when payment_state='READY' then 'ASSIGNED' else payment_state end,
      updated_at=now()
  where id=p_consegna_id
    and stato='disponibile'
    and rider_id is null
    and cliente_id<>v_uid
    and compenso_rider>0
    and payment_state in ('LEGACY','READY')
    and (offerta_scade_il is null or offerta_scade_il>now())
    and (consegna_entro is null or consegna_entro>now())
  returning * into v_delivery;

  if not found then return false; end if;

  if v_delivery.payment_state='LEGACY' then
    insert into public.delivery_p2p_payments (
      consegna_id,cliente_id,rider_id,rider_display_name,rider_satispay_phone,
      amount_unit,currency,status,platform_fee_unit,platform_fee_status
    ) values (
      v_delivery.id,v_delivery.cliente_id,v_uid,v_rider_name,v_phone,
      round(v_delivery.compenso_rider*100)::integer,'EUR','AWAITING_PAYMENT',0,'DISABLED'
    ) on conflict (consegna_id) do nothing;
  end if;

  return true;
end;
$$;

revoke all on function public.accetta_consegna(uuid) from public, anon;
grant execute on function public.accetta_consegna(uuid) to authenticated;
