import { createClient } from 'npm:@supabase/supabase-js@2.95.0';

const corsHeaders={
  'Access-Control-Allow-Origin':'*',
  'Access-Control-Allow-Headers':'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods':'POST, OPTIONS'
};
const HOST='staging.authservices.satispay.com';
const BASE=`https://${HOST}`;
const APP_RETURN='https://systemtoolbox.github.io/Tanto-Ci-Vai/?satispay=return';
const CALLBACK='https://qdsphfmcibrveygkmyex.supabase.co/functions/v1/satispay-callback?payment_id={uuid}';
const json=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{...corsHeaders,'Content-Type':'application/json','Cache-Control':'no-store'}});

function b64(bytes:Uint8Array){let out='';for(let i=0;i<bytes.length;i++)out+=String.fromCharCode(bytes[i]);return btoa(out)}
function pemToBytes(pem:string){const clean=pem.replace(/-----BEGIN [^-]+-----/g,'').replace(/-----END [^-]+-----/g,'').replace(/\s+/g,'');const raw=atob(clean);const out=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);return out}
async function digest(body:string){const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(body));return `SHA-256=${b64(new Uint8Array(hash))}`}
const admin=()=>createClient(Deno.env.get('SUPABASE_URL')!,Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,{auth:{persistSession:false,autoRefreshToken:false}});
let CACHE:any=null;
async function creds(){if(CACHE)return CACHE;const{data,error}=await admin().rpc('get_satispay_credentials_for_service');if(error)throw error;const row=Array.isArray(data)?data[0]:data;if(!row?.key_id||!row?.private_key)throw new Error('Satispay Sandbox non ancora attivato');CACHE={keyId:String(row.key_id),privatePem:String(row.private_key)};return CACHE}
async function authHeaders(method:string,path:string,body:string){const c=await creds();const date=new Date().toUTCString();const dg=await digest(body);const message=`(request-target): ${method.toLowerCase()} ${path}\nhost: ${HOST}\ndate: ${date}\ndigest: ${dg}`;const key=await crypto.subtle.importKey('pkcs8',pemToBytes(c.privatePem),{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['sign']);const sig=await crypto.subtle.sign('RSASSA-PKCS1-v1_5',key,new TextEncoder().encode(message));return{host:HOST,date,digest:dg,authorization:`Signature keyId="${c.keyId}", algorithm="rsa-sha256", headers="(request-target) host date digest", signature="${b64(new Uint8Array(sig))}"`,'content-type':'application/json',accept:'application/json','x-satispay-devicetype':'ECOMMERCE_PLUGIN','x-satispay-apph':'Kairon Labs Studio','x-satispay-appn':'Tanto Ci Vai','x-satispay-appv':'sandbox-fund-lock-v1'}}
async function sat(method:string,path:string,bodyObject?:unknown,idempotencyKey?:string){const body=bodyObject==null?'':JSON.stringify(bodyObject);const headers:any=await authHeaders(method,path,body);if(idempotencyKey)headers['idempotency-key']=idempotencyKey;const res=await fetch(`${BASE}${path}`,{method,headers,body:body||undefined});const text=await res.text();let data:any;try{data=text?JSON.parse(text):{}}catch{data={raw:text}}if(!res.ok)throw new Error(`Satispay ${res.status}: ${data?.message||text||'errore API'}`);return data}
function timePatch(status:string){const now=new Date().toISOString(),p:any={status,updated_at:now};if(status==='AUTHORIZED')p.authorized_at=now;if(status==='ACCEPTED'){p.accepted_at=now;p.captured_at=now}if(status==='CANCELED')p.cancelled_at=now;return p}
async function tracked(id:string,userId?:string){let q=admin().from('satispay_payments').select('*').eq('satispay_payment_id',id);if(userId)q=q.eq('user_id',userId);const{data,error}=await q.maybeSingle();if(error)throw error;return data}
async function syncPayment(id:string,userId?:string){const row=await tracked(id,userId);if(!row)throw new Error('Pagamento non trovato');const payment=await sat('GET',`/g_business/v1/payments/${encodeURIComponent(id)}`);const status=String(payment.status||'PENDING').toUpperCase();const patch=timePatch(status);const{error}=await admin().from('satispay_payments').update(patch).eq('satispay_payment_id',id);if(error)throw error;if(row.consegna_id){if(row.payment_kind==='APP_FEE')await admin().from('consegne').update({app_fee_status:status}).eq('id',row.consegna_id);if(row.payment_kind==='RIDER_FUND_LOCK')await admin().from('consegne').update({rider_fund_lock_status:status}).eq('id',row.consegna_id)}return{...payment,status,tracked:row}}
async function getDelivery(id:string){const{data,error}=await admin().from('consegne').select('*').eq('id',id).maybeSingle();if(error)throw error;return data}
async function saveTracked(userId:string,payment:any,deliveryId:string|null,kind:string,flow:string,ref:string,amount:number){const status=String(payment.status||'PENDING').toUpperCase();const{error}=await admin().from('satispay_payments').upsert({user_id:userId,satispay_payment_id:String(payment.id),order_ref:ref,amount_unit:amount,currency:'EUR',status,sandbox:true,consegna_id:deliveryId,payment_kind:kind,flow,updated_at:new Date().toISOString(),...timePatch(status)},{onConflict:'satispay_payment_id'});if(error)throw error;return status}
function orderRef(d:any,suffix:string){const n=d.numero_ordine!=null?String(d.numero_ordine).padStart(4,'0'):String(d.id).slice(0,8);return `TCV-${n}-${suffix}`.slice(0,50)}

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

    if(action==='health'){try{await creds();return json({ok:true,sandbox:true,configured:true,fund_lock:true})}catch{return json({ok:true,sandbox:true,configured:false,fund_lock:true})}}
    if(action==='test_auth'){const data=await sat('POST','/wally-services/protocol/tests/signature',{});return json({ok:true,sandbox:true,role:data?.authentication_key?.role||data?.role||null})}

    if(action==='create'){
      const amount=Math.round(Number(body?.amount_unit||0));if(!Number.isInteger(amount)||amount<1||amount>100000)return json({error:'Importo non valido'},400);
      const ref=String(body?.order_ref||`TCV-${Date.now()}`).slice(0,50);
      const payment=await sat('POST','/g_business/v1/payments',{flow:'MATCH_CODE',amount_unit:amount,currency:'EUR',external_code:ref,callback_url:CALLBACK,redirect_url:APP_RETURN,metadata:{tcv_user_id:user.id,tcv_order_ref:ref,environment:'sandbox'}},ref);
      const status=await saveTracked(user.id,payment,null,'TEST','MATCH_CODE',ref,amount);
      return json({ok:true,sandbox:true,id:payment.id,status,redirect_url:payment.redirect_url,code_identifier:payment.code_identifier||null,order_ref:ref});
    }

    if(action==='get'){
      const id=String(body?.payment_id||'').trim();if(!id||id.length>80)return json({error:'Payment id non valido'},400);
      const payment=await syncPayment(id,user.id);
      return json({ok:true,sandbox:true,id:payment.id,status:payment.status,amount_unit:payment.amount_unit,currency:payment.currency,external_code:payment.external_code||null,payment_kind:payment.tracked?.payment_kind||null,consegna_id:payment.tracked?.consegna_id||null});
    }

    const deliveryId=String(body?.delivery_id||'').trim();
    if(!deliveryId)return json({error:'delivery_id mancante'},400);
    const d=await getDelivery(deliveryId);
    if(!d)return json({error:'Richiesta non trovata'},404);

    if(action==='create_delivery_fee'){
      if(d.cliente_id!==user.id)return json({error:'Forbidden'},403);
      if(d.app_fee_payment_id){const p=await syncPayment(String(d.app_fee_payment_id),user.id);return json({ok:true,id:p.id,status:p.status,redirect_url:p.redirect_url||null,reused:true})}
      const amount=Math.round(Number(d.commissione_app||0)*100);if(amount!==50)return json({error:'Commissione app non valida'},400);
      const ref=orderRef(d,'FEE');
      const payment=await sat('POST','/g_business/v1/payments',{flow:'MATCH_CODE',amount_unit:amount,currency:'EUR',external_code:ref,callback_url:CALLBACK,redirect_url:APP_RETURN,metadata:{tcv_user_id:user.id,tcv_delivery_id:d.id,tcv_payment_kind:'APP_FEE',environment:'sandbox'}},ref);
      const status=await saveTracked(user.id,payment,d.id,'APP_FEE','MATCH_CODE',ref,amount);
      const{error}=await admin().from('consegne').update({app_fee_payment_id:String(payment.id),app_fee_status:status,payment_state:'FEE_PENDING'}).eq('id',d.id);if(error)throw error;
      return json({ok:true,sandbox:true,id:payment.id,status,redirect_url:payment.redirect_url,amount_unit:amount});
    }

    if(action==='create_delivery_fund_lock'){
      if(d.cliente_id!==user.id)return json({error:'Forbidden'},403);
      if(d.app_fee_payment_id){const fee=await syncPayment(String(d.app_fee_payment_id),user.id);if(fee.status!=='ACCEPTED')return json({error:'Prima conferma la commissione app da € 0,50.',fee_status:fee.status},409)}else return json({error:'Commissione app non ancora creata'},409);
      if(d.rider_fund_lock_payment_id){const p=await syncPayment(String(d.rider_fund_lock_payment_id),user.id);return json({ok:true,id:p.id,status:p.status,redirect_url:p.redirect_url||null,reused:true})}
      const amount=Math.round(Number(d.compenso_rider||0)*100);if(amount<1)return json({error:'Compenso rider non valido'},400);
      const ref=orderRef(d,'HOLD');
      let expiration=new Date(Date.now()+10*24*3600*1000);if(d.consegna_entro){const requested=new Date(new Date(d.consegna_entro).getTime()+60*60*1000);if(requested<expiration)expiration=requested}if(expiration.getTime()<Date.now()+15*60*1000)expiration=new Date(Date.now()+15*60*1000);
      const payment=await sat('POST','/g_business/v1/payments',{flow:'FUND_LOCK',amount_unit:amount,currency:'EUR',external_code:ref,callback_url:CALLBACK,redirect_url:APP_RETURN,expiration_date:expiration.toISOString(),metadata:{tcv_user_id:user.id,tcv_delivery_id:d.id,tcv_payment_kind:'RIDER_FUND_LOCK',environment:'sandbox'}},ref);
      const status=await saveTracked(user.id,payment,d.id,'RIDER_FUND_LOCK','FUND_LOCK',ref,amount);
      const{error}=await admin().from('consegne').update({rider_fund_lock_payment_id:String(payment.id),rider_fund_lock_status:status,payment_state:'HOLD_PENDING'}).eq('id',d.id);if(error)throw error;
      return json({ok:true,sandbox:true,id:payment.id,status,redirect_url:payment.redirect_url,amount_unit:amount,expiration_date:expiration.toISOString()});
    }

    if(action==='finalize_delivery_payment'){
      if(d.cliente_id!==user.id)return json({error:'Forbidden'},403);
      if(!d.app_fee_payment_id||!d.rider_fund_lock_payment_id)return json({error:'Pagamenti incompleti'},409);
      const fee=await syncPayment(String(d.app_fee_payment_id),user.id);
      const hold=await syncPayment(String(d.rider_fund_lock_payment_id),user.id);
      let state=String(d.payment_state||'PAYMENT_REQUIRED');
      if(fee.status==='ACCEPTED'&&hold.status==='AUTHORIZED')state='READY';
      else if(fee.status==='CANCELED')state='FEE_CANCELED';
      else if(hold.status==='CANCELED')state='HOLD_CANCELED';
      else if(fee.status==='ACCEPTED')state='HOLD_PENDING';
      else state='FEE_PENDING';
      const{error}=await admin().from('consegne').update({payment_state:state,app_fee_status:fee.status,rider_fund_lock_status:hold.status}).eq('id',d.id);if(error)throw error;
      return json({ok:true,sandbox:true,payment_state:state,fee_status:fee.status,hold_status:hold.status,ready:state==='READY'});
    }

    if(action==='capture_delivery'){
      if(d.rider_id!==user.id)return json({error:'Solo il rider assegnato può sbloccare il compenso.'},403);
      if(d.stato!=='consegnata')return json({error:'Il compenso si sblocca solo dopo “Consegnato”.'},409);
      if(!d.rider_fund_lock_payment_id)return json({error:'Blocco fondi non trovato'},404);
      let hold=await syncPayment(String(d.rider_fund_lock_payment_id));
      const amount=Math.round(Number(d.compenso_rider||0)*100);
      if(hold.status==='AUTHORIZED'){
        const payment=await sat('PUT',`/g_business/v1/payments/${encodeURIComponent(String(d.rider_fund_lock_payment_id))}`,{action:'ACCEPT',amount_unit:amount});
        const status=String(payment.status||'ACCEPTED').toUpperCase();
        await admin().from('satispay_payments').update(timePatch(status)).eq('satispay_payment_id',String(d.rider_fund_lock_payment_id));
        hold={...payment,status};
      }
      if(hold.status!=='ACCEPTED')return json({error:`Blocco fondi non catturabile: ${hold.status}`},409);
      const{error}=await admin().from('consegne').update({payment_state:'CAPTURED_PENDING_PAYOUT',rider_fund_lock_status:'ACCEPTED'}).eq('id',d.id);if(error)throw error;
      return json({ok:true,sandbox:true,status:'ACCEPTED',payment_state:'CAPTURED_PENDING_PAYOUT',amount_unit:amount,note:'Sandbox: fondi catturati dal merchant. Payout automatico verso Satispay personale rider non disponibile nella API pubblica.'});
    }

    if(action==='cancel_delivery_hold'){
      if(d.cliente_id!==user.id)return json({error:'Forbidden'},403);
      if(!d.rider_fund_lock_payment_id)return json({ok:true,skipped:'no_hold'});
      let hold=await syncPayment(String(d.rider_fund_lock_payment_id),user.id);
      if(hold.status==='PENDING'||hold.status==='AUTHORIZED'){
        const payment=await sat('PUT',`/g_business/v1/payments/${encodeURIComponent(String(d.rider_fund_lock_payment_id))}`,{action:'CANCEL'});
        const status=String(payment.status||'CANCELED').toUpperCase();
        await admin().from('satispay_payments').update(timePatch(status)).eq('satispay_payment_id',String(d.rider_fund_lock_payment_id));
        hold={...payment,status};
      }
      await admin().from('consegne').update({rider_fund_lock_status:hold.status,payment_state:'HOLD_CANCELED'}).eq('id',d.id);
      return json({ok:true,sandbox:true,status:hold.status});
    }

    return json({error:'Azione non valida'},400);
  }catch(e){console.error('satispay-api fatal',String((e as any)?.message||e));return json({error:String((e as any)?.message||e)},500)}
});
