from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'{label} not found')
    s = s.replace(old, new, 1)

# Availability helper: requester deadlines remove expired requests from new-runner discovery.
old = "const cleanDeliveryAddress=v=>String(v||'').replace(/,\\s*Piazzo\\s*,/gi,', ').replace(/\\s{2,}/g,' ').trim();"
new = old + "\nconst requestOpen=r=>r.stato==='disponibile'&&(!r.consegna_entro||new Date(r.consegna_entro).getTime()>Date.now());"
rep(old, new, 'availability helper anchor')

rep("function renderStats(){let uid=SESSION.user.id;statOpen.textContent=REQUESTS.filter(r=>r.stato==='disponibile').length;statMine.textContent=REQUESTS.filter(r=>r.cliente_id===uid).length;statMissions.textContent=REQUESTS.filter(r=>r.rider_id===uid&&r.stato!=='annullata').length}",
    "function renderStats(){let uid=SESSION.user.id;statOpen.textContent=REQUESTS.filter(requestOpen).length;statMine.textContent=REQUESTS.filter(r=>r.cliente_id===uid).length;statMissions.textContent=REQUESTS.filter(r=>r.rider_id===uid&&r.stato!=='annullata').length}",
    'renderStats')

rep("function renderFeed(){let uid=SESSION.user.id,arr=REQUESTS.filter(r=>r.stato==='disponibile'||r.rider_id===uid).slice(0,20);feed.innerHTML=arr.length?arr.map(card).join(''):'<div class=\"empty\">Nessuna richiesta aperta. Puoi essere il primo a pubblicarne una.</div>'}",
    "function renderFeed(){let uid=SESSION.user.id,arr=REQUESTS.filter(r=>requestOpen(r)||r.rider_id===uid).slice(0,20);feed.innerHTML=arr.length?arr.map(card).join(''):'<div class=\"empty\">Nessuna richiesta aperta. Puoi essere il primo a pubblicarne una.</div>'}",
    'renderFeed')

# Deadline shown beside compensation and runner ETA on every card.
old_meta = "<div class=\"meta\"><span class=\"pill money\">Compenso ${euro(r.compenso_rider)}</span><span class=\"pill\">fee app ${euro(r.commissione_app)}</span>${r.consegna_prevista?`<span class=\"pill\">🕒 Consegna prevista ${new Date(r.consegna_prevista).toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'})}</span>`:''}</div>"
new_meta = "<div class=\"meta\"><span class=\"pill money\">Compenso ${euro(r.compenso_rider)}</span><span class=\"pill\">fee app ${euro(r.commissione_app)}</span>${r.consegna_entro?`<span class=\"pill\">⏰ Entro ${formatDateTime(r.consegna_entro)}</span>`:''}${r.consegna_prevista?`<span class=\"pill\">🕒 Consegna prevista ${formatDateTime(r.consegna_prevista)}</span>`:''}</div>"
rep(old_meta, new_meta, 'card meta')

old_time_helper = """function localDateTimeValue(d){
  let x=new Date(d.getTime()-d.getTimezoneOffset()*60000);return x.toISOString().slice(0,16)
}
"""
new_time_helper = """function localDateTimeValue(d){
  let x=new Date(d.getTime()-d.getTimezoneOffset()*60000);return x.toISOString().slice(0,16)
}
function formatDateTime(v){
  return new Date(v).toLocaleString('it-IT',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})
}
"""
rep(old_time_helper, new_time_helper, 'time helper')

