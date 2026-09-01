from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

# 1) Reverse geocoding must keep street and house number separate.
old = """async function reverseGeocodePoint(p){
  try{
    let r=await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${p.lat}&lon=${p.lng}&zoom=18&addressdetails=1`,{headers:{'Accept-Language':'it'}});
    if(!r.ok)return p;
    let j=await r.json();
    p.label=j.display_name||'';
    p.area=j.address?.village||j.address?.hamlet||j.address?.town||j.address?.city||j.address?.municipality||'';
  }catch(e){}
  return p
}
"""
new = """async function reverseGeocodePoint(p){
  try{
    let r=await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${p.lat}&lon=${p.lng}&zoom=18&addressdetails=1`,{headers:{'Accept-Language':'it'}});
    if(!r.ok)return p;
    let j=await r.json(),a=j.address||{};
    p.label=j.display_name||'';
    p.area=a.village||a.hamlet||a.town||a.city||a.municipality||'';
    p.city=a.city||a.town||a.municipality||a.village||a.hamlet||p.area||'';
    p.street=a.road||a.pedestrian||a.path||a.footway||'';
    p.housenumber=a.house_number||'';
    p.addressNoNumber=[p.street,p.city].filter(Boolean).join(', ')||p.label||'';
  }catch(e){}
  return p
}
"""
if old not in s:
    raise SystemExit('reverseGeocodePoint block not found')
s = s.replace(old, new, 1)

# 2) Pharmacy results: store civic separately from street/address.
old = """    let street=[t['addr:street'],t['addr:housenumber']].filter(Boolean).join(' '),city=t['addr:city']||t['addr:town']||t['addr:village']||'';
    let address=t['addr:full']||[street,city].filter(Boolean).join(', ')||name;
    out.push({osm_type:el.type,osm_id:Number(el.id),name,address,lat:Number(lat),lng:Number(lng),distance:distanceKm(pos,{lat:Number(lat),lng:Number(lng)})})
"""
new = """    let street=t['addr:street']||'',housenumber=t['addr:housenumber']||'',city=t['addr:city']||t['addr:town']||t['addr:village']||'';
    let address=[street,city].filter(Boolean).join(', ')||name;
    out.push({osm_type:el.type,osm_id:Number(el.id),name,address,street,housenumber,city,lat:Number(lat),lng:Number(lng),distance:distanceKm(pos,{lat:Number(lat),lng:Number(lng)})})
"""
if old not in s:
    raise SystemExit('pharmacy address block not found')
s = s.replace(old, new, 1)

old = "<small>${esc(p.address)}</small>"
new = "<small>${esc(p.address)}${p.housenumber?` · N. ${esc(p.housenumber)}`:''}</small>"
if old not in s:
    raise SystemExit('pharmacy list address display not found')
s = s.replace(old, new, 1)

old = """function selectPharmacy(i){
  SELECTED_PLACE=PHARMACY_RESULTS[i];if(!SELECTED_PLACE)return;openNewRequest(2)
}
"""
new = """async function selectPharmacy(i){
  let p=PHARMACY_RESULTS[i];if(!p)return;
  let rev=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
  SELECTED_PLACE={...p,street:rev.street||p.street||'',housenumber:rev.housenumber||p.housenumber||'',city:rev.city||p.city||'',address:rev.addressNoNumber||p.address||p.name};
  if(PHARMACY_MAP){PHARMACY_MAP.remove();PHARMACY_MAP=null}
  openNewRequest(2)
}
"""
if old not in s:
    raise SystemExit('selectPharmacy block not found')
s = s.replace(old, new, 1)

# 3) Shop results: same separation.
old = """    let street=[t['addr:street'],t['addr:housenumber']].filter(Boolean).join(' '),city=t['addr:city']||t['addr:town']||t['addr:village']||'';
    let address=t['addr:full']||[street,city].filter(Boolean).join(', ')||name;
    out.push({osm_type:el.type,osm_id:Number(el.id),name,address,shop:type,lat:Number(lat),lng:Number(lng),distance:distanceKm(pos,{lat:Number(lat),lng:Number(lng)})})
"""
new = """    let street=t['addr:street']||'',housenumber=t['addr:housenumber']||'',city=t['addr:city']||t['addr:town']||t['addr:village']||'';
    let address=[street,city].filter(Boolean).join(', ')||name;
    out.push({osm_type:el.type,osm_id:Number(el.id),name,address,street,housenumber,city,shop:type,lat:Number(lat),lng:Number(lng),distance:distanceKm(pos,{lat:Number(lat),lng:Number(lng)})})
"""
if old not in s:
    raise SystemExit('shop address block not found')
s = s.replace(old, new, 1)

old = "<small>${esc(shopTypeLabel(p.shop))} · ${esc(p.address)}</small>"
new = "<small>${esc(shopTypeLabel(p.shop))} · ${esc(p.address)}${p.housenumber?` · N. ${esc(p.housenumber)}`:''}</small>"
if old not in s:
    raise SystemExit('shop list address display not found')
