from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

# Add map planner state.
old_state = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SHOP_MAP=null,SHOP_RESULTS=[],SHOP_FILTER='supermarket',SELECTED_PLACE=null,HOME_POS=null,SEARCH_POS=null,FAVORITES=[],NAV_MAP=null,NAV_ROUTE_LAYER=null,NAV_WATCH=null,NAV_ROUTE=null,NAV_MODE='car',NAV_MARKER=null,NAV_REQUEST=null,DELIVERY_MAP=null,DELIVERY_MARKER=null,DELIVERY_CITY_RESULTS=[],DELIVERY_STREET_RESULTS=[],DELIVERY_TIMER=null,DELIVERY_CITY_POS=null;"
new_state = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,MAP_PLAN_IDS=[],MAP_PLAN_START=null,MAP_PLAN_ROUTE=null,MAP_PLAN_ROUTE_LAYER=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SHOP_MAP=null,SHOP_RESULTS=[],SHOP_FILTER='supermarket',SELECTED_PLACE=null,HOME_POS=null,SEARCH_POS=null,FAVORITES=[],NAV_MAP=null,NAV_ROUTE_LAYER=null,NAV_WATCH=null,NAV_ROUTE=null,NAV_MODE='car',NAV_MARKER=null,NAV_REQUEST=null,DELIVERY_MAP=null,DELIVERY_MARKER=null,DELIVERY_CITY_RESULTS=[],DELIVERY_STREET_RESULTS=[],DELIVERY_TIMER=null,DELIVERY_CITY_POS=null;"
if old_state not in s:
    raise SystemExit('state declaration not found')
s = s.replace(old_state, new_state, 1)

old_map = """function renderMapPage(){mapPage.innerHTML=`<div class=\"pagehead\"><div class=\"k\">MAPPA LIVE</div><h2>Richieste disponibili</h2><p>Tocca un pin: si apre subito l'offerta completa e puoi decidere se accettarla oppure no.</p></div><button class=\"gpsbtn\" onclick=\"locateMe()\">📍 Mostra la mia posizione</button><div id=\"map\"></div>`;setTimeout(initMap,100)}
function initMap(){if(MAP){MAP.remove();MAP=null}MAP=L.map('map').setView([45.18,7.99],11);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(MAP);let pts=[];REQUESTS.filter(r=>requestOpen(r)&&r.cliente_id!==SESSION.user.id&&r.ritiro_lat&&r.ritiro_lng).forEach(r=>{let ll=[r.ritiro_lat,r.ritiro_lng];pts.push(ll);let marker=L.marker(ll).addTo(MAP);marker.bindTooltip(`${esc(r.titolo)} · ${euro(r.compenso_rider)}`,{direction:'top'});marker.on('click',()=>openRequestDetails(r.id))});if(pts.length)MAP.fitBounds(pts,{padding:[25,25],maxZoom:14})}
function focusRequest(id){let r=REQUESTS.find(x=>x.id===id);if(!r)return;page('mapPage');setTimeout(()=>{if(MAP&&r.ritiro_lat)MAP.setView([r.ritiro_lat,r.ritiro_lng],15)},250)}
function locateMe(){if(!navigator.geolocation){alert('GPS non disponibile.');return}navigator.geolocation.getCurrentPosition(pos=>{USER_POS={lat:pos.coords.latitude,lng:pos.coords.longitude};if(MAP){L.circleMarker([USER_POS.lat,USER_POS.lng],{radius:8,weight:4,fillOpacity:.9}).addTo(MAP).bindPopup('La tua posizione').openPopup();MAP.setView([USER_POS.lat,USER_POS.lng],14)}},()=>alert('Consenti la posizione al browser.'),{enableHighAccuracy:true,timeout:12000})}
"""

