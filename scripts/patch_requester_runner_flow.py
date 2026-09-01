from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

def replace_between(start, end, new_block):
    global s
    a = s.find(start)
    if a < 0:
        raise SystemExit(f'start marker not found: {start}')
    b = s.find(end, a)
    if b < 0:
        raise SystemExit(f'end marker not found: {end}')
    s = s[:a] + new_block.rstrip() + '\n' + s[b:]

old_decl = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SELECTED_PLACE=null,HOME_POS=null,FAVORITES=[],NAV_MAP=null,NAV_ROUTE_LAYER=null,NAV_WATCH=null,NAV_ROUTE=null,NAV_MODE='car',NAV_MARKER=null;"
new_decl = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SELECTED_PLACE=null,HOME_POS=null,SEARCH_POS=null,FAVORITES=[],NAV_MAP=null,NAV_ROUTE_LAYER=null,NAV_WATCH=null,NAV_ROUTE=null,NAV_MODE='car',NAV_MARKER=null,NAV_REQUEST=null;"
if old_decl in s:
    s = s.replace(old_decl, new_decl, 1)
elif 'SEARCH_POS=null' not in s:
    raise SystemExit('state declaration changed unexpectedly')

replace_between('function card(r){', 'function openSheet(html){', r'''function card(r){
  let mine=r.cliente_id===SESSION.user.id,assigned=r.rider_id===SESSION.user.id;
  let notes=esc(r.descrizione||'').replace(/\n/g,'<br>');
  return `<article class="req"><div class="reqhead"><span class="kind ${mine?'mine':''}">${mine?'MIA RICHIESTA':assigned?'MISSIONE':'DISPONIBILE'}</span><span class="dist">${esc(r.stato)}</span></div><h3>${esc(r.titolo)}</h3>${notes?`<p>${notes}</p>`:''}<div class="route"><div><small>RITIRO</small><br>${esc(r.ritiro_indirizzo)}</div><div><small>CONSEGNA</small><br>${esc(r.consegna_indirizzo)}</div></div><div class="meta"><span class="pill money">Compenso ${euro(r.compenso_rider)}</span><span class="pill">fee app ${euro(r.commissione_app)}</span></div>${!mine&&r.stato==='disponibile'?`<div class="rowbtn"><button class="btn outline" onclick="openRequestDetails('${r.id}')">Apri richiesta</button><button class="btn teal" onclick="acceptRequest('${r.id}')">Tanto ci vai?</button></div>`:''}${assigned?missionButtons(r):''}${mine&&r.stato==='disponibile'?`<button class="btn danger full" style="margin-top:10px" onclick="setStatus('${r.id}','annullata')">Annulla richiesta</button>`:''}</article>`
}
function missionButtons(r){
  let next=r.stato==='accettata'?'ritirata':r.stato==='ritirata'?'in_consegna':r.stato==='in_consegna'?'consegnata':null;
  let label=next==='ritirata'?'Segna ritirata':next==='in_consegna'?'Parto per consegna':next==='consegnata'?'Segna consegnata':'';
  if(!next)return '';
  return `<div class="rowbtn"><button class="btn outline" onclick="openRunnerNavigation('${r.id}')">🧭 Navigatore</button><button class="btn primary" onclick="setStatus('${r.id}','${next}')">${label}</button></div>`
}
function openRequestDetails(id){
  let r=REQUESTS.find(x=>x.id===id);if(!r)return;
  let mine=r.cliente_id===SESSION.user.id,assigned=r.rider_id===SESSION.user.id;
  let notes=esc(r.descrizione||'').replace(/\n/g,'<br>');
  let action=!mine&&r.stato==='disponibile'?`<button class="btn teal full" style="margin-top:10px" onclick="acceptRequest('${r.id}')">Tanto ci vai? · Prendi richiesta</button>`:assigned?`<button class="btn primary full" style="margin-top:10px" onclick="openRunnerNavigation('${r.id}')">🧭 Apri navigatore runner</button>`:'';
  openSheet(`${head('DETTAGLI RICHIESTA',r.titolo,'Prima di accettare vedi ritiro, consegna e tutte le note.')}${notes?`<div class="notice" style="margin-top:10px"><b>NOTE</b><br>${notes}</div>`:''}<div class="route"><div><small>1 · RITIRO</small><br>${esc(r.ritiro_indirizzo)}</div><div><small>2 · CONSEGNA</small><br>${esc(r.consegna_indirizzo)}</div></div><div class="meta"><span class="pill money">Compenso ${euro(r.compenso_rider)}</span><span class="pill">${esc(r.categoria||'commissione')}</span></div>${action}`)
}
''')

