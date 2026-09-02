from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

if '/* GOOGLE_PLACES_V1 */' in s:
    print('Google Places patch already present')
    raise SystemExit(0)

anchor = "async function fetchNearbyPharmacies(pos){"
if anchor not in s:
    raise SystemExit('pharmacy anchor not found')

google_block = r'''/* GOOGLE_PLACES_V1 */
let GOOGLE_MAPS_API_KEY_CACHE=null,GOOGLE_MAPS_PROMISE=null;
async function getGoogleMapsApiKey(){
  if(GOOGLE_MAPS_API_KEY_CACHE!==null)return GOOGLE_MAPS_API_KEY_CACHE;
  try{
    let {data,error}=await db.from('app_config').select('value').eq('key','google_maps_api_key').maybeSingle();
    if(error)throw error;
    GOOGLE_MAPS_API_KEY_CACHE=(data?.value||'').trim()
  }catch(e){
    console.warn('Configurazione Google Maps non disponibile',e);
    GOOGLE_MAPS_API_KEY_CACHE=''
  }
  return GOOGLE_MAPS_API_KEY_CACHE
}
async function ensureGooglePlaces(){
  let key=await getGoogleMapsApiKey();
  if(!key)return false;
  if(window.google?.maps?.importLibrary){await google.maps.importLibrary('places');return true}
  if(GOOGLE_MAPS_PROMISE)return GOOGLE_MAPS_PROMISE;
  GOOGLE_MAPS_PROMISE=new Promise((resolve,reject)=>{
    const cb='__tcvGoogleMapsReady';
    window[cb]=async()=>{
      try{await google.maps.importLibrary('places');resolve(true)}catch(e){reject(e)}
      finally{try{delete window[cb]}catch(e){}}
    };
    let sc=document.createElement('script');
    sc.async=true;sc.defer=true;
    sc.src='https://maps.googleapis.com/maps/api/js?key='+encodeURIComponent(key)+'&v=weekly&loading=async&libraries=places&callback='+cb;
    sc.onerror=()=>reject(new Error('Google Maps non raggiungibile'));
    document.head.appendChild(sc)
  });
  return GOOGLE_MAPS_PROMISE
}
function googlePlacesTextQuery(category,pos,filter=SHOP_FILTER){
  let town=(pos?.city||pos?.area||'').trim();
  if(category==='farmacia')return `farmacia ${town}`.trim();
  if(category==='pizzeria')return `pizzeria ${town}`.trim();
  if(category==='spesa'){
    if(filter==='food')return `alimentari ${town}`.trim();
    if(filter==='hardware')return `ferramenta ${town}`.trim();
    if(filter==='all')return `negozi ${town}`.trim();
    return `supermercato ${town}`.trim()
  }
  if(category==='pacco')return `ufficio postale locker pacchi ${town}`.trim();
  return ''
}
async function fetchGooglePlaces(pos,category=REQUEST_CATEGORY,filter=SHOP_FILTER){
  let ready=await ensureGooglePlaces();if(!ready)return [];
  let textQuery=googlePlacesTextQuery(category,pos,filter);if(!textQuery)return [];
  const {Place}=await google.maps.importLibrary('places');
  let {places}=await Place.searchByText({
    textQuery,
    fields:['id','displayName','formattedAddress','location','primaryType','googleMapsURI'],
    locationBias:{center:{lat:+pos.lat,lng:+pos.lng},radius:15000},
    language:'it',region:'IT',maxResultCount:20
  });
  let out=[];
  for(const place of (places||[])){
    let loc=place.location;
    let lat=typeof loc?.lat==='function'?loc.lat():Number(loc?.lat),lng=typeof loc?.lng==='function'?loc.lng():Number(loc?.lng);
    if(!Number.isFinite(lat)||!Number.isFinite(lng))continue;
    let shop=category==='pizzeria'?'pizzeria':category==='spesa'?(filter==='hardware'?'hardware':filter==='food'?'grocery':'supermarket'):category==='pacco'?'post_office':category;
    out.push({google:true,google_place_id:place.id,google_maps_uri:place.googleMapsURI||'',name:place.displayName||'Attività',address:place.formattedAddress||'',street:'',housenumber:'',city:pos.city||pos.area||'',shop,lat,lng,distance:distanceKm(pos,{lat,lng})})
  }
  out.sort((a,b)=>a.distance-b.distance||a.name.localeCompare(b.name,'it'));
  return out
}
function googlePlacesAttribution(){
  return `<div class="notice" style="margin:8px 0;background:#fff;border-color:#d9dde5;color:#5e5e5e"><b>Risultati forniti da <span translate="no">Google Maps</span></b></div>`
}
'''
s = s.replace(anchor, google_block + '\n' + anchor, 1)

