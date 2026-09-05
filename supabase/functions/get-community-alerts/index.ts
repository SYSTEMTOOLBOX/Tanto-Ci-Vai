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

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;
const HAZARD_MAX_LOOKBACK_MS = 30 * DAY_MS;

function hazardMaxAgeMs(message: unknown) {
  const m = String(message || '').toLowerCase();
  if (m.includes('buca') || m.includes('dissesto')) return 30 * DAY_MS;
  if (m.includes('albero') || m.includes('ostacolo')) return 72 * HOUR_MS;
  if (m.includes('allagat') || m.includes('acqua sulla carreggiata')) return 24 * HOUR_MS;
  if (m.includes('incidente') || m.includes('veicolo fermo')) return 8 * HOUR_MS;
  if (m.includes('animale')) return 3 * HOUR_MS;
  return 24 * HOUR_MS;
}

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
    const hazardLookbackIso = new Date(now - HAZARD_MAX_LOOKBACK_MS).toISOString();
    const dayAgoMs = now - DAY_MS;
    const dayAgoIso = new Date(dayAgoMs).toISOString();

    await admin.from('help_alerts').delete().lt('resolved_at', dayAgoIso);

    const [{ data: helpRows, error: helpErr }, { data: hazardRowsRaw, error: hazardErr }] = await Promise.all([
      admin.from('help_alerts')
        .select('id,user_id,kind,message,lat,lng,location_label,created_at,sent_at,status,resolution_count,resolved_at,owner_closed_at,resolution_note')
        .eq('status', 'sent')
        .in('kind', ['self', 'other'])
        .order('created_at', { ascending: false })
        .limit(150),
      admin.from('help_alerts')
        .select('id,user_id,kind,message,lat,lng,location_label,created_at,sent_at,status,resolution_count,resolved_at,owner_closed_at,resolution_note')
        .eq('status', 'sent')
        .eq('kind', 'hazard')
        .not('lat', 'is', null)
        .not('lng', 'is', null)
        .gte('created_at', hazardLookbackIso)
        .order('created_at', { ascending: false })
        .limit(300),
    ]);
    if (helpErr) throw helpErr;
    if (hazardErr) throw hazardErr;

    const allHelps = helpRows || [];
    const publicHelps = allHelps.filter((r: any) => {
      if (r.owner_closed_at) return false;
      if (!r.resolved_at) return true;
      const when = new Date(r.resolved_at).getTime();
      return Number.isFinite(when) && when >= dayAgoMs;
    });
    const myRows = allHelps.filter((r: any) => r.user_id === user.id).filter((r: any) => {
      if (!r.resolved_at) return true;
      const when = new Date(r.resolved_at).getTime();
      return Number.isFinite(when) && when >= dayAgoMs;
    });

    const hazardRows = (hazardRowsRaw || []).filter((r: any) => {
      if (r.owner_closed_at || r.resolved_at) return false;
      const created = new Date(r.created_at).getTime();
      if (!Number.isFinite(created)) return false;
      return now - created <= hazardMaxAgeMs(r.message);
    });

    const active = [...publicHelps, ...hazardRows].sort((a: any, b: any) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    const userIds = [...new Set([...active, ...myRows].map((r: any) => r.user_id).filter(Boolean))];
    const names = new Map<string, string>();
    if (userIds.length) {
      const { data: profiles, error: profileErr } = await admin.from('profiles').select('id,nome').in('id', userIds);
      if (profileErr) throw profileErr;
      for (const p of profiles || []) names.set(p.id, String(p.nome || 'Un utente').trim() || 'Un utente');
    }

    const publicHelpIds = publicHelps.map((r: any) => r.id);
    const voted = new Set<string>();
    if (publicHelpIds.length) {
      const { data: votes, error: voteErr } = await admin.from('help_alert_resolutions').select('help_alert_id').eq('user_id', user.id).in('help_alert_id', publicHelpIds);
      if (voteErr) throw voteErr;
      for (const v of votes || []) voted.add(String(v.help_alert_id));
    }

    const mapAlert = (r: any) => ({
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
      owner_closed_at: r.owner_closed_at || null,
      resolution_note: String(r.resolution_note || '').slice(0, 400),
      viewer_voted: voted.has(String(r.id)),
    });

    return json({
      alerts: active.map(mapAlert),
      my_sos: myRows.map(mapAlert),
    });
  } catch (e) {
    console.error('get-community-alerts fatal', String((e as any)?.message || e));
    return json({ error: String((e as any)?.message || e) }, 500);
  }
});
