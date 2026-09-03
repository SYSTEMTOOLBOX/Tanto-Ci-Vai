alter table public.help_alerts
  add column if not exists kind text not null default 'self',
  add column if not exists automatic boolean not null default false,
  add column if not exists status text not null default 'sent',
  add column if not exists send_at timestamptz,
  add column if not exists sent_at timestamptz,
  add column if not exists cancelled_at timestamptz,
  add column if not exists sent_count integer not null default 0,
  add column if not exists failed_count integer not null default 0;

do $$ begin
  alter table public.help_alerts add constraint help_alerts_kind_check check (kind in ('self','other'));
exception when duplicate_object then null; end $$;

do $$ begin
  alter table public.help_alerts add constraint help_alerts_status_check check (status in ('pending','sending','sent','cancelled'));
exception when duplicate_object then null; end $$;

create index if not exists help_alerts_pending_idx
  on public.help_alerts(status, send_at)
  where status='pending';
