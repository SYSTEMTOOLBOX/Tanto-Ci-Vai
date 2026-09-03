alter table public.help_alerts
  add column if not exists resolution_count integer not null default 0,
  add column if not exists resolved_at timestamptz;

create table if not exists public.help_alert_resolutions (
  help_alert_id uuid not null references public.help_alerts(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (help_alert_id, user_id)
);

alter table public.help_alert_resolutions enable row level security;
revoke all on table public.help_alert_resolutions from anon, authenticated;
grant select, insert, update, delete on table public.help_alert_resolutions to service_role;
grant select, update, delete on table public.help_alerts to service_role;

create index if not exists help_alerts_resolved_at_idx on public.help_alerts(resolved_at) where resolved_at is not null;
create index if not exists help_alert_resolutions_alert_idx on public.help_alert_resolutions(help_alert_id);

create or replace function public.tcv_sync_help_resolution_count()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  v_count integer;
begin
  select count(*)::integer into v_count
  from public.help_alert_resolutions
  where help_alert_id = new.help_alert_id;

  update public.help_alerts
  set resolution_count = v_count,
      resolved_at = case
        when v_count >= 3 then coalesce(resolved_at, now())
        else resolved_at
      end
  where id = new.help_alert_id
    and kind in ('self','other')
    and status = 'sent';

  return new;
end;
$$;

revoke all on function public.tcv_sync_help_resolution_count() from public;

drop trigger if exists tcv_help_resolution_after_insert on public.help_alert_resolutions;
create trigger tcv_help_resolution_after_insert
after insert on public.help_alert_resolutions
for each row execute function public.tcv_sync_help_resolution_count();

do $$
begin
  if not exists (select 1 from cron.job where jobname = 'tcv_cleanup_resolved_sos') then
    perform cron.schedule(
      'tcv_cleanup_resolved_sos',
      '*/15 * * * *',
      $cron$delete from public.help_alerts where resolved_at is not null and resolved_at < now() - interval '24 hours';$cron$
    );
  end if;
end $$;
