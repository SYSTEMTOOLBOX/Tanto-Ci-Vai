from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

# 1) Show expected delivery time to both runner and sender in request cards.
old_meta = "<div class=\"meta\"><span class=\"pill money\">Compenso ${euro(r.compenso_rider)}</span><span class=\"pill\">fee app ${euro(r.commissione_app)}</span></div>"
new_meta = "<div class=\"meta\"><span class=\"pill money\">Compenso ${euro(r.compenso_rider)}</span><span class=\"pill\">fee app ${euro(r.commissione_app)}</span>${r.consegna_prevista?`<span class=\"pill\">🕒 Consegna prevista ${new Date(r.consegna_prevista).toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'})}</span>`:''}</div>"
if old_meta in s:
    s = s.replace(old_meta, new_meta, 1)

# 2) Replace mission buttons: pickup now opens ETA confirmation instead of directly changing status.
old_mission = """function missionButtons(r){
  let next=r.stato==='accettata'?'ritirata':r.stato==='ritirata'?'in_consegna':r.stato==='in_consegna'?'consegnata':null;
  let label=next==='ritirata'?'Segna ritirata':next==='in_consegna'?'Parto per consegna':next==='consegnata'?'Segna consegnata':'';
  if(!next)return '';
  return `<div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"openRunnerNavigation('${r.id}')\">🧭 Navigatore</button><button class=\"btn primary\" onclick=\"setStatus('${r.id}','${next}')\">${label}</button></div>`
}
"""
new_mission = """function missionButtons(r){
  let next=r.stato==='accettata'?'ritirata':r.stato==='ritirata'?'in_consegna':r.stato==='in_consegna'?'consegnata':null;
  let label=next==='ritirata'?'📦 Ritirato':next==='in_consegna'?'Parto per consegna':next==='consegnata'?'Segna consegnata':'';
  if(!next)return '';
  let action=next==='ritirata'?`openPickupEta('${r.id}')`:`setStatus('${r.id}','${next}')`;
  return `<div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"openRunnerNavigation('${r.id}')\">🧭 Navigatore</button><button class=\"btn primary\" onclick=\"${action}\">${label}</button></div>`
}
function localDateTimeValue(d){
  let x=new Date(d.getTime()-d.getTimezoneOffset()*60000);return x.toISOString().slice(0,16)
}
function openPickupEta(id){
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
if old_mission not in s:
    raise SystemExit('missionButtons block not found')
s = s.replace(old_mission, new_mission, 1)

# 3) Make it impossible to get stuck in the runner map sheet.
old_nav = "<div class=\"nav-actions\"><button id=\"liveNavBtn\" class=\"btn primary\" onclick=\"toggleLiveNavigation()\">▶ Avvia navigazione</button><button class=\"btn outline\" onclick=\"openRunnerExternalNavigation()\">↗ Apri in Maps</button></div>`);"
new_nav = "<div class=\"nav-actions\"><button id=\"liveNavBtn\" class=\"btn primary\" onclick=\"toggleLiveNavigation()\">▶ Avvia navigazione</button><button class=\"btn outline\" onclick=\"openRunnerExternalNavigation()\">↗ Apri in Maps</button></div><button class=\"btn outline full\" style=\"margin-top:9px\" onclick=\"stopLiveNavigation();closeSheet()\">← Esci dalla mappa</button>`);"
if old_nav not in s:
    raise SystemExit('runner navigation actions block not found')
s = s.replace(old_nav, new_nav, 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Runner UX patch applied')
