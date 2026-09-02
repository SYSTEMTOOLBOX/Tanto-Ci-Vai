from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
original=s

old="async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');let splashPromise=runStartupSplash(session);await ensureProfile();await loadRequests();subscribeRealtime();renderAll();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000);await splashPromise}"
new="async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');let splashPromise=runStartupSplash(session);await ensureProfile();await loadRequests();subscribeRealtime();renderAll();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000);await splashPromise;setTimeout(()=>tcvMaybeOfferPush(),350);setTimeout(()=>tcvOpenRequestFromUrl(),500)}"
if old not in s: raise SystemExit('afterLogin block not found')
s=s.replace(old,new,1)

old="let {error}=await db.from('consegne').insert({cliente_id:SESSION.user.id,categoria:REQUEST_CATEGORY,titolo:title,descrizione:fullDesc,ritiro_indirizzo:a.label,ritiro_lat:a.lat,ritiro_lng:a.lng,consegna_indirizzo:deliveryLabel,consegna_lat:b.lat,consegna_lng:b.lng,consegna_entro:deadline.toISOString(),offerta_scade_il:offerExpires.toISOString(),compenso_rider:pay});if(error)throw error;"
new="let {data:created,error}=await db.from('consegne').insert({cliente_id:SESSION.user.id,categoria:REQUEST_CATEGORY,titolo:title,descrizione:fullDesc,ritiro_indirizzo:a.label,ritiro_lat:a.lat,ritiro_lng:a.lng,consegna_indirizzo:deliveryLabel,consegna_lat:b.lat,consegna_lng:b.lng,consegna_entro:deadline.toISOString(),offerta_scade_il:offerExpires.toISOString(),compenso_rider:pay}).select('id').single();if(error)throw error;try{await db.functions.invoke('send-request-push',{body:{request_id:created.id}})}catch(pushErr){console.warn('Push send failed',pushErr)}"
if old not in s: raise SystemExit('publish insert block not found')
s=s.replace(old,new,1)

old="function renderProfile(){profile.innerHTML=`<div class=\"pagehead\"><div class=\"k\">PROFILO</div><h2>${esc(PROFILE.nome||'Profilo')}</h2><p>${esc(SESSION.user.email||'')}</p></div><div class=\"req\"><div class=\"field\"><label>NOME</label><input id=\"pfName\" value=\"${esc(PROFILE.nome||'')}\"></div><div class=\"field\"><label>TELEFONO</label><input id=\"pfPhone\" value=\"${esc(PROFILE.telefono||'')}\"></div><button class=\"btn teal full\" onclick=\"saveProfile()\">Salva profilo</button><button class=\"btn outline full\" style=\"margin-top:8px\" onclick=\"logout()\">Esci dall'account</button></div><div class=\"notice green\" style=\"margin-top:10px\">✓ Profilo, richieste e missioni sono salvati online in modo sicuro.</div>`}"
new="function renderProfile(){let pushState=tcvPushStatusText();profile.innerHTML=`<div class=\"pagehead\"><div class=\"k\">PROFILO</div><h2>${esc(PROFILE.nome||'Profilo')}</h2><p>${esc(SESSION.user.email||'')}</p></div><div class=\"req\"><div class=\"field\"><label>NOME</label><input id=\"pfName\" value=\"${esc(PROFILE.nome||'')}\"></div><div class=\"field\"><label>TELEFONO</label><input id=\"pfPhone\" value=\"${esc(PROFILE.telefono||'')}\"></div><button class=\"btn teal full\" onclick=\"saveProfile()\">Salva profilo</button><button class=\"btn outline full\" style=\"margin-top:8px\" onclick=\"logout()\">Esci dall'account</button></div><div class=\"req\" style=\"margin-top:10px\"><h3>🔔 Notifiche richieste</h3><p id=\"pushProfileStatus\">${esc(pushState)}</p><button class=\"btn primary full\" style=\"margin-top:9px\" onclick=\"tcvEnablePush(true)\">Attiva notifiche</button><button class=\"btn outline full\" style=\"margin-top:7px\" onclick=\"tcvDisablePush()\">Disattiva su questo telefono</button></div><div class=\"notice green\" style=\"margin-top:10px\">✓ Profilo, richieste e missioni sono salvati online in modo sicuro.</div>`}"
if old not in s: raise SystemExit('renderProfile block not found')
s=s.replace(old,new,1)

