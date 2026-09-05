alter table public.community_public_profiles
  drop constraint if exists community_public_profiles_community_role_check;

alter table public.community_public_profiles
  add constraint community_public_profiles_community_role_check
  check (community_role in ('community_only','passenger','driver_passenger'));

alter table public.community_public_profiles
  alter column community_role set default 'community_only';

create or replace function public.tcv_require_registered_community_help_sender()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
declare
  p public.community_public_profiles%rowtype;
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

  return new;
end;
$$;

drop trigger if exists tcv_require_registered_community_help_sender on public.help_alerts;
create trigger tcv_require_registered_community_help_sender
before insert on public.help_alerts
for each row execute function public.tcv_require_registered_community_help_sender();

create or replace function public.tcv_require_registered_community_ride_request()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
declare
  p public.community_public_profiles%rowtype;
begin
  select * into p from public.community_public_profiles where user_id = new.user_id;
  if not found
     or not coalesce(p.community_enabled,false)
     or not coalesce(p.document_registered,false)
     or coalesce(btrim(p.avatar_url),'') = ''
     or p.community_role not in ('passenger','driver_passenger') then
    raise exception 'Per chiedere un passaggio completa il profilo con foto, documento e ruolo passeggero';
  end if;
  return new;
end;
$$;

drop trigger if exists tcv_require_registered_community_ride_request on public.ride_requests;
create trigger tcv_require_registered_community_ride_request
before insert on public.ride_requests
for each row execute function public.tcv_require_registered_community_ride_request();

create or replace function public.tcv_require_registered_community_driver_trip()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
declare
  p public.community_public_profiles%rowtype;
begin
  select * into p from public.community_public_profiles where user_id = new.user_id;
  if not found
     or not coalesce(p.community_enabled,false)
     or not coalesce(p.document_registered,false)
     or p.document_kind <> 'driving_license'
     or p.community_role <> 'driver_passenger'
     or coalesce(btrim(p.avatar_url),'') = '' then
    raise exception 'Per offrire passaggi serve un profilo guidatore completo con foto e patente registrata';
  end if;
  return new;
end;
$$;

drop trigger if exists tcv_require_registered_community_driver_trip on public.community_trips;
create trigger tcv_require_registered_community_driver_trip
before insert or update on public.community_trips
for each row execute function public.tcv_require_registered_community_driver_trip();