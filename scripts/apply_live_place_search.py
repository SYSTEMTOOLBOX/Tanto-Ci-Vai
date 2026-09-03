from pathlib import Path
import re

path = Path('index.html')
text = path.read_text(encoding='utf-8')

# Add live-search state next to the existing shop finder state.
old_state = "SHOP_MAP=null,SHOP_RESULTS=[],SHOP_FILTER='supermarket'"
new_state = "SHOP_MAP=null,SHOP_RESULTS=[],SHOP_BASE_RESULTS=[],SHOP_LIVE_SEARCH_ID=0,SHOP_FILTER='supermarket'"
if old_state in text:
    text = text.replace(old_state, new_state, 1)
elif "SHOP_BASE_RESULTS=[]" not in text:
    raise SystemExit('Shop finder state anchor not found')

# Preserve the generic nearby results so clearing a live search restores them.
if "SHOP_BASE_RESULTS=merged.slice();" not in text:
    text = text.replace("  SHOP_RESULTS=merged;\n", "  SHOP_RESULTS=merged;\n  SHOP_BASE_RESULTS=merged.slice();\n", 1)

# Reset both result sets when a new finder is opened.
text = text.replace(
    "REQUEST_CATEGORY=category;SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;SHOP_RESULTS=[];",
    "REQUEST_CATEGORY=category;SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;SHOP_RESULTS=[];SHOP_BASE_RESULTS=[];SHOP_LIVE_SEARCH_ID++;",
    1,
)

# Replace the old client-only filter field with an explicit online place search.
old_field = '<div class="field"><label>CERCA TRA I RISULTATI</label><input id="shopNameSearch" placeholder="${cfg.search}" oninput="renderShopList()"></div>'
new_field = '<div class="field"><label>CERCA NEGOZIO O ATTIVITÀ</label><div class="place-fallback" style="margin-top:0"><input id="shopNameSearch" autocomplete="off" placeholder="${cfg.search}" oninput="if(!this.value.trim())resetShopNameSearch()" onkeydown="if(event.key===\'Enter\'){event.preventDefault();searchShopNameLive()}"><button class="btn primary" type="button" onclick="searchShopNameLive()">Trova</button></div><div class="notice" style="margin-top:7px">Scrivi il nome reale dell’attività nella zona scelta. Esempio: <b>Calzedonia</b>.</div></div>'
if old_field in text:
    text = text.replace(old_field, new_field, 1)
elif 'CERCA NEGOZIO O ATTIVITÀ' not in text:
    raise SystemExit('Shop name search field anchor not found')

