alter table public.ride_requests
  add column if not exists platform_fee numeric(5,2) not null default 0.50 check (platform_fee >= 0);
