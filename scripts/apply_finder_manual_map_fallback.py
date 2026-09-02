from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

if '/* FINDER_MANUAL_MAP_V1 */' in s:
    print('Finder manual map fallback already applied')
    raise SystemExit(0)

def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(label + ' anchor not found')
    s = s.replace(old, new, 1)

# Add a generic exact-point picker that works even when OSM has no business entry.
anchor = "function chooseRequestCategory(cat){"
helper = r'''/* FINDER_MANUAL_MAP_V1 */
function manualFinderContext(kind='shop'){
  let isPharmacy=kind==='pharmacy';
  let typed=(document.getElementById(isPharmacy?'pharmacyNameSearch':'shopNameSearch')?.value||'').trim();
  let town=(document.getElementById(isPharmacy?'pharmacyTown':'shopTown')?.value||SEARCH_POS?.area||SEARCH_POS?.city||'').trim();
  return {kind,isPharmacy,typed,town,center:SEARCH_POS};
}
function openFinderManualMap(kind='shop'){
  document.activeElement?.blur?.();
  let ctx=manualFinderContext(kind),center=ctx.center;
  if(!center?.lat||!center?.lng){
    alert('Prima cerca il paese o la frazione, così posso centrare la mappa nella zona giusta.');
    return;
  }
  if(SHOP_MAP){try{SHOP_MAP.remove()}catch(e){}SHOP_MAP=null}
  if(PHARMACY_MAP){try{PHARMACY_MAP.remove()}catch(e){}PHARMACY_MAP=null}
  resetPickupMap();PICKUP_POINT=null;SELECTED_PLACE=null;
  let placeLabel=ctx.typed||(ctx.isPharmacy?'Farmacia':'Punto di ritiro');
  let title=ctx.town?`Indica il punto a ${ctx.town}`:'Indica il punto esatto';
  openSheet(`${head('PUNTO NON PRESENTE SULLA MAPPA',title,'Non serve che il negozio sia registrato: tocca semplicemente il punto esatto sulla mappa.')}<div class="notice green" style="margin-top:10px"><b>${esc(placeLabel)}</b><br>👆 Tocca il punto corretto. Puoi trascinare il pin se vuoi aggiustarlo.</div><div id="finderManualMap" class="route-map" style="height:390px;min-height:340px"></div><div id="finderManualStatus" class="notice yellow">Nessun punto scelto.</div><button id="finderManualConfirm" class="btn teal full" style="margin-top:10px" disabled onclick="confirmFinderManualPoint()">✓ Usa questo punto di ritiro</button><button class="btn outline full" style="margin-top:8px" onclick="resetPickupMap();openNewRequest(1)">← Cambia tipo richiesta</button>`);
  window.__tcvManualFinder={...ctx,placeLabel};
  setTimeout(()=>initFinderManualMap(center),80)
}
function initFinderManualMap(center){
  let el=document.getElementById('finderManualMap');if(!el)return;
  resetPickupMap();
  PICKUP_MAP=L.map('finderManualMap').setView([center.lat,center.lng],15);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(PICKUP_MAP);
  L.circleMarker([center.lat,center.lng],{radius:8,weight:3,fillOpacity:.8}).addTo(PICKUP_MAP).bindPopup('Centro zona cercata');
  PICKUP_MAP.on('click',e=>setFinderManualPoint(e.latlng.lat,e.latlng.lng));
  setTimeout(()=>PICKUP_MAP?.invalidateSize(),120)
}
async function setFinderManualPoint(lat,lng){
  let st=document.getElementById('finderManualStatus');if(st)st.textContent='Recupero la via del punto scelto…';
  let rev=await reverseGeocodePoint({lat:Number(lat),lng:Number(lng)});
  PICKUP_POINT={lat:Number(lat),lng:Number(lng),name:window.__tcvManualFinder?.placeLabel||'Punto di ritiro',addressNoNumber:rev.addressNoNumber||rev.label||'',address:rev.addressNoNumber||rev.label||'',housenumber:rev.housenumber||'',city:rev.city||'',street:rev.street||'',source:'manual-finder-map'};
  if(PICKUP_MAP){
    if(!PICKUP_MARKER)PICKUP_MARKER=L.marker([lat,lng],{draggable:true}).addTo(PICKUP_MAP);
    else PICKUP_MARKER.setLatLng([lat,lng]);
    PICKUP_MARKER.off('dragend');
    PICKUP_MARKER.on('dragend',e=>{let ll=e.target.getLatLng();setFinderManualPoint(ll.lat,ll.lng)});
    PICKUP_MAP.setView([lat,lng],17)
  }
  if(st)st.innerHTML=`✓ Punto scelto${PICKUP_POINT.addressNoNumber?` · <b>${esc(PICKUP_POINT.addressNoNumber)}</b>`:''}. Il runner verrà a queste coordinate esatte.`;
  let btn=document.getElementById('finderManualConfirm');if(btn)btn.disabled=false
}
function confirmFinderManualPoint(){
  if(!PICKUP_POINT){alert('Tocca prima il punto esatto sulla mappa.');return}
  let ctx=window.__tcvManualFinder||{},name=ctx.placeLabel||'Punto di ritiro';
  SELECTED_PLACE={...PICKUP_POINT,name,addressNoNumber:PICKUP_POINT.addressNoNumber||PICKUP_POINT.address||name,address:PICKUP_POINT.address||PICKUP_POINT.addressNoNumber||name};
  resetPickupMap();
  openNewRequest(2)
}
'''
replace_once(anchor, helper + anchor, 'category function')

# Shop/Pacco/Altro: replace the dead-end manual button with the exact map fallback.
old_shop = '<button class="btn outline full" style="margin-top:10px" onclick="SELECTED_PLACE=null;openNewRequest(2)">${cfg.manual}</button>'
new_shop = '<button class="btn teal full" style="margin-top:10px" onclick="openFinderManualMap(\'shop\')">🗺️ Non lo trovo · INDICA SULLA MAPPA</button>'
replace_once(old_shop, new_shop, 'shop manual button')

# Make the empty-state message tell the user exactly what to do next.
replace_once(
    "'<div class=\"notice yellow\">Nessun negozio trovato con questo filtro. Prova “Tutti” oppure cambia zona.</div>'",
    "'<div class=\"notice yellow\">Non compare nei nostri dati. Va bene lo stesso: premi <b>INDICA SULLA MAPPA</b> qui sotto e scegli il punto esatto.</div>'",
    'shop empty message'
)

# Pharmacy finder gets the same safety valve for missing or moved pharmacies.
old_pharmacy = "<div id=\"pharmacyMap\" class=\"place-map hidden\"></div><div id=\"pharmacyList\" class=\"place-list\"></div>`"
new_pharmacy = "<div id=\"pharmacyMap\" class=\"place-map hidden\"></div><div id=\"pharmacyList\" class=\"place-list\"></div><button class=\"btn teal full\" style=\"margin-top:10px\" onclick=\"openFinderManualMap('pharmacy')\">🗺️ Farmacia mancante o spostata · INDICA SULLA MAPPA</button>`"
replace_once(old_pharmacy, new_pharmacy, 'pharmacy fallback button')

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Finder manual map fallback applied')
