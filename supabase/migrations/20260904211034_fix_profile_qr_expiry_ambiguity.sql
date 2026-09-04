create or replace function public.tcv_create_profile_qr()
returns table(token text, expires_at timestamptz)
language plpgsql
security definer
set search_path to 'public','auth','pg_temp'
as $function$
declare
  v_uid uuid := auth.uid();
  v_token uuid;
  v_expires timestamptz;
begin
  if v_uid is null then
    raise exception 'Sessione non valida';
  end if;

  if not exists (
    select 1
    from public.community_public_profiles p
    where p.user_id = v_uid
      and p.community_enabled = true
      and nullif(trim(p.display_name), '') is not null
      and nullif(trim(coalesce(p.avatar_url,'')), '') is not null
  ) then
    raise exception 'Completa e attiva prima il Profilo Community con una foto reale';
  end if;

  delete from public.community_profile_qr_tokens q
   where q.user_id = v_uid
     and (q.used_at is not null or q.expires_at <= now());

  insert into public.community_profile_qr_tokens(user_id)
  values (v_uid)
  returning community_profile_qr_tokens.token,
            community_profile_qr_tokens.expires_at
       into v_token, v_expires;

  return query select v_token::text, v_expires;
end;
$function$;

revoke all on function public.tcv_create_profile_qr() from anon;
grant execute on function public.tcv_create_profile_qr() to authenticated;