# Replace loadPharmaciesAt through the next function.
start = s.index('async function loadPharmaciesAt(pos){')
end = s.index('async function openPharmacyFinder(){', start)
new_load_pharmacy = r'''async function loadPharmaciesAt(pos){
  SEARCH_POS=await reverseGeocodePoint(pos);
  let status=document.getElementById('pharmacyStatus');if(status)status.textContent='Cerco le farmacie più vicine…';
  let google=[],googleErr=null;
  try{google=await fetchGooglePlaces(SEARCH_POS,'farmacia','all')}catch(e){googleErr=e;console.warn('Google Places farmacia non disponibile',e)}
  let mapEl=document.getElementById('pharmacyMap');
  if(google.length){
    PHARMACY_RESULTS=google;
    if(PHARMACY_MAP){PHARMACY_MAP.remove();PHARMACY_MAP=null}
    if(mapEl)mapEl.classList.add('hidden');
    if(status)status.innerHTML=`📍 Zona scelta: <b>${esc(SEARCH_POS.area||SEARCH_POS.city||SEARCH_POS.label||'posizione indicata')}</b> · <b>${google.length} farmacie da <span translate="no">Google Maps</span></b>`;
    renderPharmacyList();return
  }
  PHARMACY_RESULTS=await fetchNearbyPharmacies(SEARCH_POS);
  await loadFavoritePharmacies();
  if(status)status.innerHTML=`📍 Zona scelta: <b>${esc(SEARCH_POS.area||SEARCH_POS.label||'posizione indicata')}</b> · ${PHARMACY_RESULTS.length} farmacie entro 15 km${googleErr?' · Google non disponibile, uso la mappa locale':''}`;
  if(mapEl)mapEl.classList.remove('hidden');
  initPharmacyMap(SEARCH_POS);renderPharmacyList()
}
'''
s = s[:start] + new_load_pharmacy + s[end:]

old_select_pharmacy = r'''async function selectPharmacy(i){
  let p=PHARMACY_RESULTS[i];if(!p)return;
  let rev=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
  SELECTED_PLACE={...p,street:rev.street||p.street||'',housenumber:rev.housenumber||p.housenumber||'',city:rev.city||p.city||'',address:rev.addressNoNumber||p.address||p.name};
  if(PHARMACY_MAP){PHARMACY_MAP.remove();PHARMACY_MAP=null}
  openNewRequest(2)
}'''
new_select_pharmacy = r'''async function selectPharmacy(i){
  let p=PHARMACY_RESULTS[i];if(!p)return;
  if(p.google){
    SELECTED_PLACE={...p,street:'',housenumber:'',city:p.city||SEARCH_POS?.city||SEARCH_POS?.area||'',address:p.address||p.name};
    if(PHARMACY_MAP){PHARMACY_MAP.remove();PHARMACY_MAP=null}
    openNewRequest(2);return
  }
  let rev=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
  SELECTED_PLACE={...p,street:rev.street||p.street||'',housenumber:rev.housenumber||p.housenumber||'',city:rev.city||p.city||'',address:rev.addressNoNumber||p.address||p.name};
  if(PHARMACY_MAP){PHARMACY_MAP.remove();PHARMACY_MAP=null}
  openNewRequest(2)
}'''
if old_select_pharmacy not in s:
    raise SystemExit('selectPharmacy block not found')
s = s.replace(old_select_pharmacy, new_select_pharmacy, 1)

