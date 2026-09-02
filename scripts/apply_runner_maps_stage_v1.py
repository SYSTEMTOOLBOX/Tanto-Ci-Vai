from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old = '''function missionButtons(r){
  let next=r.stato==='accettata'?'ritirata':r.stato==='ritirata'?'in_consegna':r.stato==='in_consegna'?'consegnata':null;
  let label=next==='ritirata'?'📦 Ritirato':next==='in_consegna'?'Parto per consegna':next==='consegnata'?'Segna consegnata':'';
  if(!next)return '';
  let action=next==='ritirata'?`openPickupEta('${r.id}')`:`setStatus('${r.id}','${next}')`;
  return `<div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"openRunnerNavigation('${r.id}')\">🧭 Navigatore</button><button class=\"btn primary\" onclick=\"${action}\">${label}</button></div>`
}'''

new = '''function missionButtons(r){
  let next=r.stato==='accettata'?'ritirata':r.stato==='ritirata'?'in_consegna':r.stato==='in_consegna'?'consegnata':null;
  let label=next==='ritirata'?'📦 Ritirato':next==='in_consegna'?'Parto per consegna':next==='consegnata'?'Segna consegnata':'';
  if(!next)return '';
  let action=next==='ritirata'?`openPickupEta('${r.id}')`:`setStatus('${r.id}','${next}')`;
  let goingToPickup=r.stato==='accettata';
  let mapsLabel=goingToPickup?'📍 VAI AL RITIRO CON MAPS':'🏠 VAI ALLA CONSEGNA CON MAPS';
  return `<button class=\"btn teal full\" style=\"margin-top:11px;padding:15px;font-size:12px\" onclick=\"openRunnerMapsStage('${r.id}')\">${mapsLabel}</button><div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"openRunnerNavigation('${r.id}')\">🗺️ Mappa Tanto Ci Vai</button><button class=\"btn primary\" onclick=\"${action}\">${label}</button></div>`
}'''

if old not in s:
    raise SystemExit('missionButtons block not found')
s = s.replace(old, new, 1)

old2 = '''function openRunnerExternalNavigation(){
  let r=NAV_REQUEST;if(!r)return;
  let mode=NAV_MODE==='car'?'driving':NAV_MODE==='foot'?'walking':'bicycling';
  let url=`https://www.google.com/maps/dir/?api=1&destination=${r.consegna_lat},${r.consegna_lng}&waypoints=${r.ritiro_lat},${r.ritiro_lng}&travelmode=${mode}`;
  window.open(url,'_blank','noopener')
}'''

new2 = '''function runnerMapsTarget(r){
  if(!r)return null;
  if(r.stato==='accettata')return {lat:+r.ritiro_lat,lng:+r.ritiro_lng,label:'ritiro'};
  if(['ritirata','in_consegna'].includes(r.stato))return {lat:+r.consegna_lat,lng:+r.consegna_lng,label:'consegna'};
  return null
}
function openRunnerMapsStage(id){
  let r=REQUESTS.find(x=>x.id===id);if(!r)return;
  if(r.rider_id!==SESSION.user.id){alert('Maps è disponibile solo al runner che ha preso la richiesta.');return}
  let target=runnerMapsTarget(r);if(!target||!Number.isFinite(target.lat)||!Number.isFinite(target.lng)){alert('Coordinate non disponibili per questa tappa.');return}
  let url=`https://www.google.com/maps/dir/?api=1&destination=${target.lat},${target.lng}&travelmode=driving`;
  window.open(url,'_blank','noopener')
}
function openRunnerExternalNavigation(){
  let r=NAV_REQUEST;if(!r)return;
  let target=runnerMapsTarget(r);if(!target||!Number.isFinite(target.lat)||!Number.isFinite(target.lng)){alert('Coordinate non disponibili per questa tappa.');return}
  let mode=NAV_MODE==='car'?'driving':NAV_MODE==='foot'?'walking':'bicycling';
  let url=`https://www.google.com/maps/dir/?api=1&destination=${target.lat},${target.lng}&travelmode=${mode}`;
  window.open(url,'_blank','noopener')
}'''

if old2 not in s:
    raise SystemExit('openRunnerExternalNavigation block not found')
s = s.replace(old2, new2, 1)

# Make the Maps button inside the internal navigator clearer without changing the map itself.
s = s.replace('↗ Apri in Maps</button>', '↗ Apri questa tappa in Maps</button>', 1)

p.write_text(s, encoding='utf-8')
print('patched staged runner Maps navigation')
