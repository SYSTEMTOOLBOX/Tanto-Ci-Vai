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

const supportedEvents = new Set(['new_request', 'accepted', 'picked_up']);

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

    const body = await req.json();
    const requestId = String(body?.request_id || '');
    const eventType = String(body?.event || 'new_request');
    if (!requestId) return json({ error: 'Missing request_id' }, 400);
    if (!supportedEvents.has(eventType)) return json({ error: 'Unsupported event' }, 400);

    const admin = createClient(supabaseUrl, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });

    let delivery: any = null;
    let deliveryErr: any = null;
    for (let attempt = 0; attempt < 3 && !delivery; attempt++) {
      const result = await admin
        .from('consegne')
        .select('id,numero_ordine,cliente_id,rider_id,titolo,categoria,ritiro_indirizzo,consegna_indirizzo,compenso_rider,consegna_prevista,stato')
        .eq('id', requestId)
        .maybeSingle();
      delivery = result.data;
      deliveryErr = result.error;
      if (!delivery && attempt < 2) await new Promise((resolve) => setTimeout(resolve, 150 * (attempt + 1)));
    }

    if (deliveryErr) {
      console.error('delivery lookup failed', { requestId, code: deliveryErr.code, message: deliveryErr.message });
      return json({ error: 'Request lookup failed' }, 500);
    }
    if (!delivery) return json({ error: 'Request not found' }, 404);

    let recipientUserId: string | null = null;
    if (eventType === 'new_request') {
      if (delivery.cliente_id !== user.id) return json({ error: 'Forbidden' }, 403);
      if (delivery.stato !== 'disponibile') return json({ sent: 0, skipped: 'not_available' });
    } else if (eventType === 'accepted') {
      if (delivery.rider_id !== user.id) return json({ error: 'Forbidden' }, 403);
      if (delivery.stato !== 'accettata') return json({ sent: 0, skipped: 'not_accepted' });
      recipientUserId = delivery.cliente_id;
    } else if (eventType === 'picked_up') {
      if (delivery.rider_id !== user.id) return json({ error: 'Forbidden' }, 403);
      if (!['ritirata', 'in_consegna'].includes(delivery.stato)) return json({ sent: 0, skipped: 'not_picked_up' });
      recipientUserId = delivery.cliente_id;
    }

    const { data: vapidRows, error: vapidErr } = await admin.rpc('get_push_vapid_config_for_service');
    if (vapidErr || !vapidRows?.length) throw vapidErr || new Error('Push config unavailable');
    const cfg = vapidRows[0];
    webpush.setVapidDetails(cfg.subject, cfg.public_key, cfg.private_key);

    let subsQuery = admin
      .from('push_subscriptions')
      .select('id,user_id,endpoint,p256dh,auth_key')
      .eq('enabled', true);
    subsQuery = recipientUserId
      ? subsQuery.eq('user_id', recipientUserId)
      : subsQuery.neq('user_id', user.id);
    const { data: subs, error: subErr } = await subsQuery;
    if (subErr) throw subErr;

    const orderLabel = delivery.numero_ordine != null
      ? `Ordine #${String(delivery.numero_ordine).padStart(4, '0')}`
      : 'La tua richiesta';

    let title = '🔔 Nuova richiesta di ritiro';
    let notificationBody = `${delivery.titolo} · ${delivery.ritiro_indirizzo} · € ${Number(delivery.compenso_rider || 0).toFixed(2).replace('.', ',')}`;
    if (eventType === 'accepted') {
      title = '✅ Ritiro accettato';
      notificationBody = `${orderLabel}: un runner ha accettato la richiesta. Ti avviseremo appena ritira.`;
    } else if (eventType === 'picked_up') {
      title = '📦 Ritirato · in consegna';
      notificationBody = `${orderLabel}: il runner ha ritirato il tuo ordine. La consegna è in corso.`;
    }

    const payload = JSON.stringify({
      title,
      body: notificationBody,
      request_id: delivery.id,
      event: eventType,
      url: `./?request=${encodeURIComponent(delivery.id)}`,
      tag: `tcv-request-${delivery.id}-${eventType}`,
    });

    console.log('send-request-push', { requestId, eventType, recipientUserId, recipientSubscriptions: subs?.length || 0 });

    let sent = 0;
    let failed = 0;
    for (const s of subs || []) {
      try {
        await webpush.sendNotification(
          { endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth_key } },
          payload,
          { TTL: 3600, urgency: 'high' },
        );
        sent++;
      } catch (e) {
        failed++;
        const status = Number(e?.statusCode || e?.status || 0);
        if (status === 404 || status === 410) {
          await admin.from('push_subscriptions').delete().eq('id', s.id);
        } else {
          console.error('push delivery failed', { subscriptionId: s.id, status, message: String(e?.message || e) });
        }
      }
    }

    console.log('send-request-push complete', { requestId, eventType, sent, failed });
    return json({ event: eventType, sent, failed });
  } catch (e) {
    console.error('send-request-push fatal', String(e?.message || e));
    return json({ error: String(e?.message || e) }, 500);
  }
});
