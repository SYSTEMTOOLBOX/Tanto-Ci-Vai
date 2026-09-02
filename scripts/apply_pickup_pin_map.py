from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

if '/* PICKUP_PIN_MAP_V1 */' in s:
    print('Pickup pin map already applied')
    raise SystemExit(0)

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(label + ' anchor not found')
    s = s.replace(old, new, 1)

# Dedicated pickup pin state, separate from delivery map and from possibly stale OSM POI coordinates.
replace_once(
    "SHOP_FILTER='supermarket',SELECTED_PLACE=null,HOME_POS=null,SEARCH_POS=null",
    "SHOP_FILTER='supermarket',SELECTED_PLACE=null,PICKUP_MAP=null,PICKUP_MARKER=null,PICKUP_POINT=null,HOME_POS=null,SEARCH_POS=null",
    'pickup globals'
)

# Clean Leaflet pickup map when a sheet closes.
replace_once(
    "function closeSheet(){ov.classList.add('hidden');sheet.classList.add('hidden');document.body.style.overflow=''}",
    "function resetPickupMap(){if(PICKUP_MAP){try{PICKUP_MAP.remove()}catch(e){}}PICKUP_MAP=null;PICKUP_MARKER=null}\nfunction closeSheet(){resetPickupMap();ov.classList.add('hidden');sheet.classList.add('hidden');document.body.style.overflow=''}",
    'close sheet cleanup'
)

# Insert simple pickup-map/GPS helpers before category selection.
anchor = "/* PACCO_ALTRO_V1 */\nfunction chooseRequestCategory(cat){"
helpers = r'''/* PICKUP_PIN_MAP_V1 */
function pickupTextChanged(){
  PICKUP_POINT=null;
  let el=document.getElementById('pickupPicked');if(el){el.classList.add('hidden');el.textContent=''}
}
function pickupStatus(message,ok=true){
  let el=document.getElementById('pickupPicked');if(!el)return;
  el.classList.remove('hidden');el.classList.toggle('delivery-picked',ok);el.textContent=message
}
async function setPickupPointFromCoords(lat,lng,source='map'){
  let nrFromEl=document.getElementById('nrFrom'),nrNum=document.getElementById('nrPickupNumber');
  let typed=(nrFromEl?.value||'').trim(),selectedName=SELECTED_PLACE?.name||'';
  pickupStatus(source==='gps'?'Rilevo indirizzo dalla tua posizione…':'Rilevo l’indirizzo del punto scelto…');
  let rev=await reverseGeocodePoint({lat:Number(lat),lng:Number(lng)});
  let mapped=(rev.addressNoNumber||rev.label||'').trim();
  let name=selectedName||typed||'Punto di ritiro';
  if(SELECTED_PLACE&&mapped&&nrFromEl)nrFromEl.value=mapped;
  else if(!typed&&mapped&&nrFromEl)nrFromEl.value=mapped;
  if(nrNum&&rev.housenumber)nrNum.value=rev.housenumber;
  PICKUP_POINT={lat:Number(lat),lng:Number(lng),name,addressNoNumber:mapped,address:mapped,housenumber:rev.housenumber||'',city:rev.city||'',street:rev.street||'',source};
  if(PICKUP_MAP){
    if(!PICKUP_MARKER)PICKUP_MARKER=L.marker([PICKUP_POINT.lat,PICKUP_POINT.lng],{draggable:true}).addTo(PICKUP_MAP);
    else PICKUP_MARKER.setLatLng([PICKUP_POINT.lat,PICKUP_POINT.lng]);
    PICKUP_MARKER.off('dragend');
    PICKUP_MARKER.on('dragend',e=>{let ll=e.target.getLatLng();setPickupPointFromCoords(ll.lat,ll.lng,'map')});
    PICKUP_MAP.setView([PICKUP_POINT.lat,PICKUP_POINT.lng],17)
  }
  pickupStatus(source==='gps'?'✓ Posizione GPS salvata. Il runner verrà esattamente qui.':'✓ Punto di ritiro salvato. Il runner userà questo pin anche se il negozio non compare sulla mappa.')
}
async function fillPickupWithGps(){
  pickupStatus('Rilevo la posizione GPS…');
  try{let pos=await currentPosition();await setPickupPointFromCoords(pos.lat,pos.lng,'gps')}
  catch(e){pickupStatus('GPS non disponibile o non autorizzato. Puoi usare “Indica sulla mappa”.',false)}
}
async function togglePickupMap(){
  let el=document.getElementById('pickupMap');if(!el)return;
  if(PICKUP_MAP){resetPickupMap();el.classList.add('hidden');return}
  el.classList.remove('hidden');
  pickupStatus('Tocca sulla mappa il punto esatto del ritiro. Puoi anche trascinare il pin dopo averlo messo.');
  let center=PICKUP_POINT||SEARCH_POS||SELECTED_PLACE||null;
  if(!center?.lat){
    let q=(document.getElementById('nrFrom')?.value||'').trim();
    if(q){try{center=await geocode(q)}catch(e){}}
  }
  if(!center?.lat){try{center=await currentPosition()}catch(e){}}
  if(!center?.lat){pickupStatus('Non riesco a centrare la mappa. Scrivi almeno il paese oppure usa “Sono qui”.',false);return}
  PICKUP_MAP=L.map('pickupMap').setView([center.lat,center.lng],PICKUP_POINT?17:14);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(PICKUP_MAP);
  if(PICKUP_POINT){
    PICKUP_MARKER=L.marker([PICKUP_POINT.lat,PICKUP_POINT.lng],{draggable:true}).addTo(PICKUP_MAP);
    PICKUP_MARKER.on('dragend',e=>{let ll=e.target.getLatLng();setPickupPointFromCoords(ll.lat,ll.lng,'map')})
  }
  PICKUP_MAP.on('click',e=>setPickupPointFromCoords(e.latlng.lat,e.latlng.lng,'map'));
  setTimeout(()=>PICKUP_MAP?.invalidateSize(),120)
}
'''
replace_once(anchor, helpers + anchor, 'pickup helpers')

