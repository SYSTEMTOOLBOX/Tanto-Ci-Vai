import { createClient } from 'npm:@supabase/supabase-js@2.95.0';

const corsHeaders={
  'Access-Control-Allow-Origin':'*',
  'Access-Control-Allow-Headers':'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods':'POST, OPTIONS'
};
const HOST='staging.authservices.satispay.com';
const BASE=`https://${HOST}`;
const RETURN_URL='https://systemtoolbox.github.io/Tanto-Ci-Vai/?satispay=account-return';
const CALLBACK='https://qdsphfmcibrveygkmyex.supabase.co/functions/v1/satispay-account-callback?authorization_id={uuid}';
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{...corsHeaders,'Content-Type':'application/json','Cache-Control':'no-store'}});

function b64(bytes:Uint8Array){let out='';for(let i=0;i<bytes.length;i++)out+=String.fromCharCode(bytes[i]);return btoa(out)}
function pemToBytes(pem:string){const clean=pem.replace(/-----BEGIN [^-]+-----/g,'').replace(/-----END [^-]+-----/g,'').replace(/\s+/g,'');const raw=atob(clean);const out=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);return out}
async function digest(body:string){const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body));return `SHA-256=${b64(new Uint8Array(hash))}`}
const admin=()=>createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,{auth:{persistSession:false,autoRefreshToken:false}});
let CACHE:any=null;
async function creds(){if(CACHE)return CACHE;const{data,error}=await admin().rpc('get_satispay_credentials_for_service');if(error)throw error;const row=Array.isArray(data)?data[0]:data;if(!row?.key_id||!row?.private_key)throw new Error('Satispay Sandbox non ancora attivato');CACHE={keyId:String(row.key_id),privatePem:String(row.private_key)};return CACHE}
async function headers(method:string,path:string,body:string){const c=await creds();const date=new Date().toUTCString();const dg=await digest(body);const msg=`(request-target): ${method.toLowerCase()} ${path}\nhost: ${HOST}\ndate: ${date}\ndigest: ${dg}`;const key=await crypto.subtle.importKey('pkcs8',pemToBytes(c.privatePem),{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['sign']);const sig=await crypto.subtle.sign('RSASSA-PKCS1-v1_5',key,new TextEncoder().encode(msg));return{host:HOST,date,digest:dg,authorization:`Signature keyId="${c.keyId}", algorithm="rsa-sha256", headers="(request-target) host date digest", signature="${b64(new Uint8Array(sig))}"`,'content-type':'application/json',accept:'application/json','x-satispay-devicetype':'ECOMMERCE_PLUGIN','x-satispay-apph':'Kairon Labs Studio','x-satispay-appn':'Tanto Ci Vai','x-satispay-appv':'sandbox-account-confirm-v1'}}
async function sat(method:string,path:string,bodyObject?:unknown,idempotencyKey?:string){const body=bodyObject==null?'':JSON.stringify(bodyObject);const h:any=await headers(method,path,body);if(idempotencyKey)h['idempotency-key']=idempotencyKey;const res=await fetch(`${BASE}${path}`,{method,headers:h,body:body||undefined});const text=await res.text();let data:any;try{data=text?JSON.parse(text):{}}catch{data={raw:text}}if(!res.ok)throw new Error(`Satispay ${res.status}: ${data?.message||text||'errore API'}`);return data}
async function syncPublic(db:any,userId:string,status:string,confirmedAt:string|null){await db.from('community_public_profiles').update({account_confirmed:status==='ACCEPTED',account_confirmed_at:confirmedAt}).eq('user_id',userId)}

Deno.serve(async(req)=>{
  if(req.method==='OPTIONS')return new Response('ok',{headers:corsHeaders});
  if(req.method!=='POST')return json({error:'Method not allowed'},405);
  try{
    const auth=req.headers.get('Authorization')||'';
    const userClient=createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_ANON_KEY')!,{global:{headers:{Authorization:auth}},auth:{persistSession:false,autoRefreshToken:false}});
    const{data:{user},error:userErr}=await userClient.auth.getUser();
    if(userErr||!user)return json({error:'Unauthorized'},401);
    const body=await req.json().catch(()=>({}));
    const action=String(body?.action||'');
    const db=admin();

    if(action==='status'){
      const{data:row,error}=await db.from('community_satispay_accounts').select('authorization_id,status,confirmed_at').eq('user_id',user.id).maybeSingle();if(error)throw error;
      if(!row?.authorization_id)return json({ok:true,status:'NONE',confirmed:false});
      const a=await sat('GET',`/g_business/v1/pre_authorized_payment_tokens/${encodeURIComponent(row.authorization_id)}`);
      const status=String(a.status||'PENDING').toUpperCase();const confirmedAt=status==='ACCEPTED'?(row.confirmed_at||new Date().toISOString()):null;
      const{error:upErr}=await db.from('community_satispay_accounts').update({status,consumer_uid:a.consumer_uid||null,confirmed_at:confirmedAt,updated_at:new Date().toISOString()}).eq('user_id',user.id);if(upErr)throw upErr;
      await syncPublic(db,user.id,status,confirmedAt);
      return json({ok:true,status,confirmed:status==='ACCEPTED'});
    }

    if(action==='create'){
      const{data:existing,error:readErr}=await db.from('community_satispay_accounts').select('authorization_id,status').eq('user_id',user.id).maybeSingle();if(readErr)throw readErr;
      if(existing?.authorization_id&&existing.status==='ACCEPTED')return json({ok:true,status:'ACCEPTED',confirmed:true});
      const idem=`tcv-account-${user.id}-${crypto.randomUUID()}`;
      const a=await sat('POST','/g_business/v1/pre_authorized_payment_tokens',{reason:'Conferma account Tanto Ci Vai',callback_url:CALLBACK,redirect_url:RETURN_URL,metadata:{tcv_user_id:user.id,environment:'sandbox',purpose:'community_account_confirmation'}},idem);
      const status=String(a.status||'PENDING').toUpperCase();
      const{error}=await db.from('community_satispay_accounts').upsert({user_id:user.id,authorization_id:String(a.id),consumer_uid:a.consumer_uid||null,status,sandbox:true,updated_at:new Date().toISOString(),confirmed_at:status==='ACCEPTED'?new Date().toISOString():null},{onConflict:'user_id'});if(error)throw error;
      return json({ok:true,status,confirmed:status==='ACCEPTED',authorization_id:a.id,redirect_url:a.redirect_url||null});
    }

    return json({error:'Azione non valida'},400);
  }catch(e){console.error('satispay-account fatal',String((e as any)?.message||e));return json({error:String((e as any)?.message||e)},500)}
});
