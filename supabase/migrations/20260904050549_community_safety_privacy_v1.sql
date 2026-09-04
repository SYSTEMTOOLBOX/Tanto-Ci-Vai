create table if not exists public.community_public_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default 'Utente',
  avatar_url text,
  community_enabled boolean not null default false,
  identity_verified boolean not null default false,
  phone_verified boolean not null default false,
  completed_rides integer not null default 0 check (completed_rides >= 0),
  rating_avg numeric(3,2) not null default 0 check (rating_avg >= 0 and rating_avg <= 5),
  rating_count integer not null default 0 check (rating_count >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.community_public_profiles enable row level security;

drop policy if exists community_public_profiles_select on public.community_public_profiles;
create policy community_public_profiles_select on public.community_public_profiles
for select to authenticated using (community_enabled = true or user_id = auth.uid());

drop policy if exists community_public_profiles_insert on public.community_public_profiles;
create policy community_public_profiles_insert on public.community_public_profiles
for insert to authenticated with check (user_id = auth.uid());

drop policy if exists community_public_profiles_update on public.community_public_profiles;
create policy community_public_profiles_update on public.community_public_profiles
for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

grant select, insert, update on public.community_public_profiles to authenticated;

create or replace function public.tcv_protect_community_profile_system_fields()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  new.display_name := left(coalesce(nullif(trim(new.display_name),''),'Utente'),60);
  new.updated_at := now();
  if auth.role() = 'authenticated' then
    if tg_op = 'INSERT' then
      new.identity_verified := false;
      new.phone_verified := false;
      new.completed_rides := 0;
      new.rating_avg := 0;
      new.rating_count := 0;
    else
      new.identity_verified := old.identity_verified;
      new.phone_verified := old.phone_verified;
      new.completed_rides := old.completed_rides;
      new.rating_avg := old.rating_avg;
      new.rating_count := old.rating_count;
      new.created_at := old.created_at;
      new.user_id := old.user_id;
    end if;
  end if;
  return new;
end;
$$;

drop trigger if exists tcv_protect_community_profile_system_fields on public.community_public_profiles;
create trigger tcv_protect_community_profile_system_fields before insert or update on public.community_public_profiles for each row execute function public.tcv_protect_community_profile_system_fields();

create table if not exists public.community_user_blocks (
  blocker_id uuid not null references auth.users(id) on delete cascade,
  blocked_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (blocker_id, blocked_id),
  check (blocker_id <> blocked_id)
);
alter table public.community_user_blocks enable row level security;
drop policy if exists community_user_blocks_select on public.community_user_blocks;
create policy community_user_blocks_select on public.community_user_blocks for select to authenticated using (blocker_id = auth.uid());
drop policy if exists community_user_blocks_insert on public.community_user_blocks;
create policy community_user_blocks_insert on public.community_user_blocks for insert to authenticated with check (blocker_id = auth.uid());
drop policy if exists community_user_blocks_delete on public.community_user_blocks;
create policy community_user_blocks_delete on public.community_user_blocks for delete to authenticated using (blocker_id = auth.uid());
grant select, insert, delete on public.community_user_blocks to authenticated;

create table if not exists public.community_safety_reports (
  id uuid primary key default gen_random_uuid(),
  reporter_id uuid not null references auth.users(id) on delete cascade,
  reported_user_id uuid not null references auth.users(id) on delete cascade,
  ride_request_id uuid references public.ride_requests(id) on delete set null,
  category text not null check (category in ('behavior','harassment','unsafe_driving','fraud','identity','other')),
  details text not null default '',
  status text not null default 'open' check (status in ('open','reviewing','resolved','dismissed')),
  created_at timestamptz not null default now(),
  check (reporter_id <> reported_user_id)
);
alter table public.community_safety_reports enable row level security;
drop policy if exists community_safety_reports_select on public.community_safety_reports;
create policy community_safety_reports_select on public.community_safety_reports for select to authenticated using (reporter_id = auth.uid());
drop policy if exists community_safety_reports_insert on public.community_safety_reports;
create policy community_safety_reports_insert on public.community_safety_reports for insert to authenticated with check (reporter_id = auth.uid());
grant select, insert on public.community_safety_reports to authenticated;

alter table public.ride_requests add column if not exists requester_display_name text not null default '';
alter table public.ride_requests add column if not exists requester_avatar_url text;
alter table public.ride_requests add column if not exists requester_identity_verified boolean not null default false;
alter table public.ride_requests add column if not exists requester_phone_verified boolean not null default false;
alter table public.ride_requests add column if not exists requester_completed_rides integer not null default 0;
alter table public.ride_requests add column if not exists requester_rating_avg numeric(3,2) not null default 0;
alter table public.ride_requests add column if not exists driver_seen_profile_at timestamptz;
alter table public.ride_requests add column if not exists accepted_at timestamptz;
alter table public.ride_requests add column if not exists declined_at timestamptz;
alter table public.ride_requests add column if not exists pickup_confirmed_at timestamptz;
alter table public.ride_requests add column if not exists dropoff_confirmed_at timestamptz;

update public.ride_requests r set driver_id = t.user_id from public.community_trips t where r.community_trip_id = t.id and r.driver_id is null;

insert into public.community_public_profiles(user_id, display_name)
select p.id, coalesce(nullif(split_part(trim(coalesce(p.nome,'')),' ',1),''),'Utente') from public.profiles p
on conflict (user_id) do nothing;

update public.community_trips set driver_name = coalesce(nullif(split_part(trim(driver_name),' ',1),''),'Utente') where driver_name is not null;

create or replace function public.tcv_prepare_ride_request_privacy()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  p public.community_public_profiles%rowtype;
  trip_owner uuid;
begin
  if new.community_trip_id is not null then
    select user_id into trip_owner from public.community_trips where id = new.community_trip_id and active = true;
    if trip_owner is null then raise exception 'Percorso Community non disponibile'; end if;
    if trip_owner = new.user_id then raise exception 'Non puoi richiedere un posto sul tuo stesso percorso'; end if;
    new.driver_id := trip_owner;
  end if;

  select * into p from public.community_public_profiles where user_id = new.user_id and community_enabled = true;
  if not found or coalesce(trim(p.display_name),'') = '' or coalesce(trim(p.avatar_url),'') = '' then
    raise exception 'Completa e attiva il Profilo Sicurezza Community prima di richiedere un passaggio';
  end if;

  if new.driver_id is not null and exists (
    select 1 from public.community_user_blocks b
    where (b.blocker_id = new.user_id and b.blocked_id = new.driver_id)
       or (b.blocker_id = new.driver_id and b.blocked_id = new.user_id)
  ) then raise exception 'Richiesta non disponibile per motivi di sicurezza'; end if;

  new.requester_display_name := p.display_name;
  new.requester_avatar_url := p.avatar_url;
  new.requester_identity_verified := p.identity_verified;
  new.requester_phone_verified := p.phone_verified;
  new.requester_completed_rides := p.completed_rides;
  new.requester_rating_avg := p.rating_avg;
  return new;
end;
$$;

drop trigger if exists tcv_prepare_ride_request_privacy on public.ride_requests;
create trigger tcv_prepare_ride_request_privacy before insert on public.ride_requests for each row execute function public.tcv_prepare_ride_request_privacy();

create or replace function public.tcv_guard_ride_request_updates()
returns trigger language plpgsql security definer set search_path = public as $$
declare actor uuid := auth.uid();
begin
  if auth.role() <> 'authenticated' then return new; end if;
  new.user_id := old.user_id; new.driver_id := old.driver_id; new.community_trip_id := old.community_trip_id;
  new.from_label := old.from_label; new.from_lat := old.from_lat; new.from_lng := old.from_lng;
  new.to_label := old.to_label; new.to_lat := old.to_lat; new.to_lng := old.to_lng;
  new.departure_at := old.departure_at; new.flex_minutes := old.flex_minutes; new.passengers := old.passengers;
  new.note := old.note; new.distance_km := old.distance_km; new.contribution_per_person := old.contribution_per_person; new.platform_fee := old.platform_fee;
  new.requester_display_name := old.requester_display_name; new.requester_avatar_url := old.requester_avatar_url;
  new.requester_identity_verified := old.requester_identity_verified; new.requester_phone_verified := old.requester_phone_verified;
  new.requester_completed_rides := old.requester_completed_rides; new.requester_rating_avg := old.requester_rating_avg;

  if actor = old.driver_id then
    if new.status is distinct from old.status then
      if old.status = 'open' and new.status = 'matched' then new.accepted_at := coalesce(new.accepted_at, now());
      elsif old.status = 'open' and new.status = 'declined' then new.declined_at := coalesce(new.declined_at, now());
      elsif old.status = 'matched' and new.status = 'onboard' then new.pickup_confirmed_at := coalesce(new.pickup_confirmed_at, now());
      elsif old.status = 'onboard' and new.status = 'completed' then new.dropoff_confirmed_at := coalesce(new.dropoff_confirmed_at, now());
      else raise exception 'Transizione stato non consentita'; end if;
    end if;
  elsif actor = old.user_id then
    if new.status is distinct from old.status and new.status <> 'cancelled' then raise exception 'Il passeggero può solo annullare la richiesta'; end if;
  else raise exception 'Operazione non autorizzata'; end if;
  return new;
end;
$$;

drop trigger if exists tcv_guard_ride_request_updates on public.ride_requests;
create trigger tcv_guard_ride_request_updates before update on public.ride_requests for each row execute function public.tcv_guard_ride_request_updates();

create or replace function public.tcv_count_completed_community_ride()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if old.status is distinct from 'completed' and new.status = 'completed' then
    update public.community_public_profiles set completed_rides = completed_rides + 1, updated_at = now() where user_id in (new.user_id, new.driver_id);
  end if;
  return new;
end;
$$;

drop trigger if exists tcv_count_completed_community_ride on public.ride_requests;
create trigger tcv_count_completed_community_ride after update on public.ride_requests for each row execute function public.tcv_count_completed_community_ride();

drop policy if exists ride_requests_select on public.ride_requests;
create policy ride_requests_select on public.ride_requests for select to authenticated using (user_id = auth.uid() or driver_id = auth.uid());
drop policy if exists ride_requests_update on public.ride_requests;
create policy ride_requests_update on public.ride_requests for update to authenticated using (user_id = auth.uid() or driver_id = auth.uid()) with check (user_id = auth.uid() or driver_id = auth.uid());
grant select, insert, update, delete on public.ride_requests to authenticated;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('community-avatars','community-avatars',true,5242880,array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = excluded.public, file_size_limit = excluded.file_size_limit, allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists tcv_community_avatar_insert on storage.objects;
create policy tcv_community_avatar_insert on storage.objects for insert to authenticated with check (bucket_id = 'community-avatars' and (storage.foldername(name))[1] = auth.uid()::text);
drop policy if exists tcv_community_avatar_update on storage.objects;
create policy tcv_community_avatar_update on storage.objects for update to authenticated using (bucket_id = 'community-avatars' and (storage.foldername(name))[1] = auth.uid()::text) with check (bucket_id = 'community-avatars' and (storage.foldername(name))[1] = auth.uid()::text);
drop policy if exists tcv_community_avatar_delete on storage.objects;
create policy tcv_community_avatar_delete on storage.objects for delete to authenticated using (bucket_id = 'community-avatars' and (storage.foldername(name))[1] = auth.uid()::text);
