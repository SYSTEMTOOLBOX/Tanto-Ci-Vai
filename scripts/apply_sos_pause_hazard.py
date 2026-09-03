from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s
marker = '/* TCV_SOS_V5_PAUSE_HAZARD */'

if marker in s:
    print('SOS pause/hazard patch already applied')
    raise SystemExit(0)

css = r'''
/* TCV_SOS_V5_PAUSE_HAZARD */
.sos-pause{width:100%;min-height:55px;border:2px solid #d5a126;border-radius:18px;background:#fff8df;color:#684c00;font-size:13px;font-weight:950}
.hazard-note{margin:10px 0;padding:11px 12px;border-radius:15px;background:#eef7ff;border:1px solid #cfe2f6;color:#315b7d;font-size:10px;line-height:1.45}
.hazard-presets{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0 12px}.hazard-preset{border:1px solid #e6d39a;background:#fffaf0;border-radius:15px;min-height:62px;padding:9px 7px;font-size:21px;font-weight:900;color:var(--ink)}.hazard-preset b{display:block;font-size:9px;margin-top:3px;line-height:1.2}.hazard-preset.chosen{background:#fff0bd;border-color:#d6a92d}.hazard-map{height:285px;border-radius:18px;overflow:hidden;border:1px solid var(--line);margin:10px 0}.hazard-target{padding:10px 11px;border-radius:14px;background:#f7faff;border:1px solid #dfe8f4;font-size:9px;line-height:1.45}.hazard-target.ok{background:#effff8;border-color:#d5f4e8;color:#316b58}
@media(max-width:380px){.hazard-presets{grid-template-columns:1fr}.hazard-preset{min-height:56px}}
'''
if '</style>' not in s:
    raise SystemExit('style close tag not found')
s = s.replace('</style>', css + '</style>', 1)

# Add a calm pause/report button to the armed SOS sheet.
actions_old = '<div class="sos-big-actions"><button class="sos-send-now" onclick="tcvSendSosNow(false)">🆘 INVIA SUBITO</button>'
actions_new = '<div class="sos-big-actions"><button class="sos-pause" onclick="tcvPauseSosForReport()">⏸ FERMA COUNTDOWN / SEGNALA CON CALMA</button><button class="sos-send-now" onclick="tcvSendSosNow(false)">🆘 INVIA SUBITO</button>'
if actions_old not in s:
    raise SystemExit('SOS actions anchor not found')
s = s.replace(actions_old, actions_new, 1)

# Track the arm/cancel race and a dedicated hazard map.
state_old = 'let TCV_SOS_ARMED=false,TCV_SOS_ALERT_ID=null,TCV_SOS_DEADLINE=0,TCV_SOS_TIMER=null,TCV_SOS_POS=null,TCV_SOS_MESSAGE_TIMER=null,TCV_SOS_SENDING=false,TCV_SOS_LAST_AUTO_ATTEMPT=0;\nlet TCV_OTHER_HELP_POS=null,TCV_OTHER_HELP_MAP=null,TCV_OTHER_HELP_MARKER=null;'
state_new = 'let TCV_SOS_ARMED=false,TCV_SOS_ALERT_ID=null,TCV_SOS_DEADLINE=0,TCV_SOS_TIMER=null,TCV_SOS_POS=null,TCV_SOS_MESSAGE_TIMER=null,TCV_SOS_SENDING=false,TCV_SOS_LAST_AUTO_ATTEMPT=0,TCV_SOS_PAUSING=false;\nlet TCV_OTHER_HELP_POS=null,TCV_OTHER_HELP_MAP=null,TCV_OTHER_HELP_MARKER=null;\nlet TCV_HAZARD_POS=null,TCV_HAZARD_MAP=null,TCV_HAZARD_MARKER=null;'
if state_old not in s:
    raise SystemExit('SOS state anchor not found')
s = s.replace(state_old, state_new, 1)

