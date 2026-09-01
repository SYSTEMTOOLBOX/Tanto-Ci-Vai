from pathlib import Path

p = Path('index.html')
s = p.read_text()

old = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SELECTED_PLACE=null,HOME_POS=null,FAVORITES=[];"
new = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SELECTED_PLACE=null,HOME_POS=null,FAVORITES=[],NAV_MAP=null,NAV_ROUTE_LAYER=null,NAV_WATCH=null,NAV_ROUTE=null,NAV_MODE='car',NAV_MARKER=null;"
if old in s:
    s = s.replace(old, new, 1)

css = ".nav-modes{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin:10px 0}.nav-mode{border:1px solid var(--line);background:#fff;border-radius:14px;padding:11px 7px;font-size:10px;font-weight:900;color:var(--muted)}.nav-mode.on{background:#eaf3ff;border-color:#8eb7ff;color:var(--blue)}.nav-summary{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.nav-summary>div{border:1px solid var(--line);border-radius:15px;padding:11px;background:#f8fbff}.nav-summary b{display:block;font-size:18px;letter-spacing:-.03em}.nav-summary span{font-size:8px;color:var(--muted);font-weight:850}.nav-steps{display:grid;gap:6px;max-height:190px;overflow:auto;margin:9px 0}.nav-step{display:grid;grid-template-columns:28px 1fr auto;gap:8px;align-items:center;padding:9px;border:1px solid var(--line);border-radius:12px;background:#fff;font-size:9px}.nav-step .turn{font-size:17px;text-align:center}.nav-step small{color:var(--muted);font-size:8px}.nav-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:9px}.nav-live{background:#effff8;border:1px solid #cdeedd;color:#267259;border-radius:14px;padding:10px 12px;font-size:9px;line-height:1.4;margin-top:8px}.nav-live.active{background:#e9f4ff;border-color:#c9dfff;color:#1f5da8}.route-map{height:330px;min-height:280px;border-radius:18px;overflow:hidden;border:1px solid var(--line);margin:10px 0}"
if '.nav-modes{' not in s:
    s = s.replace('.field{margin:11px 0}', css + '.field{margin:11px 0}', 1)

oldsel = """function selectPharmacy(i){
  SELECTED_PLACE=PHARMACY_RESULTS[i];if(!SELECTED_PLACE)return;openNewRequest(2)
}
"""
newsel = """function selectPharmacy(i){
  SELECTED_PLACE=PHARMACY_RESULTS[i];if(!SELECTED_PLACE)return;openRoutePlanner()
}
"""
if oldsel in s:
    s = s.replace(oldsel, newsel, 1)
elif 'openRoutePlanner()' not in s:
    raise SystemExit('selectPharmacy block not found')

