from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# State for smart delivery address picker.
old = "NAV_REQUEST=null;"
new = "NAV_REQUEST=null,DELIVERY_MAP=null,DELIVERY_MARKER=null,DELIVERY_CITY_RESULTS=[],DELIVERY_STREET_RESULTS=[],DELIVERY_TIMER=null,DELIVERY_CITY_POS=null;"
if old in s and "DELIVERY_CITY_RESULTS" not in s:
    s = s.replace(old, new, 1)

# UI styles for autocomplete and map picker.
css = r'''.delivery-smart{margin:12px 0;padding:12px;border:1px solid var(--line);border-radius:18px;background:#f8fbff}.delivery-smart-title{font-size:10px;font-weight:950;margin-bottom:7px}.autocomplete-wrap{position:relative}.autocomplete-box{display:grid;gap:4px;margin-top:5px}.autocomplete-item{width:100%;border:1px solid var(--line);background:#fff;border-radius:12px;padding:10px;text-align:left;font-size:9px;line-height:1.35;color:var(--ink)}.autocomplete-item b{display:block;font-size:10px}.autocomplete-item small{display:block;color:var(--muted);margin-top:2px}.delivery-tools{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:8px}.delivery-map{height:300px;border-radius:17px;overflow:hidden;border:1px solid var(--line);margin-top:9px}.delivery-picked{margin-top:8px;padding:9px 10px;border-radius:12px;background:#effff8;border:1px solid #d5f4e8;color:#316b58;font-size:9px;line-height:1.4}'''
if '.delivery-smart{' not in s:
    s = s.replace('.field{margin:11px 0}', css + '.field{margin:11px 0}', 1)

# Replace the single rigid delivery field with smart city + street fields, map and GPS.
old_form = '''<div class="field"><label>INDIRIZZO DI CONSEGNA</label><input id="nrTo" value="" placeholder="Es. Via Roma 12, Lauriano (TO)"></div><button class="gpsbtn" onclick="fillDeliveryWithGps()">📍 Usa il GPS per questo indirizzo di consegna</button>'''
new_form = '''<div class="delivery-smart"><div class="delivery-smart-title">📍 DOVE VA CONSEGNATO?</div><div class="field autocomplete-wrap"><label>CITTÀ / FRAZIONE</label><input id="nrCity" value="" placeholder="Es. Lauriano" autocomplete="off" oninput="deliveryCityChanged()"><div id="deliveryCitySuggest" class="autocomplete-box"></div></div><div class="field autocomplete-wrap"><label>VIA E NUMERO CIVICO</label><input id="nrStreet" value="" placeholder="Es. Via Anselmina 14/A" autocomplete="off" oninput="deliveryStreetChanged()"><div id="deliveryStreetSuggest" class="autocomplete-box"></div></div><div class="delivery-tools"><button type="button" class="btn outline" onclick="toggleDeliveryMap()">🗺️ Scegli sulla mappa</button><button type="button" class="btn outline" onclick="fillDeliveryWithGps()">📍 Usa GPS</button></div><div id="deliveryMap" class="delivery-map hidden"></div><div id="deliveryPicked" class="delivery-picked hidden"></div></div>'''
if old_form in s:
    s = s.replace(old_form, new_form, 1)

