alter table public.community_public_profiles
  add column if not exists driver_license_since date;

create or replace function public.tcv_sync_profile_document_badge()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_kind text;
  v_since date;
begin
  select d.document_type,
         case when d.document_type = 'driving_license' then d.license_b_since else null end
    into v_kind, v_since
  from public.community_identity_documents d
  where d.user_id = new.user_id
    and d.front_path is not null
    and d.back_path is not null
  limit 1;

  new.document_registered := (v_kind is not null);
  new.document_kind := v_kind;
  new.driver_license_since := v_since;
  return new;
end;
$$;

create or replace function public.tcv_refresh_document_badge_from_document()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_uid uuid;
  v_kind text;
  v_since date;
begin
  v_uid := coalesce(new.user_id, old.user_id);

  select d.document_type,
         case when d.document_type = 'driving_license' then d.license_b_since else null end
    into v_kind, v_since
  from public.community_identity_documents d
  where d.user_id = v_uid
    and d.front_path is not null
    and d.back_path is not null
  limit 1;

  update public.community_public_profiles
  set document_registered = (v_kind is not null),
      document_kind = v_kind,
      driver_license_since = v_since,
      updated_at = now()
  where user_id = v_uid;

  return coalesce(new, old);
end;
$$;

drop trigger if exists tcv_profile_document_badge_guard on public.community_public_profiles;
create trigger tcv_profile_document_badge_guard
before insert or update of document_registered, document_kind, driver_license_since, user_id
on public.community_public_profiles
for each row execute function public.tcv_sync_profile_document_badge();

update public.community_public_profiles p
set document_registered = true,
    document_kind = d.document_type,
    driver_license_since = case when d.document_type = 'driving_license' then d.license_b_since else null end,
    updated_at = now()
from public.community_identity_documents d
where d.user_id = p.user_id
  and d.front_path is not null
  and d.back_path is not null;

update public.community_public_profiles p
set document_registered = false,
    document_kind = null,
    driver_license_since = null,
    updated_at = now()
where not exists (
  select 1 from public.community_identity_documents d
  where d.user_id = p.user_id
    and d.front_path is not null
    and d.back_path is not null
);

create or replace function public.tcv_require_registered_community_driver_trip()
returns trigger
language plpgsql
set search_path = public
as $$
declare
  p public.community_public_profiles%rowtype;
  d public.community_identity_documents%rowtype;
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

  select * into d
  from public.community_identity_documents
  where user_id = new.user_id
    and document_type = 'driving_license'
    and front_path is not null
    and back_path is not null
  limit 1;

  if not found or d.license_b_since is null or d.license_expires_on is null then
    raise exception 'Patente incompleta: registra data di conseguimento e scadenza';
  end if;
  if d.license_b_since > current_date then
    raise exception 'La data di conseguimento della patente non è valida';
  end if;
  if d.license_expires_on < current_date then
    raise exception 'Patente scaduta: aggiorna il documento prima di offrire passaggi';
  end if;

  return new;
end;
$$;