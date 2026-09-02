from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

pattern_points = re.compile(r"function mapPlanPoints\(reqs,start=MAP_PLAN_START\)\{.*?\n\}\nasync function ensureMapPlanStart\(\)\{", re.S)
replacement_points = r'''function mapPlanCrowKm(a,b){
  if(!a||!b)return Infinity;
  let lat1=+a.lat,lng1=+a.lng,lat2=+b.lat,lng2=+b.lng;
  if(![lat1,lng1,lat2,lng2].every(Number.isFinite))return Infinity;
  let rad=x=>x*Math.PI/180,dLat=rad(lat2-lat1),dLng=rad(lng2-lng1);
  let h=Math.sin(dLat/2)**2+Math.cos(rad(lat1))*Math.cos(rad(lat2))*Math.sin(dLng/2)**2;
  return 6371*2*Math.atan2(Math.sqrt(h),Math.sqrt(1-h))
}
function mapPlanPoints(reqs,start=MAP_PLAN_START){
  let pts=[];if(!start)return pts;
  let first={lat:+start.lat,lng:+start.lng};if(!Number.isFinite(first.lat)||!Number.isFinite(first.lng))return pts;pts.push(first);
  let jobs=reqs.map(r=>({
    id:r.id,r,picked:false,delivered:false,
    pickup:{lat:+r.ritiro_lat,lng:+r.ritiro_lng},
    delivery:{lat:+r.consegna_lat,lng:+r.consegna_lng}
  })).filter(j=>[j.pickup.lat,j.pickup.lng,j.delivery.lat,j.delivery.lng].every(Number.isFinite));
  let cur=first,stops=[],straight=0,guard=0;
  while(jobs.some(j=>!j.delivered)&&guard++<30){
    let choices=[];
    jobs.forEach(j=>{
      if(!j.picked){
        let d=mapPlanCrowKm(cur,j.pickup);choices.push({j,kind:'pickup',pt:j.pickup,dist:d,score:d})
      }else if(!j.delivered){
        let d=mapPlanCrowKm(cur,j.delivery),score=d;
        if(j.r.consegna_entro){
          let left=(new Date(j.r.consegna_entro).getTime()-Date.now())/60000;
          if(Number.isFinite(left)){if(left<45)score*=.45;else if(left<90)score*=.65;else if(left<150)score*=.82}
        }
        choices.push({j,kind:'delivery',pt:j.delivery,dist:d,score})
      }
    });
    choices=choices.filter(c=>Number.isFinite(c.dist)).sort((a,b)=>a.score-b.score||a.dist-b.dist);
    if(!choices.length)break;
    let c=choices[0];
    if(c.kind==='pickup')c.j.picked=true;else c.j.delivered=true;
    straight+=c.dist;pts.push({lat:c.pt.lat,lng:c.pt.lng});stops.push({id:c.j.id,kind:c.kind});cur=c.pt
  }
  pts.planStops=stops;pts.planStraightKm=straight;return pts
}
async function ensureMapPlanStart(){'''
s, n = pattern_points.subn(replacement_points, s, count=1)
if n != 1:
    raise SystemExit('mapPlanPoints block not found')

pattern_route = re.compile(r"async function mapRouteDetailed\(points\)\{.*?\n\}\nfunction fmtPlanDelta", re.S)
replacement_route = r'''async function mapRouteDetailed(points){
  if(points.length<2)return {distance:0,duration:0,legs:[],geometry:null,planStops:points.planStops||[]};
  for(let i=1;i<points.length;i++){
    let crow=mapPlanCrowKm(points[i-1],points[i]);
    if(crow>60)throw new Error(`Una tappa risulta a ${Math.round(crow)} km dalla precedente: coordinate fuori zona. Toglila o ricontrolla l'indirizzo.`)
  }
  let coords=points.map(p=>`${p.lng},${p.lat}`).join(';');
  let res=await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson&steps=false`);
  let j=await res.json();if(j.code!=='Ok'||!j.routes?.length)throw new Error('Percorso non trovato');
  let out=j.routes[0];out.planStops=points.planStops||[];out.planStraightKm=points.planStraightKm||0;
  let legs=out.legs||[];
  for(let i=0;i<legs.length&&i<points.length-1;i++){
    let crow=mapPlanCrowKm(points[i],points[i+1]),road=(legs[i].distance||0)/1000;
    if(road>Math.max(35,crow*4+12))throw new Error(`Percorso stradale anomalo (${Math.round(road)} km per una tappa vicina). Aggiorna il GPS o ricontrolla l'indirizzo.`)
  }
  return out
}
function fmtPlanDelta'''
s, n = pattern_route.subn(replacement_route, s, count=1)
if n != 1:
    raise SystemExit('mapRouteDetailed block not found')

pattern_arrival = re.compile(r"function mapPlanArrivalInfo\(routeData,reqs\)\{.*?\n\}\nfunction drawMapPlanRoute", re.S)
replacement_arrival = r'''function mapPlanArrivalInfo(routeData,reqs){
  let legs=routeData?.legs||[],stops=routeData?.planStops||[];
  if(stops.length===legs.length&&stops.length){
    let cum=0,byId=new Map();
    stops.forEach((st,i)=>{
      cum+=legs[i]?.duration||0;
      if(st.kind==='delivery'){
        let r=reqs.find(x=>x.id===st.id),arrival=new Date(Date.now()+cum*1000),deadline=r?.consegna_entro?new Date(r.consegna_entro):null;
        byId.set(st.id,{arrival,late:!!(deadline&&Number.isFinite(deadline.getTime())&&arrival>deadline),deadline})
      }
    });
    return reqs.map(r=>byId.get(r.id)||{arrival:null,late:false,deadline:r.consegna_entro?new Date(r.consegna_entro):null})
  }
  let cum=0,rows=[];
  reqs.forEach((r,i)=>{
    let pickupLeg=i*2,deliveryLeg=i*2+1;
    if(legs[pickupLeg])cum+=legs[pickupLeg].duration||0;
    if(legs[deliveryLeg])cum+=legs[deliveryLeg].duration||0;
    let arrival=new Date(Date.now()+cum*1000),deadline=r.consegna_entro?new Date(r.consegna_entro):null;
    rows.push({arrival,late:!!(deadline&&Number.isFinite(deadline.getTime())&&arrival>deadline),deadline})
  });
  return rows
}
function drawMapPlanRoute'''
s, n = pattern_arrival.subn(replacement_arrival, s, count=1)
if n != 1:
    raise SystemExit('mapPlanArrivalInfo block not found')

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Smart map planner route order applied')
# trigger: 2026-09-02 smart-route-v1
