from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
marker = '/* TCV_SOS_V3 */'
if marker in s:
    print('SOS v3 already applied')
    raise SystemExit(0)

old_help = '<button class="urgent-help" onclick="openCommunityHelp()"><div class="sosico">🆘</div><div><b>AIUTO</b><span>Invia una richiesta urgente di aiuto alla comunità.</span></div><div class="sosarrow">→</div></button>'
if old_help not in s:
    raise SystemExit('Current help button not found')
s = s.replace(old_help, '', 1)

home_anchor = '<main id="home"><section class="hero">'
if home_anchor not in s:
    raise SystemExit('Home anchor not found')
new_help = '<main id="home"><button class="urgent-help" onclick="openCommunityHelp()"><div class="sosico">🆘</div><div><b>AIUTO SUBITO</b><span>1 tocco · prende il GPS · se non annulli parte automaticamente tra 60 secondi</span></div><div class="sosarrow">→</div></button><section class="hero">'
s = s.replace(home_anchor, new_help, 1)

css = r'''
/* TCV_SOS_V3 */
.urgent-help{margin:4px 0 15px;min-height:112px;border-radius:29px;padding:18px 20px;background:linear-gradient(135deg,#b90f2f,#ef334f);box-shadow:0 16px 34px rgba(185,15,47,.30);border:3px solid rgba(255,255,255,.92)}
.urgent-help .sosico{width:70px;height:70px;border-radius:22px;font-size:38px;background:rgba(255,255,255,.20);box-shadow:inset 0 0 0 2px rgba(255,255,255,.16)}
.urgent-help b{font-size:27px;line-height:1;letter-spacing:-.04em}.urgent-help span{font-size:11px;line-height:1.45;margin-top:7px;font-weight:800}.urgent-help .sosarrow{font-size:30px}
.sos-panel{padding:2px 0 8px}.sos-kicker{font-size:10px;font-weight:950;letter-spacing:.12em;color:#c51f35}.sos-title{font-size:29px;line-height:1.02;letter-spacing:-.045em;margin:5px 0 6px}.sos-copy{font-size:11px;line-height:1.5;color:var(--muted);margin:0}
.sos-countdown{margin:14px 0;padding:18px;border-radius:24px;background:#fff1f3;border:2px solid #f3b3be;text-align:center}.sos-countdown strong{display:block;font-size:52px;line-height:1;color:#b90f2f;letter-spacing:-.06em}.sos-countdown span{display:block;margin-top:6px;font-size:11px;font-weight:900;color:#863243}
.sos-gps{display:flex;align-items:center;gap:10px;padding:12px 13px;border-radius:16px;background:#f6f9fd;border:1px solid var(--line);font-size:10px;line-height:1.45}.sos-gps.ok{background:#effff8;border-color:#ccebdc;color:#21664f}.sos-gps .dot{width:12px;height:12px;border-radius:50%;background:#e6a12f;flex:0 0 auto}.sos-gps.ok .dot{background:#20ad69}
.sos-big-actions{display:grid;gap:9px;margin-top:12px}.sos-send-now{width:100%;min-height:58px;border:0;border-radius:18px;background:#c51f35;color:#fff;font-size:15px;font-weight:950}.sos-cancel{width:100%;min-height:54px;border:2px solid #b8c5d8;border-radius:18px;background:#fff;color:#182846;font-size:14px;font-weight:950}.sos-other{width:100%;min-height:52px;border:1px solid #cdd9ea;border-radius:17px;background:#eef5ff;color:#1e5a9c;font-size:12px;font-weight:950}.sos-112{display:block;text-align:center;text-decoration:none;margin-top:10px;padding:13px;border-radius:16px;background:#071a3d;color:#fff;font-weight:950;font-size:13px}
.help-other-map{height:260px;border-radius:18px;overflow:hidden;border:1px solid var(--line);margin:10px 0}.help-target{padding:11px 12px;border-radius:15px;background:#effff8;border:1px solid #d5f4e8;color:#316b58;font-size:10px;line-height:1.45;margin:8px 0}
@media (max-width:420px){.urgent-help{min-height:106px;padding:16px}.urgent-help .sosico{width:64px;height:64px}.urgent-help b{font-size:24px}.urgent-help span{font-size:10px}}
'''
s = s.replace('</style>', css + '</style>', 1)

