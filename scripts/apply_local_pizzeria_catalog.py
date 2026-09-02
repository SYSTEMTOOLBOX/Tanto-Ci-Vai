from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

marker='/* LOCAL_PIZZERIA_CATALOG_V1 */'
if marker in s:
    print('already applied')
    raise SystemExit(0)

# Label pizza results correctly.
s=s.replace("let t=el.tags||{},type=t.shop||t.amenity||'shop',name=t.name||t.brand||shopTypeLabel(type);",
            "let t=el.tags||{},type=REQUEST_CATEGORY==='pizzeria'?'pizzeria':(t.shop||t.amenity||'shop'),name=t.name||t.brand||shopTypeLabel(type);")
s=s.replace("post_office:'Ufficio postale',parcel_locker:'Locker pacchi'", "post_office:'Ufficio postale',parcel_locker:'Locker pacchi',pizzeria:'Pizzeria'")

old_load="""async function loadShopsAt(pos){
  SEARCH_POS=await reverseGeocodePoint({lat:pos.lat,lng:pos.lng});
  let status=document.getElementById('shopStatus');if(status)status.textContent='Cerco '+shopFilterTitle(SHOP_FILTER).toLowerCase()+' nella zona…';
  try{
    SHOP_RESULTS=await fetchNearbyShops(SEARCH_POS,SHOP_FILTER);
    if(status)status.innerHTML=`📍 Zona scelta: <b>${esc(SEARCH_POS.area||SEARCH_POS.label||'posizione indicata')}</b> · ${SHOP_RESULTS.length} risultati entro 15 km`;
    let mapEl=document.getElementById('shopMap');if(mapEl)mapEl.classList.remove('hidden');
    initShopMap(SEARCH_POS);renderShopList()
  }catch(e){if(status)status.textContent='Errore ricerca negozi: '+e.message}
}
"""

new_load="""/* LOCAL_PIZZERIA_CATALOG_V1 */
async function fetchLocalPlaces(pos){
  if(!REQUEST_CATEGORY||!SESSION?.user)return [];
  let town=(pos.city||pos.area||'').trim();
  if(!town)return [];
  try{
    let {data,error}=await db.from('luoghi_locali').select('id,categoria,nome,indirizzo,citta,lat,lng,verificato').eq('categoria',REQUEST_CATEGORY).ilike('citta',`%${town}%`).limit(30);
    if(error)throw error;
    let out=[];
    for(const row of (data||[])){
      let lat=Number(row.lat),lng=Number(row.lng);
      if(!Number.isFinite(lat)||!Number.isFinite(lng)){
        try{let g=await geocode(row.indirizzo);lat=Number(g.lat);lng=Number(g.lng)}catch(e){continue}
      }
      let rev={};
      try{rev=await reverseGeocodePoint({lat,lng})}catch(e){}
      out.push({local_id:row.id,local:true,verified:!!row.verificato,name:row.nome,address:row.indirizzo,street:rev.street||'',housenumber:rev.housenumber||'',city:row.citta||rev.city||town,shop:REQUEST_CATEGORY==='pizzeria'?'pizzeria':REQUEST_CATEGORY,lat,lng,distance:distanceKm(pos,{lat,lng})});
    }
    return out
  }catch(e){console.warn('Catalogo locale non disponibile',e);return []}
}
async function loadShopsAt(pos){
  SEARCH_POS=await reverseGeocodePoint({lat:pos.lat,lng:pos.lng});
  let status=document.getElementById('shopStatus');if(status)status.textContent=REQUEST_CATEGORY==='pizzeria'?'Cerco pizzerie nella zona…':'Cerco '+shopFilterTitle(SHOP_FILTER).toLowerCase()+' nella zona…';
  let osm=[],local=[],osmErr=null;
  try{osm=await fetchNearbyShops(SEARCH_POS,SHOP_FILTER)}catch(e){osmErr=e;console.warn('Ricerca mappa non disponibile',e)}
  local=await fetchLocalPlaces(SEARCH_POS);
  let merged=[...local];
  for(const p of osm){
    let dup=merged.some(x=>x.name.toLowerCase()===p.name.toLowerCase()||distanceKm({lat:x.lat,lng:x.lng},{lat:p.lat,lng:p.lng})<0.04);
    if(!dup)merged.push(p)
  }
  merged.sort((a,b)=>(b.local?1:0)-(a.local?1:0)||a.distance-b.distance||a.name.localeCompare(b.name,'it'));
  SHOP_RESULTS=merged;
  if(status){
    let area=esc(SEARCH_POS.area||SEARCH_POS.city||SEARCH_POS.label||'posizione indicata');
    if(SHOP_RESULTS.length)status.innerHTML=`📍 Zona scelta: <b>${area}</b> · ${SHOP_RESULTS.length} risultati${local.length?` · <b>${local.length} salvati da Tanto Ci Vai</b>`:''}`;
    else status.innerHTML=`📍 Zona scelta: <b>${area}</b> · nessun locale censito. <b>Puoi comunque indicarlo sulla mappa qui sotto.</b>${osmErr?'':''}`;
  }
  let mapEl=document.getElementById('shopMap');if(mapEl)mapEl.classList.remove('hidden');
  initShopMap(SEARCH_POS);renderShopList()
}
"""
if old_load not in s:
    raise SystemExit('loadShopsAt block not found')
