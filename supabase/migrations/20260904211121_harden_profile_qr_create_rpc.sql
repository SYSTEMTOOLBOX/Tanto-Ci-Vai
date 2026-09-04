revoke all on function public.tcv_create_profile_qr() from public;
revoke all on function public.tcv_create_profile_qr() from anon;
grant execute on function public.tcv_create_profile_qr() to authenticated;
