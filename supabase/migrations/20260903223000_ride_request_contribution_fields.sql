alter table public.ride_requests
  add column if not exists distance_km numeric(8,2),
  add column if not exists contribution_per_person numeric(8,2),
  add column if not exists community_trip_id uuid references public.community_trips(id) on delete set null;

create index if not exists ride_requests_community_trip_idx on public.ride_requests(community_trip_id, status, departure_at);