s = s.replace(old, new, 1)

old = """async function selectShop(i){
  let p=SHOP_RESULTS[i];if(!p)return;
  let st=document.getElementById('shopStatus');if(st)st.textContent='Recupero indirizzo completo del negozio…';
  try{
    let rev=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
    SELECTED_PLACE={...p,address:rev.label||p.address||p.name};
  }catch(e){SELECTED_PLACE=p}
  if(SHOP_MAP){SHOP_MAP.remove();SHOP_MAP=null}
  openNewRequest(2)
}
"""
new = """async function selectShop(i){
  let p=SHOP_RESULTS[i];if(!p)return;
  let st=document.getElementById('shopStatus');if(st)st.textContent='Recupero indirizzo e numero civico…';
  try{
    let rev=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
    SELECTED_PLACE={...p,street:rev.street||p.street||'',housenumber:rev.housenumber||p.housenumber||'',city:rev.city||p.city||'',address:rev.addressNoNumber||p.address||p.name};
  }catch(e){SELECTED_PLACE=p}
  if(SHOP_MAP){SHOP_MAP.remove();SHOP_MAP=null}
  openNewRequest(2)
}
"""
if old not in s:
    raise SystemExit('selectShop block not found')
s = s.replace(old, new, 1)

# 4) Request form: keep pickup civic in its own field for pharmacy/spesa.
anchor = "let REQUEST_CATEGORY='spesa';\n"
addition = """let REQUEST_CATEGORY='spesa';
function pickupAddressWithoutCivic(p){return String(p?.addressNoNumber||p?.address||p?.name||'').trim()}
function formatPickupAddress(base,civic){
  base=String(base||'').trim();civic=String(civic||'').trim();if(!civic)return base;
  let parts=base.split(',');if(parts.length>1){let first=parts.shift().trim();return `${first} ${civic}, ${parts.join(',').trim()}`}
  return `${base} ${civic}`.trim()
}
"""
if anchor not in s:
    raise SystemExit('request category anchor not found')
s = s.replace(anchor, addition, 1)

old = "let fromValue=SELECTED_PLACE?(SELECTED_PLACE.address||SELECTED_PLACE.name):'';"
new = "let fromValue=SELECTED_PLACE?pickupAddressWithoutCivic(SELECTED_PLACE):'';let pickupCivic=SELECTED_PLACE?.housenumber||'';let showPickupCivic=REQUEST_CATEGORY==='farmacia'||REQUEST_CATEGORY==='spesa';"
if old not in s:
    raise SystemExit('fromValue line not found')
s = s.replace(old, new, 1)

old = "let pharmacyNote=SELECTED_PLACE?`<div class=\"pharmacy-location\">${REQUEST_CATEGORY==='farmacia'?'💊':'🏪'} <b>${esc(SELECTED_PLACE.name)}</b><br>${esc(SELECTED_PLACE.address||'Luogo selezionato')}${Number.isFinite(SELECTED_PLACE.distance)?` · ${SELECTED_PLACE.distance.toFixed(1)} km dalla zona cercata`:''}</div>`:'';"
new = "let pharmacyNote=SELECTED_PLACE?`<div class=\"pharmacy-location\">${REQUEST_CATEGORY==='farmacia'?'💊':'🏪'} <b>${esc(SELECTED_PLACE.name)}</b><br>${esc(pickupAddressWithoutCivic(SELECTED_PLACE))}${SELECTED_PLACE.housenumber?` · <b>N. ${esc(SELECTED_PLACE.housenumber)}</b>`:''}${Number.isFinite(SELECTED_PLACE.distance)?` · ${SELECTED_PLACE.distance.toFixed(1)} km dalla zona cercata`:''}</div>`:'';"
if old not in s:
    raise SystemExit('selected place note line not found')
s = s.replace(old, new, 1)

old = "<div class=\"field\"><label>DOVE RITIRARE</label><input id=\"nrFrom\" value=\"${esc(fromValue)}\" placeholder=\"Indirizzo completo o luogo\" ${SELECTED_PLACE?'readonly':''}></div><div class=\"delivery-smart\">"
new = "<div class=\"field\"><label>DOVE RITIRARE · VIA / LUOGO</label><input id=\"nrFrom\" value=\"${esc(fromValue)}\" placeholder=\"Via o luogo, senza numero civico\" ${SELECTED_PLACE?'readonly':''}></div>${showPickupCivic?`<div class=\"field\"><label>NUMERO CIVICO</label><input id=\"nrPickupNumber\" value=\"${esc(pickupCivic)}\" placeholder=\"Es. 12/A\" inputmode=\"text\"><div class=\"notice\" style=\"margin-top:7px\">Il numero resta separato dalla via per evitare indirizzi confusi.</div></div>`:''}<div class=\"delivery-smart\">"
if old not in s:
    raise SystemExit('pickup field template not found')
s = s.replace(old, new, 1)

