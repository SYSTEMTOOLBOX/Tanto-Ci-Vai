import { createClient } from 'npm:@supabase/supabase-js@2.95.0';
import webpush from 'npm:web-push@3.6.7';

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

    const body = await req.json().catch(() => ({}));
    const message = String(body?.message || '').trim().slice(0, 180);
    const lat = Number(body?.lat);
    const lng = Number(body?.lng);
    const locationLabel = String(body?.location_label || '').trim().slice(0, 220);
    const safeLat = Number.isFinite(lat) && lat >= -90 && lat <= 90 ? lat : null;
    const safeLng = Number.isFinite(lng) && lng >= -180 && lng <= 180 ? lng : null;

    const admin = createClient(supabaseUrl, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });

    const since = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    const { data: recent, error: recentErr } = await admin
      .from('help_alerts')
      .select('id,created_at')
      .eq('user_id', user.id)
      .gte('created_at', since)
      .order('created_at', { ascending: false })
      .limit(1);
    if (recentErr) throw recentErr;
    if (recent?.length) return json({ error: 'Hai già inviato una richiesta di aiuto negli ultimi 5 minuti.' }, 429);

    const { data: profile } = await admin.from('profiles').select('nome').eq('id', user.id).maybeSingle();
    const senderName = String(profile?.nome || 'Un utente').trim().slice(0, 60) || 'Un utente';

    const { data: alert, error: insertErr } = await admin
      .from('help_alerts')
      .insert({ user_id: user.id, message, lat: safeLat, lng: safeLng, location_label: locationLabel || null })
      .select('id')
      .single();
    if (insertErr) throw insertErr;

    const { data: vapidRows, error: vapidErr } = await admin.rpc('get_push_vapid_config_for_service');
    if (vapidErr || !vapidRows?.length) throw vapidErr || new Error('Push config unavailable');
    const cfg = vapidRows[0];
    webpush.setVapidDetails(cfg.subject, cfg.public_key, cfg.private_key);

    const { data: subs, error: subErr } = await admin
      .from('push_subscriptions')
      .select('id,user_id,endpoint,p256dh,auth_key')
      .eq('enabled', true)
      .neq('user_id', user.id);
    if (subErr) throw subErr;

    const where = locationLabel ? ` · 📍 ${locationLabel}` : (safeLat != null && safeLng != null ? ` · 📍 ${safeLat.toFixed(5)}, ${safeLng.toFixed(5)}` : '');
    const what = message || 'ha bisogno urgente di una mano';
    const payload = JSON.stringify({
      title: '🆘 AIUTO NELLA COMUNITÀ',
      body: `${senderName}: ${what}${where}. Se c’è pericolo immediato chiama il 112.`,
      event: 'help_alert',
      help_id: alert.id,
      url: './',
      tag: `tcv-help-${alert.id}`,
    });

    let sent = 0;
    let failed = 0;
    for (const s of subs || []) {
      try {
        await webpush.sendNotification(
          { endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth_key } },
          payload,
          { TTL: 900, urgency: 'high' },
        );
        sent++;
      } catch (e) {
        failed++;
        const status = Number(e?.statusCode || e?.status || 0);
        if (status === 404 || status === 410) await admin.from('push_subscriptions').delete().eq('id', s.id);
        else console.error('help push failed', { subscriptionId: s.id, status, message: String(e?.message || e) });
      }
    }

    console.log('send-help-push complete', { alertId: alert.id, sender: user.id, sent, failed });
    return json({ alert_id: alert.id, sent, failed, location_included: !!where });
  } catch (e) {
    console.error('send-help-push fatal', String(e?.message || e));
    return json({ error: String(e?.message || e) }, 500);
  }
});
