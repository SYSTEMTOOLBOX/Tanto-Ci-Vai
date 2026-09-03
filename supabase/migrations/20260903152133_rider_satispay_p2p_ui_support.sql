alter table public.profiles
  add column if not exists satispay_phone text,
  add column if not exists satispay_ready boolean not null default false;

grant update (satispay_phone, satispay_ready)
on public.profiles
to authenticated;

alter table public.consegne
  alter column commissione_app set default 0;

update public.consegne
set commissione_app = 0
where commissione_app is distinct from 0
  and stato in ('disponibile','accettata','ritirata','in_consegna');

create table if not exists public.delivery_p2p_payments (
  consegna_id uuid primary key references public.consegne(id) on delete cascade,
  cliente_id uuid not null references public.profiles(id) on delete cascade,
  rider_id uuid not null references public.profiles(id) on delete cascade,
  rider_display_name text not null,
  rider_satispay_phone text not null,
  amount_unit integer not null check (amount_unit > 0),
  currency text not null default 'EUR',
  status text not null default 'AWAITING_PAYMENT'
    check (status in ('AWAITING_PAYMENT','SENDER_CONFIRMED','RECEIVED','CANCELED')),
  sender_confirmed_at timestamptz,
  receiver_confirmed_at timestamptz,
  platform_fee_unit integer not null default 0,
  platform_fee_status text not null default 'DISABLED',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.delivery_p2p_payments enable row level security;

drop policy if exists delivery_p2p_select_participants on public.delivery_p2p_payments;
create policy delivery_p2p_select_participants
on public.delivery_p2p_payments
for select
to authenticated
using (auth.uid() = cliente_id or auth.uid() = rider_id);

revoke all on public.delivery_p2p_payments from anon, authenticated;
grant select on public.delivery_p2p_payments to authenticated;

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
    raise exception using
      errcode = 'P0001',
      message = 'Prima di accettare configura il tuo numero Satispay nel Profilo.';
  end if;

  update public.consegne
  set
    rider_id = v_uid,
    stato = 'accettata',
    commissione_app = 0,
    updated_at = now()
  where
    id = p_consegna_id
    and stato = 'disponibile'
    and rider_id is null
    and cliente_id <> v_uid
    and compenso_rider > 0
    and (offerta_scade_il is null or offerta_scade_il > now())
    and (consegna_entro is null or consegna_entro > now())
  returning * into v_delivery;

  if not found then
    return false;
  end if;

  insert into public.delivery_p2p_payments (
    consegna_id, cliente_id, rider_id, rider_display_name,
    rider_satispay_phone, amount_unit, currency, status,
    platform_fee_unit, platform_fee_status
  ) values (
    v_delivery.id, v_delivery.cliente_id, v_uid, v_rider_name,
    v_phone, round(v_delivery.compenso_rider * 100)::integer,
    'EUR', 'AWAITING_PAYMENT', 0, 'DISABLED'
  )
  on conflict (consegna_id) do nothing;

  return true;
end;
$$;

revoke all on function public.accetta_consegna(uuid) from public, anon;
grant execute on function public.accetta_consegna(uuid) to authenticated;

create schema if not exists private;

create or replace function private.tcv_cancel_delivery_p2p_payment()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.stato in ('annullata', 'scaduta')
     and old.stato is distinct from new.stato then
    update public.delivery_p2p_payments
    set status = 'CANCELED', updated_at = now()
    where consegna_id = new.id
      and status <> 'RECEIVED';
  end if;
  return new;
end;
$$;

drop trigger if exists tcv_cancel_p2p_on_delivery on public.consegne;
create trigger tcv_cancel_p2p_on_delivery
after update of stato on public.consegne
for each row execute function private.tcv_cancel_delivery_p2p_payment();

create or replace function public.tcv_confirm_delivery_p2p_payment(
  p_consegna_id uuid,
  p_action text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_uid uuid := auth.uid();
  v_payment public.delivery_p2p_payments%rowtype;
  v_delivery_status text;
  v_action text := upper(trim(coalesce(p_action, '')));
begin
  if v_uid is null then
    raise exception using errcode = '42501', message = 'Accesso richiesto.';
  end if;

  select * into v_payment
  from public.delivery_p2p_payments p
  where p.consegna_id = p_consegna_id
  for update;

  if not found then
    raise exception using errcode = 'P0002', message = 'Pagamento diretto non trovato.';
  end if;

  if v_uid <> v_payment.cliente_id and v_uid <> v_payment.rider_id then
    raise exception using errcode = '42501', message = 'Non puoi accedere a questo pagamento.';
  end if;

  if v_payment.status = 'CANCELED' then
    raise exception using errcode = 'P0001', message = 'La missione è stata annullata.';
  end if;

  select c.stato into v_delivery_status
  from public.consegne c
  where c.id = p_consegna_id;

  if v_delivery_status is distinct from 'consegnata' then
    raise exception using errcode = 'P0001',
      message = 'Il pagamento si conferma dopo che il rider ha segnato la consegna come completata.';
  end if;

  if v_action = 'SENDER_PAID' then
    if v_uid <> v_payment.cliente_id then
      raise exception using errcode = '42501', message = 'Solo il cliente può confermare l''invio.';
    end if;
    if v_payment.status = 'AWAITING_PAYMENT' then
      update public.delivery_p2p_payments
      set status='SENDER_CONFIRMED', sender_confirmed_at=now(), updated_at=now()
      where consegna_id=p_consegna_id;
    end if;
  elsif v_action = 'RIDER_RECEIVED' then
    if v_uid <> v_payment.rider_id then
      raise exception using errcode = '42501', message = 'Solo il rider può confermare la ricezione.';
    end if;
    if v_payment.sender_confirmed_at is null then
      raise exception using errcode = 'P0001', message = 'Il cliente non ha ancora confermato l''invio del pagamento.';
    end if;
    if v_payment.status = 'SENDER_CONFIRMED' then
      update public.delivery_p2p_payments
      set status='RECEIVED', receiver_confirmed_at=now(), updated_at=now()
      where consegna_id=p_consegna_id;
    end if;
  else
    raise exception using errcode = '22023', message = 'Azione di pagamento non valida.';
  end if;

  select * into v_payment
  from public.delivery_p2p_payments p
  where p.consegna_id = p_consegna_id;

  return jsonb_build_object(
    'consegna_id', v_payment.consegna_id,
    'status', v_payment.status,
    'sender_confirmed_at', v_payment.sender_confirmed_at,
    'receiver_confirmed_at', v_payment.receiver_confirmed_at
  );
end;
$$;

revoke all on function public.tcv_confirm_delivery_p2p_payment(uuid,text) from public, anon;
grant execute on function public.tcv_confirm_delivery_p2p_payment(uuid,text) to authenticated;
