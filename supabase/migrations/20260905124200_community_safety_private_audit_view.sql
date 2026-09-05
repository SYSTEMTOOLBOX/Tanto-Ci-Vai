create or replace view private.community_safety_audit as
select
  h.id as alert_id,
  h.user_id,
  d.first_name,
  d.last_name,
  d.document_type,
  h.kind,
  h.message,
  h.lat,
  h.lng,
  h.location_label,
  h.status,
  h.created_at,
  h.sent_at,
  h.cancelled_at,
  h.resolved_at,
  h.owner_closed_at,
  h.resolution_note,
  h.sent_count,
  h.failed_count
from public.help_alerts h
left join public.community_identity_documents d on d.user_id = h.user_id;

revoke all on table private.community_safety_audit from public, anon, authenticated;
grant select on table private.community_safety_audit to service_role;

comment on view private.community_safety_audit is 'Private administrative audit view linking Community safety alerts to the registered document name. Not exposed to app clients.';