# Replace the old "filter only the already loaded results" logic with a targeted live lookup.
pattern = re.compile(r"function visibleShopResults\(\)\{.*?\n\}\nfunction initShopMap\(pos\)\{", re.S)
replacement = r'''function visibleShopResults(){
  return SHOP_RESULTS
}
function liveShopAreaName(){
  return String(SEARCH_POS?.city||SEARCH_POS?.area||document.getElementById('shopTown')?.value||'').trim()
}
function liveShopDistanceOk(p){
  return !SEARCH_POS||!Number.isFinite(+p.lat)||!Number.isFinite(+p.lng)||distanceKm(SEARCH_POS,{lat:+p.lat,lng:+p.lng})<=25
}
function liveShopResult(name,address,street,housenumber,city,shop,lat,lng,source){
  lat=+lat;lng=+lng;if(!Number.isFinite(lat)||!Number.isFinite(lng))return null;
  const p={name:String(name||'Attività').trim(),address:String(address||'').trim(),street:String(street||'').trim(),housenumber:String(housenumber||'').trim(),city:String(city||'').trim(),shop:String(shop||'general').trim(),lat,lng,live:true,source:source||'online'};
  p.distance=SEARCH_POS?distanceKm(SEARCH_POS,p):0;
  return p
}
function liveShopMatchesName(p,q){
  const needle=String(q||'').trim().toLowerCase();if(!needle)return true;
  const hay=(String(p?.name||'')+' '+String(p?.address||'')).toLowerCase();
  return needle.split(/\s+/).filter(Boolean).every(x=>hay.includes(x))
}
function liveShopMerge(rows,p){
  if(!p||!liveShopDistanceOk(p))return;
  const dup=rows.some(x=>String(x.name||'').toLowerCase()===String(p.name||'').toLowerCase()&&distanceKm(x,p)<0.08);
  if(!dup)rows.push(p)
}
async function fetchLiveShopsNominatim(q,area){
  const query=[q,area].filter(Boolean).join(', ');
  const url=`https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=it&addressdetails=1&namedetails=1&limit=15&q=${encodeURIComponent(query)}`;
  const r=await fetch(url,{headers:{'Accept-Language':'it'}});if(!r.ok)throw new Error('Nominatim '+r.status);
  const json=await r.json(),out=[];
  for(const x of json||[]){
    const a=x.address||{},name=x.namedetails?.name||x.name||String(x.display_name||'').split(',')[0]||q;
    if(!liveShopMatchesName({name,address:x.display_name},q))continue;
    const city=a.city||a.town||a.municipality||a.village||a.hamlet||area||'';
    const street=a.road||a.pedestrian||a.footway||a.path||'';
    const hn=a.house_number||'';
    const address=[street+(hn?' '+hn:''),city].filter(Boolean).join(', ')||x.display_name||'';
    liveShopMerge(out,liveShopResult(name,address,street,hn,city,x.type||a.shop||'general',x.lat,x.lon,'nominatim'))
  }
  return out
}
async function fetchLiveShopsPhoton(q,area){
  const query=[q,area].filter(Boolean).join(' ');
  let url=`https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=15`;
  if(SEARCH_POS)url+=`&lat=${encodeURIComponent(SEARCH_POS.lat)}&lon=${encodeURIComponent(SEARCH_POS.lng)}`;
  const r=await fetch(url);if(!r.ok)throw new Error('Photon '+r.status);
  const json=await r.json(),out=[];
  for(const f of json.features||[]){
    const p=f.properties||{},c=f.geometry?.coordinates||[],name=p.name||p.street||'';
    if(!name||!liveShopMatchesName({name,address:[p.street,p.city,p.locality].filter(Boolean).join(' ')},q))continue;
    const city=p.city||p.locality||p.county||area||'',street=p.street||'',hn=p.housenumber||'';
    const address=[street+(hn?' '+hn:''),city].filter(Boolean).join(', ');
    liveShopMerge(out,liveShopResult(name,address,street,hn,city,p.osm_value||p.type||'general',c[1],c[0],'photon'))
  }
  return out
}
function overpassNameRegex(q){
  return String(q||'').replace(/[.*+?^${}()|[\]\\]/g,'\\$&').replace(/"/g,'\\"').slice(0,70)
}
async function fetchLiveShopsOverpass(q){
  if(!SEARCH_POS)return [];
  const needle=overpassNameRegex(q);if(!needle)return [];
  const lat=SEARCH_POS.lat,lng=SEARCH_POS.lng;
  const oq=`[out:json][timeout:15];(nwr["name"~"${needle}",i](around:20000,${lat},${lng});nwr["brand"~"${needle}",i](around:20000,${lat},${lng}););out center tags;`;
  const endpoints=['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter'];
  let json=null,lastErr=null;
  for(const ep of endpoints){try{const r=await fetch(ep+'?data='+encodeURIComponent(oq));if(!r.ok)throw new Error('Overpass '+r.status);json=await r.json();break}catch(e){lastErr=e}}
  if(!json){if(lastErr)console.warn(lastErr);return []}
  const out=[];
  for(const el of json.elements||[]){
    const t=el.tags||{},pt=el.type==='node'?{lat:el.lat,lng:el.lon}:{lat:el.center?.lat,lng:el.center?.lon};
    if(!Number.isFinite(+pt.lat)||!Number.isFinite(+pt.lng))continue;
    const name=t.name||t.brand||q;if(!liveShopMatchesName({name,address:''},q))continue;
    const street=t['addr:street']||'',hn=t['addr:housenumber']||'',city=t['addr:city']||liveShopAreaName();
    const address=[street+(hn?' '+hn:''),city].filter(Boolean).join(', ');
    liveShopMerge(out,liveShopResult(name,address,street,hn,city,t.shop||t.amenity||t.office||'general',pt.lat,pt.lng,'overpass'))
  }
  return out
}
function resetShopNameSearch(){
  SHOP_LIVE_SEARCH_ID++;
  SHOP_RESULTS=SHOP_BASE_RESULTS.slice();
  const st=document.getElementById('shopStatus'),area=liveShopAreaName();
  if(st&&SEARCH_POS)st.innerHTML=`📍 Zona scelta: <b>${esc(area||SEARCH_POS.label||'posizione indicata')}</b> · ${SHOP_RESULTS.length} risultati`;
  if(SEARCH_POS){initShopMap(SEARCH_POS);renderShopList()}
}
async function searchShopNameLive(){
  const input=document.getElementById('shopNameSearch'),q=String(input?.value||'').trim();
  const st=document.getElementById('shopStatus');
  if(!q){resetShopNameSearch();return}
  if(q.length<2){if(st)st.textContent='Scrivi almeno 2 caratteri del nome dell’attività.';return}
  if(!SEARCH_POS){if(st)st.textContent='Prima scegli la città/frazione oppure usa il GPS.';return}
  const id=++SHOP_LIVE_SEARCH_ID,area=liveShopAreaName();
  if(st)st.innerHTML=`🔎 Cerco online <b>${esc(q)}</b>${area?` a <b>${esc(area)}</b>`:''}…`;
  const rows=[];
  for(const p of SHOP_BASE_RESULTS.filter(x=>liveShopMatchesName(x,q)))liveShopMerge(rows,{...p});
  const results=await Promise.allSettled([fetchLiveShopsNominatim(q,area),fetchLiveShopsPhoton(q,area),fetchLiveShopsOverpass(q)]);
  if(id!==SHOP_LIVE_SEARCH_ID)return;
  for(const r of results)if(r.status==='fulfilled')for(const p of r.value||[])liveShopMerge(rows,p);
  const needle=q.toLowerCase();
  rows.sort((a,b)=>{
    const an=String(a.name||'').toLowerCase(),bn=String(b.name||'').toLowerCase();
    const as=an===needle?0:an.startsWith(needle)?1:2,bs=bn===needle?0:bn.startsWith(needle)?1:2;
    return as-bs||a.distance-b.distance||an.localeCompare(bn,'it')
  });
  SHOP_RESULTS=rows.slice(0,30);
  if(st){
    if(SHOP_RESULTS.length)st.innerHTML=`✅ <b>${esc(q)}</b>${area?` · ${esc(area)}`:''} · ${SHOP_RESULTS.length} risultati online`;
    else st.innerHTML=`⚠️ Non trovo <b>${esc(q)}</b>${area?` a ${esc(area)}`:''} nei servizi mappa disponibili. Puoi comunque indicare il punto sulla mappa.`
  }
  initShopMap(SEARCH_POS);renderShopList()
}
function renderShopList(){
  let el=document.getElementById('shopList');if(!el)return;let rows=visibleShopResults();
  el.innerHTML=rows.length?rows.map(p=>{let i=SHOP_RESULTS.indexOf(p);return `<button type="button" class="place-card" onclick="selectShop(${i})"><div><b>${esc(p.name)}</b><small>${p.live?'🌐 Ricerca online · ':''}${esc(shopTypeLabel(p.shop))} · ${esc(p.address||p.city||'Posizione sulla mappa')}${p.housenumber&&!String(p.address||'').includes(String(p.housenumber))?` · N. ${esc(p.housenumber)}`:''}</small></div><span class="place-distance">${Number(p.distance||0).toFixed(1)} km</span></button>`}).join(''):'<div class="notice yellow">Nessun risultato. Prova il nome completo dell’attività oppure premi <b>INDICA SULLA MAPPA</b> qui sotto.</div>'
}
function initShopMap(pos){'''
text2, n = pattern.subn(lambda m: replacement, text, count=1)
if n != 1:
    if 'async function searchShopNameLive()' not in text:
        raise SystemExit(f'Could not replace old shop filtering logic: matches={n}')
    text2 = text
text = text2

# Bump service worker version to push the updated interface promptly.
text = re.sub(r"sw\.js\?v=\d+", "sw.js?v=5", text)

path.write_text(text, encoding='utf-8')
print('Applied live place search: targeted online lookup by business name + selected area')
