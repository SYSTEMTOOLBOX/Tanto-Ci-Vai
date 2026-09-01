from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

# 1) Add shop finder state.
old_state = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SELECTED_PLACE=null,HOME_POS=null,SEARCH_POS=null,FAVORITES=[],NAV_MAP=null,NAV_ROUTE_LAYER=null,NAV_WATCH=null,NAV_ROUTE=null,NAV_MODE='car',NAV_MARKER=null,NAV_REQUEST=null,DELIVERY_MAP=null,DELIVERY_MARKER=null,DELIVERY_CITY_RESULTS=[],DELIVERY_STREET_RESULTS=[],DELIVERY_TIMER=null,DELIVERY_CITY_POS=null;"
new_state = "let AUTH_MODE='login',SESSION=null,PROFILE=null,REQUESTS=[],CHANNEL=null,MAP=null,USER_POS=null,PHARMACY_MAP=null,PHARMACY_RESULTS=[],SHOP_MAP=null,SHOP_RESULTS=[],SHOP_FILTER='supermarket',SELECTED_PLACE=null,HOME_POS=null,SEARCH_POS=null,FAVORITES=[],NAV_MAP=null,NAV_ROUTE_LAYER=null,NAV_WATCH=null,NAV_ROUTE=null,NAV_MODE='car',NAV_MARKER=null,NAV_REQUEST=null,DELIVERY_MAP=null,DELIVERY_MARKER=null,DELIVERY_CITY_RESULTS=[],DELIVERY_STREET_RESULTS=[],DELIVERY_TIMER=null,DELIVERY_CITY_POS=null;"
if old_state not in s:
    raise SystemExit('state declaration not found')
s = s.replace(old_state, new_state, 1)

# 2) Spesa now opens the real shop finder before the request form.
old_choose = """function chooseRequestCategory(cat){
  REQUEST_CATEGORY=cat;
  SELECTED_PLACE=null;
  if(cat==='farmacia'){openPharmacyFinder();return}
  openNewRequest(2)
}
"""
new_choose = """function chooseRequestCategory(cat){
  REQUEST_CATEGORY=cat;
  SELECTED_PLACE=null;
  if(cat==='farmacia'){openPharmacyFinder();return}
  if(cat==='spesa'){openShopFinder();return}
  openNewRequest(2)
}
"""
if old_choose not in s:
    raise SystemExit('chooseRequestCategory block not found')
s = s.replace(old_choose, new_choose, 1)

# 3) Make the selected shop visible in the request form exactly like a pharmacy.
old_detail = "let detailLabel=REQUEST_CATEGORY==='farmacia'?'ORDINE / PRENOTAZIONE / COSA RITIRARE':'NOTE PER IL RUNNER / PUNTO DI RITIRO';"
new_detail = "let detailLabel=REQUEST_CATEGORY==='farmacia'?'ORDINE / PRENOTAZIONE / COSA RITIRARE':REQUEST_CATEGORY==='spesa'?'LISTA SPESA / COSA COMPRARE / NOTE':'NOTE PER IL RUNNER / PUNTO DI RITIRO';"
if old_detail not in s:
    raise SystemExit('detail label not found')
s = s.replace(old_detail, new_detail, 1)

old_note = "let pharmacyNote=REQUEST_CATEGORY==='farmacia'&&SELECTED_PLACE?`<div class=\"pharmacy-location\">💊 <b>${esc(SELECTED_PLACE.name)}</b><br>${esc(SELECTED_PLACE.address||'Farmacia selezionata')} · ${SELECTED_PLACE.distance.toFixed(1)} km dalla zona cercata</div>`:'';"
new_note = "let pharmacyNote=SELECTED_PLACE?`<div class=\"pharmacy-location\">${REQUEST_CATEGORY==='farmacia'?'💊':'🏪'} <b>${esc(SELECTED_PLACE.name)}</b><br>${esc(SELECTED_PLACE.address||'Luogo selezionato')}${Number.isFinite(SELECTED_PLACE.distance)?` · ${SELECTED_PLACE.distance.toFixed(1)} km dalla zona cercata`:''}</div>`:'';"
if old_note not in s:
    raise SystemExit('selected place note not found')
s = s.replace(old_note, new_note, 1)

# 4) When a shop is selected, use its exact coordinates/address instead of geocoding a text field again.
old_pickup = "let a=(REQUEST_CATEGORY==='farmacia'&&SELECTED_PLACE)?{lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng,label:SELECTED_PLACE.address||SELECTED_PLACE.name}:await geocode(from);"
new_pickup = "let a=((REQUEST_CATEGORY==='farmacia'||REQUEST_CATEGORY==='spesa')&&SELECTED_PLACE)?{lat:SELECTED_PLACE.lat,lng:SELECTED_PLACE.lng,label:SELECTED_PLACE.address||SELECTED_PLACE.name}:await geocode(from);"
if old_pickup not in s:
    raise SystemExit('pickup geocode line not found')
s = s.replace(old_pickup, new_pickup, 1)

