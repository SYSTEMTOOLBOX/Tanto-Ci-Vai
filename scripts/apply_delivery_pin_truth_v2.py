from pathlib import Path

INDEX = Path("index.html")
MARKER = "/* DELIVERY_PIN_TRUTH_V2 */"

text = INDEX.read_text(encoding="utf-8")

required = [
    "const _tcvPublishRequest=publishRequest;",
    "function deliveryCivicChanged()",
    "async function suggestDeliveryStreets()",
    "async function geocodeDeliveryAddress(city,street)",
]
missing = [needle for needle in required if needle not in text]
if missing:
    raise SystemExit("Cannot apply delivery pin patch; missing anchors: " + ", ".join(missing))

if MARKER in text:
    print("DELIVERY_PIN_TRUTH_V2 already applied")
    raise SystemExit(0)

patch = r'''

/* DELIVERY_PIN_TRUTH_V2 */
// A point explicitly chosen on the map (or by GPS) is authoritative.
// Text geocoding remains the fallback when no exact pin was chosen.
let TCV_DELIVERY_PIN_EXACT=false;

function tcvDeliveryTownNorm(v){
  return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim()
}
function tcvDeliverySameTown(actual,selected){
  const a=tcvDeliveryTownNorm(actual),b=tcvDeliveryTownNorm(selected);
  if(!a||!b)return true;
  return a===b||a.includes(b)||b.includes(a)
}
function tcvDeliveryActualTown(pt){
  const raw=pt?.raw||{};
  return String(pt?.city||raw.city||raw.town||raw.municipality||raw.village||raw.locality||raw.hamlet||'').trim()
}

const _tcvReverseDeliveryPointPinV2=reverseDeliveryPoint;
reverseDeliveryPoint=async function(pos){
  const pt=await _tcvReverseDeliveryPointPinV2(pos);
  TCV_DELIVERY_PIN_EXACT=true;
  return pt
};

const _tcvDeliveryCityChangedPinV2=deliveryCityChanged;
deliveryCityChanged=function(){
  TCV_DELIVERY_PIN_EXACT=false;
  return _tcvDeliveryCityChangedPinV2()
};
const _tcvDeliveryStreetChangedPinV2=deliveryStreetChanged;
deliveryStreetChanged=function(){
  TCV_DELIVERY_PIN_EXACT=false;
  return _tcvDeliveryStreetChangedPinV2()
};
const _tcvChooseDeliveryCityPinV2=chooseDeliveryCity;
chooseDeliveryCity=async function(i){
  TCV_DELIVERY_PIN_EXACT=false;
  return await _tcvChooseDeliveryCityPinV2(i)
};
const _tcvChooseDeliveryStreetPinV2=chooseDeliveryStreet;
chooseDeliveryStreet=async function(i){
  TCV_DELIVERY_PIN_EXACT=false;
  return await _tcvChooseDeliveryStreetPinV2(i)
};

const _tcvDeliveryCivicChangedPinV2=deliveryCivicChanged;
deliveryCivicChanged=function(){
  const st=document.getElementById('nrStreet'),cv=document.getElementById('nrCivic'),city=document.getElementById('nrCity');
  if(TCV_DELIVERY_PIN_EXACT&&HOME_POS&&Number.isFinite(+HOME_POS.lat)&&Number.isFinite(+HOME_POS.lng)){
    const street=(st?.value||'').trim(),civic=(cv?.value||'').trim(),cityText=(city?.value||'').trim(),full=[street,civic].filter(Boolean).join(' ');
    HOME_POS={...HOME_POS,city:cityText||HOME_POS.city,street:full||street,cityText,streetText:full||street,civicText:civic,label:canonicalDeliveryLabel(full||street,cityText)};
    showPickedDelivery(HOME_POS);
    return
  }
  return _tcvDeliveryCivicChangedPinV2()
};

// Street autocomplete: never pair the typed municipality with a postcode returned
// by a different OSM result. Show the real municipality and omit unverified CAPs.
suggestDeliveryStreets=async function(){
  const city=document.getElementById('nrCity')?.value.trim()||'',input=document.getElementById('nrStreet'),box=document.getElementById('deliveryStreetSuggest');
  if(!input||!box)return;
  const street=input.value.trim(),queryId=++DELIVERY_QUERY_ID;
  if(city.length<2){deliverySearchMessage(box,'Prima scegli la città.');return}
  if(street.length<2){box.innerHTML='';return}
  try{
    let points=[];
    try{
      const bias=DELIVERY_CITY_POS?`&lat=${DELIVERY_CITY_POS.lat}&lon=${DELIVERY_CITY_POS.lng}`:'';
      const fs=await photonSearch(`https://photon.komoot.io/api/?q=${encodeURIComponent(street+', '+city)}&limit=18&layer=street&layer=house${bias}`);
      points=fs.map(f=>{
        const pt=photonFeatureToPoint(f),p=f.properties||{},actualCity=tcvDeliveryActualTown(pt);
        return {...pt,name:deliveryStreetParts(pt).street||pt.street||p.name||'',actualCity,sub:[actualCity,p.county,p.state].filter(Boolean).join(' · ')}
      }).filter(p=>p.name&&tcvDeliverySameTown(p.actualCity,city))
    }catch(e){}
    if(!points.length){
      const ns=await nominatimDeliverySearch(street+', '+city,18);
      points=ns.map(x=>{
        const pt=nominatimDeliveryPoint(x),a=x.address||{},actualCity=tcvDeliveryActualTown(pt);
        return {...pt,name:deliveryStreetParts(pt).street||pt.street||x.name||'',actualCity,sub:[actualCity,a.county,a.state].filter(Boolean).join(' · ')}
      }).filter(p=>p.name&&tcvDeliverySameTown(p.actualCity,city))
    }
    if(queryId!==DELIVERY_QUERY_ID||input.value.trim()!==street)return;
    const seen=new Set();
    DELIVERY_STREET_RESULTS=points.filter(p=>{
      const key=tcvDeliveryTownNorm((p.name||'')+'|'+(p.actualCity||city));
      if(!key||seen.has(key))return false;seen.add(key);return true
    }).slice(0,8);
    box.innerHTML=DELIVERY_STREET_RESULTS.length?DELIVERY_STREET_RESULTS.map((p,i)=>{
      const place=p.actualCity||city,sub=p.sub||place;
      return `<button type="button" class="autocomplete-item" onpointerdown="event.preventDefault();chooseDeliveryStreet(${i})"><b>${esc(p.name)}</b><small>${esc(sub)}</small></button>`
    }).join(''):'<div class="notice yellow">Nessuna via sicura trovata in questa località: continua a scrivere oppure scegli il punto esatto sulla mappa.</div>'
  }catch(e){
    if(queryId===DELIVERY_QUERY_ID)deliverySearchMessage(box,'Ricerca vie temporaneamente non disponibile.')
  }
};

// Text lookup must resolve inside the municipality the user selected.
// If we cannot validate the municipality, fail safely and invite map selection
// rather than silently accepting a nearby town.
geocodeDeliveryAddress=async function(city,street){
  const q=[street,city,'Italia'].filter(Boolean).join(', ');
  try{
    const ns=await nominatimDeliverySearch(q,12);
    const rows=ns.map(nominatimDeliveryPoint).filter(p=>tcvDeliverySameTown(tcvDeliveryActualTown(p),city));
    if(rows.length){const p=rows[0];return {lat:p.lat,lng:p.lng,label:canonicalDeliveryLabel(street,city),city,street,raw:p.raw}}
  }catch(e){}
  try{
    const fs=await photonSearch(`https://photon.komoot.io/api/?q=${encodeURIComponent(q)}&limit=12&layer=house&layer=street`);
    const rows=fs.map(photonFeatureToPoint).filter(p=>tcvDeliverySameTown(tcvDeliveryActualTown(p),city));
    if(rows.length){const p=rows[0];return {lat:p.lat,lng:p.lng,label:canonicalDeliveryLabel(street,city),city,street,raw:p.raw}}
  }catch(e){}
  throw new Error('Indirizzo non verificato nella località scelta: usa “Scegli sulla mappa” e tocca il punto esatto.')
};

const _tcvCurrentPublishPinV2=publishRequest;
publishRequest=async function(){
  const st=document.getElementById('nrStreet'),cv=document.getElementById('nrCivic'),cityEl=document.getElementById('nrCity');
  const base=(st?.value||'').trim(),civic=(cv?.value||'').trim(),city=(cityEl?.value||'').trim(),full=[base,civic].filter(Boolean).join(' ');
  const hasExactPin=TCV_DELIVERY_PIN_EXACT&&HOME_POS&&Number.isFinite(+HOME_POS.lat)&&Number.isFinite(+HOME_POS.lng);
  if(!hasExactPin)return await _tcvCurrentPublishPinV2();

  const finalStreet=full||base;
  HOME_POS={...HOME_POS,city:city||HOME_POS.city,street:finalStreet,cityText:city,streetText:finalStreet,civicText:civic,label:canonicalDeliveryLabel(finalStreet,city)};
  if(st)st.value=finalStreet;
  const status=document.getElementById('nrStatus');
  if(status)status.textContent='✓ Uso il punto esatto scelto sulla mappa per la consegna.';
  try{
    // Call the original publisher preserved by DELIVERY_CIVIC_SEPARATE_V1.
    // Its HOME_POS equality check now succeeds, so it uses these exact coordinates
    // and does not force another text geocoding or a mandatory civic number.
    return await _tcvPublishRequest()
  }finally{
    if(st)st.value=base
  }
};
'''

pos = text.rfind("</script>")
if pos < 0:
    raise SystemExit("Cannot apply delivery pin patch: closing </script> not found")

text = text[:pos] + patch + "\n" + text[pos:]
INDEX.write_text(text, encoding="utf-8")
print("Applied DELIVERY_PIN_TRUTH_V2")