funcs = r'''function routeModeLabel(mode){return mode==='car'?'Auto':mode==='foot'?'A piedi':'Bici'}
function routeModeIcon(mode){return mode==='car'?'🚗':mode==='foot'?'🚶':'🚲'}
function routeBase(mode){return `https://routing.openstreetmap.de/routed-${mode}/route/v1/driving/`}
function fmtDistance(m){return m<1000?`${Math.round(m)} m`:`${(m/1000).toFixed(m<10000?1:0)} km`}
function fmtDuration(sec){let min=Math.max(1,Math.round(sec/60));if(min<60)return `${min} min`;let h=Math.floor(min/60),r=min%60;return r?`${h} h ${r} min`:`${h} h`}
function turnIcon(step){let t=step?.maneuver?.type||'',m=step?.maneuver?.modifier||'';if(t==='arrive')return '🏁';if(t==='depart')return '📍';if(m.includes('left'))return '↰';if(m.includes('right'))return '↱';if(t==='roundabout'||t==='rotary')return '⟳';if(t==='uturn')return '↶';return '↑'}
function stepText(step){
  let t=step?.maneuver?.type||'',m=step?.maneuver?.modifier||'',name=step?.name?` su ${step.name}`:'';
  if(t==='depart')return `Parti${name}`;
  if(t==='arrive')return 'Sei arrivato a destinazione';
  if(t==='roundabout'||t==='rotary')return `Entra nella rotonda${name}`;
  if(t==='merge')return `Immettiti${name}`;
  if(t==='continue'||t==='new name')return `Continua${name}`;
  if(t==='turn'){if(m.includes('left'))return `Svolta a sinistra${name}`;if(m.includes('right'))return `Svolta a destra${name}`;return `Svolta${name}`}
  return `Prosegui${name}`
}
function stopLiveNavigation(){
  if(NAV_WATCH!=null){navigator.geolocation.clearWatch(NAV_WATCH);NAV_WATCH=null}
  NAV_MARKER=null;
  let b=document.getElementById('liveNavBtn');if(b)b.textContent='▶ Avvia navigazione';
  let st=document.getElementById('liveNavStatus');if(st){st.classList.remove('active');st.textContent='GPS pronto. Premi Avvia navigazione per seguire la tua posizione sulla mappa.'}
}
function openRoutePlanner(){
  if(!SELECTED_PLACE)return;
  stopLiveNavigation();
  openSheet(`${head('PERCORSO SMART',SELECTED_PLACE.name,'Scegli come vuoi muoverti. Il percorso parte dalla tua posizione GPS reale.')}<div class="pharmacy-location">💊 <b>${esc(SELECTED_PLACE.name)}</b><br>${esc(SELECTED_PLACE.address||'Farmacia selezionata')}</div><div class="nav-modes"><button id="mode-car" class="nav-mode on" onclick="calculateSmartRoute('car')">🚗 Auto</button><button id="mode-foot" class="nav-mode" onclick="calculateSmartRoute('foot')">🚶 A piedi</button><button id="mode-bike" class="nav-mode" onclick="calculateSmartRoute('bike')">🚲 Bici</button></div><div id="smartRouteStatus" class="notice green">📍 Rilevo la posizione e preparo il percorso…</div><div id="smartRouteMap" class="route-map"></div><div id="routeSummary"></div><div id="routeSteps" class="nav-steps"></div><div id="liveNavStatus" class="nav-live">GPS pronto. Premi Avvia navigazione per seguire la tua posizione sulla mappa.</div><div class="nav-actions"><button id="liveNavBtn" class="btn primary" onclick="toggleLiveNavigation()">▶ Avvia navigazione</button><button class="btn outline" onclick="openExternalNavigation()">↗ Apri in Maps</button></div><button class="btn teal full" style="margin-top:9px" onclick="stopLiveNavigation();openNewRequest(2)">✓ Usa questa farmacia</button>`);
  calculateSmartRoute('car')
}
async function fetchSmartRoute(start,end,mode){
  let coords=`${start.lng},${start.lat};${end.lng},${end.lat}`;
  let url=routeBase(mode)+coords+'?overview=full&geometries=geojson&steps=true&alternatives=false';
  let r=await fetch(url);if(!r.ok)throw new Error('Servizio percorso non disponibile');
  let j=await r.json();if(j.code!=='Ok'||!j.routes?.length)throw new Error('Percorso non trovato');return j.routes[0]
}
function drawSmartRoute(start,end,route){
  if(NAV_MAP){NAV_MAP.remove();NAV_MAP=null}
  NAV_MAP=L.map('smartRouteMap').setView([start.lat,start.lng],14);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(NAV_MAP);
  L.circleMarker([start.lat,start.lng],{radius:9,weight:4,fillOpacity:.95}).addTo(NAV_MAP).bindPopup('Partenza · la tua posizione');
  L.marker([end.lat,end.lng]).addTo(NAV_MAP).bindPopup(esc(SELECTED_PLACE?.name||'Destinazione'));
  let latlngs=(route.geometry?.coordinates||[]).map(c=>[c[1],c[0]]);
  if(latlngs.length){NAV_ROUTE_LAYER=L.polyline(latlngs,{weight:6,opacity:.88}).addTo(NAV_MAP);NAV_MAP.fitBounds(NAV_ROUTE_LAYER.getBounds(),{padding:[24,24]})}
  setTimeout(()=>NAV_MAP?.invalidateSize(),100)
}
function renderRouteSteps(route){
  let steps=(route.legs||[]).flatMap(l=>l.steps||[]),el=document.getElementById('routeSteps');if(!el)return;
  el.innerHTML=steps.slice(0,30).map(s=>`<div class="nav-step"><div class="turn">${turnIcon(s)}</div><div><b>${esc(stepText(s))}</b><br><small>${esc(s.name||'')}</small></div><div>${fmtDistance(s.distance||0)}</div></div>`).join('')
}
async function calculateSmartRoute(mode){
  NAV_MODE=mode;['car','foot','bike'].forEach(m=>document.getElementById('mode-'+m)?.classList.toggle('on',m===mode));
  stopLiveNavigation();
  let st=document.getElementById('smartRouteStatus');if(st)st.textContent=`${routeModeIcon(mode)} Calcolo percorso ${routeModeLabel(mode).toLowerCase()}…`;
  try{
    let start=await currentPosition();HOME_POS=await reverseGeocodePoint(start);let end={lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng};
    NAV_ROUTE=await fetchSmartRoute(start,end,mode);drawSmartRoute(start,end,NAV_ROUTE);renderRouteSteps(NAV_ROUTE);
    let sum=document.getElementById('routeSummary');if(sum)sum.innerHTML=`<div class="nav-summary"><div><b>${fmtDistance(NAV_ROUTE.distance)}</b><span>DISTANZA · ${routeModeIcon(mode)} ${routeModeLabel(mode)}</span></div><div><b>${fmtDuration(NAV_ROUTE.duration)}</b><span>TEMPO STIMATO</span></div></div>`;
    if(st)st.innerHTML=`✓ Percorso pronto dalla tua posizione a <b>${esc(SELECTED_PLACE.name)}</b>.`;
  }catch(e){
    if(st)st.textContent='Errore percorso: '+e.message;
    let rs=document.getElementById('routeSummary');if(rs)rs.innerHTML='';let steps=document.getElementById('routeSteps');if(steps)steps.innerHTML=''
  }
}
function toggleLiveNavigation(){
  if(NAV_WATCH!=null){stopLiveNavigation();return}
  if(!navigator.geolocation){alert('GPS non disponibile.');return}
  let st=document.getElementById('liveNavStatus'),btn=document.getElementById('liveNavBtn');
  if(st){st.classList.add('active');st.textContent='● Navigazione GPS attiva · seguo la tua posizione'}if(btn)btn.textContent='■ Ferma navigazione';
  NAV_WATCH=navigator.geolocation.watchPosition(pos=>{
    let pt={lat:pos.coords.latitude,lng:pos.coords.longitude};USER_POS=pt;
    if(!NAV_MAP)return;
    if(!NAV_MARKER)NAV_MARKER=L.circleMarker([pt.lat,pt.lng],{radius:10,weight:4,fillOpacity:.95}).addTo(NAV_MAP).bindPopup('Tu sei qui');else NAV_MARKER.setLatLng([pt.lat,pt.lng]);
    NAV_MAP.panTo([pt.lat,pt.lng],{animate:true});
  },e=>{if(st)st.textContent='GPS: '+e.message;stopLiveNavigation()},{enableHighAccuracy:true,maximumAge:3000,timeout:15000})
}
function openExternalNavigation(){
  if(!SELECTED_PLACE)return;
  let mode=NAV_MODE==='car'?'driving':NAV_MODE==='foot'?'walking':'bicycling';
  let url=`https://www.google.com/maps/dir/?api=1&destination=${SELECTED_PLACE.lat},${SELECTED_PLACE.lng}&travelmode=${mode}`;
  window.open(url,'_blank','noopener')
}
'''

anchor = 'async function fillDeliveryWithGps(){'
if 'function openRoutePlanner(){' not in s:
    if anchor not in s:
        raise SystemExit('fillDeliveryWithGps anchor not found')
    s = s.replace(anchor, funcs + anchor, 1)

p.write_text(s)