s=s.replace(old_load,new_load)

old_confirm="""function confirmFinderManualPoint(){
  if(!PICKUP_POINT){alert('Tocca prima il punto esatto sulla mappa.');return}
  let ctx=window.__tcvManualFinder||{},name=ctx.placeLabel||'Punto di ritiro';
  SELECTED_PLACE={...PICKUP_POINT,name,addressNoNumber:PICKUP_POINT.addressNoNumber||PICKUP_POINT.address||name,address:PICKUP_POINT.address||PICKUP_POINT.addressNoNumber||name};
  resetPickupMap();
  openNewRequest(2)
}
"""
new_confirm="""async function confirmFinderManualPoint(){
  if(!PICKUP_POINT){alert('Tocca prima il punto esatto sulla mappa.');return}
  let ctx=window.__tcvManualFinder||{},name=ctx.placeLabel||'Punto di ritiro';
  SELECTED_PLACE={...PICKUP_POINT,name,addressNoNumber:PICKUP_POINT.addressNoNumber||PICKUP_POINT.address||name,address:PICKUP_POINT.address||PICKUP_POINT.addressNoNumber||name};
  if(REQUEST_CATEGORY==='pizzeria'&&ctx.typed&&ctx.typed.trim().length>=3&&SESSION?.user){
    try{
      let city=(PICKUP_POINT.city||ctx.town||SEARCH_POS?.city||SEARCH_POS?.area||'').trim();
      let address=(PICKUP_POINT.address||PICKUP_POINT.addressNoNumber||ctx.town||name).trim();
      let {data:exists}=await db.from('luoghi_locali').select('id').eq('categoria','pizzeria').ilike('nome',ctx.typed.trim()).ilike('citta',city||'%').limit(1);
      if(!exists?.length){
        await db.from('luoghi_locali').insert({categoria:'pizzeria',nome:ctx.typed.trim(),indirizzo:address,citta:city||ctx.town||'Zona locale',lat:PICKUP_POINT.lat,lng:PICKUP_POINT.lng,verificato:false,creato_da:SESSION.user.id});
      }
    }catch(e){console.warn('Salvataggio pizzeria locale non riuscito',e)}
  }
  resetPickupMap();
  openNewRequest(2)
}
"""
if old_confirm not in s:
    raise SystemExit('confirmFinderManualPoint block not found')
s=s.replace(old_confirm,new_confirm)

p.write_text(s,encoding='utf-8')
print('patched')
