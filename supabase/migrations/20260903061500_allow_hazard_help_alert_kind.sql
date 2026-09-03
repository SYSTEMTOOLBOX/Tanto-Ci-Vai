alter table public.help_alerts drop constraint if exists help_alerts_kind_check;

alter table public.help_alerts
  add constraint help_alerts_kind_check
  check (kind = any (array['self'::text, 'other'::text, 'hazard'::text]));