new_map = r'''function mapPlanRequests(extraId=null){
  let ids=[...MAP_PLAN_IDS];if(extraId&&!ids.includes(extraId))ids.push(extraId);
  return ids.map(id=>REQUESTS.find(r=>r.id===id)).filter(r=>r&&(requestOpen(r)||r.rider_id===SESSION.user.id)&&r.ritiro_lat&&r.ritiro_lng&&r.consegna_lat&&r.consegna_lng)
}
function mapPlanPoints(reqs,start=MAP_PLAN_START){
  let pts=[];if(start)pts.push({lat:start.lat,lng:start.lng});
  reqs.forEach(r=>{pts.push({lat:+r.ritiro_lat,lng:+r.ritiro_lng});pts.push({lat:+r.consegna_lat,lng:+r.consegna_lng})});
  return pts
}
async function ensureMapPlanStart(){
  if(MAP_PLAN_START)return MAP_PLAN_START;
  if(USER_POS){MAP_PLAN_START={...USER_POS};return MAP_PLAN_START}
  let pos=await currentPosition();USER_POS={lat:pos.lat,lng:pos.lng};MAP_PLAN_START={...USER_POS};return MAP_PLAN_START
}
async function mapRouteDetailed(points){
  if(points.length<2)return {distance:0,duration:0,legs:[],geometry:null};
  let coords=points.map(p=>`${p.lng},${p.lat}`).join(';');
  let res=await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson&steps=false`);
  let j=await res.json();if(j.code!=='Ok'||!j.routes?.length)throw new Error('Percorso non trovato');return j.routes[0]
}
function fmtPlanDelta(n,kind){
  if(kind==='km')return `${(n/1000).toFixed(n<10000?1:0)} km`;
  return fmtDuration(n)
}
function mapPlanArrivalInfo(routeData,reqs){
  let legs=routeData?.legs||[],cum=0,rows=[];
  reqs.forEach((r,i)=>{
    let pickupLeg=i*2,deliveryLeg=i*2+1;
    if(legs[pickupLeg])cum+=legs[pickupLeg].duration||0;
    if(legs[deliveryLeg])cum+=legs[deliveryLeg].duration||0;
    let arrival=new Date(Date.now()+cum*1000),deadline=r.consegna_entro?new Date(r.consegna_entro):null;
    rows.push({arrival,late:!!(deadline&&Number.isFinite(deadline.getTime())&&arrival>deadline),deadline})
  });
  return rows
}
function drawMapPlanRoute(routeData){
  if(!MAP)return;if(MAP_PLAN_ROUTE_LAYER){MAP.removeLayer(MAP_PLAN_ROUTE_LAYER);MAP_PLAN_ROUTE_LAYER=null}
  if(routeData?.geometry){MAP_PLAN_ROUTE_LAYER=L.geoJSON(routeData.geometry).addTo(MAP);try{MAP.fitBounds(MAP_PLAN_ROUTE_LAYER.getBounds(),{padding:[28,28],maxZoom:15})}catch(e){}}
}
function renderMapPlanPanel(routeData=MAP_PLAN_ROUTE,error=''){
  let el=document.getElementById('mapPlanPanel');if(!el)return;let reqs=mapPlanRequests();
  if(!reqs.length){el.innerHTML='<div class="notice">🎯 Tocca una richiesta sulla mappa per calcolare chilometri e tempo. Poi puoi aggiungerne altre al giro.</div>';return}
  let arrivals=routeData?mapPlanArrivalInfo(routeData,reqs):[];
  let total=routeData?`<div class="nav-summary"><div><b>${fmtDistance(routeData.distance)}</b><span>GIRO TOTALE</span></div><div><b>${fmtDuration(routeData.duration)}</b><span>TEMPO STIMATO</span></div></div>`:`<div class="notice">Calcolo percorso…</div>`;
  let rows=reqs.map((r,i)=>{let a=arrivals[i],warn=a?.late?' ⚠️ OLTRE LIMITE':'';return `<div class="req" style="margin-top:8px;padding:10px"><div class="reqhead"><span class="kind">TAPPA ${i+1}</span><button class="btn outline" style="padding:7px 10px" onclick="removeMapPlanStop('${r.id}')">✕ Togli</button></div><b>${esc(r.titolo)}</b><p style="margin:6px 0">${esc(r.ritiro_indirizzo)} → ${esc(cleanDeliveryAddress(r.consegna_indirizzo))}</p>${a?`<div class="meta"><span class="pill">🕒 Arrivo ~${a.arrival.toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'})}</span>${r.consegna_entro?`<span class="pill">⏰ Entro ${formatDateTime(r.consegna_entro)}${warn}</span>`:''}</div>`:''}</div>`}).join('');
  el.innerHTML=`${error?`<div class="notice yellow">${esc(error)}</div>`:''}${total}${rows}<div class="rowbtn" style="margin-top:10px"><button class="btn outline" onclick="clearMapPlan()">Svuota giro</button><button class="btn teal" onclick="acceptMapPlan()">✓ Accetta giro (${reqs.length})</button></div>`
}
async function recalculateMapPlan(){
  let reqs=mapPlanRequests();if(!reqs.length){MAP_PLAN_ROUTE=null;if(MAP_PLAN_ROUTE_LAYER&&MAP){MAP.removeLayer(MAP_PLAN_ROUTE_LAYER);MAP_PLAN_ROUTE_LAYER=null}renderMapPlanPanel();return}
  renderMapPlanPanel(null);
  try{let start=await ensureMapPlanStart(),data=await mapRouteDetailed(mapPlanPoints(reqs,start));MAP_PLAN_ROUTE=data;renderMapPlanPanel(data);drawMapPlanRoute(data)}catch(e){MAP_PLAN_ROUTE=null;renderMapPlanPanel(null,'GPS/percorso non disponibile: '+e.message)}
}
function addMapPlanStop(id){
  if(MAP_PLAN_IDS.includes(id)){closeSheet();recalculateMapPlan();return}
  if(MAP_PLAN_IDS.length>=5){alert('Per ora puoi pianificare fino a 5 richieste nello stesso giro.');return}
  let r=REQUESTS.find(x=>x.id===id);if(!r||!requestOpen(r)){alert('Questa richiesta non è più disponibile.');return}
  MAP_PLAN_IDS.push(id);closeSheet();page('mapPage');setTimeout(recalculateMapPlan,130)
}
function removeMapPlanStop(id){MAP_PLAN_IDS=MAP_PLAN_IDS.filter(x=>x!==id);MAP_PLAN_ROUTE=null;recalculateMapPlan()}
function clearMapPlan(){MAP_PLAN_IDS=[];MAP_PLAN_ROUTE=null;if(MAP_PLAN_ROUTE_LAYER&&MAP){MAP.removeLayer(MAP_PLAN_ROUTE_LAYER);MAP_PLAN_ROUTE_LAYER=null}renderMapPlanPanel();initMap()}
async function acceptMapPlan(){
  let ids=[...MAP_PLAN_IDS];if(!ids.length)return;if(!confirm(`Accettare ${ids.length} richieste di questo giro?`))return;
  let ok=0,failed=0;
  for(let id of ids){let r=REQUESTS.find(x=>x.id===id);if(!r||!requestOpen(r)){failed++;continue}let {data,error}=await db.rpc('accetta_consegna',{p_consegna_id:id});if(error||!data)failed++;else ok++}
  await loadRequests();renderAll();MAP_PLAN_IDS=[];MAP_PLAN_ROUTE=null;MAP_PLAN_START=USER_POS?{...USER_POS}:MAP_PLAN_START;if(MAP_PLAN_ROUTE_LAYER&&MAP){MAP.removeLayer(MAP_PLAN_ROUTE_LAYER);MAP_PLAN_ROUTE_LAYER=null}
  alert(failed?`${ok} richieste accettate. ${failed} non erano più disponibili.`:`${ok} richieste accettate.`);page('missions')
}
async function openMapOffer(id){
  let r=REQUESTS.find(x=>x.id===id);if(!r||!requestOpen(r))return;
  openSheet(`${head('CALCOLO TAPPA',r.titolo,'Calcolo km e tempo dalla tua posizione, considerando anche le tappe già aggiunte.')}<div id="mapOfferCalc" class="notice green">📍 Calcolo percorso…</div><div class="route"><div><small>RITIRO</small><br>${esc(r.ritiro_indirizzo)}</div><div><small>CONSEGNA</small><br>${esc(cleanDeliveryAddress(r.consegna_indirizzo))}</div></div><div class="meta"><span class="pill money">${euro(r.compenso_rider)}</span>${r.consegna_entro?`<span class="pill">⏰ Entro ${formatDateTime(r.consegna_entro)}</span>`:''}</div><div class="rowbtn"><button class="btn outline" onclick="closeSheet()">Non ora</button><button class="btn primary" onclick="addMapPlanStop('${r.id}')">➕ Aggiungi tappa</button></div><button class="btn teal full" style="margin-top:9px" onclick="acceptRequest('${r.id}')">✓ Accetta solo questa</button>`);
  let box=document.getElementById('mapOfferCalc');
  try{
    let start=await ensureMapPlanStart(),reqs=mapPlanRequests(id),data=await mapRouteDetailed(mapPlanPoints(reqs,start));if(!box)return;
    let base=MAP_PLAN_ROUTE,extraD=base?Math.max(0,data.distance-base.distance):data.distance,extraT=base?Math.max(0,data.duration-base.duration):data.duration;
    let arrivals=mapPlanArrivalInfo(data,reqs),candidate=arrivals[arrivals.length-1],late=candidate?.late;
    box.className='notice '+(late?'yellow':'green');
    box.innerHTML=`🚗 <b>${fmtDistance(data.distance)}</b> · <b>${fmtDuration(data.duration)}</b> per il giro${MAP_PLAN_IDS.length?`<br>Questa tappa aggiunge circa <b>${fmtPlanDelta(extraD,'km')}</b> · <b>${fmtPlanDelta(extraT,'time')}</b>`:''}${candidate?`<br>Consegna stimata: <b>${candidate.arrival.toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'})}</b>${late?' · ⚠️ oltre il limite richiesto':''}`:''}`
  }catch(e){if(box){box.className='notice yellow';box.innerHTML=`Non riesco a calcolare dalla posizione attuale: ${esc(e.message)}. Puoi comunque vedere ritiro/consegna e decidere.`}}
}
function renderMapPage(){mapPage.innerHTML=`<div class="pagehead"><div class="k">MAPPA LIVE</div><h2>Richieste disponibili</h2><p>Tocca un bersaglio: calcolo km e tempo. Aggiungi 2ª, 3ª o altre tappe e toglile se il giro diventa troppo lungo.</p></div><button class="gpsbtn" onclick="locateMe()">📍 Aggiorna la mia posizione</button><div id="mapPlanPanel" style="margin:10px 0"></div><div id="map"></div>`;setTimeout(()=>{initMap();setTimeout(recalculateMapPlan,100)},100)}
function initMap(){
  if(MAP){MAP.remove();MAP=null}MAP_PLAN_ROUTE_LAYER=null;MAP=L.map('map').setView([45.18,7.99],11);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(MAP);let pts=[];
  REQUESTS.filter(r=>requestOpen(r)&&r.cliente_id!==SESSION.user.id&&r.ritiro_lat&&r.ritiro_lng).forEach(r=>{let ll=[r.ritiro_lat,r.ritiro_lng];pts.push(ll);let marker=L.marker(ll).addTo(MAP);let inPlan=MAP_PLAN_IDS.includes(r.id);marker.bindTooltip(`${inPlan?'✓ ':''}${esc(r.titolo)} · ${euro(r.compenso_rider)}`,{direction:'top'});marker.on('click',()=>openMapOffer(r.id))});
  if(USER_POS){L.circleMarker([USER_POS.lat,USER_POS.lng],{radius:8,weight:4,fillOpacity:.9}).addTo(MAP).bindPopup('La tua posizione')}
  if(pts.length&&!MAP_PLAN_IDS.length)MAP.fitBounds(pts,{padding:[25,25],maxZoom:14})
}
function focusRequest(id){let r=REQUESTS.find(x=>x.id===id);if(!r)return;page('mapPage');setTimeout(()=>{if(MAP&&r.ritiro_lat)MAP.setView([r.ritiro_lat,r.ritiro_lng],15)},250)}
function locateMe(){if(!navigator.geolocation){alert('GPS non disponibile.');return}navigator.geolocation.getCurrentPosition(pos=>{USER_POS={lat:pos.coords.latitude,lng:pos.coords.longitude};MAP_PLAN_START={...USER_POS};if(MAP){L.circleMarker([USER_POS.lat,USER_POS.lng],{radius:8,weight:4,fillOpacity:.9}).addTo(MAP).bindPopup('La tua posizione').openPopup();MAP.setView([USER_POS.lat,USER_POS.lng],14)}recalculateMapPlan()},()=>alert('Consenti la posizione al browser.'),{enableHighAccuracy:true,timeout:12000})}
'''

if old_map not in s:
    raise SystemExit('map block not found')
s = s.replace(old_map, new_map, 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Multi-stop runner map planner patch applied')
