from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')

# State for SOS / hazard markers shown on the community map.
if 'COMMUNITY_ALERTS=[]' not in text:
    text = text.replace('WALLET_ENTRIES=[],WALLET_YEAR_ROW=null;', 'WALLET_ENTRIES=[],WALLET_YEAR_ROW=null,COMMUNITY_ALERTS=[];', 1)

# Clear, high-contrast markers + large post-send confirmation screen.
css_marker = '/* TCV_COMMUNITY_ALERT_MAP_V1 */'
if css_marker not in text:
    css = r'''
/* TCV_COMMUNITY_ALERT_MAP_V1 */
.map-community-legend{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 12px}.map-community-legend span{display:flex;align-items:center;gap:6px;padding:7px 10px;border:1px solid var(--line);border-radius:999px;background:#fff;font-size:9px;font-weight:950}.map-key-dot{width:14px;height:14px;border-radius:50%;display:inline-block;border:2px solid #fff;box-shadow:0 0 0 1px rgba(7,26,61,.16)}.map-key-dot.pickup{background:#3388ff}.map-key-dot.hazard{background:#f5c400}.map-key-dot.help{background:#d92132}.community-marker-wrap{background:transparent!important;border:0!important}.community-marker{width:46px;height:46px;border-radius:50%;display:grid;place-items:center;font-size:23px;border:4px solid #fff;box-shadow:0 7px 20px rgba(7,26,61,.32);font-weight:950}.community-marker.hazard{background:#f5c400;color:#332700}.community-marker.help{background:#d92132;color:#fff;animation:tcvHelpPulse 1.35s infinite}.community-popup{min-width:210px;line-height:1.35}.community-popup b{font-size:13px}.community-popup .where{font-size:10px;color:#53627c;margin-top:5px}.community-popup .msg{font-size:11px;margin-top:6px}.community-popup button{width:100%;border:0;border-radius:10px;padding:9px;margin-top:8px;background:#0b66ff;color:#fff;font-weight:900}@keyframes tcvHelpPulse{0%,100%{box-shadow:0 7px 20px rgba(217,33,50,.25),0 0 0 0 rgba(217,33,50,.30)}50%{box-shadow:0 7px 20px rgba(217,33,50,.36),0 0 0 10px rgba(217,33,50,0)}}
.tcv-alert-success{text-align:center;padding:24px 4px 12px;min-height:56vh;display:flex;flex-direction:column;justify-content:center}.tcv-alert-success-icon{width:132px;height:132px;border-radius:50%;display:grid;place-items:center;margin:0 auto 18px;font-size:62px;border:7px solid #fff;box-shadow:0 15px 34px rgba(7,26,61,.16)}.tcv-alert-success.hazard .tcv-alert-success-icon{background:#f5c400}.tcv-alert-success.help .tcv-alert-success-icon{background:#d92132;color:#fff}.tcv-alert-success .big-kicker{font-size:11px;letter-spacing:.14em;font-weight:950;margin-bottom:7px}.tcv-alert-success h2{font-size:34px;line-height:1.02;letter-spacing:-.045em;margin:0 auto 10px;max-width:480px}.tcv-alert-success p{font-size:13px;line-height:1.5;color:var(--muted);max-width:470px;margin:0 auto 18px}.tcv-success-home{width:100%;border:0;border-radius:18px;padding:17px 14px;background:linear-gradient(135deg,var(--blue),#277bff);color:#fff;font-size:16px;font-weight:950}.tcv-success-map{width:100%;border:1px solid var(--line);border-radius:18px;padding:15px 14px;background:#fff;color:var(--ink);font-size:14px;font-weight:950;margin-top:9px}
'''
    text = text.replace('</style>', css + '\n</style>', 1)