marker="/* TCV_PWA_SHELL_V1 */"
push_code=r'''/* TCV_WEB_PUSH_V1 */
function tcvUrlBase64ToUint8Array(base64String){
  const padding='='.repeat((4-base64String.length%4)%4),base64=(base64String+padding).replace(/-/g,'+').replace(/_/g,'/');
  const raw=atob(base64);return Uint8Array.from([...raw].map(c=>c.charCodeAt(0)))
}
function tcvPushStatusText(){
  if(!('Notification' in window)||!('serviceWorker' in navigator)||!('PushManager' in window))return 'Notifiche push non supportate su questo dispositivo/browser.';
  if(Notification.permission==='denied')return 'Notifiche bloccate nelle impostazioni del telefono/browser.';
  if(Notification.permission==='granted')return 'Notifiche consentite su questo telefono.';
  return 'Notifiche non ancora attivate.'
}
async function tcvSavePushSubscription(sub){
  const json=sub.toJSON(),keys=json.keys||{};
  const row={user_id:SESSION.user.id,endpoint:sub.endpoint,p256dh:keys.p256dh,auth_key:keys.auth,user_agent:navigator.userAgent,enabled:true,updated_at:new Date().toISOString()};
  const {error}=await db.from('push_subscriptions').upsert(row,{onConflict:'endpoint'});if(error)throw error
}
async function tcvEnablePush(fromProfile=false){
  try{
    if(!SESSION)throw new Error('Accedi prima di attivare le notifiche.');
    if(!('Notification' in window)||!('serviceWorker' in navigator)||!('PushManager' in window))throw new Error('Notifiche push non supportate su questo dispositivo/browser.');
    let permission=Notification.permission;
    if(permission!=='granted')permission=await Notification.requestPermission();
    if(permission!=='granted'){if(permission==='denied')localStorage.setItem('tcv_push_prompt_v1','denied');return false}
    const reg=await navigator.serviceWorker.ready;
    let sub=await reg.pushManager.getSubscription();
    if(!sub){const {data:key,error}=await db.rpc('get_push_public_key');if(error||!key)throw error||new Error('Chiave notifiche non disponibile');sub=await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:tcvUrlBase64ToUint8Array(key)})}
    await tcvSavePushSubscription(sub);localStorage.setItem('tcv_push_prompt_v1','enabled');
    if(fromProfile){alert('Notifiche attivate su questo telefono.');renderProfile()}
    return true
  }catch(e){if(fromProfile)alert('Notifiche: '+e.message);console.warn(e);return false}
}
async function tcvDisablePush(){
  try{
    const reg=await navigator.serviceWorker.ready,sub=await reg.pushManager.getSubscription();
    if(sub){await db.from('push_subscriptions').delete().eq('endpoint',sub.endpoint);await sub.unsubscribe()}
    localStorage.setItem('tcv_push_prompt_v1','disabled');alert('Notifiche disattivate su questo telefono.');renderProfile()
  }catch(e){alert('Non riesco a disattivare le notifiche: '+e.message)}
}
function tcvMaybeOfferPush(){
  if(!SESSION||!('Notification' in window)||Notification.permission==='denied')return;
  let state='';try{state=localStorage.getItem('tcv_push_prompt_v1')||''}catch(e){}
  if(state)return;
  openSheet(`${head('NOTIFICHE','Vuoi ricevere le nuove richieste?','Se accetti, il telefono ti avvisa con la normale notifica di sistema anche quando Tanto Ci Vai non è aperta.')}<div class="notice green" style="margin-top:10px">🔔 Puoi disattivarle in qualsiasi momento dal Profilo o dalle impostazioni del telefono.</div><div class="rowbtn" style="margin-top:10px"><button class="btn outline" onclick="localStorage.setItem('tcv_push_prompt_v1','later');closeSheet()">Non ora</button><button class="btn primary" onclick="tcvEnablePush(false).then(ok=>{if(ok)closeSheet()})">Attiva notifiche</button></div>`)
}
function tcvOpenRequestById(id){if(!id||!SESSION)return;let r=REQUESTS.find(x=>x.id===id);if(r)openRequestDetails(id)}
function tcvOpenRequestFromUrl(){try{let u=new URL(location.href),id=u.searchParams.get('request');if(id){tcvOpenRequestById(id);u.searchParams.delete('request');history.replaceState({},'',u.pathname+u.search+u.hash)}}catch(e){}}
navigator.serviceWorker?.addEventListener('message',event=>{if(event.data?.type==='TCV_OPEN_REQUEST')tcvOpenRequestById(event.data.request_id)});

'''
if marker not in s: raise SystemExit('PWA marker not found')
s=s.replace(marker,push_code+marker,1)
s=s.replace("navigator.serviceWorker.register('./sw.js?v=1'", "navigator.serviceWorker.register('./sw.js?v=2'",1)

if s==original: raise SystemExit('No changes applied')
p.write_text(s,encoding='utf-8')
print('Push notifications patch applied')