replace_between('function openNewRequest(step=1){', 'function distanceKm(a,b){', r'''function openNewRequest(step=1){
  if(step===1){
    openSheet(`${head('NUOVA RICHIESTA','Di cosa hai bisogno?','Per Farmacia puoi usare il GPS oppure cercare una città o frazione diversa da dove ti trovi.')}<div class="choices">${[
      ['spesa','🛒','Spesa','Piccola spesa o prodotti già pronti'],
      ['farmacia','💊','Farmacia','GPS oppure città/frazione · raggio 15 km'],
      ['ritiro','📦','Ritiro','Pacco, documento o altro ritiro'],
      ['altro','🤝','Altro','Una piccola commissione locale']
    ].map(x=>`<button class="choice" onclick="chooseRequestCategory('${x[0]}')"><span class="em">${x[1]}</span><b>${x[2]}</b><small>${x[3]}</small></button>`).join('')}</div>`);return
  }
  const presets={spesa:['Ritirare una spesa','Es. cosa ritirare, nominativo, dettagli utili'],farmacia:['Ritiro in farmacia','Es. ordine già pronto, nominativo al banco, numero ordine'],ritiro:['Ritirare un pacco','Es. pacco, documento o ordine da ritirare'],altro:['Piccola commissione','Descrivi cosa bisogna fare']};
  let pr=presets[REQUEST_CATEGORY]||presets.altro;
  let fromValue=SELECTED_PLACE?(SELECTED_PLACE.address||SELECTED_PLACE.name):'';
  let pharmacyNote=REQUEST_CATEGORY==='farmacia'&&SELECTED_PLACE?`<div class="pharmacy-location">💊 <b>${esc(SELECTED_PLACE.name)}</b><br>${esc(SELECTED_PLACE.address||'Farmacia selezionata')} · ${SELECTED_PLACE.distance.toFixed(1)} km dalla zona cercata</div>`:'';
  openSheet(`${head('NUOVA RICHIESTA',pr[0],'Il runner vedrà chiaramente persona, ritiro, note e indirizzo finale.')}${pharmacyNote}<div class="kind" style="display:inline-block;margin-top:10px">${REQUEST_CATEGORY.toUpperCase()}</div><div class="field"><label>PER CHI È LA COMMISSIONE?</label><input id="nrPerson" placeholder="Es. Signora Maria"></div><div class="field"><label>TITOLO</label><input id="nrTitle" value="${pr[0]}"></div><div class="field"><label>NOTE PER IL RUNNER / PUNTO DI RITIRO</label><textarea id="nrDesc" rows="3" placeholder="${pr[1]}"></textarea></div><div class="field"><label>DOVE RITIRARE</label><input id="nrFrom" value="${esc(fromValue)}" placeholder="Indirizzo completo o luogo" ${SELECTED_PLACE?'readonly':''}></div><div class="field"><label>INDIRIZZO DI CONSEGNA</label><input id="nrTo" value="" placeholder="Es. Via Roma 12, Lauriano (TO)"></div><button class="gpsbtn" onclick="fillDeliveryWithGps()">📍 Usa il GPS per questo indirizzo di consegna</button><div class="field"><label>COMPENSO RIDER</label><select id="nrPay"><option value="3.5">€ 3,50</option><option value="4" selected>€ 4,00</option><option value="5">€ 5,00</option><option value="6">€ 6,00</option></select></div><div id="nrStatus" class="notice green">Il navigatore sarà disponibile al runner dopo che avrà preso la richiesta: posizione runner → ritiro → consegna.</div><div class="backrow"><button class="btn outline" onclick="openNewRequest(1)">← Tipo</button><button class="btn teal" onclick="publishRequest()">Pubblica richiesta</button></div>`)
}
''')

replace_between('async function loadPharmaciesAt(pos){', 'async function searchPharmaciesByText(){', r'''async function loadPharmaciesAt(pos){
  SEARCH_POS=await reverseGeocodePoint(pos);
  let status=document.getElementById('pharmacyStatus');if(status)status.textContent='Cerco le farmacie più vicine…';
  PHARMACY_RESULTS=await fetchNearbyPharmacies(SEARCH_POS);
  await loadFavoritePharmacies();
  if(status)status.innerHTML=`📍 Zona scelta: <b>${esc(SEARCH_POS.area||SEARCH_POS.label||'posizione indicata')}</b> · ${PHARMACY_RESULTS.length} farmacie entro 15 km`;
  let mapEl=document.getElementById('pharmacyMap');if(mapEl)mapEl.classList.remove('hidden');
  initPharmacyMap(SEARCH_POS);renderPharmacyList()
}
async function openPharmacyFinder(){
  REQUEST_CATEGORY='farmacia';SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;
  openSheet(`${head('FARMACIE VICINE','Dove devo cercare?','Puoi essere anche lontanissimo dalla persona che stai aiutando: scegli il GPS oppure scrivi la sua città o frazione.')}<button class="gpsbtn" onclick="searchPharmaciesByGps()">📍 Usa la posizione GPS di questo telefono</button><div class="place-fallback"><input id="pharmacyTown" placeholder="Oppure scrivi città o frazione · es. Lauriano Po"><button class="btn outline" onclick="searchPharmaciesByText()">Cerca</button></div><div id="pharmacyStatus" class="pharmacy-location">Raggio di ricerca: 15 km dalla posizione scelta.</div><div id="pharmacyMap" class="place-map hidden"></div><div id="pharmacyList" class="place-list"></div>`)
}
async function searchPharmaciesByGps(){
  let st=document.getElementById('pharmacyStatus');if(st)st.textContent='Rilevo il GPS…';
  try{let pos=await currentPosition();await loadPharmaciesAt(pos)}catch(e){if(st)st.textContent='GPS non disponibile o non autorizzato. Puoi sempre scrivere città o frazione.'}
}
''')

