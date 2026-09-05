revoke all on table public.community_satispay_accounts from anon, authenticated;
grant select, insert, update, delete on table public.community_satispay_accounts to service_role;
