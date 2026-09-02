alter table public.profiles
  add column if not exists home_city text,
  add column if not exists home_street text,
  add column if not exists home_civic text,
  add column if not exists home_lat double precision,
  add column if not exists home_lng double precision,
  add column if not exists home_label text;
