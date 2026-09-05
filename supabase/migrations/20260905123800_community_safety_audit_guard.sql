create or replace function public.tcv_require_registered_community_help_sender()
returns trigger
language plpgsql
set search_path to 'public'
as $function$
declare
  p public.community_public_profiles%rowtype;
  v_suspended_until timestamptz;
begin
  select * into p
  from public.community_public_profiles
  where user_id = new.user_id;

  if not found
     or not coalesce(p.community_enabled,false)
     or coalesce(btrim(p.display_name),'') = ''
     or coalesce(btrim(p.avatar_url),'') = ''
     or not coalesce(p.document_registered,false)
     or p.document_kind is null then
    raise exception 'Completa il Profilo Community con foto e documento prima di usare SOS e segnalazioni';
  end if;

  if p.community_role = 'driver_passenger' and p.document_kind <> 'driving_license' then
    raise exception 'Per il profilo guidatore serve una patente registrata';
  end if;

  select r.suspended_until into v_suspended_until
  from public.community_safety_restrictions r
  where r.user_id = new.user_id
    and r.suspended_until > now();

  if v_suspended_until is not null then
    raise exception 'Funzione sicurezza temporaneamente sospesa per questo account fino al %', v_suspended_until;
  end if;

  return new;
end;
$function$;

create or replace function public.tcv_preserve_recent_help_alert_history()
returns trigger
language plpgsql
set search_path to 'public'
as $function$
begin
  if old.resolved_at is not null
     and old.resolved_at >= now() - interval '90 days'
     and current_user <> 'postgres' then
    return null;
  end if;
  return old;
end;
$function$;

drop trigger if exists tcv_preserve_recent_help_alert_history on public.help_alerts;
create trigger tcv_preserve_recent_help_alert_history
before delete on public.help_alerts
for each row execute function public.tcv_preserve_recent_help_alert_history();