# Reset pin when a new category starts.
replace_once(
    "function chooseRequestCategory(cat){\n  REQUEST_CATEGORY=cat;\n  SELECTED_PLACE=null;",
    "function chooseRequestCategory(cat){\n  REQUEST_CATEGORY=cat;\n  SELECTED_PLACE=null;PICKUP_POINT=null;resetPickupMap();",
    'category pickup reset'
)

# When the request form opens, use the selected POI as an initial point but allow a later override.
replace_once(
    "  const presets={spesa:",
    "  resetPickupMap();PICKUP_POINT=SELECTED_PLACE?.lat!=null&&SELECTED_PLACE?.lng!=null?{...SELECTED_PLACE,source:'poi'}:null;\n  const presets={spesa:",
    'form pickup init'
)

# Make pickup address editable and invalidate stale coordinates if the user manually changes it.
replace_once(
    "<input id=\"nrFrom\" value=\"${esc(fromValue)}\" placeholder=\"Via o luogo, senza numero civico\" ${SELECTED_PLACE?'readonly':''}>",
    "<input id=\"nrFrom\" value=\"${esc(fromValue)}\" placeholder=\"Via o luogo, senza numero civico\" oninput=\"pickupTextChanged()\">",
    'editable pickup field'
)

# Add very simple correction controls directly below pickup/civic fields.
old = "${showPickupCivic?`<div class=\"field\"><label>NUMERO CIVICO</label><input id=\"nrPickupNumber\" value=\"${esc(pickupCivic)}\" placeholder=\"Es. 12/A\" inputmode=\"text\"><div class=\"notice\" style=\"margin-top:7px\">Il numero resta separato dalla via per evitare indirizzi confusi.</div></div>`:''}<div class=\"delivery-smart\">"
new = "${showPickupCivic?`<div class=\"field\"><label>NUMERO CIVICO</label><input id=\"nrPickupNumber\" value=\"${esc(pickupCivic)}\" placeholder=\"Es. 12/A\" inputmode=\"text\"><div class=\"notice\" style=\"margin-top:7px\">Il numero resta separato dalla via per evitare indirizzi confusi.</div></div>`:''}<div class=\"delivery-tools\" style=\"margin-top:8px\"><button type=\"button\" class=\"btn outline\" onclick=\"togglePickupMap()\">🗺️ Indica sulla mappa</button><button type=\"button\" class=\"btn outline\" onclick=\"fillPickupWithGps()\">📍 Sono qui</button></div><div class=\"notice green\" style=\"margin-top:8px\">Negozio mancante o spostato? Non importa: indica il punto esatto. Il navigatore userà il pin e non la vecchia scheda del negozio.</div><div id=\"pickupMap\" class=\"delivery-map hidden\"></div><div id=\"pickupPicked\" class=\"delivery-picked hidden\"></div><div class=\"delivery-smart\">"
replace_once(old, new, 'pickup correction controls')

# Publish exact manually chosen/GPS coordinates instead of trusting the possibly stale OSM POI.
old = "    let pickupAddress=formatPickupAddress(from,pickupNumber),selectedPickup=['farmacia','spesa','pacco','altro'].includes(REQUEST_CATEGORY)&&SELECTED_PLACE;let a=selectedPickup?{lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng,label:`${SELECTED_PLACE.name} · ${pickupAddress}`}:await geocode(pickupAddress);"
new = "    let pickupAddress=formatPickupAddress(from,pickupNumber),selectedPickup=PICKUP_POINT;let a;if(selectedPickup){let mappedAddress=formatPickupAddress(selectedPickup.addressNoNumber||selectedPickup.address||'',pickupNumber||selectedPickup.housenumber||'');let parts=[selectedPickup.name||'',mappedAddress||pickupAddress||from].map(x=>String(x||'').trim()).filter(Boolean);let unique=parts.filter((x,i,arr)=>arr.findIndex(y=>y.toLowerCase()===x.toLowerCase())===i);a={lat:selectedPickup.lat,lng:selectedPickup.lng,label:unique.join(' · ')||pickupAddress||from}}else a=await geocode(pickupAddress);"
replace_once(old, new, 'publish exact pickup pin')

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Pickup pin map applied')
