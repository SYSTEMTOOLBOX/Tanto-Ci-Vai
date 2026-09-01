from pathlib import Path
import re

p = Path('index.html')
s = p.read_text()

css = r'''.place-map{height:300px;min-height:260px;border-radius:18px;overflow:hidden;border:1px solid var(--line);margin:10px 0}.place-list{display:grid;gap:8px;margin-top:10px}.place-card{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;width:100%;text-align:left;border:1px solid var(--line);background:#fff;border-radius:16px;padding:12px}.place-card b{display:block;font-size:12px}.place-card small{display:block;color:var(--muted);font-size:8px;line-height:1.4;margin-top:3px}.place-distance{font-weight:950;color:var(--blue);font-size:10px;white-space:nowrap}.place-actions{display:flex;gap:6px;align-items:center}.favbtn{width:40px;height:40px;border-radius:12px;border:1px solid var(--line);background:#fff;font-size:18px}.favbtn.on{background:#fff7d8;border-color:#f1c94f}.pharmacy-location{padding:10px 12px;border-radius:14px;background:#eef6ff;border:1px solid #d9e8ff;color:#315b92;font-size:9px;line-height:1.45;margin:9px 0}.place-fallback{display:grid;grid-template-columns:1fr auto;gap:7px;margin-top:9px}.place-fallback input{min-width:0}'''
if '.place-map{' not in s:
    s = s.replace('.field{margin:11px 0}', css + '.field{margin:11px 0}', 1)

old_globals = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null;"
new_globals = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SELECTED_PLACE=null,HOME_POS=null,FAVORITES=[];"
if old_globals in s:
    s = s.replace(old_globals, new_globals, 1)

