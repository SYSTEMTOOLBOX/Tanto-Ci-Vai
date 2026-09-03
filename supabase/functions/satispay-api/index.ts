import { createClient } from 'npm:@supabase/supabase-js@2.95.0';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

const HOST = 'staging.authservices.satispay.com';
const BASE = `https://${HOST}`;
const APP_RETURN = 'https://systemtoolbox.github.io/Tanto-Ci-Vai/?satispay=return';
const CALLBACK = 'https://qdsphfmcibrveygkmyex.supabase.co/functions/v1/satispay-callback?payment_id={uuid}';

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { ...corsHeaders, 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
});

function b64(bytes: Uint8Array) {
  let out = '';
  for (let i = 0; i < bytes.length; i++) out += String.fromCharCode(bytes[i]);
  return btoa(out);
}

function pemToBytes(pem: string) {
  const clean = pem.replace(/-----BEGIN [^-]+-----/g, '').replace(/-----END [^-]+-----/g, '').replace(/\s+/g, '');
  const raw = atob(clean);
  const out = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
  return out;
}

async function importPrivateKey(pem: string) {
  return crypto.subtle.importKey(
    'pkcs8',
    pemToBytes(pem),
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['sign'],
  );
}

async function digest(body: string) {
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(body));
  return `SHA-256=${b64(new Uint8Array(hash))}`;
}

async function authHeaders(method: string, path: string, body: string) {
  const keyId = Deno.env.get('SATISPAY_KEY_ID') || '';
  const privatePem = (Deno.env.get('SATISPAY_PRIVATE_KEY') || '').replace(/\\n/g, '\n');
  if (!keyId || !privatePem) throw new Error('Satispay Sandbox non ancora configurato nei Secrets Supabase');

  const date = new Date().toUTCString();
  const dg = await digest(body);
  const message = `(request-target): ${method.toLowerCase()} ${path}\nhost: ${HOST}\ndate: ${date}\ndigest: ${dg}`;
  const key = await importPrivateKey(privatePem);
  const sig = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(message));
  const signature = b64(new Uint8Array(sig));

  return {
    host: HOST,
    date,
    digest: dg,
    authorization: `Signature keyId="${keyId}", algorithm="rsa-sha256", headers="(request-target) host date digest", signature="${signature}"`,
    'content-type': 'application/json',
    accept: 'application/json',
    'x-satispay-devicetype': 'ECOMMERCE_PLUGIN',
    'x-satispay-apph': 'Kairon Labs Studio',
    'x-satispay-appn': 'Tanto Ci Vai',
    'x-satispay-appv': 'sandbox-v1',
  };
}

async function satispayRequest(method: string, path: string, bodyObject?: unknown) {
  const body = bodyObject == null ? '' : JSON.stringify(bodyObject);
  const headers = await authHeaders(method, path, body);
  const res = await fetch(`${BASE}${path}`, { method, headers, body: body || undefined });
  const text = await res.text();
  let data: any;
  try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
  if (!res.ok) throw new Error(`Satispay ${res.status}: ${data?.message || text || 'errore API'}`);
  return data;
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') return json({ error: 'Method not allowed' }, 405);

  try {
    const auth = req.headers.get('Authorization') || '';
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const anonKey = Deno.env.get('SUPABASE_ANON_KEY')!;
    const userClient = createClient(supabaseUrl, anonKey, {
      global: { headers: { Authorization: auth } },
      auth: { persistSession: false, autoRefreshToken: false },
    });
    const { data: { user }, error: userErr } = await userClient.auth.getUser();
    if (userErr || !user) return json({ error: 'Unauthorized' }, 401);

    const body = await req.json().catch(() => ({}));
    const action = String(body?.action || '');

    if (action === 'create') {
      const amount = Math.round(Number(body?.amount_unit || 0));
      if (!Number.isInteger(amount) || amount < 1 || amount > 100000) return json({ error: 'Importo non valido' }, 400);
      const orderRef = String(body?.order_ref || `TCV-${Date.now()}`).slice(0, 50);
      const payload = {
        flow: 'MATCH_CODE',
        amount_unit: amount,
        currency: 'EUR',
        external_code: orderRef,
        callback_url: CALLBACK,
        redirect_url: APP_RETURN,
        metadata: {
          tcv_user_id: user.id,
          tcv_order_ref: orderRef,
          environment: 'sandbox',
        },
      };
      const payment = await satispayRequest('POST', '/g_business/v1/payments', payload);
      return json({
        ok: true,
        sandbox: true,
        id: payment.id,
        status: payment.status,
        redirect_url: payment.redirect_url,
        code_identifier: payment.code_identifier || null,
      });
    }

    if (action === 'get') {
      const id = String(body?.payment_id || '').trim();
      if (!id || id.length > 80) return json({ error: 'Payment id non valido' }, 400);
      const payment = await satispayRequest('GET', `/g_business/v1/payments/${encodeURIComponent(id)}`);
      return json({
        ok: true,
        sandbox: true,
        id: payment.id,
        status: payment.status,
        amount_unit: payment.amount_unit,
        currency: payment.currency,
        external_code: payment.external_code || null,
      });
    }

    if (action === 'health') {
      return json({ ok: true, sandbox: true, configured: Boolean(Deno.env.get('SATISPAY_KEY_ID') && Deno.env.get('SATISPAY_PRIVATE_KEY')) });
    }

    return json({ error: 'Azione non valida' }, 400);
  } catch (e) {
    console.error('satispay-api fatal', String((e as any)?.message || e));
    return json({ error: String((e as any)?.message || e) }, 500);
  }
});