# Runner ETA respects the requester's maximum delivery time while that deadline is still achievable.
old_pickup = """function openPickupEta(id){
  let r=REQUESTS.find(x=>x.id===id);if(!r||r.rider_id!==SESSION.user.id)return;
  let suggested=new Date(Date.now()+30*60000);
  openSheet(`${head('RITIRO COMPLETATO','Pacco ritirato','Imposta l’orario previsto di consegna. Il mittente lo vedrà subito.')}<div class=\"notice green\" style=\"margin-top:10px\">📦 Confermando, la richiesta passa a <b>ritirata</b> e il mittente riceve il nuovo stato in tempo reale.</div><div class=\"field\"><label>CONSEGNA PREVISTA</label><input id=\"pickupEta\" type=\"datetime-local\" value=\"${localDateTimeValue(suggested)}\" min=\"${localDateTimeValue(new Date(Date.now()+5*60000))}\"></div><div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"closeSheet()\">Annulla</button><button class=\"btn teal\" onclick=\"confirmPickupEta('${id}')\">✓ Conferma ritirato</button></div>`)
}
async function confirmPickupEta(id){
  let el=document.getElementById('pickupEta'),eta=el?.value;if(!eta){alert('Imposta la consegna prevista.');return}
  let when=new Date(eta);if(!Number.isFinite(when.getTime())||when.getTime()<=Date.now()){alert('Scegli un orario futuro.');return}
  let {data,error}=await db.rpc('segna_ritiro_con_eta',{p_consegna_id:id,p_consegna_prevista:when.toISOString()});
  if(error){alert(error.message);return}if(!data){alert('Non posso confermare il ritiro: controlla stato e orario.');return}
  await loadRequests();renderAll();closeSheet();page('missions')
}
"""
new_pickup = """function openPickupEta(id){
  let r=REQUESTS.find(x=>x.id===id);if(!r||r.rider_id!==SESSION.user.id)return;
  let now=Date.now(),minimum=new Date(now+5*60000),suggested=new Date(now+30*60000),deadline=r.consegna_entro?new Date(r.consegna_entro):null;
  let activeDeadline=deadline&&Number.isFinite(deadline.getTime())&&deadline.getTime()>minimum.getTime();
  if(activeDeadline&&suggested.getTime()>deadline.getTime())suggested=new Date(deadline);
  let maxAttr=activeDeadline?` max=\"${localDateTimeValue(deadline)}\"`:'';
  let deadlineNotice=deadline?(activeDeadline?`<div class=\"notice yellow\" style=\"margin-top:10px\">⏰ Il mittente ha richiesto la consegna <b>entro ${formatDateTime(deadline)}</b>.</div>`:`<div class=\"notice yellow\" style=\"margin-top:10px\">⚠️ Il limite richiesto (${formatDateTime(deadline)}) è ormai scaduto o troppo vicino. Inserisci l’orario reale previsto.</div>`):'';
  openSheet(`${head('RITIRO COMPLETATO','Pacco ritirato','Imposta l’orario previsto di consegna. Il mittente lo vedrà subito.')}${deadlineNotice}<div class=\"notice green\" style=\"margin-top:10px\">📦 Confermando, la richiesta passa a <b>ritirata</b> e il mittente riceve il nuovo stato in tempo reale.</div><div class=\"field\"><label>CONSEGNA PREVISTA</label><input id=\"pickupEta\" type=\"datetime-local\" value=\"${localDateTimeValue(suggested)}\" min=\"${localDateTimeValue(minimum)}\"${maxAttr}></div><div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"closeSheet()\">Annulla</button><button class=\"btn teal\" onclick=\"confirmPickupEta('${id}')\">✓ Conferma ritirato</button></div>`)
}
async function confirmPickupEta(id){
  let r=REQUESTS.find(x=>x.id===id),el=document.getElementById('pickupEta'),eta=el?.value;if(!eta){alert('Imposta la consegna prevista.');return}
  let when=new Date(eta);if(!Number.isFinite(when.getTime())||when.getTime()<=Date.now()){alert('Scegli un orario futuro.');return}
  let deadline=r?.consegna_entro?new Date(r.consegna_entro):null;
  if(deadline&&deadline.getTime()>Date.now()&&when.getTime()>deadline.getTime()){alert('La consegna prevista non può superare il limite richiesto dal mittente: '+formatDateTime(deadline));return}
  let {data,error}=await db.rpc('segna_ritiro_con_eta',{p_consegna_id:id,p_consegna_prevista:when.toISOString()});
  if(error){alert(error.message);return}if(!data){alert('Non posso confermare il ritiro: controlla stato e orario massimo richiesto.');return}
  await loadRequests();renderAll();closeSheet();page('missions')
}
"""
rep(old_pickup, new_pickup, 'pickup ETA block')

# Details shown before acceptance include the requester's deadline.
old_details_meta = "<div class=\"meta\"><span class=\"pill money\">Compenso ${euro(r.compenso_rider)}</span><span class=\"pill\">${esc(r.categoria||'commissione')}</span></div>"
new_details_meta = "<div class=\"meta\"><span class=\"pill money\">Compenso ${euro(r.compenso_rider)}</span><span class=\"pill\">${esc(r.categoria||'commissione')}</span>${r.consegna_entro?`<span class=\"pill\">⏰ Consegna entro ${formatDateTime(r.consegna_entro)}</span>`:''}</div>"
rep(old_details_meta, new_details_meta, 'request details meta')

