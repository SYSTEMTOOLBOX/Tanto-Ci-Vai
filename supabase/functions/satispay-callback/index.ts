const HOST = 'staging.authservices.satispay.com';
const BASE = `https://${HOST}`;

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

async function getPayment(paymentId: string) {
  const keyId = Deno.env.get('SATISPAY_KEY_ID') || '';
  const privatePem = (Deno.env.get('SATISPAY_PRIVATE_KEY') || '').replace(/\\n/g, '\n');
  if (!keyId || !privatePem) throw new Error('Satispay secrets missing');
  const path = `/g_business/v1/payments/${encodeURIComponent(paymentId)}`;
  const body = '';
  const digestRaw = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(body));
  const digest = `SHA-256=${b64(new Uint8Array(digestRaw))}`;
  const date = new Date().toUTCString();
  const message = `(request-target): get ${path}\nhost: ${HOST}\ndate: ${date}\ndigest: ${digest}`;
  const key = await crypto.subtle.importKey('pkcs8', pemToBytes(privatePem), { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['sign']);
  const signed = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', key, new TextEncoder().encode(message));
  const authorization = `Signature keyId="${keyId}", algorithm="rsa-sha256", headers="(request-target) host date digest", signature="${b64(new Uint8Array(signed))}"`;
  const res = await fetch(`${BASE}${path}`, { headers: { host: HOST, date, digest, authorization, accept: 'application/json' } });
  const text = await res.text();
  if (!res.ok) throw new Error(`Satispay callback GET ${res.status}: ${text}`);
  return JSON.parse(text);
}

Deno.serve(async (req) => {
  if (req.method !== 'GET') return new Response('Method not allowed', { status: 405 });
  try {
    const paymentId = new URL(req.url).searchParams.get('payment_id') || '';
    if (!paymentId) return new Response('Missing payment_id', { status: 400 });
    const payment = await getPayment(paymentId);
    console.log('SATISPAY_CALLBACK', JSON.stringify({ id: payment.id, status: payment.status, amount_unit: payment.amount_unit, external_code: payment.external_code || null }));
    return new Response('ok', { status: 200, headers: { 'cache-control': 'no-store' } });
  } catch (e) {
    console.error('satispay-callback fatal', String((e as any)?.message || e));
    return new Response('callback error', { status: 500 });
  }
});