# Smart autocomplete / map / GPS helpers. Photon is made for search-as-you-type;
# Nominatim remains only as the existing one-shot fallback geocoder.
start = s.find('async function fillDeliveryWithGps(){')
end = s.find('async function geocode(q){', start)
if start != -1 and end != -1:
    helpers = r'''function photonFeatureToPoint(f){
  let p=f?.properties||{},c=f?.geometry?.coordinates||[];
  let city=p.city||p.locality||p.district||p.county||p.name||'';
  let street=[p.street||((p.osm_value==='street'||p.osm_value==='residential')?p.name:''),p.housenumber].filter(Boolean).join(' ');
  let label=[street,city,p.postcode,p.state].filter(Boolean).join(', ');
  return {lat:+c[1],lng:+c[0],city,street,label:label||p.name||'',raw:p}
}
function deliveryCityChanged(){
  DELIVERY_CITY_POS=null;HOME_POS=null;
  clearTimeout(DELIVERY_TIMER);DELIVERY_TIMER=setTimeout(suggestDeliveryCities,260)
}
function deliveryStreetChanged(){
  HOME_POS=null;
  clearTimeout(DELIVERY_TIMER);DELIVERY_TIMER=setTimeout(suggestDeliveryStreets,260)
}
async function photonSearch(url){
  let r=await fetch(url);if(!r.ok)throw new Error('Ricerca indirizzo non disponibile');
  let j=await r.json();return (j.features||[]).filter(f=>String(f.properties?.countrycode||'').toUpperCase()==='IT')
}
function citySuggestionLabel(f){
  let p=f.properties||{};return [p.name,p.county,p.state].filter(Boolean).join(' · ')
}
async function suggestDeliveryCities(){
  let input=document.getElementById('nrCity'),box=document.getElementById('deliveryCitySuggest');if(!input||!box)return;
  let q=input.value.trim();if(q.length<2){box.innerHTML='';return}
  try{
    let url=`https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&limit=8&lang=it&layer=city&layer=locality&layer=district`;
    let fs=await photonSearch(url),seen=new Set();
    DELIVERY_CITY_RESULTS=fs.filter(f=>{let k=citySuggestionLabel(f).toLowerCase();if(!k||seen.has(k))return false;seen.add(k);return true}).slice(0,6);
    box.innerHTML=DELIVERY_CITY_RESULTS.map((f,i)=>`<button type="button" class="autocomplete-item" onclick="chooseDeliveryCity(${i})"><b>${esc(f.properties?.name||'Località')}</b><small>${esc([f.properties?.county,f.properties?.state].filter(Boolean).join(' · '))}</small></button>`).join('')
  }catch(e){box.innerHTML=''}
}
function chooseDeliveryCity(i){
  let f=DELIVERY_CITY_RESULTS[i];if(!f)return;let pt=photonFeatureToPoint(f),input=document.getElementById('nrCity');
  if(input)input.value=f.properties?.name||pt.city;DELIVERY_CITY_POS=pt;HOME_POS=null;
  let box=document.getElementById('deliveryCitySuggest');if(box)box.innerHTML='';
  let st=document.getElementById('nrStreet');if(st){st.focus();st.dispatchEvent(new Event('input'))}
}
async function suggestDeliveryStreets(){
  let city=document.getElementById('nrCity')?.value.trim()||'',input=document.getElementById('nrStreet'),box=document.getElementById('deliveryStreetSuggest');if(!input||!box)return;
  let street=input.value.trim();if(city.length<2||street.length<2){box.innerHTML='';return}
  try{
    let bias=DELIVERY_CITY_POS?`&lat=${DELIVERY_CITY_POS.lat}&lon=${DELIVERY_CITY_POS.lng}`:'';
    let url=`https://photon.komoot.io/api/?q=${encodeURIComponent(street+', '+city)}&limit=10&lang=it&layer=street&layer=house${bias}`;
    let fs=await photonSearch(url),seen=new Set();
    DELIVERY_STREET_RESULTS=fs.filter(f=>{let pt=photonFeatureToPoint(f),name=pt.street||f.properties?.name||'';let k=(name+'|'+pt.city).toLowerCase();if(!name||seen.has(k))return false;seen.add(k);return true}).slice(0,7);
    box.innerHTML=DELIVERY_STREET_RESULTS.map((f,i)=>{let pt=photonFeatureToPoint(f),name=pt.street||f.properties?.name||'Indirizzo';return `<button type="button" class="autocomplete-item" onclick="chooseDeliveryStreet(${i})"><b>${esc(name)}</b><small>${esc([pt.city,f.properties?.postcode,f.properties?.state].filter(Boolean).join(' · '))}</small></button>`}).join('')
  }catch(e){box.innerHTML=''}
}
function chooseDeliveryStreet(i){
  let f=DELIVERY_STREET_RESULTS[i];if(!f)return;let pt=photonFeatureToPoint(f);
  let st=document.getElementById('nrStreet'),city=document.getElementById('nrCity');if(st)st.value=pt.street||f.properties?.name||'';if(city&&pt.city)city.value=pt.city;
  HOME_POS={lat:pt.lat,lng:pt.lng,label:pt.label,city:pt.city,street:pt.street,cityText:(city?.value||''),streetText:(st?.value||'')};
  let box=document.getElementById('deliveryStreetSuggest');if(box)box.innerHTML='';showPickedDelivery(HOME_POS);updateDeliveryMapMarker(HOME_POS)
}
function showPickedDelivery(pt){
  let el=document.getElementById('deliveryPicked');if(!el||!pt)return;el.classList.remove('hidden');el.innerHTML=`✓ Destinazione impostata<br><b>${esc(pt.label||[pt.street,pt.city].filter(Boolean).join(', '))}</b>`
}
async function reverseDeliveryPoint(pt){
  let r=await fetch(`https://photon.komoot.io/reverse?lat=${pt.lat}&lon=${pt.lng}&lang=it`);if(!r.ok)throw new Error('Indirizzo non trovato sulla mappa');
  let j=await r.json(),f=(j.features||[])[0];if(!f)return {...pt,label:`${pt.lat.toFixed(6)}, ${pt.lng.toFixed(6)}`};
  let x=photonFeatureToPoint(f);return {...x,lat:pt.lat,lng:pt.lng}
}
function updateDeliveryMapMarker(pt){
  if(!DELIVERY_MAP||!pt)return;
  if(!DELIVERY_MARKER)DELIVERY_MARKER=L.marker([pt.lat,pt.lng]).addTo(DELIVERY_MAP);else DELIVERY_MARKER.setLatLng([pt.lat,pt.lng]);
  DELIVERY_MAP.panTo([pt.lat,pt.lng])
}
async function toggleDeliveryMap(){
  let el=document.getElementById('deliveryMap');if(!el)return;
  if(!el.classList.contains('hidden')){el.classList.add('hidden');if(DELIVERY_MAP){DELIVERY_MAP.remove();DELIVERY_MAP=null;DELIVERY_MARKER=null}return}
  el.classList.remove('hidden');
  let center=HOME_POS||DELIVERY_CITY_POS||USER_POS;
  if(!center){try{center=await currentPosition()}catch(e){center={lat:45.07,lng:7.69}}}
  DELIVERY_MAP=L.map('deliveryMap').setView([center.lat,center.lng],HOME_POS?17:13);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(DELIVERY_MAP);
  if(HOME_POS)updateDeliveryMapMarker(HOME_POS);
  DELIVERY_MAP.on('click',async ev=>{
    let status=document.getElementById('nrStatus');if(status)status.textContent='Leggo il punto scelto sulla mappa…';
    try{
      let pt=await reverseDeliveryPoint({lat:ev.latlng.lat,lng:ev.latlng.lng});let city=document.getElementById('nrCity'),street=document.getElementById('nrStreet');
      if(city)city.value=pt.city||city.value;if(street)street.value=pt.street||street.value;
      HOME_POS={...pt,cityText:city?.value||'',streetText:street?.value||''};updateDeliveryMapMarker(HOME_POS);showPickedDelivery(HOME_POS);
      if(status)status.textContent='✓ Punto di consegna scelto sulla mappa.'
    }catch(e){if(status)status.textContent='Errore mappa: '+e.message}
  });
  setTimeout(()=>DELIVERY_MAP?.invalidateSize(),100)
}
async function fillDeliveryWithGps(){
  let st=document.getElementById('nrStatus');if(st)st.textContent='Rilevo la posizione GPS…';
  try{
    let raw=await currentPosition(),pt=await reverseDeliveryPoint(raw),city=document.getElementById('nrCity'),street=document.getElementById('nrStreet');
    if(city)city.value=pt.city||'';if(street)street.value=pt.street||'';
    HOME_POS={...pt,cityText:city?.value||'',streetText:street?.value||''};DELIVERY_CITY_POS={lat:pt.lat,lng:pt.lng,city:pt.city};
    showPickedDelivery(HOME_POS);updateDeliveryMapMarker(HOME_POS);if(st)st.textContent='✓ Indirizzo di consegna impostato dal GPS.'
  }catch(e){if(st)st.textContent='GPS non disponibile: '+e.message}
}
async function geocodeDeliveryAddress(city,street){
  let q=[street,city,'Italia'].filter(Boolean).join(', ');
  try{
    let fs=await photonSearch(`https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&limit=5&lang=it&layer=house&layer=street`);
    if(fs.length){let pt=photonFeatureToPoint(fs[0]);return {lat:pt.lat,lng:pt.lng,label:pt.label||q,city:pt.city,street:pt.street}}
  }catch(e){}
  let pt=await geocode(q);return {lat:pt.lat,lng:pt.lng,label:pt.label||q,city,street}
}
'''
    s = s[:start] + helpers + s[end:]

