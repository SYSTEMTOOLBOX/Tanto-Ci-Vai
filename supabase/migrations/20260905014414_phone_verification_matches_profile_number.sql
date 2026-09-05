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
    join public.profiles p on p.id = u.id
    where u.id = new.user_id
      and u.phone_confirmed_at is not null
      and nullif(regexp_replace(coalesce(u.phone, ''), '[^0-9]', '', 'g'), '') is not null
      and regexp_replace(coalesce(u.phone, ''), '[^0-9]', '', 'g') = regexp_replace(coalesce(p.telefono, ''), '[^0-9]', '', 'g')
  ) into new.phone_verified;
  return new;
end;
$$;

create or replace function private.tcv_sync_phone_verified_from_auth()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.community_public_profiles cpp
     set phone_verified = exists(
       select 1
       from public.profiles p
       where p.id = new.id
         and new.phone_confirmed_at is not null
         and nullif(regexp_replace(coalesce(new.phone, ''), '[^0-9]', '', 'g'), '') is not null
         and regexp_replace(coalesce(new.phone, ''), '[^0-9]', '', 'g') = regexp_replace(coalesce(p.telefono, ''), '[^0-9]', '', 'g')
     )
   where cpp.user_id = new.id;
  return new;
end;
$$;

create or replace function private.tcv_sync_phone_verified_from_profile()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  update public.community_public_profiles cpp
     set phone_verified = exists(
       select 1
       from auth.users u
       where u.id = new.id
         and u.phone_confirmed_at is not null
         and nullif(regexp_replace(coalesce(u.phone, ''), '[^0-9]', '', 'g'), '') is not null
         and regexp_replace(coalesce(u.phone, ''), '[^0-9]', '', 'g') = regexp_replace(coalesce(new.telefono, ''), '[^0-9]', '', 'g')
     )
   where cpp.user_id = new.id;
  return new;
end;
$$;

revoke all on function private.tcv_sync_phone_verified_from_profile() from public, anon, authenticated;

drop trigger if exists tcv_sync_phone_verified_from_profile on public.profiles;
create trigger tcv_sync_phone_verified_from_profile
after update of telefono on public.profiles
for each row execute function private.tcv_sync_phone_verified_from_profile();

update public.community_public_profiles cpp
   set phone_verified = exists(
     select 1
     from auth.users u
     join public.profiles p on p.id = u.id
     where u.id = cpp.user_id
       and u.phone_confirmed_at is not null
       and nullif(regexp_replace(coalesce(u.phone, ''), '[^0-9]', '', 'g'), '') is not null
       and regexp_replace(coalesce(u.phone, ''), '[^0-9]', '', 'g') = regexp_replace(coalesce(p.telefono, ''), '[^0-9]', '', 'g')
   );