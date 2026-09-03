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

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function cleanPoint(body: any) {
  const lat = Number(body?.lat);
  const lng = Number(body?.lng);
  return {
    lat: Number.isFinite(lat) && lat >= -90 && lat <= 90 ? lat : null,
    lng: Number.isFinite(lng) && lng >= -180 && lng <= 180 ? lng : null,
    locationLabel: String(body?.location_label || '').trim().slice(0, 220),
  };
}

async function dispatchAlert(admin: any, alertId: string, userId: string, senderName: string) {
  const { data: claimed, error: claimErr } = await admin
    .from('help_alerts')
    .update({ status: 'sending' })
    .eq('id', alertId)
    .eq('user_id', userId)
    .eq('status', 'pending')
    .select('id,user_id,message,lat,lng,location_label,kind,automatic,status')
    .maybeSingle();
  if (claimErr) throw claimErr;
  if (!claimed) return { skipped: true };

  try {
    const { data: vapidRows, error: vapidErr } = await admin.rpc('get_push_vapid_config_for_service');
    if (vapidErr || !vapidRows?.length) throw vapidErr || new Error('Push config unavailable');
    const cfg = vapidRows[0];
    webpush.setVapidDetails(cfg.subject, cfg.public_key, cfg.private_key);

    const { data: subs, error: subErr } = await admin
      .from('push_subscriptions')
      .select('id,user_id,endpoint,p256dh,auth_key')
      .eq('enabled', true)
      .neq('user_id', userId);
    if (subErr) throw subErr;

    const hasPoint = claimed.lat != null && claimed.lng != null;
    const where = claimed.location_label
      ? ` · 📍 ${claimed.location_label}`
      : (hasPoint ? ` · 📍 ${Number(claimed.lat).toFixed(5)}, ${Number(claimed.lng).toFixed(5)}` : ' · posizione GPS non disponibile');
    const defaultWhat = claimed.kind === 'other'
      ? 'sta chiedendo aiuto per un’altra persona'
      : (claimed.automatic ? 'ha attivato un SOS automatico' : 'ha bisogno urgente di aiuto');
    const what = String(claimed.message || '').trim() || defaultWhat;
    const title = claimed.kind === 'other' ? '🆘 AIUTO PER UNA PERSONA' : '🆘 SOS · AIUTO SUBITO';
    const mapUrl = hasPoint
      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${claimed.lat},${claimed.lng}`)}`
      : './';
    const payload = JSON.stringify({
      title,
      body: `${senderName}: ${what}${where}. Se è un’emergenza chiama il 112.`,
      event: 'help_alert',
      help_id: claimed.id,
      help_kind: claimed.kind,
      lat: claimed.lat,
      lng: claimed.lng,
      url: mapUrl,
      tag: `tcv-help-${claimed.id}`,
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

    await admin.from('help_alerts').update({
      status: 'sent',
      sent_at: new Date().toISOString(),
      sent_count: sent,
      failed_count: failed,
    }).eq('id', claimed.id);

    console.log('send-help-push complete', { alertId: claimed.id, sender: userId, sent, failed, kind: claimed.kind });
    return { alert_id: claimed.id, sent, failed, location_included: hasPoint || !!claimed.location_label };
  } catch (e) {
    await admin.from('help_alerts').update({ status: 'pending' }).eq('id', alertId).eq('status', 'sending');
    throw e;
  }
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

    const body = await req.json().catch(() => ({}));
    const action = String(body?.action || 'send_now');
    const message = String(body?.message || '').trim().slice(0, 180);
    const { lat, lng, locationLabel } = cleanPoint(body);

    const admin = createClient(supabaseUrl, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: profile } = await admin.from('profiles').select('nome').eq('id', user.id).maybeSingle();
    const senderName = String(profile?.nome || 'Un utente').trim().slice(0, 60) || 'Un utente';

    if (action === 'arm') {
      const since = new Date(Date.now() - 2 * 60 * 1000).toISOString();
      const { data: existing } = await admin
        .from('help_alerts')
        .select('id,send_at,status')
        .eq('user_id', user.id)
        .eq('status', 'pending')
        .gte('created_at', since)
        .order('created_at', { ascending: false })
        .limit(1)
        .maybeSingle();
      if (existing) return json({ alert_id: existing.id, send_at: existing.send_at, reused: true });

      const sendAt = new Date(Date.now() + 60_000).toISOString();
      const { data: alert, error: insertErr } = await admin
        .from('help_alerts')
        .insert({
          user_id: user.id,
          message,
          lat,
          lng,
          location_label: locationLabel || null,
          kind: 'self',
          automatic: true,
          status: 'pending',
          send_at: sendAt,
        })
        .select('id,send_at')
        .single();
      if (insertErr) throw insertErr;

      const job = (async () => {
        await sleep(61_000);
        try { await dispatchAlert(admin, alert.id, user.id, senderName); }
        catch (e) { console.error('automatic SOS dispatch failed', String(e?.message || e)); }
      })();
      // @ts-ignore Supabase Edge Runtime global
      EdgeRuntime.waitUntil(job);
      return json({ alert_id: alert.id, send_at: alert.send_at, armed: true });
    }

    if (action === 'update_pending') {
      const alertId = String(body?.alert_id || '');
      if (!alertId) return json({ error: 'Missing alert_id' }, 400);
      const patch: any = {};
      if ('message' in body) patch.message = message;
      if ('lat' in body && 'lng' in body) { patch.lat = lat; patch.lng = lng; }
      if ('location_label' in body) patch.location_label = locationLabel || null;
      const { data, error } = await admin.from('help_alerts')
        .update(patch)
        .eq('id', alertId)
        .eq('user_id', user.id)
        .eq('status', 'pending')
        .select('id,status,send_at')
        .maybeSingle();
      if (error) throw error;
      return json({ updated: !!data, alert: data });
    }

    if (action === 'cancel') {
      const alertId = String(body?.alert_id || '');
      if (!alertId) return json({ error: 'Missing alert_id' }, 400);
      const { data, error } = await admin.from('help_alerts')
        .update({ status: 'cancelled', cancelled_at: new Date().toISOString() })
        .eq('id', alertId)
        .eq('user_id', user.id)
        .eq('status', 'pending')
        .select('id,status')
        .maybeSingle();
      if (error) throw error;
      return json({ cancelled: !!data, alert: data });
    }

    if (action === 'other') {
      if (lat == null || lng == null) return json({ error: 'Per aiutare un’altra persona devi indicare la posizione.' }, 400);
      const { data: alert, error: insertErr } = await admin.from('help_alerts').insert({
        user_id: user.id,
        message,
        lat,
        lng,
        location_label: locationLabel || null,
        kind: 'other',
        automatic: false,
        status: 'pending',
        send_at: new Date().toISOString(),
      }).select('id').single();
      if (insertErr) throw insertErr;
      const result = await dispatchAlert(admin, alert.id, user.id, senderName);
      return json(result);
    }

    if (action === 'send_now') {
      let alertId = String(body?.alert_id || '');
      if (alertId) {
        const patch: any = {};
        if ('message' in body) patch.message = message;
        if ('lat' in body && 'lng' in body) { patch.lat = lat; patch.lng = lng; }
        if ('location_label' in body) patch.location_label = locationLabel || null;
        if (Object.keys(patch).length) await admin.from('help_alerts').update(patch).eq('id', alertId).eq('user_id', user.id).eq('status', 'pending');
      } else {
        const { data: alert, error: insertErr } = await admin.from('help_alerts').insert({
          user_id: user.id,
          message,
          lat,
          lng,
          location_label: locationLabel || null,
          kind: 'self',
          automatic: false,
          status: 'pending',
          send_at: new Date().toISOString(),
        }).select('id').single();
        if (insertErr) throw insertErr;
        alertId = alert.id;
      }
      const result = await dispatchAlert(admin, alertId, user.id, senderName);
      return json(result);
    }

    return json({ error: 'Unknown action' }, 400);
  } catch (e) {
    console.error('send-help-push fatal', String(e?.message || e));
    return json({ error: String(e?.message || e) }, 500);
  }
});
