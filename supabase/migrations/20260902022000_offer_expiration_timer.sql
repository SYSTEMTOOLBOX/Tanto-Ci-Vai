-- Automatic expiration for unanswered offers
alter table public.consegne
  add column if not exists offerta_scade_il timestamptz;

update public.consegne
set offerta_scade_il = coalesce(offerta_scade_il, created_at + interval '3 hours')
where offerta_scade_il is null;

alter table public.consegne
  alter column offerta_scade_il set default (now() + interval '3 hours');

-- Add a dedicated status so the requester can distinguish an expired offer
-- from one they cancelled manually.
alter table public.consegne
  drop constraint if exists consegne_stato_check;

alter table public.consegne
  add constraint consegne_stato_check
  check (
    stato in (
      'disponibile',
      'accettata',
      'ritirata',
      'in_consegna',
      'consegnata',
      'annullata',
      'scaduta'
    )
  );

create or replace function public.scadi_offerte()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare
  n integer;
begin
  update public.consegne
  set
    stato = 'scaduta',
    updated_at = now()
  where
    stato = 'disponibile'
    and rider_id is null
    and offerta_scade_il is not null
    and offerta_scade_il <= now();

  get diagnostics n = row_count;
  return n;
end;
$$;

revoke all on function public.scadi_offerte() from public;
grant execute on function public.scadi_offerte() to authenticated;

-- A runner cannot accept an offer after either its offer timer or
-- the requester delivery deadline has elapsed.
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
    and (offerta_scade_il is null or offerta_scade_il > now())
    and (consegna_entro is null or consegna_entro > now());

  get diagnostics n = row_count;
  return n = 1;
end;
$$;

revoke all on function public.accetta_consegna(uuid) from public;
grant execute on function public.accetta_consegna(uuid) to authenticated;

-- Supabase Cron / pg_cron: mark unanswered offers as expired every minute.
create extension if not exists pg_cron with schema extensions;

do $$
declare
  old_job bigint;
begin
  select jobid into old_job
  from cron.job
  where jobname = 'tanto-ci-vai-scadi-offerte'
  limit 1;

  if old_job is not null then
    perform cron.unschedule(old_job);
  end if;
end;
$$;

select cron.schedule(
  'tanto-ci-vai-scadi-offerte',
  '* * * * *',
  $cmd$select public.scadi_offerte();$cmd$
);