replace_between('function selectPharmacy(i){', 'function routeModeLabel(mode){', r'''function selectPharmacy(i){
  SELECTED_PLACE=PHARMACY_RESULTS[i];if(!SELECTED_PLACE)return;openNewRequest(2)
}
''')

replace_between('async function publishRequest(){', 'async function acceptRequest(id){', r'''async function publishRequest(){
  let person=nrPerson.value.trim(),title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),to=nrTo.value.trim(),pay=+nrPay.value;
  if(!person||!title||!from||!to){nrStatus.textContent='Compila nome della persona, titolo, ritiro e indirizzo di consegna.';return}
  nrStatus.textContent='Preparo coordinate e pubblico…';
  try{
    let a=(REQUEST_CATEGORY==='farmacia'&&SELECTED_PLACE)?{lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng,label:SELECTED_PLACE.address||SELECTED_PLACE.name}:await geocode(from);
    let homeLabel=HOME_POS?(HOME_POS.label||`${HOME_POS.lat.toFixed(6)},${HOME_POS.lng.toFixed(6)}`):'';
    let b=(HOME_POS&&to===homeLabel)?{lat:HOME_POS.lat,lng:HOME_POS.lng,label:HOME_POS.label||to}:await geocode(to);
    let fullDesc=`Per: ${person}${desc?`\nNote: ${desc}`:''}`;
    let {error}=await db.from('consegne').insert({cliente_id:SESSION.user.id,categoria:REQUEST_CATEGORY,titolo:title,descrizione:fullDesc,ritiro_indirizzo:a.label,ritiro_lat:a.lat,ritiro_lng:a.lng,consegna_indirizzo:b.label,consegna_lat:b.lat,consegna_lng:b.lng,compenso_rider:pay});if(error)throw error;
    await loadRequests();renderAll();closeSheet();SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;alert('Richiesta pubblicata nel database.')
  }catch(e){nrStatus.textContent='Errore: '+e.message}
}
''')

# Replace acceptRequest so detail sheet closes after successful acceptance.
replace_between('async function acceptRequest(id){', 'async function setStatus(id,status){', r'''async function acceptRequest(id){
  if(!confirm('Vuoi prendere questa commissione?'))return;
  let {data,error}=await db.rpc('accetta_consegna',{p_consegna_id:id});
  if(error){alert(error.message);return}if(!data){alert('Questa richiesta è già stata presa da qualcun altro.');return}
  await loadRequests();renderAll();closeSheet();page('missions')
}
''')