start = s.index('function renderPharmacyList(){')
end = s.index('function initPharmacyMap(pos){', start)
new_render_pharmacy = r'''function renderPharmacyList(){
  let el=document.getElementById('pharmacyList');if(!el)return;
  if(!PHARMACY_RESULTS.length){el.innerHTML='<div class="notice yellow">Nessuna farmacia trovata entro 15 km.</div>';return}
  let google=PHARMACY_RESULTS.some(p=>p.google);
  let rows=PHARMACY_RESULTS.map((p,i)=>{
    if(p.google)return `<div class="place-card"><button style="border:0;background:transparent;text-align:left;padding:0;min-width:0;width:100%" onclick="selectPharmacy(${i})"><b>${esc(p.name)}</b><small>${esc(p.address)}</small></button><div class="place-actions"><span class="place-distance">${p.distance.toFixed(1)} km</span></div></div>`;
    return `<div class="place-card"><button style="border:0;background:transparent;text-align:left;padding:0;min-width:0" onclick="selectPharmacy(${i})"><b>${esc(p.name)}</b><small>${esc(p.address)}${p.housenumber?` · N. ${esc(p.housenumber)}`:''}</small></button><div class="place-actions"><span class="place-distance">${p.distance.toFixed(1)} km</span><button class="favbtn ${isFavoritePlace(p)?'on':''}" onclick="toggleFavoritePharmacy(${i},event)" aria-label="Preferita">${isFavoritePlace(p)?'★':'☆'}</button></div></div>`
  }).join('');
  el.innerHTML=(google?googlePlacesAttribution():'')+rows
}
'''
s = s[:start] + new_render_pharmacy + s[end:]

# Replace loadShopsAt through openShopFinder.
start = s.index('async function loadShopsAt(pos){')
end = s.index('function openShopFinder(category=', start)
new_load_shops = r'''async function loadShopsAt(pos){
  SEARCH_POS=await reverseGeocodePoint({lat:pos.lat,lng:pos.lng});
  let status=document.getElementById('shopStatus');if(status)status.textContent=REQUEST_CATEGORY==='pizzeria'?'Cerco pizzerie nella zona…':'Cerco '+shopFilterTitle(SHOP_FILTER).toLowerCase()+' nella zona…';
  let google=[],googleErr=null,local=[];
  try{google=await fetchGooglePlaces(SEARCH_POS,REQUEST_CATEGORY,SHOP_FILTER)}catch(e){googleErr=e;console.warn('Google Places non disponibile',e)}
  local=await fetchLocalPlaces(SEARCH_POS);
  let mapEl=document.getElementById('shopMap');
  if(google.length){
    let merged=[...google];
    for(const p of local){
      let dup=merged.some(x=>x.name.toLowerCase()===p.name.toLowerCase()||distanceKm({lat:x.lat,lng:x.lng},{lat:p.lat,lng:p.lng})<0.04);
      if(!dup)merged.push(p)
    }
    SHOP_RESULTS=merged;
    if(SHOP_MAP){SHOP_MAP.remove();SHOP_MAP=null}
    if(mapEl)mapEl.classList.add('hidden');
    if(status){
      let area=esc(SEARCH_POS.area||SEARCH_POS.city||SEARCH_POS.label||'posizione indicata');
      status.innerHTML=`📍 Zona scelta: <b>${area}</b> · <b>${google.length} risultati da <span translate="no">Google Maps</span></b>${local.length?` · ${local.length} salvati da Tanto Ci Vai`:''}`
    }
    renderShopList();return
  }
  let osm=[],osmErr=null;
  try{osm=await fetchNearbyShops(SEARCH_POS,SHOP_FILTER)}catch(e){osmErr=e;console.warn('Ricerca mappa non disponibile',e)}
  let merged=[...local];
  for(const p of osm){
    let dup=merged.some(x=>x.name.toLowerCase()===p.name.toLowerCase()||distanceKm({lat:x.lat,lng:x.lng},{lat:p.lat,lng:p.lng})<0.04);
    if(!dup)merged.push(p)
  }
  merged.sort((a,b)=>(b.local?1:0)-(a.local?1:0)||a.distance-b.distance||a.name.localeCompare(b.name,'it'));
  SHOP_RESULTS=merged;
  if(status){
    let area=esc(SEARCH_POS.area||SEARCH_POS.city||SEARCH_POS.label||'posizione indicata');
    if(SHOP_RESULTS.length)status.innerHTML=`📍 Zona scelta: <b>${area}</b> · ${SHOP_RESULTS.length} risultati${local.length?` · <b>${local.length} salvati da Tanto Ci Vai</b>`:''}${googleErr?' · Google non disponibile, uso la mappa locale':''}`;
    else status.innerHTML=`📍 Zona scelta: <b>${area}</b> · nessun locale censito. <b>Puoi comunque indicarlo sulla mappa qui sotto.</b>`;
  }
  if(mapEl)mapEl.classList.remove('hidden');
  initShopMap(SEARCH_POS);renderShopList()
}
'''
s = s[:start] + new_load_shops + s[end:]