# 5) Add real shop/supermarket/hardware discovery using OpenStreetMap/Overpass.
anchor = """function selectPharmacy(i){
  SELECTED_PLACE=PHARMACY_RESULTS[i];if(!SELECTED_PLACE)return;openNewRequest(2)
}
"""
if anchor not in s:
    raise SystemExit('pharmacy selection anchor not found')

shop_code = r'''function shopFilterValues(filter){
  if(filter==='food')return ['convenience','grocery','bakery','butcher','greengrocer','deli','cheese','pasta','farm'];
  if(filter==='hardware')return ['hardware','doityourself','paint','garden_centre','trade'];
  if(filter==='all')return ['supermarket','convenience','grocery','bakery','butcher','greengrocer','deli','cheese','pasta','farm','hardware','doityourself','paint','garden_centre','trade','general','department_store','variety_store'];
  return ['supermarket','convenience','grocery'];
}
function shopTypeLabel(v){
  const labels={supermarket:'Supermercato',convenience:'Alimentari',grocery:'Alimentari',bakery:'Panetteria',butcher:'Macelleria',greengrocer:'Frutta e verdura',deli:'Gastronomia',cheese:'Formaggi',pasta:'Pasta fresca',farm:'Prodotti agricoli',hardware:'Ferramenta',doityourself:'Brico / fai da te',paint:'Colorificio',garden_centre:'Garden / ferramenta',trade:'Forniture',general:'Negozio',department_store:'Grande magazzino',variety_store:'Emporio'};
  return labels[v]||'Negozio'
}
function shopFilterTitle(filter){return filter==='food'?'Alimentari':filter==='hardware'?'Ferramenta / Brico':filter==='all'?'Tutti i negozi':'Supermercati'}
function setShopFilter(filter){
  SHOP_FILTER=filter;
  ['supermarket','food','hardware','all'].forEach(x=>document.getElementById('shop-filter-'+x)?.classList.toggle('on',x===filter));
  if(SEARCH_POS)loadShopsAt(SEARCH_POS)
}
async function fetchNearbyShops(pos,filter=SHOP_FILTER){
  const values=shopFilterValues(filter).join('|');
  const q=`[out:json][timeout:20];(node["shop"~"^(${values})$"](around:15000,${pos.lat},${pos.lng});way["shop"~"^(${values})$"](around:15000,${pos.lat},${pos.lng});relation["shop"~"^(${values})$"](around:15000,${pos.lat},${pos.lng}););out center tags;`;
  const endpoints=['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter'];
  let json=null,lastErr=null;
  for(const ep of endpoints){try{let r=await fetch(ep+'?data='+encodeURIComponent(q));if(!r.ok)throw new Error('servizio '+r.status);json=await r.json();break}catch(e){lastErr=e}}
  if(!json)throw lastErr||new Error('Ricerca negozi non disponibile');
  let seen=new Set(),out=[];
  for(const el of json.elements||[]){
    let lat=el.lat??el.center?.lat,lng=el.lon??el.center?.lon;if(lat==null||lng==null)continue;
    let t=el.tags||{},type=t.shop||'shop',name=t.name||t.brand||shopTypeLabel(type);
    let key=`${el.type}:${el.id}`;if(seen.has(key))continue;seen.add(key);
    let street=[t['addr:street'],t['addr:housenumber']].filter(Boolean).join(' '),city=t['addr:city']||t['addr:town']||t['addr:village']||'';
    let address=t['addr:full']||[street,city].filter(Boolean).join(', ')||name;
    out.push({osm_type:el.type,osm_id:Number(el.id),name,address,shop:type,lat:Number(lat),lng:Number(lng),distance:distanceKm(pos,{lat:Number(lat),lng:Number(lng)})})
  }
  out.sort((a,b)=>a.distance-b.distance||a.name.localeCompare(b.name,'it'));
  return out.slice(0,40)
}
function visibleShopResults(){
  let q=(document.getElementById('shopNameSearch')?.value||'').trim().toLowerCase();
  if(!q)return SHOP_RESULTS;
  return SHOP_RESULTS.filter(p=>(p.name+' '+p.address+' '+shopTypeLabel(p.shop)).toLowerCase().includes(q))
}
function renderShopList(){
  let el=document.getElementById('shopList');if(!el)return;let rows=visibleShopResults();
  el.innerHTML=rows.length?rows.map(p=>{let i=SHOP_RESULTS.indexOf(p);return `<button type="button" class="place-card" onclick="selectShop(${i})"><div><b>${esc(p.name)}</b><small>${esc(shopTypeLabel(p.shop))} · ${esc(p.address)}</small></div><span class="place-distance">${p.distance.toFixed(1)} km</span></button>`}).join(''):'<div class="notice yellow">Nessun negozio trovato con questo filtro. Prova “Tutti” oppure cambia zona.</div>'
}
function initShopMap(pos){
  if(SHOP_MAP){SHOP_MAP.remove();SHOP_MAP=null}
  SHOP_MAP=L.map('shopMap').setView([pos.lat,pos.lng],13);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(SHOP_MAP);
  let bounds=[[pos.lat,pos.lng]];
  L.circleMarker([pos.lat,pos.lng],{radius:10,weight:4,fillOpacity:.95}).addTo(SHOP_MAP).bindPopup('<b>Zona scelta</b>');
  SHOP_RESULTS.slice(0,30).forEach((p,i)=>{bounds.push([p.lat,p.lng]);L.marker([p.lat,p.lng]).addTo(SHOP_MAP).bindPopup(`<b>${esc(p.name)}</b><br>${esc(shopTypeLabel(p.shop))}<br>${p.distance.toFixed(1)} km<br><button onclick="selectShop(${i})">Scegli questo negozio</button>`) });
  if(bounds.length>1)SHOP_MAP.fitBounds(bounds,{padding:[25,25],maxZoom:14});
  setTimeout(()=>SHOP_MAP?.invalidateSize(),120)
}
async function loadShopsAt(pos){
  SEARCH_POS=await reverseGeocodePoint({lat:pos.lat,lng:pos.lng});
  let status=document.getElementById('shopStatus');if(status)status.textContent='Cerco '+shopFilterTitle(SHOP_FILTER).toLowerCase()+' nella zona…';
  try{
    SHOP_RESULTS=await fetchNearbyShops(SEARCH_POS,SHOP_FILTER);
    if(status)status.innerHTML=`📍 Zona scelta: <b>${esc(SEARCH_POS.area||SEARCH_POS.label||'posizione indicata')}</b> · ${SHOP_RESULTS.length} risultati entro 15 km`;
    let mapEl=document.getElementById('shopMap');if(mapEl)mapEl.classList.remove('hidden');
    initShopMap(SEARCH_POS);renderShopList()
  }catch(e){if(status)status.textContent='Errore ricerca negozi: '+e.message}
}
function openShopFinder(){
  REQUEST_CATEGORY='spesa';SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;SHOP_RESULTS=[];SHOP_FILTER='supermarket';
  openSheet(`${head('NEGOZI VICINI','Dove devo fare la spesa?','Scegli la zona: troviamo supermercati, CRAI/Lidl se presenti nei dati della zona, alimentari, ferramenta e altri negozi reali.')}<button class="gpsbtn" onclick="searchShopsByGps()">📍 Usa la posizione GPS di questo telefono</button><div class="place-fallback"><input id="shopTown" placeholder="Oppure scrivi città o frazione · es. Cavagnolo"><button class="btn outline" onclick="searchShopsByText()">Cerca</button></div><div class="delivery-tools" style="margin-top:10px"><button id="shop-filter-supermarket" class="nav-mode on" onclick="setShopFilter('supermarket')">🛒 Supermercati</button><button id="shop-filter-food" class="nav-mode" onclick="setShopFilter('food')">🥖 Alimentari</button><button id="shop-filter-hardware" class="nav-mode" onclick="setShopFilter('hardware')">🔧 Ferramenta</button><button id="shop-filter-all" class="nav-mode" onclick="setShopFilter('all')">🏪 Tutti</button></div><div id="shopStatus" class="pharmacy-location">Raggio di ricerca: 15 km dalla posizione scelta.</div><div id="shopMap" class="place-map hidden"></div><div class="field"><label>CERCA TRA I RISULTATI</label><input id="shopNameSearch" placeholder="Es. CRAI, Lidl, ferramenta…" oninput="renderShopList()"></div><div id="shopList" class="place-list"></div><button class="btn outline full" style="margin-top:10px" onclick="SELECTED_PLACE=null;openNewRequest(2)">Non trovo il negozio · inserisco manualmente</button>`)
}
async function searchShopsByGps(){
  let st=document.getElementById('shopStatus');if(st)st.textContent='Rilevo il GPS…';
  try{let pos=await currentPosition();await loadShopsAt(pos)}catch(e){if(st)st.textContent='GPS non disponibile o non autorizzato. Puoi sempre scrivere città o frazione.'}
}
async function searchShopsByText(){
  let q=document.getElementById('shopTown')?.value.trim();if(!q)return;
  let st=document.getElementById('shopStatus');if(st)st.textContent='Cerco '+q+'…';
  try{let p=await geocode(q);await loadShopsAt(p)}catch(e){if(st)st.textContent='Errore: '+e.message}
}
async function selectShop(i){
  let p=SHOP_RESULTS[i];if(!p)return;
  let st=document.getElementById('shopStatus');if(st)st.textContent='Recupero indirizzo completo del negozio…';
  try{
    let rev=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
    SELECTED_PLACE={...p,address:rev.label||p.address||p.name};
  }catch(e){SELECTED_PLACE=p}
  if(SHOP_MAP){SHOP_MAP.remove();SHOP_MAP=null}
  openNewRequest(2)
}
'''

s = s.replace(anchor, anchor + shop_code, 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Shop finder patch applied')
