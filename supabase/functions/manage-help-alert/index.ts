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
    const body = await req.json().catch(() => ({}));
    const action = String(body?.action || '');
    const alertId = String(body?.alert_id || '');
    if (!/^[0-9a-f-]{36}$/i.test(alertId)) return json({ error: 'SOS non valido' }, 400);

    const { data: alert, error: alertErr } = await admin
      .from('help_alerts')
      .select('id,user_id,kind,status,resolution_count,resolved_at')
      .eq('id', alertId)
      .maybeSingle();
    if (alertErr) throw alertErr;
    if (!alert || !['self', 'other'].includes(String(alert.kind)) || alert.status !== 'sent') {
      return json({ error: 'SOS non più disponibile' }, 404);
    }

    if (action === 'owner_close') {
      if (alert.user_id !== user.id) return json({ error: 'Solo chi ha inviato il SOS può eliminarlo subito' }, 403);
      const { error: delErr } = await admin.from('help_alerts').delete().eq('id', alertId).eq('user_id', user.id);
      if (delErr) throw delErr;
      return json({ deleted: true });
    }

    if (action === 'vote_resolved') {
      if (alert.resolved_at) {
        return json({ voted: true, resolved: true, resolution_count: Number(alert.resolution_count || 3) });
      }
      const { error: voteErr } = await admin
        .from('help_alert_resolutions')
        .upsert({ help_alert_id: alertId, user_id: user.id }, {
          onConflict: 'help_alert_id,user_id',
          ignoreDuplicates: true,
        });
      if (voteErr) throw voteErr;

      const { data: updated, error: updateErr } = await admin
        .from('help_alerts')
        .select('resolution_count,resolved_at')
        .eq('id', alertId)
        .single();
      if (updateErr) throw updateErr;
      return json({
        voted: true,
        resolved: Boolean(updated.resolved_at),
        resolution_count: Number(updated.resolution_count || 0),
        resolved_at: updated.resolved_at || null,
      });
    }

    return json({ error: 'Azione non valida' }, 400);
  } catch (e) {
    console.error('manage-help-alert fatal', String((e as any)?.message || e));
    return json({ error: String((e as any)?.message || e) }, 500);
  }
});