open_old = 'TCV_SOS_ARMED=true;TCV_SOS_ALERT_ID=null;TCV_SOS_POS=null;TCV_SOS_DEADLINE=Date.now()+30000;TCV_SOS_SENDING=false;TCV_SOS_LAST_AUTO_ATTEMPT=0;'
open_new = 'TCV_SOS_ARMED=true;TCV_SOS_ALERT_ID=null;TCV_SOS_POS=null;TCV_SOS_DEADLINE=Date.now()+30000;TCV_SOS_SENDING=false;TCV_SOS_LAST_AUTO_ATTEMPT=0;TCV_SOS_PAUSING=false;'
if open_old not in s:
    raise SystemExit('SOS open anchor not found')
s = s.replace(open_old, open_new, 1)

# If the user pauses in the fraction of a second while ARM is still returning,
# cancel that server-side alarm immediately when its id arrives.
arm_old = "const {data,error}=await db.functions.invoke('send-help-push',{body:{action:'arm'}});if(error)throw error;if(data?.error)throw new Error(data.error);\n    TCV_SOS_ALERT_ID=data?.alert_id||null;if(data?.send_at){const d=Date.parse(data.send_at);if(Number.isFinite(d))TCV_SOS_DEADLINE=d}\n    if(TCV_SOS_POS)await tcvSyncPendingSos();"
arm_new = "const {data,error}=await db.functions.invoke('send-help-push',{body:{action:'arm'}});if(error)throw error;if(data?.error)throw new Error(data.error);\n    const armedId=data?.alert_id||null;\n    if(TCV_SOS_PAUSING){if(armedId){try{await db.functions.invoke('send-help-push',{body:{action:'cancel',alert_id:armedId}})}catch(e){console.warn('late SOS cancel failed',e)}}TCV_SOS_PAUSING=false;return}\n    TCV_SOS_ALERT_ID=armedId;if(data?.send_at){const d=Date.parse(data.send_at);if(Number.isFinite(d))TCV_SOS_DEADLINE=d}\n    if(TCV_SOS_POS)await tcvSyncPendingSos();"
if arm_old not in s:
    raise SystemExit('SOS ARM response anchor not found')
s = s.replace(arm_old, arm_new, 1)

# Make sure a failed ARM clears the pending-pause guard too.
catch_old = "}catch(e){const st=document.getElementById('sosStatus');if(st)st.innerHTML=`⚠️ Il conto alla rovescia resta attivo su questo telefono, ma il salvataggio di sicurezza sul server non è riuscito: ${esc(e?.message||String(e))}`}"
catch_new = "}catch(e){if(TCV_SOS_PAUSING){TCV_SOS_PAUSING=false;return}const st=document.getElementById('sosStatus');if(st)st.innerHTML=`⚠️ Il conto alla rovescia resta attivo su questo telefono, ma il salvataggio di sicurezza sul server non è riuscito: ${esc(e?.message||String(e))}`}"
if catch_old not in s:
    raise SystemExit('SOS ARM catch anchor not found')
s = s.replace(catch_old, catch_new, 1)

fn_anchor = 'async function tcvOpenOtherHelp(){'
if fn_anchor not in s:
    raise SystemExit('other help function anchor not found')

