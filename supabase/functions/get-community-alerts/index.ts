import { createClient } from 'npm:@supabase/supabase-js@2.95.0';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { ...corsHeaders, 'Content-Type': 'application/json' },
});

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);

  try {
    const auth = req.headers.get('Authorization') || '';
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const anonKey = Deno.env.get('SUPABASE_ANON_KEY')!;
    const serviceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const userClient = createClient(supabaseUrl, anonKey, {
      global: { headers: { Authorization: auth } },
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: { user }, error: userErr } = await userClient.auth.getUser();
    if (userErr || !user) return json({ error: 'Unauthorized' }, 401);

    const admin = createClient(supabaseUrl, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });

    const now = Date.now();
    const sixHoursAgo = new Date(now - 6 * 60 * 60 * 1000).toISOString();
    const dayAgoMs = now - 24 * 60 * 60 * 1000;

    await admin.from('help_alerts').delete().lt('resolved_at', new Date(dayAgoMs).toISOString());

    const [{ data: helpRows, error: helpErr }, { data: hazardRows, error: hazardErr }] = await Promise.all([
      admin.from('help_alerts')
        .select('id,user_id,kind,message,lat,lng,location_label,created_at,sent_at,status,resolution_count,resolved_at')
        .eq('status', 'sent')
        .in('kind', ['self', 'other'])
        .order('created_at', { ascending: false })
        .limit(150),
      admin.from('help_alerts')
        .select('id,user_id,kind,message,lat,lng,location_label,created_at,sent_at,status,resolution_count,resolved_at')
        .eq('status', 'sent')
        .eq('kind', 'hazard')
        .not('lat', 'is', null)
        .not('lng', 'is', null)
        .gte('created_at', sixHoursAgo)
        .order('created_at', { ascending: false })
        .limit(100),
    ]);
    if (helpErr) throw helpErr;
    if (hazardErr) throw hazardErr;

    const helps = (helpRows || []).filter((r: any) => {
      if (!r.resolved_at) return true;
      const when = new Date(r.resolved_at).getTime();
      return Number.isFinite(when) && when >= dayAgoMs;
    });
    const active = [...helps, ...(hazardRows || [])].sort((a: any, b: any) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    const userIds = [...new Set(active.map((r: any) => r.user_id).filter(Boolean))];
    const names = new Map<string, string>();
    if (userIds.length) {
      const { data: profiles, error: profileErr } = await admin.from('profiles').select('id,nome').in('id', userIds);
      if (profileErr) throw profileErr;
      for (const p of profiles || []) names.set(p.id, String(p.nome || 'Un utente').trim() || 'Un utente');
    }

    const helpIds = helps.map((r: any) => r.id);
    const voted = new Set<string>();
    if (helpIds.length) {
      const { data: votes, error: voteErr } = await admin.from('help_alert_resolutions').select('help_alert_id').eq('user_id', user.id).in('help_alert_id', helpIds);
      if (voteErr) throw voteErr;
      for (const v of votes || []) voted.add(String(v.help_alert_id));
    }

    return json({ alerts: active.map((r: any) => ({
      id: r.id,
      kind: r.kind,
      message: String(r.message || '').slice(0, 180),
      lat: r.lat == null ? null : Number(r.lat),
      lng: r.lng == null ? null : Number(r.lng),
      location_label: String(r.location_label || '').slice(0, 220),
      created_at: r.created_at,
      sent_at: r.sent_at,
      sender_name: names.get(r.user_id) || 'Un utente',
      is_owner: r.user_id === user.id,
      resolution_count: Number(r.resolution_count || 0),
      resolved_at: r.resolved_at || null,
      viewer_voted: voted.has(String(r.id)),
    })) });
  } catch (e) {
    console.error('get-community-alerts fatal', String((e as any)?.message || e));
    return json({ error: String((e as any)?.message || e) }, 500);
  }
});
