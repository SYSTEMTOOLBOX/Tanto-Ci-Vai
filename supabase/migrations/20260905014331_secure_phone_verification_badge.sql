create schema if not exists private;

create or replace function private.tcv_enforce_phone_verified()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  select exists(
    select 1
    from auth.users u
    where u.id = new.user_id
      and u.phone_confirmed_at is not null
      and nullif(trim(coalesce(u.phone, '')), '') is not null
  ) into new.phone_verified;
  return new;
end;
$$;

revoke all on function private.tcv_enforce_phone_verified() from public, anon, authenticated;

drop trigger if exists tcv_enforce_phone_verified on public.community_public_profiles;
create trigger tcv_enforce_phone_verified
before insert or update of phone_verified, user_id on public.community_public_profiles
for each row execute function private.tcv_enforce_phone_verified();

create or replace function private.tcv_sync_phone_verified_from_auth()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.community_public_profiles
     set phone_verified = (new.phone_confirmed_at is not null and nullif(trim(coalesce(new.phone, '')), '') is not null)
   where user_id = new.id;
  return new;
end;
$$;

revoke all on function private.tcv_sync_phone_verified_from_auth() from public, anon, authenticated;

drop trigger if exists tcv_sync_phone_verified_from_auth on auth.users;
create trigger tcv_sync_phone_verified_from_auth
after update of phone, phone_confirmed_at on auth.users
for each row execute function private.tcv_sync_phone_verified_from_auth();

update public.community_public_profiles p
   set phone_verified = exists(
     select 1 from auth.users u
      where u.id = p.user_id
        and u.phone_confirmed_at is not null
        and nullif(trim(coalesce(u.phone, '')), '') is not null
   );