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

    const body = await req.json();
    const requestId = String(body?.request_id || '');
    if (!requestId) return json({ error: 'Missing request_id' }, 400);

    const admin = createClient(supabaseUrl, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });

    // Leggiamo la richiesta con la sessione del mittente: la policy RLS
    // consente al cliente di vedere subito la riga che ha appena creato.
    // Un breve retry copre eventuali ritardi tra inserimento e invocazione.
    let delivery: any = null;
    let deliveryErr: any = null;
    for (let attempt = 0; attempt < 3 && !delivery; attempt++) {
      const result = await userClient
        .from('consegne')
        .select('id,cliente_id,titolo,categoria,ritiro_indirizzo,consegna_indirizzo,compenso_rider,stato')
        .eq('id', requestId)
        .eq('cliente_id', user.id)
        .maybeSingle();
      delivery = result.data;
      deliveryErr = result.error;
      if (!delivery && attempt < 2) await new Promise((resolve) => setTimeout(resolve, 150 * (attempt + 1)));
    }

    if (deliveryErr) {
      console.error('delivery lookup failed', {
        requestId,
        code: deliveryErr.code,
        message: deliveryErr.message,
      });
      return json({ error: 'Request lookup failed' }, 500);
    }
    if (!delivery) {
      console.error('delivery not found for authenticated sender', { requestId, userId: user.id });
      return json({ error: 'Request not found' }, 404);
    }
    if (delivery.stato !== 'disponibile') return json({ sent: 0, skipped: 'not_available' });

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

    console.log('send-request-push', { requestId, recipientSubscriptions: subs?.length || 0 });

    const payload = JSON.stringify({
      title: '🔔 Nuova richiesta di ritiro',
      body: `${delivery.titolo} · ${delivery.ritiro_indirizzo} · € ${Number(delivery.compenso_rider || 0).toFixed(2).replace('.', ',')}`,
      request_id: delivery.id,
      url: `./?request=${encodeURIComponent(delivery.id)}`,
      tag: `tcv-request-${delivery.id}`,
    });

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

    console.log('send-request-push complete', { requestId, sent, failed });
    return json({ sent, failed });
  } catch (e) {
    console.error('send-request-push fatal', String(e?.message || e));
    return json({ error: String(e?.message || e) }, 500);
  }
});
