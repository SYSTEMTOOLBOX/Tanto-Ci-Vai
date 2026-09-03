alter table public.help_alerts
  add column if not exists owner_closed_at timestamptz,
  add column if not exists resolution_note text;

create index if not exists help_alerts_owner_closed_idx
  on public.help_alerts (user_id, owner_closed_at desc)
  where owner_closed_at is not null;

comment on column public.help_alerts.owner_closed_at is 'Timestamp when the SOS creator explicitly closed the alert; it must disappear immediately from public active alerts.';
comment on column public.help_alerts.resolution_note is 'Optional closing note written by the SOS creator, e.g. what happened or a thank-you message.';