# 5) Publication: combine civic only for geocoding/saved route, while UI stays separate.
old = "let person=nrPerson.value.trim(),title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',deadlineValue=document.getElementById('nrDeadline')?.value||'',pay=+nrPay.value;"
new = "let person=nrPerson.value.trim(),title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),pickupNumber=document.getElementById('nrPickupNumber')?.value.trim()||'',city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',deadlineValue=document.getElementById('nrDeadline')?.value||'',pay=+nrPay.value;"
if old not in s:
    raise SystemExit('publishRequest variables line not found')
s = s.replace(old, new, 1)

old = "let a=((REQUEST_CATEGORY==='farmacia'||REQUEST_CATEGORY==='spesa')&&SELECTED_PLACE)?{lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng,label:SELECTED_PLACE.address||SELECTED_PLACE.name}:await geocode(from);"
new = "let pickupAddress=formatPickupAddress(from,pickupNumber),selectedPickup=(REQUEST_CATEGORY==='farmacia'||REQUEST_CATEGORY==='spesa')&&SELECTED_PLACE;let a=selectedPickup?{lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng,label:`${SELECTED_PLACE.name} · ${pickupAddress}`}:await geocode(pickupAddress);"
if old not in s:
    raise SystemExit('pickup geocode line not found')
s = s.replace(old, new, 1)

# 6) Offer details: give the runner an explicit yes/no choice and do not offer expired requests.
old = "let action=!mine&&r.stato==='disponibile'?`<button class=\"btn teal full\" style=\"margin-top:10px\" onclick=\"acceptRequest('${r.id}')\">Tanto ci vai? · Prendi richiesta</button>`:assigned?`<button class=\"btn primary full\" style=\"margin-top:10px\" onclick=\"openRunnerNavigation('${r.id}')\">🧭 Apri navigatore runner</button>`:'';"
new = "let action=!mine&&requestOpen(r)?`<div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"closeSheet()\">Non ora</button><button class=\"btn teal\" onclick=\"acceptRequest('${r.id}')\">✓ Accetta richiesta</button></div>`:assigned?`<button class=\"btn primary full\" style=\"margin-top:10px\" onclick=\"openRunnerNavigation('${r.id}')\">🧭 Apri navigatore runner</button>`:'';"
if old not in s:
    raise SystemExit('openRequestDetails action line not found')
s = s.replace(old, new, 1)

# 7) Runner map: tapping a pin opens the offer directly instead of just re-centering.
old = "function renderMapPage(){mapPage.innerHTML=`<div class=\"pagehead\"><div class=\"k\">MAPPA LIVE</div><h2>Richieste disponibili</h2><p>I pin usano le coordinate salvate nel database.</p></div><button class=\"gpsbtn\" onclick=\"locateMe()\">📍 Mostra la mia posizione</button><div id=\"map\"></div>`;setTimeout(initMap,100)}"
new = "function renderMapPage(){mapPage.innerHTML=`<div class=\"pagehead\"><div class=\"k\">MAPPA LIVE</div><h2>Richieste disponibili</h2><p>Tocca un pin: si apre subito l'offerta completa e puoi decidere se accettarla oppure no.</p></div><button class=\"gpsbtn\" onclick=\"locateMe()\">📍 Mostra la mia posizione</button><div id=\"map\"></div>`;setTimeout(initMap,100)}"
if old not in s:
    raise SystemExit('renderMapPage line not found')
s = s.replace(old, new, 1)

old = "function initMap(){if(MAP){MAP.remove();MAP=null}MAP=L.map('map').setView([45.18,7.99],11);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(MAP);let pts=[];REQUESTS.filter(r=>requestOpen(r)&&r.ritiro_lat&&r.ritiro_lng).forEach(r=>{let ll=[r.ritiro_lat,r.ritiro_lng];pts.push(ll);L.marker(ll).addTo(MAP).bindPopup(`<b>${esc(r.titolo)}</b><br>${euro(r.compenso_rider)}<br><button onclick=\"focusRequest('${r.id}')\">Apri</button>`)});if(pts.length)MAP.fitBounds(pts,{padding:[25,25],maxZoom:14})}"
new = "function initMap(){if(MAP){MAP.remove();MAP=null}MAP=L.map('map').setView([45.18,7.99],11);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(MAP);let pts=[];REQUESTS.filter(r=>requestOpen(r)&&r.cliente_id!==SESSION.user.id&&r.ritiro_lat&&r.ritiro_lng).forEach(r=>{let ll=[r.ritiro_lat,r.ritiro_lng];pts.push(ll);let marker=L.marker(ll).addTo(MAP);marker.bindTooltip(`${esc(r.titolo)} · ${euro(r.compenso_rider)}`,{direction:'top'});marker.on('click',()=>openRequestDetails(r.id))});if(pts.length)MAP.fitBounds(pts,{padding:[25,25],maxZoom:14})}"
if old not in s:
    raise SystemExit('initMap line not found')
s = s.replace(old, new, 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Pickup civic + direct map offer patch applied')