# Requester must set a maximum delivery deadline. Default: two hours from now.
old_pay_anchor = "</div><div class=\"field\"><label>COMPENSO RIDER</label><select id=\"nrPay\">"
new_pay_anchor = "</div><div class=\"field\"><label>CONSEGNA ENTRO (MASSIMO)</label><input id=\"nrDeadline\" type=\"datetime-local\" value=\"${localDateTimeValue(new Date(Date.now()+2*60*60000))}\" min=\"${localDateTimeValue(new Date(Date.now()+15*60000))}\"><div class=\"notice yellow\" style=\"margin-top:7px\">⏰ Il runner vedrà questo limite <b>prima di accettare</b> la richiesta.</div></div><div class=\"field\"><label>COMPENSO RIDER</label><select id=\"nrPay\">"
rep(old_pay_anchor, new_pay_anchor, 'new request deadline field')

old_publish_vars = "let person=nrPerson.value.trim(),title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',pay=+nrPay.value;"
new_publish_vars = "let person=nrPerson.value.trim(),title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',deadlineValue=document.getElementById('nrDeadline')?.value||'',pay=+nrPay.value;"
rep(old_publish_vars, new_publish_vars, 'publish vars')

old_publish_check = "if(!person||!title||!from||!city||!street){nrStatus.textContent='Compila nome della persona, ritiro, città/frazione e via di consegna.';return}\n  nrStatus.textContent='Verifico ritiro e destinazione…';"
new_publish_check = "if(!person||!title||!from||!city||!street||!deadlineValue){nrStatus.textContent='Compila nome, ritiro, destinazione e orario massimo di consegna.';return}\n  let deadline=new Date(deadlineValue);if(!Number.isFinite(deadline.getTime())||deadline.getTime()<Date.now()+15*60000){nrStatus.textContent='La consegna massima deve essere almeno 15 minuti nel futuro.';return}\n  nrStatus.textContent='Verifico ritiro e destinazione…';"
rep(old_publish_check, new_publish_check, 'publish validation')

old_insert = "consegna_indirizzo:deliveryLabel,consegna_lat:b.lat,consegna_lng:b.lng,compenso_rider:pay}"
new_insert = "consegna_indirizzo:deliveryLabel,consegna_lat:b.lat,consegna_lng:b.lng,consegna_entro:deadline.toISOString(),compenso_rider:pay}"
rep(old_insert, new_insert, 'delivery insert')

rep("if(error){alert(error.message);return}if(!data){alert('Questa richiesta è già stata presa da qualcun altro.');return}",
    "if(error){alert(error.message);return}if(!data){alert('Questa richiesta è già stata presa oppure il tempo massimo di consegna è scaduto.');return}",
    'accept error')

# Expired available requests disappear from map and route matching.
rep("REQUESTS.filter(r=>r.stato==='disponibile'&&r.ritiro_lat&&r.ritiro_lng).forEach",
    "REQUESTS.filter(r=>requestOpen(r)&&r.ritiro_lat&&r.ritiro_lng).forEach",
    'map available filter')
rep("available=REQUESTS.filter(r=>r.stato==='disponibile'&&r.cliente_id!==SESSION.user.id&&r.ritiro_lat&&r.consegna_lat)",
    "available=REQUESTS.filter(r=>requestOpen(r)&&r.cliente_id!==SESSION.user.id&&r.ritiro_lat&&r.consegna_lat)",
    'trip matching filter')

# Match cards also display the deadline before acceptance.
old_match_meta = "<span class=\"pill money\">${euro(x.r.compenso_rider)}</span></div><button class=\"btn teal full\""
new_match_meta = "<span class=\"pill money\">${euro(x.r.compenso_rider)}</span>${x.r.consegna_entro?`<span class=\"pill\">⏰ Entro ${formatDateTime(x.r.consegna_entro)}</span>`:''}</div><button class=\"btn teal full\""
rep(old_match_meta, new_match_meta, 'match deadline')

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Requester delivery deadline patch applied')