start = s.index('function renderShopList(){')
end = s.index('function initShopMap(pos){', start)
new_render_shop = r'''function renderShopList(){
  let el=document.getElementById('shopList');if(!el)return;let rows=visibleShopResults();
  if(!rows.length){el.innerHTML='<div class="notice yellow">Non compare nei nostri dati. Va bene lo stesso: premi <b>INDICA SULLA MAPPA</b> qui sotto e scegli il punto esatto.</div>';return}
  let googleRows=rows.filter(p=>p.google),otherRows=rows.filter(p=>!p.google),html='';
  if(googleRows.length){
    html+=googlePlacesAttribution();
    html+=googleRows.map(p=>{let i=SHOP_RESULTS.indexOf(p);return `<button type="button" class="place-card" onclick="selectShop(${i})"><div><b>${esc(p.name)}</b><small>${esc(shopTypeLabel(p.shop))} · ${esc(p.address)}</small></div><span class="place-distance">${p.distance.toFixed(1)} km</span></button>`}).join('')
  }
  if(otherRows.length){
    if(googleRows.length)html+='<div class="notice green" style="margin-top:10px"><b>Salvati da Tanto Ci Vai</b></div>';
    html+=otherRows.map(p=>{let i=SHOP_RESULTS.indexOf(p);return `<button type="button" class="place-card" onclick="selectShop(${i})"><div><b>${esc(p.name)}</b><small>${esc(shopTypeLabel(p.shop))} · ${esc(p.address)}${p.housenumber?` · N. ${esc(p.housenumber)}`:''}</small></div><span class="place-distance">${p.distance.toFixed(1)} km</span></button>`}).join('')
  }
  el.innerHTML=html
}
'''
s = s[:start] + new_render_shop + s[end:]

old_select_shop = r'''async function selectShop(i){
  let p=SHOP_RESULTS[i];if(!p)return;
  let st=document.getElementById('shopStatus');if(st)st.textContent='Recupero indirizzo e numero civico…';
  try{
    let rev=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
    SELECTED_PLACE={...p,street:rev.street||p.street||'',housenumber:rev.housenumber||p.housenumber||'',city:rev.city||p.city||'',address:rev.addressNoNumber||p.address||p.name};
  }catch(e){SELECTED_PLACE=p}
  if(SHOP_MAP){SHOP_MAP.remove();SHOP_MAP=null}
  openNewRequest(2)
}'''
new_select_shop = r'''async function selectShop(i){
  let p=SHOP_RESULTS[i];if(!p)return;
  if(p.google){
    SELECTED_PLACE={...p,street:'',housenumber:'',city:p.city||SEARCH_POS?.city||SEARCH_POS?.area||'',address:p.address||p.name};
    if(SHOP_MAP){SHOP_MAP.remove();SHOP_MAP=null}
    openNewRequest(2);return
  }
  let st=document.getElementById('shopStatus');if(st)st.textContent='Recupero indirizzo e numero civico…';
  try{
    let rev=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
    SELECTED_PLACE={...p,street:rev.street||p.street||'',housenumber:rev.housenumber||p.housenumber||'',city:rev.city||p.city||'',address:rev.addressNoNumber||p.address||p.name};
  }catch(e){SELECTED_PLACE=p}
  if(SHOP_MAP){SHOP_MAP.remove();SHOP_MAP=null}
  openNewRequest(2)
}'''
if old_select_shop not in s:
    raise SystemExit('selectShop block not found')
s = s.replace(old_select_shop, new_select_shop, 1)

p.write_text(s, encoding='utf-8')
print('Google Places ready patch applied')