# Large, explicit confirmation view shared by hazard / other-help / SOS sends.
if 'function tcvShowAlertSuccess(kind)' not in text:
    helper = r'''
function tcvGoHomeAfterAlert(){closeSheet();page('home')}
function tcvGoMapAfterAlert(){closeSheet();page('mapPage')}
function tcvShowAlertSuccess(kind){
  const hazard=kind==='hazard',sos=kind==='sos';
  COMMUNITY_ALERTS=[];
  const icon=hazard?'⚠️':'🆘';
  const kicker=hazard?'SEGNALAZIONE INVIATA':(sos?'SOS INVIATO':'RICHIESTA INVIATA');
  const title=hazard?'PERICOLO SEGNALATO':(sos?'SOS INVIATO':'RICHIESTA D’AIUTO INVIATA');
  const copy=hazard?'Il punto è stato pubblicato sulla mappa della comunità. Gli utenti vedranno un indicatore giallo di attenzione.':'La posizione è stata pubblicata sulla mappa della comunità con un indicatore rosso di assistenza immediata.';
  const emergency=hazard?'':`<div class="notice yellow" style="margin:0 auto 14px;max-width:470px"><b>Se è un’emergenza reale chiama sempre il 112.</b> La comunità non sostituisce i soccorsi ufficiali.</div><a class="sos-112" href="tel:112" style="margin-bottom:10px">📞 CHIAMA 112</a>`;
  openSheet(`<div class="tcv-alert-success ${hazard?'hazard':'help'}"><div class="tcv-alert-success-icon">${icon}</div><div class="big-kicker">${kicker}</div><h2>${title}</h2><p>${copy}</p>${emergency}<button class="tcv-success-home" onclick="tcvGoHomeAfterAlert()">🏠 VAI ALLA HOME</button><button class="tcv-success-map" onclick="tcvGoMapAfterAlert()">⌖ VEDI SULLA MAPPA</button></div>`)
}

'''
    text = text.replace('function tcvLockSosOverlay(lock){', helper + 'function tcvLockSosOverlay(lock){', 1)

# Hazard success: replace the tiny technical delivery-count message with the large confirmation.
old_hazard = "if(error)throw error;if(data?.error)throw new Error(data.error);if(st)st.innerHTML=`✓ <b>Pericolo segnalato.</b> Notifiche recapitate: ${Number(data?.sent||0)}.`"
new_hazard = "if(error)throw error;if(data?.error)throw new Error(data.error);tcvShowAlertSuccess('hazard')"
if old_hazard in text:
    text = text.replace(old_hazard, new_hazard, 1)

# Third-person help success.
old_other = "if(error)throw error;if(data?.error)throw new Error(data.error);if(st)st.innerHTML=`✓ <b>Aiuto inviato in quella posizione.</b> Notifiche recapitate: ${Number(data?.sent||0)}.`"
new_other = "if(error)throw error;if(data?.error)throw new Error(data.error);tcvShowAlertSuccess('help')"
if old_other in text:
    text = text.replace(old_other, new_other, 1)

# Self SOS success.
old_sos = "openSheet(`<div class=\"sos-panel\"><div class=\"sos-kicker\">SOS INVIATO</div><h2 class=\"sos-title\">✓ Aiuto richiesto</h2><div class=\"notice green\">La richiesta è partita agli utenti con notifiche attive${TCV_SOS_POS?' con la tua posizione GPS':''}. Notifiche recapitate: <b>${Number(data?.sent||0)}</b>.</div><div class=\"notice yellow\" style=\"margin-top:9px\">Se stai male o sei in pericolo, non aspettare la comunità: chiama il <b>112</b>.</div><a class=\"sos-112\" href=\"tel:112\">📞 CHIAMA 112</a><button class=\"btn outline full\" style=\"margin-top:9px\" onclick=\"closeSheet()\">Chiudi</button></div>`)"
if old_sos in text:
    text = text.replace(old_sos, "tcvShowAlertSuccess('sos')", 1)

# Clean up the stale armed-status copy now that the countdown can also be paused for a calm report.
text = text.replace('✓ SOS armato. Per fermarlo devi premere <b>ANNULLA SOS</b>.', '✓ SOS armato. Puoi inviarlo subito, annullarlo oppure fermare il countdown per compilare con calma.', 1)