hazard_functions = r'''async function tcvPauseSosForReport(){
  if(TCV_SOS_SENDING)return;
  const st=document.getElementById('sosStatus');if(st)st.textContent='⏸ Fermo il countdown e annullo l’invio automatico…';
  TCV_SOS_PAUSING=true;clearInterval(TCV_SOS_TIMER);TCV_SOS_TIMER=null;
  try{
    if(TCV_SOS_ALERT_ID){const {data,error}=await db.functions.invoke('send-help-push',{body:{action:'cancel',alert_id:TCV_SOS_ALERT_ID}});if(error)throw error;if(data?.error)throw new Error(data.error);if(data?.cancelled===false)throw new Error('L’SOS non è più annullabile');TCV_SOS_PAUSING=false}
    TCV_SOS_ARMED=false;TCV_SOS_ALERT_ID=null;TCV_SOS_SENDING=false;tcvLockSosOverlay(false);tcvOpenHazardReport()
  }catch(e){
    TCV_SOS_PAUSING=false;TCV_SOS_ARMED=true;clearInterval(TCV_SOS_TIMER);TCV_SOS_TIMER=setInterval(tcvSosTick,250);
    if(st)st.innerHTML=`⚠️ Non riesco a fermare con certezza l'SOS: ${esc(e?.message||String(e))}. Il countdown resta attivo.`
  }
}
function tcvOpenHazardReport(){
  TCV_HAZARD_POS=null;if(TCV_HAZARD_MAP){try{TCV_HAZARD_MAP.remove()}catch(e){}TCV_HAZARD_MAP=null;TCV_HAZARD_MARKER=null}
  openSheet(`<div class="sos-panel"><div class="sos-kicker">SEGNALAZIONE ALLA COMUNITÀ</div><h2 class="sos-title">⚠️ Segnala un pericolo</h2><div class="hazard-note"><b>✓ Countdown fermato.</b> Qui non parte più nulla automaticamente: puoi compilare con calma e inviare solo quando sei pronto.</div><p class="sos-copy">Indica cosa c'è e tocca direttamente il punto sulla mappa. La segnalazione avviserà gli utenti con notifiche attive e aprirà il punto sulla mappa.</p><div class="hazard-presets"><button class="hazard-preset" onclick="tcvHazardPreset('Animale in carreggiata',this)">🐗<b>Animale in strada</b></button><button class="hazard-preset" onclick="tcvHazardPreset('Albero o ostacolo sulla carreggiata',this)">🌳<b>Albero / ostacolo</b></button><button class="hazard-preset" onclick="tcvHazardPreset('Strada allagata o acqua sulla carreggiata',this)">🌊<b>Strada allagata</b></button><button class="hazard-preset" onclick="tcvHazardPreset('Buca o dissesto pericoloso',this)">🕳️<b>Buca / dissesto</b></button><button class="hazard-preset" onclick="tcvHazardPreset('Incidente o veicolo fermo sulla carreggiata',this)">🚧<b>Incidente / veicolo</b></button><button class="hazard-preset" onclick="tcvHazardPreset('Altro pericolo sulla strada',this)">⚠️<b>Altro pericolo</b></button></div><div class="field"><label>COSA VUOI SEGNALARE?</label><textarea id="hazardMessage" rows="3" maxlength="180" placeholder="Es. cinghiale fermo in mezzo alla carreggiata"></textarea></div><div class="grid2"><div class="field"><label>CITTÀ / FRAZIONE</label><input id="hazardCity" placeholder="Es. Lauriano"></div><div class="field"><label>VIA / STRADA</label><input id="hazardStreet" placeholder="Es. SP 590"></div></div><div class="field"><label>NUMERO / RIFERIMENTO · FACOLTATIVO</label><input id="hazardCivic" placeholder="Es. vicino al km 12"></div><div class="rowbtn"><button class="btn primary" onclick="tcvSearchHazardAddress()">🔎 Cerca sulla mappa</button><button class="btn outline" onclick="tcvUseGpsForHazard()">📍 Usa mia posizione</button></div><div id="hazardMap" class="hazard-map"></div><div id="hazardTarget" class="hazard-target">👆 Tocca la mappa nel punto esatto del pericolo.</div><div id="hazardStatus" class="notice yellow" style="margin-top:9px">Nessuna segnalazione è stata ancora inviata.</div><button class="sos-send-now" style="margin-top:10px;background:#d58b00" onclick="tcvSendHazard()">⚠️ INVIA SEGNALAZIONE</button><button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi senza inviare</button></div>`);
  setTimeout(tcvInitHazardMap,100)
}
function tcvHazardPreset(text,btn){const ta=document.getElementById('hazardMessage');if(ta)ta.value=text;document.querySelectorAll('.hazard-preset').forEach(x=>x.classList.remove('chosen'));if(btn)btn.classList.add('chosen')}
function tcvInitHazardMap(){
  const el=document.getElementById('hazardMap');if(!el||typeof L==='undefined')return;
  if(TCV_HAZARD_MAP){try{TCV_HAZARD_MAP.remove()}catch(e){}}
  const start=TCV_SOS_POS?[TCV_SOS_POS.lat,TCV_SOS_POS.lng]:[45.1,7.8],zoom=TCV_SOS_POS?14:7;
  TCV_HAZARD_MAP=L.map('hazardMap').setView(start,zoom);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(TCV_HAZARD_MAP);
  if(TCV_SOS_POS)tcvSetHazardPoint({...TCV_SOS_POS});
  TCV_HAZARD_MAP.on('click',async e=>{let p={lat:e.latlng.lat,lng:e.latlng.lng,label:''};try{p=await reverseGeocodePoint(p)}catch(err){}tcvSetHazardPoint(p)});setTimeout(()=>TCV_HAZARD_MAP.invalidateSize(),120)
}
function tcvSetHazardPoint(p){
  TCV_HAZARD_POS=p;if(TCV_HAZARD_MAP){if(TCV_HAZARD_MARKER)TCV_HAZARD_MARKER.setLatLng([p.lat,p.lng]);else TCV_HAZARD_MARKER=L.marker([p.lat,p.lng]).addTo(TCV_HAZARD_MAP);TCV_HAZARD_MAP.setView([p.lat,p.lng],17)}
  const box=document.getElementById('hazardTarget');if(box){box.classList.add('ok');box.innerHTML=`✓ Pericolo segnato qui: <b>${esc(p.label||`${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}`)}</b>`}
}
async function tcvSearchHazardAddress(){
  const city=document.getElementById('hazardCity')?.value.trim()||'',street=document.getElementById('hazardStreet')?.value.trim()||'',civic=document.getElementById('hazardCivic')?.value.trim()||'',st=document.getElementById('hazardStatus');if(!city||!street){if(st)st.textContent='Inserisci almeno città e strada, oppure tocca direttamente la mappa.';return}if(st)st.textContent='Cerco il punto…';
  try{const full=[street,civic].filter(Boolean).join(' '),p=await geocodeDeliveryAddress(city,full);tcvSetHazardPoint({...p,label:canonicalDeliveryLabel(full,city)});if(st)st.textContent='✓ Punto trovato. Puoi spostarlo toccando la mappa.'}catch(e){if(st)st.textContent='Non trovo bene quel punto: tocca direttamente la mappa.'}
}
async function tcvUseGpsForHazard(){
  const st=document.getElementById('hazardStatus');if(st)st.textContent='Cerco la posizione del telefono…';try{let p=await currentPosition();try{p=await reverseGeocodePoint(p)}catch(e){}tcvSetHazardPoint(p);if(st)st.textContent='✓ Posizione del telefono impostata. Tocca la mappa se il pericolo è più avanti.'}catch(e){if(st)st.textContent='GPS non disponibile: cerca l’indirizzo o tocca la mappa.'}
}
async function tcvSendHazard(){
  const st=document.getElementById('hazardStatus'),msg=document.getElementById('hazardMessage')?.value.trim()||'';if(!msg){if(st)st.textContent='Scrivi o scegli che tipo di pericolo vuoi segnalare.';return}if(!TCV_HAZARD_POS){if(st)st.textContent='Prima indica sulla mappa dove si trova il pericolo.';return}if(st)st.textContent='⚠️ Invio segnalazione…';
  try{const {data,error}=await db.functions.invoke('send-help-push',{body:{action:'hazard',message:msg,lat:TCV_HAZARD_POS.lat,lng:TCV_HAZARD_POS.lng,location_label:TCV_HAZARD_POS.label||''}});if(error)throw error;if(data?.error)throw new Error(data.error);if(st)st.innerHTML=`✓ <b>Pericolo segnalato.</b> Notifiche recapitate: ${Number(data?.sent||0)}.`}catch(e){if(st)st.textContent='Segnalazione non riuscita: '+(e?.message||e)}
}
'''
s = s.replace(fn_anchor, hazard_functions + fn_anchor, 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('SOS pause + calm hazard reporting with clickable map applied')