js = r'''
// TCV SOS V3: one-tap, 60-second automatic fallback, GPS and third-person help.
let TCV_SOS_ARMED=false,TCV_SOS_ALERT_ID=null,TCV_SOS_DEADLINE=0,TCV_SOS_TIMER=null,TCV_SOS_POS=null,TCV_SOS_MESSAGE_TIMER=null,TCV_SOS_SENDING=false;
let TCV_OTHER_HELP_POS=null,TCV_OTHER_HELP_MAP=null,TCV_OTHER_HELP_MARKER=null;

function tcvLockSosOverlay(lock){
  const ov=document.getElementById('ov');if(!ov)return;
  if(lock){ov.onclick=null;ov.style.cursor='default'}else{ov.onclick=closeSheet;ov.style.cursor=''}
}
function tcvSosSeconds(){return Math.max(0,Math.ceil((TCV_SOS_DEADLINE-Date.now())/1000))}
function tcvRenderSosSheet(){
  const sec=tcvSosSeconds();
  openSheet(`<div class="sos-panel"><div class="sos-kicker">SOS DELLA COMUNITÀ</div><h2 class="sos-title">🆘 AIUTO SUBITO</h2><p class="sos-copy">Non devi compilare niente. Da questo momento l'SOS è attivo: se non lo annulli, tra un minuto viene inviata la tua posizione agli utenti con le notifiche attive.</p><div class="notice yellow" style="margin-top:10px"><b>Emergenza medica o pericolo immediato?</b> Chiama sempre il <b>112</b>. Tanto Ci Vai non sostituisce i soccorsi ufficiali.</div><div class="sos-countdown"><strong id="sosSeconds">${sec}</strong><span id="sosCountdownText">secondi prima dell'invio automatico</span></div><div id="sosGpsBox" class="sos-gps ${TCV_SOS_POS?'ok':''}"><span class="dot"></span><div id="sosGpsText">${TCV_SOS_POS?`GPS acquisito · ${esc(TCV_SOS_POS.label||'posizione pronta')}`:'Sto cercando la posizione GPS…'}</div></div><div class="field"><label>COSA SUCCEDE? · FACOLTATIVO</label><textarea id="sosMessage" rows="2" maxlength="180" placeholder="Puoi lasciare vuoto" oninput="tcvSosMessageChanged()"></textarea></div><div id="sosStatus" class="notice green">✓ SOS armato. Per fermarlo devi premere <b>ANNULLA SOS</b>.</div><div class="sos-big-actions"><button class="sos-send-now" onclick="tcvSendSosNow(false)">🆘 INVIA SUBITO</button><button class="sos-cancel" onclick="tcvCancelSos()">ANNULLA SOS</button><button class="sos-other" onclick="tcvOpenOtherHelp()">📍 AIUTO PER UN'ALTRA PERSONA</button></div><a class="sos-112" href="tel:112">📞 CHIAMA 112</a></div>`);
  tcvLockSosOverlay(true);
}
async function openCommunityHelp(){
  if(TCV_SOS_ARMED){tcvRenderSosSheet();tcvUpdateSosUi();return}
  TCV_SOS_ARMED=true;TCV_SOS_ALERT_ID=null;TCV_SOS_POS=null;TCV_SOS_DEADLINE=Date.now()+60000;TCV_SOS_SENDING=false;
  tcvRenderSosSheet();
  clearInterval(TCV_SOS_TIMER);TCV_SOS_TIMER=setInterval(tcvSosTick,250);
  tcvAcquireSosGps();
  try{
    const {data,error}=await db.functions.invoke('send-help-push',{body:{action:'arm'}});if(error)throw error;if(data?.error)throw new Error(data.error);
    TCV_SOS_ALERT_ID=data?.alert_id||null;if(data?.send_at){const d=Date.parse(data.send_at);if(Number.isFinite(d))TCV_SOS_DEADLINE=d}
    if(TCV_SOS_POS)await tcvSyncPendingSos();
  }catch(e){const st=document.getElementById('sosStatus');if(st)st.innerHTML=`⚠️ Il conto alla rovescia resta attivo su questo telefono, ma il salvataggio di sicurezza sul server non è riuscito: ${esc(e?.message||String(e))}`}
}
function tcvSosTick(){
  tcvUpdateSosUi();
  if(TCV_SOS_ARMED&&tcvSosSeconds()<=0&&!TCV_SOS_SENDING)tcvSendSosNow(true)
}
function tcvUpdateSosUi(){
  const n=document.getElementById('sosSeconds');if(n)n.textContent=String(tcvSosSeconds());
  const g=document.getElementById('sosGpsBox'),t=document.getElementById('sosGpsText');if(g&&TCV_SOS_POS)g.classList.add('ok');if(t&&TCV_SOS_POS)t.textContent='GPS acquisito · '+(TCV_SOS_POS.label||`${TCV_SOS_POS.lat.toFixed(5)}, ${TCV_SOS_POS.lng.toFixed(5)}`)
}
async function tcvAcquireSosGps(){
  for(let attempt=0;attempt<3&&TCV_SOS_ARMED&&!TCV_SOS_POS;attempt++){
    try{let p=await currentPosition();try{p=await reverseGeocodePoint(p)}catch(e){}TCV_SOS_POS=p;tcvUpdateSosUi();await tcvSyncPendingSos();return}catch(e){if(attempt<2)await new Promise(r=>setTimeout(r,8000))}
  }
  const t=document.getElementById('sosGpsText');if(t&&!TCV_SOS_POS)t.textContent='GPS non disponibile: controlla che il permesso Posizione sia attivo. L’SOS partirà comunque.'
}
async function tcvSyncPendingSos(){
  if(!TCV_SOS_ALERT_ID)return;
  const msg=document.getElementById('sosMessage')?.value.trim()||'';
  const body={action:'update_pending',alert_id:TCV_SOS_ALERT_ID,message:msg};
  if(TCV_SOS_POS){body.lat=TCV_SOS_POS.lat;body.lng=TCV_SOS_POS.lng;body.location_label=TCV_SOS_POS.label||''}
  try{await db.functions.invoke('send-help-push',{body})}catch(e){}
}
function tcvSosMessageChanged(){clearTimeout(TCV_SOS_MESSAGE_TIMER);TCV_SOS_MESSAGE_TIMER=setTimeout(()=>tcvSyncPendingSos(),600)}
async function tcvSendSosNow(automatic=false){
  if(TCV_SOS_SENDING)return;TCV_SOS_SENDING=true;
  const st=document.getElementById('sosStatus');if(st)st.textContent=automatic?'🆘 Tempo scaduto: invio automatico in corso…':'🆘 Invio SOS in corso…';
  const msg=document.getElementById('sosMessage')?.value.trim()||'';
  const body={action:'send_now',alert_id:TCV_SOS_ALERT_ID||undefined,message:msg};if(TCV_SOS_POS){body.lat=TCV_SOS_POS.lat;body.lng=TCV_SOS_POS.lng;body.location_label=TCV_SOS_POS.label||''}
  try{
    const {data,error}=await db.functions.invoke('send-help-push',{body});if(error)throw error;if(data?.error)throw new Error(data.error);
    TCV_SOS_ARMED=false;clearInterval(TCV_SOS_TIMER);TCV_SOS_TIMER=null;tcvLockSosOverlay(false);
    openSheet(`<div class="sos-panel"><div class="sos-kicker">SOS INVIATO</div><h2 class="sos-title">✓ Aiuto richiesto</h2><div class="notice green">La richiesta è partita agli utenti con notifiche attive${TCV_SOS_POS?' con la tua posizione GPS':''}. Notifiche recapitate: <b>${Number(data?.sent||0)}</b>.</div><div class="notice yellow" style="margin-top:9px">Se stai male o sei in pericolo, non aspettare la comunità: chiama il <b>112</b>.</div><a class="sos-112" href="tel:112">📞 CHIAMA 112</a><button class="btn outline full" style="margin-top:9px" onclick="closeSheet()">Chiudi</button></div>`)
  }catch(e){TCV_SOS_SENDING=false;if(st)st.innerHTML=`⚠️ Non riesco a confermare l'invio: ${esc(e?.message||String(e))}. Premi INVIA SUBITO oppure chiama il 112.`}
}
async function tcvCancelSos(){
  if(!TCV_SOS_ARMED){closeSheet();return}
  const st=document.getElementById('sosStatus');if(st)st.textContent='Annullamento SOS…';
  try{
    if(TCV_SOS_ALERT_ID){const {data,error}=await db.functions.invoke('send-help-push',{body:{action:'cancel',alert_id:TCV_SOS_ALERT_ID}});if(error)throw error;if(data?.error)throw new Error(data.error);if(data?.cancelled===false&&tcvSosSeconds()<=0)throw new Error('L’SOS potrebbe essere già partito')}
    TCV_SOS_ARMED=false;clearInterval(TCV_SOS_TIMER);TCV_SOS_TIMER=null;TCV_SOS_ALERT_ID=null;tcvLockSosOverlay(false);closeSheet()
  }catch(e){if(st)st.innerHTML=`⚠️ Non riesco a confermare l'annullamento: ${esc(e?.message||String(e))}. Se l'SOS è partito, avvisa chi riceve la notifica.`}
}
async function tcvOpenOtherHelp(){
  if(TCV_SOS_ARMED&&TCV_SOS_ALERT_ID){
    try{const {error}=await db.functions.invoke('send-help-push',{body:{action:'cancel',alert_id:TCV_SOS_ALERT_ID}});if(error)throw error}catch(e){const st=document.getElementById('sosStatus');if(st)st.textContent='Non riesco ad annullare il tuo SOS automatico. Riprova prima di passare alla posizione di un’altra persona.';return}
  }
  TCV_SOS_ARMED=false;clearInterval(TCV_SOS_TIMER);TCV_SOS_TIMER=null;TCV_SOS_ALERT_ID=null;tcvLockSosOverlay(false);TCV_OTHER_HELP_POS=null;
  if(TCV_OTHER_HELP_MAP){try{TCV_OTHER_HELP_MAP.remove()}catch(e){}TCV_OTHER_HELP_MAP=null;TCV_OTHER_HELP_MARKER=null}
  openSheet(`<div class="sos-panel"><div class="sos-kicker">AIUTO PER UN'ALTRA PERSONA</div><h2 class="sos-title">📍 Indica dove serve aiuto</h2><p class="sos-copy">Per esempio: tua nonna ti chiama e tu invii l'allerta nella sua posizione. Qui l'invio non è automatico: prima scegli il punto e poi confermi.</p><div class="grid2"><div class="field"><label>CITTÀ / FRAZIONE</label><input id="helpOtherCity" placeholder="Es. Lauriano"></div><div class="field"><label>VIA</label><input id="helpOtherStreet" placeholder="Es. Via Roma"></div></div><div class="field"><label>NUMERO CIVICO</label><input id="helpOtherCivic" placeholder="Es. 12/A"></div><div class="rowbtn"><button class="btn primary" onclick="tcvSearchOtherHelpAddress()">🔎 Cerca posizione</button><button class="btn outline" onclick="tcvUseGpsForOtherHelp()">📍 Sono con lei</button></div><div id="helpOtherMap" class="help-other-map"></div><div id="helpOtherTarget" class="help-target">Tocca la mappa oppure cerca l'indirizzo.</div><div class="field"><label>COSA SUCCEDE? · FACOLTATIVO</label><textarea id="helpOtherMessage" rows="2" maxlength="180" placeholder="Es. mia nonna non risponde bene, serve qualcuno vicino"></textarea></div><div id="helpOtherStatus" class="notice yellow">Controlla bene il punto prima di inviare.</div><button class="sos-send-now" style="margin-top:10px" onclick="tcvSendOtherHelp()">🆘 INVIA AIUTO IN QUESTA POSIZIONE</button><button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Annulla</button><a class="sos-112" href="tel:112">📞 CHIAMA 112</a></div>`);
  setTimeout(tcvInitOtherHelpMap,100)
}
function tcvInitOtherHelpMap(){
  const el=document.getElementById('helpOtherMap');if(!el||typeof L==='undefined')return;
  if(TCV_OTHER_HELP_MAP){try{TCV_OTHER_HELP_MAP.remove()}catch(e){}}
  TCV_OTHER_HELP_MAP=L.map('helpOtherMap').setView([42.6,12.5],6);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(TCV_OTHER_HELP_MAP);
  TCV_OTHER_HELP_MAP.on('click',async e=>{let p={lat:e.latlng.lat,lng:e.latlng.lng,label:''};try{p=await reverseGeocodePoint(p)}catch(err){}tcvSetOtherHelpPoint(p)});setTimeout(()=>TCV_OTHER_HELP_MAP.invalidateSize(),100)
}
function tcvSetOtherHelpPoint(p){
  TCV_OTHER_HELP_POS=p;if(TCV_OTHER_HELP_MAP){if(TCV_OTHER_HELP_MARKER)TCV_OTHER_HELP_MARKER.setLatLng([p.lat,p.lng]);else TCV_OTHER_HELP_MARKER=L.marker([p.lat,p.lng]).addTo(TCV_OTHER_HELP_MAP);TCV_OTHER_HELP_MAP.setView([p.lat,p.lng],17)}
  const box=document.getElementById('helpOtherTarget');if(box)box.innerHTML=`✓ Posizione aiuto: <b>${esc(p.label||`${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}`)}</b>`
}
async function tcvSearchOtherHelpAddress(){
  const city=document.getElementById('helpOtherCity')?.value.trim()||'',street=document.getElementById('helpOtherStreet')?.value.trim()||'',civic=document.getElementById('helpOtherCivic')?.value.trim()||'',st=document.getElementById('helpOtherStatus');
  if(!city||!street){if(st)st.textContent='Inserisci almeno città e via.';return}
  if(st)st.textContent='Cerco il punto…';
  try{const full=[street,civic].filter(Boolean).join(' '),p=await geocodeDeliveryAddress(city,full);tcvSetOtherHelpPoint({...p,label:canonicalDeliveryLabel(full,city)});if(st)st.textContent='✓ Posizione trovata. Controlla il pin sulla mappa.'}catch(e){if(st)st.textContent='Non trovo bene l’indirizzo: prova a toccare direttamente la mappa.'}
}
async function tcvUseGpsForOtherHelp(){
  const st=document.getElementById('helpOtherStatus');if(st)st.textContent='Cerco la posizione del telefono…';
  try{let p=await currentPosition();try{p=await reverseGeocodePoint(p)}catch(e){}tcvSetOtherHelpPoint(p);if(st)st.textContent='✓ Posizione del telefono impostata.'}catch(e){if(st)st.textContent='GPS non disponibile. Cerca l’indirizzo o tocca la mappa.'}
}
async function tcvSendOtherHelp(){
  const st=document.getElementById('helpOtherStatus');if(!TCV_OTHER_HELP_POS){if(st)st.textContent='Prima devi indicare sulla mappa dove si trova la persona.';return}
  const msg=document.getElementById('helpOtherMessage')?.value.trim()||'';if(st)st.textContent='🆘 Invio richiesta di aiuto…';
  try{const {data,error}=await db.functions.invoke('send-help-push',{body:{action:'other',message:msg,lat:TCV_OTHER_HELP_POS.lat,lng:TCV_OTHER_HELP_POS.lng,location_label:TCV_OTHER_HELP_POS.label||''}});if(error)throw error;if(data?.error)throw new Error(data.error);if(st)st.innerHTML=`✓ <b>Aiuto inviato in quella posizione.</b> Notifiche recapitate: ${Number(data?.sent||0)}.`}catch(e){if(st)st.textContent='Invio non riuscito: '+(e?.message||e)}
}
'''

idx = s.rfind('</script>')
if idx < 0:
    raise SystemExit('Closing script tag not found')
s = s[:idx] + js + '\n' + s[idx:]
p.write_text(s, encoding='utf-8')
print('SOS v3 patch applied')
