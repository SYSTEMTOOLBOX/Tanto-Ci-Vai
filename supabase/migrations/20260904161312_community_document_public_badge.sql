alter table public.community_public_profiles
  add column if not exists document_registered boolean not null default false,
  add column if not exists document_kind text;

alter table public.community_public_profiles
  drop constraint if exists community_public_profiles_document_kind_check;
alter table public.community_public_profiles
  add constraint community_public_profiles_document_kind_check
  check (document_kind is null or document_kind in ('identity_card','driving_license'));

create or replace function public.tcv_sync_profile_document_badge()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_kind text;
begin
  select d.document_type into v_kind
  from public.community_identity_documents d
  where d.user_id = new.user_id
    and d.front_path is not null
    and d.back_path is not null
  limit 1;

  new.document_registered := (v_kind is not null);
  new.document_kind := v_kind;
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
begin
  v_uid := coalesce(new.user_id, old.user_id);
  select d.document_type into v_kind
  from public.community_identity_documents d
  where d.user_id = v_uid
    and d.front_path is not null
    and d.back_path is not null
  limit 1;

  update public.community_public_profiles
  set document_registered = (v_kind is not null),
      document_kind = v_kind,
      updated_at = now()
  where user_id = v_uid;

  return coalesce(new, old);
end;
$$;

drop trigger if exists tcv_profile_document_badge_guard on public.community_public_profiles;
create trigger tcv_profile_document_badge_guard
before insert or update of document_registered, document_kind, user_id on public.community_public_profiles
for each row execute function public.tcv_sync_profile_document_badge();

drop trigger if exists tcv_document_badge_sync on public.community_identity_documents;
create trigger tcv_document_badge_sync
after insert or update or delete on public.community_identity_documents
for each row execute function public.tcv_refresh_document_badge_from_document();

update public.community_public_profiles p
set document_registered = true,
    document_kind = d.document_type,
    updated_at = now()
from public.community_identity_documents d
where d.user_id = p.user_id
  and d.front_path is not null
  and d.back_path is not null;

update public.community_public_profiles p
set document_registered = false,
    document_kind = null,
    updated_at = now()
where not exists (
  select 1 from public.community_identity_documents d
  where d.user_id = p.user_id
    and d.front_path is not null
    and d.back_path is not null
);
