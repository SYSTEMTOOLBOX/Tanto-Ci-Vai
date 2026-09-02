from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old = '''function missionButtons(r){
  let next=r.stato==='accettata'?'ritirata':r.stato==='ritirata'?'in_consegna':r.stato==='in_consegna'?'consegnata':null;
  let label=next==='ritirata'?'📦 Ritirato':next==='in_consegna'?'Parto per consegna':next==='consegnata'?'Segna consegnata':'';
  if(!next)return '';
  let action=next==='ritirata'?`openPickupEta('${r.id}')`:`setStatus('${r.id}','${next}')`;
  let goingToPickup=r.stato==='accettata';
  let mapsLabel=goingToPickup?'📍 VAI AL RITIRO CON MAPS':'🏠 VAI ALLA CONSEGNA CON MAPS';
  return `<button class=\"btn teal full\" style=\"margin-top:11px;padding:15px;font-size:12px\" onclick=\"openRunnerMapsStage('${r.id}')\">${mapsLabel}</button><div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"openRunnerNavigation('${r.id}')\">🗺️ Mappa Tanto Ci Vai</button><button class=\"btn primary\" onclick=\"${action}\">${label}</button></div>`
}'''

new = '''function runnerPendingPickups(){
  return REQUESTS.filter(x=>x.rider_id===SESSION.user.id&&x.stato==='accettata'&&Number.isFinite(+x.ritiro_lat)&&Number.isFinite(+x.ritiro_lng))
}
function runnerUniquePickupStops(reqs){
  let seen=new Set(),out=[];
  reqs.forEach(r=>{let lat=+r.ritiro_lat,lng=+r.ritiro_lng,key=lat.toFixed(5)+','+lng.toFixed(5);if(seen.has(key))return;seen.add(key);out.push({lat,lng,r})});
  return out
}
function runnerOrderPickupStops(stops){
  let start=USER_POS||MAP_PLAN_START;if(!start||!Number.isFinite(+start.lat)||!Number.isFinite(+start.lng))return [...stops];
  let left=[...stops],ordered=[],cur={lat:+start.lat,lng:+start.lng};
  while(left.length){let best=0,bestD=Infinity;left.forEach((x,i)=>{let d=mapPlanCrowKm(cur,x);if(d<bestD){bestD=d;best=i}});let hit=left.splice(best,1)[0];ordered.push(hit);cur=hit}
  return ordered
}
function missionButtons(r){
  let next=r.stato==='accettata'?'ritirata':r.stato==='ritirata'?'in_consegna':r.stato==='in_consegna'?'consegnata':null;
  let label=next==='ritirata'?'📦 Ritirato':next==='in_consegna'?'Parto per consegna':next==='consegnata'?'Segna consegnata':'';
  if(!next)return '';
  let action=next==='ritirata'?`openPickupEta('${r.id}')`:`setStatus('${r.id}','${next}')`;
  let pending=runnerPendingPickups(),stops=runnerUniquePickupStops(pending);
  let mapsLabel=pending.length?(pending.length===1?'📍 VAI AL RITIRO CON MAPS':`📍 VAI AI RITIRI CON MAPS · ${pending.length} ordini${stops.length<pending.length?` / ${stops.length} fermate`:''}`):'🏠 VAI ALLA CONSEGNA CON MAPS';
  return `<button class=\"btn teal full\" style=\"margin-top:11px;padding:15px;font-size:12px\" onclick=\"openRunnerMapsStage('${r.id}')\">${mapsLabel}</button><div class=\"rowbtn\"><button class=\"btn outline\" onclick=\"openRunnerNavigation('${r.id}')\">🗺️ Mappa Tanto Ci Vai</button><button class=\"btn primary\" onclick=\"${action}\">${label}</button></div>`
}'''

if old not in s:
    raise SystemExit('missionButtons v1 block not found')
s = s.replace(old, new, 1)

old2 = '''function openRunnerMapsStage(id){
  let r=REQUESTS.find(x=>x.id===id);if(!r)return;
  if(r.rider_id!==SESSION.user.id){alert('Maps è disponibile solo al runner che ha preso la richiesta.');return}
  let target=runnerMapsTarget(r);if(!target||!Number.isFinite(target.lat)||!Number.isFinite(target.lng)){alert('Coordinate non disponibili per questa tappa.');return}
  let url=`https://www.google.com/maps/dir/?api=1&destination=${target.lat},${target.lng}&travelmode=driving`;
  window.open(url,'_blank','noopener')
}'''

new2 = '''function openRunnerMapsStage(id){
  let r=REQUESTS.find(x=>x.id===id);if(!r)return;
  if(r.rider_id!==SESSION.user.id){alert('Maps è disponibile solo al runner che ha preso la richiesta.');return}
  let pending=runnerPendingPickups();
  if(pending.length){
    let stops=runnerOrderPickupStops(runnerUniquePickupStops(pending));
    if(!stops.length){alert('Coordinate dei ritiri non disponibili.');return}
    let last=stops[stops.length-1],url=`https://www.google.com/maps/dir/?api=1&destination=${last.lat},${last.lng}&travelmode=driving`;
    if(stops.length>1){let waypoints=stops.slice(0,-1).map(x=>`${x.lat},${x.lng}`).join('|');url+=`&waypoints=${encodeURIComponent(waypoints)}`}
    window.open(url,'_blank','noopener');return
  }
  let target=runnerMapsTarget(r);if(!target||!Number.isFinite(target.lat)||!Number.isFinite(target.lng)){alert('Coordinate non disponibili per questa tappa.');return}
  let url=`https://www.google.com/maps/dir/?api=1&destination=${target.lat},${target.lng}&travelmode=driving`;
  window.open(url,'_blank','noopener')
}'''

if old2 not in s:
    raise SystemExit('openRunnerMapsStage v1 block not found')
s = s.replace(old2, new2, 1)

p.write_text(s, encoding='utf-8')
print('patched multi-pickup Google Maps routing')