# Insert runner-only navigator before delivery GPS helper.
anchor = 'async function fillDeliveryWithGps(){'
if 'function openRunnerNavigation(id){' not in s:
    a = s.find(anchor)
    if a < 0:
        raise SystemExit('runner navigation anchor not found')
    runner = r'''function openRunnerNavigation(id){
  let r=REQUESTS.find(x=>x.id===id);if(!r)return;
  if(r.rider_id!==SESSION.user.id){alert('Il navigatore è disponibile solo al runner che ha preso la richiesta.');return}
  NAV_REQUEST=r;stopLiveNavigation();
  let notes=esc(r.descrizione||'').replace(/\n/g,'<br>');
  openSheet(`${head('NAVIGATORE RUNNER',r.titolo,'Percorso completo: dalla tua posizione al ritiro, poi alla consegna.')}<div class="notice" style="margin-top:10px">${notes||'Nessuna nota'}</div><div class="route"><div><small>1 · RITIRO</small><br>${esc(r.ritiro_indirizzo)}</div><div><small>2 · CONSEGNA</small><br>${esc(r.consegna_indirizzo)}</div></div><div class="nav-modes"><button id="runner-mode-car" class="nav-mode on" onclick="calculateRunnerRoute('car')">🚗 Auto</button><button id="runner-mode-foot" class="nav-mode" onclick="calculateRunnerRoute('foot')">🚶 A piedi</button><button id="runner-mode-bike" class="nav-mode" onclick="calculateRunnerRoute('bike')">🚲 Bici</button></div><div id="runnerRouteStatus" class="notice green">📍 Rilevo la posizione del runner…</div><div id="smartRouteMap" class="route-map"></div><div id="routeSummary"></div><div id="routeSteps" class="nav-steps"></div><div id="liveNavStatus" class="nav-live">GPS pronto. Premi Avvia navigazione per seguire la tua posizione.</div><div class="nav-actions"><button id="liveNavBtn" class="btn primary" onclick="toggleLiveNavigation()">▶ Avvia navigazione</button><button class="btn outline" onclick="openRunnerExternalNavigation()">↗ Apri in Maps</button></div>`);
  calculateRunnerRoute('car')
}
async function fetchRunnerRoute(start,r,mode){
  let points=[start,{lat:+r.ritiro_lat,lng:+r.ritiro_lng},{lat:+r.consegna_lat,lng:+r.consegna_lng}];
  let coords=points.map(p=>`${p.lng},${p.lat}`).join(';');
  let url=routeBase(mode)+coords+'?overview=full&geometries=geojson&steps=true&alternatives=false';
  let res=await fetch(url);if(!res.ok)throw new Error('Servizio percorso non disponibile');
  let j=await res.json();if(j.code!=='Ok'||!j.routes?.length)throw new Error('Percorso non trovato');return j.routes[0]
}
function drawRunnerRoute(start,r,route){
  if(NAV_MAP){NAV_MAP.remove();NAV_MAP=null}
  NAV_MAP=L.map('smartRouteMap').setView([start.lat,start.lng],13);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(NAV_MAP);
  L.circleMarker([start.lat,start.lng],{radius:9,weight:4,fillOpacity:.95}).addTo(NAV_MAP).bindPopup('Runner · sei qui');
  L.marker([r.ritiro_lat,r.ritiro_lng]).addTo(NAV_MAP).bindPopup(`<b>1 · RITIRO</b><br>${esc(r.ritiro_indirizzo)}`);
  L.marker([r.consegna_lat,r.consegna_lng]).addTo(NAV_MAP).bindPopup(`<b>2 · CONSEGNA</b><br>${esc(r.consegna_indirizzo)}`);
  let latlngs=(route.geometry?.coordinates||[]).map(c=>[c[1],c[0]]);
  if(latlngs.length){NAV_ROUTE_LAYER=L.polyline(latlngs,{weight:6,opacity:.88}).addTo(NAV_MAP);NAV_MAP.fitBounds(NAV_ROUTE_LAYER.getBounds(),{padding:[24,24]})}
  setTimeout(()=>NAV_MAP?.invalidateSize(),100)
}
async function calculateRunnerRoute(mode){
  if(!NAV_REQUEST)return;
  NAV_MODE=mode;['car','foot','bike'].forEach(m=>document.getElementById('runner-mode-'+m)?.classList.toggle('on',m===mode));
  stopLiveNavigation();let st=document.getElementById('runnerRouteStatus');if(st)st.textContent=`${routeModeIcon(mode)} Calcolo percorso completo…`;
  try{
    let start=await currentPosition();NAV_ROUTE=await fetchRunnerRoute(start,NAV_REQUEST,mode);drawRunnerRoute(start,NAV_REQUEST,NAV_ROUTE);renderRouteSteps(NAV_ROUTE);
    let sum=document.getElementById('routeSummary');if(sum)sum.innerHTML=`<div class="nav-summary"><div><b>${fmtDistance(NAV_ROUTE.distance)}</b><span>DISTANZA TOTALE · ${routeModeIcon(mode)} ${routeModeLabel(mode)}</span></div><div><b>${fmtDuration(NAV_ROUTE.duration)}</b><span>TEMPO STIMATO</span></div></div>`;
    if(st)st.innerHTML='✓ Percorso pronto: <b>tu → ritiro → consegna</b>.'
  }catch(e){if(st)st.textContent='Errore percorso: '+e.message}
}
function openRunnerExternalNavigation(){
  let r=NAV_REQUEST;if(!r)return;
  let mode=NAV_MODE==='car'?'driving':NAV_MODE==='foot'?'walking':'bicycling';
  let url=`https://www.google.com/maps/dir/?api=1&destination=${r.consegna_lat},${r.consegna_lng}&waypoints=${r.ritiro_lat},${r.ritiro_lng}&travelmode=${mode}`;
  window.open(url,'_blank','noopener')
}
'''
    s = s[:a] + runner + s[a:]

p.write_text(s, encoding='utf-8')
print('requester/runner flow patched')
