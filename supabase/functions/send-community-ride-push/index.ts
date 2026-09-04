import { createClient } from 'npm:@supabase/supabase-js@2.95.0';
import webpush from 'npm:web-push@3.6.7';

const corsHeaders={
  'Access-Control-Allow-Origin':'*',
  'Access-Control-Allow-Headers':'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods':'POST, OPTIONS'
};
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{...corsHeaders,'Content-Type':'application/json'}});
const validEvents=new Set(['requested','accepted','declined','onboard','completed']);

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({error:'Method not allowed'},405);
  try{
    const auth=req.headers.get('Authorization')||'';
    const supabaseUrl=Deno.env.get('SUPABASE_URL')!;
    const anonKey=Deno.env.get('SUPABASE_ANON_KEY')!;
    const serviceKey=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const userClient=createClient(supabaseUrl,anonKey,{global:{headers:{Authorization:auth}},auth:{persistSession:false,autoRefreshToken:false}});
    const {data:{user},error:userErr}=await userClient.auth.getUser();
    if(userErr||!user)return json({error:'Unauthorized'},401);

    const body=await req.json();
    const rideId=String(body?.ride_id||'');
    const eventType=String(body?.event||'');
    if(!rideId||!validEvents.has(eventType))return json({error:'Invalid payload'},400);

    const admin=createClient(supabaseUrl,serviceKey,{auth:{persistSession:false,autoRefreshToken:false}});
    const {data:ride,error:rideErr}=await admin.from('ride_requests')
      .select('id,user_id,driver_id,community_trip_id,from_label,to_label,departure_at,passengers,status,requester_display_name')
      .eq('id',rideId).maybeSingle();
    if(rideErr)throw rideErr;
    if(!ride)return json({error:'Ride not found'},404);

    const expectedStatus:Record<string,string>={requested:'open',accepted:'matched',declined:'declined',onboard:'onboard',completed:'completed'};
    if(String(ride.status)!==expectedStatus[eventType])return json({sent:0,skipped:'status_mismatch'});

    let recipientUserId:string|null=null;
    if(eventType==='requested'){
      if(String(ride.user_id)!==user.id)return json({error:'Forbidden'},403);
      recipientUserId=ride.driver_id;
    }else{
      if(String(ride.driver_id)!==user.id)return json({error:'Forbidden'},403);
      recipientUserId=ride.user_id;
    }
    if(!recipientUserId)return json({sent:0,skipped:'recipient_missing'});

    const {data:driverProfile}=await admin.from('community_public_profiles').select('display_name').eq('user_id',ride.driver_id).maybeSingle();
    const driverName=String(driverProfile?.display_name||'Il guidatore');
    const passengerName=String(ride.requester_display_name||'Un passeggero');
    const route=`${ride.from_label} → ${ride.to_label}`;
    const pax=Math.max(1,Number(ride.passengers||1));

    let title='🚘 Nuova richiesta di posto';
    let notificationBody=`${passengerName} vuole salire sul tuo percorso: ${route} · ${pax} ${pax===1?'persona':'persone'}.`;
    if(eventType==='accepted'){
      title='✅ Passaggio accettato';
      notificationBody=`${driverName} ha accettato la tua richiesta: ${route}.`;
    }else if(eventType==='declined'){
      title='Passaggio non disponibile';
      notificationBody=`${driverName} non può accettare questa richiesta: ${route}.`;
    }else if(eventType==='onboard'){
      title='🚘 Passeggero a bordo';
      notificationBody=`${driverName} ha confermato la salita a bordo per ${route}.`;
    }else if(eventType==='completed'){
      title='🏁 Viaggio completato';
      notificationBody=`Arrivo confermato per ${route}.`;
    }

    const {data:vapidRows,error:vapidErr}=await admin.rpc('get_push_vapid_config_for_service');
    if(vapidErr||!vapidRows?.length)throw vapidErr||new Error('Push config unavailable');
    const cfg=vapidRows[0];
    webpush.setVapidDetails(cfg.subject,cfg.public_key,cfg.private_key);

    const {data:subs,error:subErr}=await admin.from('push_subscriptions')
      .select('id,endpoint,p256dh,auth_key').eq('enabled',true).eq('user_id',recipientUserId);
    if(subErr)throw subErr;

    const payload=JSON.stringify({title,body:notificationBody,request_id:ride.id,event:`community_${eventType}`,url:'./',tag:`tcv-community-${ride.id}-${eventType}`});
    let sent=0,failed=0;
    for(const s of subs||[]){
      try{
        await webpush.sendNotification({endpoint:s.endpoint,keys:{p256dh:s.p256dh,auth:s.auth_key}},payload,{TTL:3600,urgency:'high'});
        sent++;
      }catch(e){
        failed++;
        const status=Number(e?.statusCode||e?.status||0);
        if(status===404||status===410)await admin.from('push_subscriptions').delete().eq('id',s.id);
        else console.error('community ride push failed',{status,message:String(e?.message||e)});
      }
    }
    console.log('community ride push',{rideId,eventType,recipientUserId,sent,failed});
    return json({event:eventType,sent,failed});
  }catch(e){
    console.error('community ride push fatal',String(e?.message||e));
    return json({error:String(e?.message||e)},500);
  }
});