pattern = r"let REQUEST_CATEGORY='spesa';\nfunction openNewRequest\(step=1\)\{.*?\nasync function geocode"
block = r'''let REQUEST_CATEGORY='spesa';
function chooseRequestCategory(cat){
  REQUEST_CATEGORY=cat;
  SELECTED_PLACE=null;
  if(cat==='farmacia'){openPharmacyFinder();return}
  openNewRequest(2)
}
function openNewRequest(step=1){
  if(step===1){
    openSheet(`${head('NUOVA RICHIESTA','Di cosa hai bisogno?','Tocca una categoria. Per Farmacia cerco subito quelle più vicine alla tua posizione.')}<div class="choices">${[
      ['spesa','🛒','Spesa','Piccola spesa o prodotti già pronti'],
      ['farmacia','💊','Farmacia','Mostra automaticamente le farmacie vicine'],
      ['ritiro','📦','Ritiro','Pacco, documento o altro ritiro'],
      ['altro','🤝','Altro','Una piccola commissione locale']
    ].map(x=>`<button class="choice" onclick="chooseRequestCategory('${x[0]}')"><span class="em">${x[1]}</span><b>${x[2]}</b><small>${x[3]}</small></button>`).join('')}</div>`);return
  }
  const presets={spesa:['Ritirare una spesa','Es. prodotti già preparati o piccola spesa'],farmacia:['Ritiro in farmacia','Es. ordine già pronto al banco'],ritiro:['Ritirare un pacco','Es. pacco, documento o ordine da ritirare'],altro:['Piccola commissione','Descrivi cosa bisogna fare']};
  let pr=presets[REQUEST_CATEGORY]||presets.altro;
  let fromValue=SELECTED_PLACE?(SELECTED_PLACE.address||SELECTED_PLACE.name):'';
  let homeValue=HOME_POS?(HOME_POS.label||`${HOME_POS.lat.toFixed(6)},${HOME_POS.lng.toFixed(6)}`):'';
  let pharmacyNote=REQUEST_CATEGORY==='farmacia'&&SELECTED_PLACE?`<div class="pharmacy-location">💊 <b>${esc(SELECTED_PLACE.name)}</b><br>${esc(SELECTED_PLACE.address||'Posizione selezionata sulla mappa')} · ${SELECTED_PLACE.distance.toFixed(1)} km dalla tua posizione</div>`:'';
  openSheet(`${head('NUOVA RICHIESTA',pr[0],'Verrà salvata nel database e comparirà sugli altri telefoni della beta.')}${pharmacyNote}<div class="kind" style="display:inline-block;margin-top:10px">${REQUEST_CATEGORY.toUpperCase()}</div><div class="field"><label>TITOLO</label><input id="nrTitle" value="${pr[0]}"></div><div class="field"><label>DESCRIZIONE</label><textarea id="nrDesc" rows="3" placeholder="${pr[1]}"></textarea></div><div class="field"><label>DOVE RITIRARE</label><input id="nrFrom" value="${esc(fromValue)}" placeholder="Indirizzo completo o luogo" ${SELECTED_PLACE?'readonly':''}></div><div class="field"><label>DOVE CONSEGNARE</label><input id="nrTo" value="${esc(homeValue)}" placeholder="Indirizzo completo"></div><button class="gpsbtn" onclick="fillDeliveryWithGps()">📍 Usa la mia posizione per la consegna</button><div class="field"><label>COMPENSO RIDER</label><select id="nrPay"><option value="3.5">€ 3,50</option><option value="4" selected>€ 4,00</option><option value="5">€ 5,00</option><option value="6">€ 6,00</option></select></div><div id="nrStatus" class="notice green">📍 Ritiro e consegna vengono salvati con coordinate GPS per il matching.</div><div class="backrow"><button class="btn outline" onclick="openNewRequest(1)">← Tipo</button><button class="btn teal" onclick="publishRequest()">Pubblica richiesta</button></div>`)
}
function distanceKm(a,b){
  const R=6371,dLat=(b.lat-a.lat)*Math.PI/180,dLng=(b.lng-a.lng)*Math.PI/180;
  const x=Math.sin(dLat/2)**2+Math.cos(a.lat*Math.PI/180)*Math.cos(b.lat*Math.PI/180)*Math.sin(dLng/2)**2;
  return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x))
}
function currentPosition(){
  return new Promise((resolve,reject)=>{
    if(!navigator.geolocation){reject(new Error('GPS non disponibile'));return}
    navigator.geolocation.getCurrentPosition(p=>resolve({lat:p.coords.latitude,lng:p.coords.longitude,accuracy:p.coords.accuracy}),reject,{enableHighAccuracy:true,timeout:15000,maximumAge:30000})
  })
}
async function reverseGeocodePoint(p){
  try{
    let r=await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${p.lat}&lon=${p.lng}&zoom=18&addressdetails=1`,{headers:{'Accept-Language':'it'}});
    if(!r.ok)return p;
    let j=await r.json();
    p.label=j.display_name||'';
    p.area=j.address?.village||j.address?.hamlet||j.address?.town||j.address?.city||j.address?.municipality||'';
  }catch(e){}
  return p
}
async function fetchNearbyPharmacies(pos){
  const q=`[out:json][timeout:18];(node["amenity"="pharmacy"](around:15000,${pos.lat},${pos.lng});way["amenity"="pharmacy"](around:15000,${pos.lat},${pos.lng});relation["amenity"="pharmacy"](around:15000,${pos.lat},${pos.lng}););out center tags;`;
  const endpoints=['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter'];
  let json=null,lastErr=null;
  for(const ep of endpoints){try{let r=await fetch(ep+'?data='+encodeURIComponent(q));if(!r.ok)throw new Error('servizio '+r.status);json=await r.json();break}catch(e){lastErr=e}}
  if(!json)throw lastErr||new Error('Ricerca farmacie non disponibile');
  let seen=new Set(),out=[];
  for(const el of json.elements||[]){
    let lat=el.lat??el.center?.lat,lng=el.lon??el.center?.lon;if(lat==null||lng==null)continue;
    let t=el.tags||{},name=t.name||t.brand||'Farmacia';
    let key=`${el.type}:${el.id}`;if(seen.has(key))continue;seen.add(key);
    let street=[t['addr:street'],t['addr:housenumber']].filter(Boolean).join(' '),city=t['addr:city']||t['addr:town']||t['addr:village']||'';
    let address=t['addr:full']||[street,city].filter(Boolean).join(', ')||name;
    out.push({osm_type:el.type,osm_id:Number(el.id),name,address,lat:Number(lat),lng:Number(lng),distance:distanceKm(pos,{lat:Number(lat),lng:Number(lng)})})
  }
  out.sort((a,b)=>a.distance-b.distance);
  return out.slice(0,12)
}
async function loadFavoritePharmacies(){
  let {data,error}=await db.from('luoghi_preferiti').select('*').eq('tipo','farmacia');
  if(error){FAVORITES=[];return}
  FAVORITES=data||[]
}
function isFavoritePlace(p){return FAVORITES.some(f=>f.osm_type===p.osm_type&&Number(f.osm_id)===Number(p.osm_id))}
async function toggleFavoritePharmacy(i,ev){
  ev?.stopPropagation();let p=PHARMACY_RESULTS[i];if(!p)return;
  let fav=FAVORITES.find(f=>f.osm_type===p.osm_type&&Number(f.osm_id)===Number(p.osm_id));
  if(fav){let {error}=await db.from('luoghi_preferiti').delete().eq('id',fav.id);if(error){alert(error.message);return}}
  else{let {error}=await db.from('luoghi_preferiti').insert({user_id:SESSION.user.id,tipo:'farmacia',osm_type:p.osm_type,osm_id:p.osm_id,nome:p.name,indirizzo:p.address,lat:p.lat,lng:p.lng});if(error){alert(error.message);return}}
  await loadFavoritePharmacies();renderPharmacyList()
}
function renderPharmacyList(){
  let el=document.getElementById('pharmacyList');if(!el)return;
  el.innerHTML=PHARMACY_RESULTS.length?PHARMACY_RESULTS.map((p,i)=>`<div class="place-card"><button style="border:0;background:transparent;text-align:left;padding:0;min-width:0" onclick="selectPharmacy(${i})"><b>${esc(p.name)}</b><small>${esc(p.address)}</small></button><div class="place-actions"><span class="place-distance">${p.distance.toFixed(1)} km</span><button class="favbtn ${isFavoritePlace(p)?'on':''}" onclick="toggleFavoritePharmacy(${i},event)" aria-label="Preferita">${isFavoritePlace(p)?'★':'☆'}</button></div></div>`).join(''):'<div class="notice yellow">Nessuna farmacia trovata entro 15 km.</div>'
}
function initPharmacyMap(pos){
  if(PHARMACY_MAP){PHARMACY_MAP.remove();PHARMACY_MAP=null}
  PHARMACY_MAP=L.map('pharmacyMap').setView([pos.lat,pos.lng],13);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(PHARMACY_MAP);
  let bounds=[[pos.lat,pos.lng]];
  L.circleMarker([pos.lat,pos.lng],{radius:10,weight:4,fillOpacity:.95}).addTo(PHARMACY_MAP).bindPopup('<b>Sei qui</b>');
  PHARMACY_RESULTS.forEach((p,i)=>{bounds.push([p.lat,p.lng]);L.marker([p.lat,p.lng]).addTo(PHARMACY_MAP).bindPopup(`<b>${esc(p.name)}</b><br>${p.distance.toFixed(1)} km<br><button onclick="selectPharmacy(${i})">Scegli questa farmacia</button>`) });
  if(bounds.length>1)PHARMACY_MAP.fitBounds(bounds,{padding:[25,25],maxZoom:14});
  setTimeout(()=>PHARMACY_MAP?.invalidateSize(),120)
}
async function loadPharmaciesAt(pos){
  HOME_POS=await reverseGeocodePoint(pos);
  let topLoc=document.querySelector('.loc span:first-child');if(topLoc)topLoc.textContent='📍 '+(HOME_POS.area||'Posizione rilevata');
  let status=document.getElementById('pharmacyStatus');if(status)status.textContent='Cerco le farmacie più vicine…';
  PHARMACY_RESULTS=await fetchNearbyPharmacies(HOME_POS);
  await loadFavoritePharmacies();
  if(status)status.innerHTML=`📍 <b>${esc(HOME_POS.area||'Posizione rilevata')}</b> · ${PHARMACY_RESULTS.length} farmacie trovate entro 15 km`;
  initPharmacyMap(HOME_POS);renderPharmacyList()
}
async function openPharmacyFinder(){
  REQUEST_CATEGORY='farmacia';SELECTED_PLACE=null;
  openSheet(`${head('FARMACIE VICINE','Scegli la farmacia','Uso la posizione del telefono: il punto blu sei tu, i pin sono le farmacie vicine.')}<div id="pharmacyStatus" class="pharmacy-location">📍 Rilevo la tua posizione…</div><div id="pharmacyMap" class="place-map"></div><div id="pharmacyList" class="place-list"><div class="notice">Caricamento farmacie…</div></div><div class="place-fallback"><input id="pharmacyTown" placeholder="Oppure scrivi paese o frazione"><button class="btn outline" onclick="searchPharmaciesByText()">Cerca</button></div>`);
  try{let pos=await currentPosition();await loadPharmaciesAt(pos)}catch(e){let st=document.getElementById('pharmacyStatus');if(st)st.innerHTML='GPS non disponibile o non autorizzato. Consenti la posizione oppure cerca il paese/frazione qui sotto.';let list=document.getElementById('pharmacyList');if(list)list.innerHTML=''}
}
async function searchPharmaciesByText(){
  let q=document.getElementById('pharmacyTown')?.value.trim();if(!q)return;
  let st=document.getElementById('pharmacyStatus');if(st)st.textContent='Cerco '+q+'…';
  try{let p=await geocode(q);await loadPharmaciesAt(p)}catch(e){if(st)st.textContent='Errore: '+e.message}
}
function selectPharmacy(i){
  SELECTED_PLACE=PHARMACY_RESULTS[i];if(!SELECTED_PLACE)return;openNewRequest(2)
}
async function fillDeliveryWithGps(){
  let st=document.getElementById('nrStatus');if(st)st.textContent='Rilevo la tua posizione…';
  try{HOME_POS=await reverseGeocodePoint(await currentPosition());let input=document.getElementById('nrTo');if(input)input.value=HOME_POS.label||`${HOME_POS.lat.toFixed(6)},${HOME_POS.lng.toFixed(6)}`;if(st)st.textContent='✓ Posizione di consegna aggiornata.'}catch(e){if(st)st.textContent='GPS non disponibile: '+e.message}
}
async function geocode'''