# Replace the map renderer: pickups remain blue; hazards are yellow; urgent assistance is red.
map_pattern = re.compile(r"function renderMapPage\(\)\{.*?\n\}\nfunction focusRequest\(id\)\{", re.S)
map_replacement = r'''async function loadCommunityAlerts(){
  const st=document.getElementById('mapAlertStatus');
  try{
    if(st)st.textContent='Aggiorno pericoli e richieste di aiuto…';
    const {data,error}=await db.functions.invoke('get-community-alerts',{body:{}});if(error)throw error;if(data?.error)throw new Error(data.error);
    COMMUNITY_ALERTS=Array.isArray(data?.alerts)?data.alerts.filter(a=>Number.isFinite(+a.lat)&&Number.isFinite(+a.lng)):[];
    const hazards=COMMUNITY_ALERTS.filter(a=>a.kind==='hazard').length,helps=COMMUNITY_ALERTS.length-hazards;
    if(st)st.innerHTML=`Aggiornata ora · <b>${hazards}</b> pericoli · <b>${helps}</b> richieste di assistenza`;
  }catch(e){COMMUNITY_ALERTS=[];if(st)st.textContent='Ritiri aggiornati. Avvisi comunità momentaneamente non disponibili.';console.warn('Community alerts map',e)}
}
function communityAlertIcon(kind){
  const hazard=kind==='hazard';
  return L.divIcon({className:'community-marker-wrap',html:`<div class="community-marker ${hazard?'hazard':'help'}">${hazard?'⚠':'🆘'}</div>`,iconSize:[46,46],iconAnchor:[23,23],popupAnchor:[0,-25]})
}
function openCommunityAlertMaps(lat,lng){
  const url=`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${lat},${lng}`)}&dir_action=navigate`;
  window.open(url,'_blank')
}
function communityAlertPopup(a){
  const hazard=a.kind==='hazard',title=hazard?'⚠️ PERICOLO SEGNALATO':'🆘 ASSISTENZA IMMEDIATA';
  const msg=String(a.message||'').trim()||(hazard?'Pericolo segnalato dalla comunità':'Richiesta urgente di aiuto');
  const where=String(a.location_label||'').trim();
  return `<div class="community-popup"><b>${title}</b><div class="msg">${esc(msg)}</div>${where?`<div class="where">📍 ${esc(where)}</div>`:''}<div class="where">Segnalato da ${esc(a.sender_name||'un utente')}</div><button onclick="openCommunityAlertMaps(${Number(a.lat)},${Number(a.lng)})">🧭 INDICAZIONI</button></div>`
}
function renderMapPage(){
  mapPage.innerHTML=`<div class="pagehead"><div class="k">MAPPA LIVE</div><h2>Mappa della comunità</h2><p>Qui vedi ritiri, pericoli segnalati e richieste di assistenza immediata.</p></div><div class="map-community-legend"><span><i class="map-key-dot pickup"></i> Ritiro</span><span><i class="map-key-dot hazard"></i> Attenzione / pericolo</span><span><i class="map-key-dot help"></i> Assistenza immediata</span></div><div id="mapAlertStatus" class="notice" style="margin-bottom:9px">Aggiorno la mappa…</div><button class="gpsbtn" onclick="locateMe()">📍 Aggiorna la mia posizione</button><div class="map-shell"><div id="map"></div><button id="mapPlanChip" class="map-plan-chip hidden" onclick="expandMapPlanPanel()">🧭 Giro</button><div id="mapPlanPanel" class="map-plan-sheet hidden"></div></div>`;
  loadCommunityAlerts().finally(()=>setTimeout(()=>{initMap();setTimeout(recalculateMapPlan,100)},60))
}
function initMap(){
  if(MAP){MAP.remove();MAP=null}MAP_PLAN_ROUTE_LAYER=null;MAP=L.map('map').setView([45.18,7.99],11);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(MAP);let pts=[];
  REQUESTS.filter(r=>requestOpen(r)&&r.cliente_id!==SESSION.user.id&&r.ritiro_lat&&r.ritiro_lng).forEach(r=>{let ll=[r.ritiro_lat,r.ritiro_lng];pts.push(ll);let marker=L.marker(ll).addTo(MAP);let inPlan=MAP_PLAN_IDS.includes(r.id);marker.bindTooltip(`📦 ${inPlan?'✓ ':''}${esc(r.titolo)} · ${euro(r.compenso_rider)}`,{direction:'top'});marker.on('click',()=>openMapOffer(r.id))});
  COMMUNITY_ALERTS.forEach(a=>{const ll=[Number(a.lat),Number(a.lng)];pts.push(ll);L.marker(ll,{icon:communityAlertIcon(a.kind),zIndexOffset:a.kind==='hazard'?700:1000}).addTo(MAP).bindPopup(communityAlertPopup(a),{maxWidth:290})});
  if(USER_POS){L.circleMarker([USER_POS.lat,USER_POS.lng],{radius:8,weight:4,fillOpacity:.9}).addTo(MAP).bindPopup('La tua posizione')}
  if(pts.length&&!MAP_PLAN_IDS.length)MAP.fitBounds(pts,{padding:[30,30],maxZoom:14})
}
function focusRequest(id){'''
text2, n = map_pattern.subn(lambda m: map_replacement, text, count=1)
if n != 1:
    if 'function communityAlertIcon(kind)' not in text:
        raise SystemExit(f'Could not replace map renderer: matches={n}')
    text2 = text
text = text2

# Force devices to re-check the updated app shell / service worker registration.
text = re.sub(r"sw\.js\?v=\d+", "sw.js?v=6", text)

path.write_text(text, encoding='utf-8')
print('Applied community alert map markers and large send confirmation screens')