# Publish using separate city + street and the selected GPS/map/autocomplete coordinate when available.
start = s.find('async function publishRequest(){')
end = s.find('async function acceptRequest(id){', start)
if start != -1 and end != -1:
    publish = r'''async function publishRequest(){
  let person=nrPerson.value.trim(),title=nrTitle.value.trim(),desc=nrDesc.value.trim(),from=nrFrom.value.trim(),city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',pay=+nrPay.value;
  if(!person||!title||!from||!city||!street){nrStatus.textContent='Compila nome della persona, ritiro, città/frazione e via di consegna.';return}
  nrStatus.textContent='Verifico ritiro e destinazione…';
  try{
    let a=(REQUEST_CATEGORY==='farmacia'&&SELECTED_PLACE)?{lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng,label:SELECTED_PLACE.address||SELECTED_PLACE.name}:await geocode(from);
    let b=(HOME_POS&&HOME_POS.cityText===city&&HOME_POS.streetText===street)?HOME_POS:await geocodeDeliveryAddress(city,street);
    let fullDesc=`Per: ${person}${desc?`\nNote: ${desc}`:''}`;
    let deliveryLabel=b.label||`${street}, ${city}`;
    let {error}=await db.from('consegne').insert({cliente_id:SESSION.user.id,categoria:REQUEST_CATEGORY,titolo:title,descrizione:fullDesc,ritiro_indirizzo:a.label,ritiro_lat:a.lat,ritiro_lng:a.lng,consegna_indirizzo:deliveryLabel,consegna_lat:b.lat,consegna_lng:b.lng,compenso_rider:pay});if(error)throw error;
    await loadRequests();renderAll();closeSheet();SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;DELIVERY_CITY_POS=null;if(DELIVERY_MAP){DELIVERY_MAP.remove();DELIVERY_MAP=null;DELIVERY_MARKER=null}alert('Richiesta pubblicata.')
  }catch(e){nrStatus.textContent='Errore indirizzo: '+e.message+' · prova a scegliere un suggerimento, il GPS o un punto sulla mappa.'}
}
'''
    s = s[:start] + publish + s[end:]

p.write_text(s, encoding='utf-8')
print('smart delivery address patch applied')