m = re.search(pattern, s, re.S)
if not m:
    raise SystemExit('request category block not found')
s = s[:m.start()] + block + s[m.end():]

pub_pattern = r"async function publishRequest\(\)\{.*?\nasync function acceptRequest"
pub = r'''async function publishRequest(){
  let title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),to=nrTo.value.trim(),pay=+nrPay.value;if(!title||!from||!to){nrStatus.textContent='Compila titolo, ritiro e consegna.';return}nrStatus.textContent='Preparo coordinate e pubblico…';
  try{
    let a=(REQUEST_CATEGORY==='farmacia'&&SELECTED_PLACE)?{lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng,label:SELECTED_PLACE.address||SELECTED_PLACE.name}:await geocode(from);
    let homeLabel=HOME_POS?(HOME_POS.label||`${HOME_POS.lat.toFixed(6)},${HOME_POS.lng.toFixed(6)}`):'';
    let b=(HOME_POS&&to===homeLabel)?{lat:HOME_POS.lat,lng:HOME_POS.lng,label:HOME_POS.label||to}:await geocode(to);
    let {error}=await db.from('consegne').insert({cliente_id:SESSION.user.id,categoria:REQUEST_CATEGORY,titolo:title,descrizione:desc,ritiro_indirizzo:a.label,ritiro_lat:a.lat,ritiro_lng:a.lng,consegna_indirizzo:b.label,consegna_lat:b.lat,consegna_lng:b.lng,compenso_rider:pay});if(error)throw error;await loadRequests();renderAll();closeSheet();SELECTED_PLACE=null;alert('Richiesta pubblicata nel database.')
  }catch(e){nrStatus.textContent='Errore: '+e.message}
}
async function acceptRequest'''

m = re.search(pub_pattern, s, re.S)
if not m:
    raise SystemExit('publishRequest block not found')
s = s[:m.start()] + pub + s[m.end():]

p.write_text(s)
print('index.html patched')
