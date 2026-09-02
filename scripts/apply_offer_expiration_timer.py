from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(label + ' anchor not found')
    s = s.replace(old, new, 1)

replace_once(
    "const requestOpen=r=>r.stato==='disponibile'&&(!r.consegna_entro||new Date(r.consegna_entro).getTime()>Date.now());",
    """const offerExpiresAt=r=>r.offerta_scade_il?new Date(r.offerta_scade_il).getTime():Infinity;
const requestOpen=r=>r.stato==='disponibile'&&offerExpiresAt(r)>Date.now()&&(!r.consegna_entro||new Date(r.consegna_entro).getTime()>Date.now());
function offerCountdown(r){
  if(!r?.offerta_scade_il)return '';
  let ms=offerExpiresAt(r)-Date.now();
  if(ms<=0)return '⌛ Offerta scaduta';
  let total=Math.ceil(ms/60000),h=Math.floor(total/60),m=total%60;
  return h?`⏳ Scade tra ${h}h${m?` ${m}m`:''}`:`⏳ Scade tra ${m}m`
}""",
    'requestOpen'
)

replace_once(
    "async function loadRequests(){feedStatus.textContent='Aggiorno…';let {data,error}=await db.from('consegne').select('*').order('created_at',{ascending:false});if(error){feedStatus.textContent='Errore sync';throw error}REQUESTS=data||[];feedStatus.textContent='Sincronizzate'}",
    "async function loadRequests(){feedStatus.textContent='Aggiorno…';try{await db.rpc('scadi_offerte')}catch(e){}let {data,error}=await db.from('consegne').select('*').order('created_at',{ascending:false});if(error){feedStatus.textContent='Errore sync';throw error}REQUESTS=data||[];feedStatus.textContent='Sincronizzate'}",
    'loadRequests'
)

replace_once(
    "async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');await ensureProfile();await loadRequests();subscribeRealtime();renderAll()}",
    "async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');await ensureProfile();await loadRequests();subscribeRealtime();renderAll();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000)}",
    'afterLogin'
)

replace_once(
    '<div class="field"><label>CONSEGNA ENTRO (MASSIMO)</label><input id="nrDeadline" type="datetime-local" value="${localDateTimeValue(new Date(Date.now()+2*60*60000))}"',
    '<div class="field"><label>PER QUANTO RESTA ATTIVA L\'OFFERTA?</label><select id="nrOfferHours"><option value="2">2 ore</option><option value="3" selected>3 ore</option><option value="4">4 ore</option></select><div class="notice" style="margin-top:7px">⏳ Se nessun runner la accetta entro questo tempo, l\'offerta scade automaticamente.</div></div><div class="field"><label>CONSEGNA ENTRO (MASSIMO)</label><input id="nrDeadline" type="datetime-local" value="${localDateTimeValue(new Date(Date.now()+4*60*60000))}"',
    'request form deadline'
)

replace_once(
    "let person=nrPerson.value.trim(),title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),pickupNumber=document.getElementById('nrPickupNumber')?.value.trim()||'',city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',deadlineValue=document.getElementById('nrDeadline')?.value||'',pay=+nrPay.value;",
    "let person=nrPerson.value.trim(),title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),pickupNumber=document.getElementById('nrPickupNumber')?.value.trim()||'',city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',deadlineValue=document.getElementById('nrDeadline')?.value||'',offerHours=+(document.getElementById('nrOfferHours')?.value||3),pay=+nrPay.value;",
    'publish variables'
)

replace_once(
    "let deadline=new Date(deadlineValue);if(!Number.isFinite(deadline.getTime())||deadline.getTime()<Date.now()+15*60000){nrStatus.textContent='La consegna massima deve essere almeno 15 minuti nel futuro.';return}",
    "let deadline=new Date(deadlineValue);if(!Number.isFinite(deadline.getTime())||deadline.getTime()<Date.now()+15*60000){nrStatus.textContent='La consegna massima deve essere almeno 15 minuti nel futuro.';return}if(![2,3,4].includes(offerHours))offerHours=3;let offerExpires=new Date(Date.now()+offerHours*60*60000);if(offerExpires>=deadline)offerExpires=new Date(Math.max(Date.now()+15*60000,deadline.getTime()-5*60000));",
    'deadline validation'
)

replace_once(
    "consegna_entro:deadline.toISOString(),compenso_rider:pay",
    "consegna_entro:deadline.toISOString(),offerta_scade_il:offerExpires.toISOString(),compenso_rider:pay",
    'insert payload'
)

replace_once(
    "  let mine=r.cliente_id===SESSION.user.id,assigned=r.rider_id===SESSION.user.id;\n",
    "  let mine=r.cliente_id===SESSION.user.id,assigned=r.rider_id===SESSION.user.id;\n  let expiredOffer=r.stato==='scaduta'||(r.stato==='disponibile'&&r.offerta_scade_il&&offerExpiresAt(r)<=Date.now()),statusLabel=expiredOffer?'scaduta':r.stato;\n",
    'card variables'
)

replace_once(
    '<span class="dist">${esc(r.stato)}</span>',
    '<span class="dist">${esc(statusLabel)}</span>',
    'card status'
)

replace_once(
    '<span class="pill">fee app ${euro(r.commissione_app)}</span>${r.consegna_entro?',
    '<span class="pill">fee app ${euro(r.commissione_app)}</span>${r.offerta_scade_il?`<span class="pill">${offerCountdown(r)}</span>`:``}${r.consegna_entro?',
    'card meta'
)

replace_once("${!mine&&r.stato==='disponibile'?", "${!mine&&requestOpen(r)?", 'card accept')
replace_once("${mine&&r.stato==='disponibile'?", "${mine&&requestOpen(r)?", 'card cancel')

replace_once(
    '<span class="pill">${esc(r.categoria||\'commissione\')}</span>${r.consegna_entro?',
    '<span class="pill">${esc(r.categoria||\'commissione\')}</span>${r.offerta_scade_il?`<span class="pill">${offerCountdown(r)}</span>`:``}${r.consegna_entro?',
    'details meta'
)

replace_once(
    '<div class="meta"><span class="pill money">${euro(r.compenso_rider)}</span>${r.consegna_entro?',
    '<div class="meta"><span class="pill money">${euro(r.compenso_rider)}</span>${r.offerta_scade_il?`<span class="pill">${offerCountdown(r)}</span>`:``}${r.consegna_entro?',
    'map offer meta'
)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Offer expiration timer UI applied')
