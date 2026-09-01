from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

css = r'''
.map-shell{position:relative;height:calc(100dvh - 245px);min-height:460px;max-height:680px;margin-top:10px;border:1px solid var(--line);border-radius:20px;overflow:hidden;background:#eaf1f8}
.map-shell #map{height:100%!important;min-height:0!important;margin:0!important;border:0!important;border-radius:0!important}
.map-plan-sheet{position:absolute;left:10px;right:10px;bottom:10px;z-index:1200;max-height:min(44%,330px);overflow:auto;padding:10px;background:rgba(255,255,255,.98);border:1px solid var(--line);border-radius:20px;box-shadow:0 16px 38px rgba(5,17,39,.22);backdrop-filter:blur(12px)}
.map-plan-sheet .req{box-shadow:none;border-radius:15px}
.map-plan-head{position:sticky;top:-10px;z-index:2;margin:-10px -10px 8px;padding:10px 10px 8px;background:rgba(255,255,255,.98);border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:8px}
.map-plan-head b{font-size:13px}.map-plan-head small{display:block;color:var(--muted);font-size:8px;margin-top:2px}
.map-plan-collapse{border:0;background:#f0f3f7;border-radius:12px;width:38px;height:34px;font-weight:950;color:var(--ink)}
.map-plan-chip{position:absolute;left:12px;bottom:12px;z-index:1200;border:0;border-radius:999px;padding:11px 14px;background:var(--navy);color:#fff;font-size:10px;font-weight:950;box-shadow:0 10px 26px rgba(5,17,39,.24)}
@media(max-height:720px){.map-shell{height:430px;min-height:430px}.map-plan-sheet{max-height:48%}}
'''
if '.map-plan-sheet{' not in s:
    s = s.replace('</style>', css + '\n</style>', 1)

old_page = '''function renderMapPage(){mapPage.innerHTML=`<div class="pagehead"><div class="k">MAPPA LIVE</div><h2>Richieste disponibili</h2><p>Tocca un bersaglio: calcolo km e tempo. Aggiungi 2ª, 3ª o altre tappe e toglile se il giro diventa troppo lungo.</p></div><button class="gpsbtn" onclick="locateMe()">📍 Aggiorna la mia posizione</button><div id="mapPlanPanel" style="margin:10px 0"></div><div id="map"></div>`;setTimeout(()=>{initMap();setTimeout(recalculateMapPlan,100)},100)}'''
new_page = '''function renderMapPage(){mapPage.innerHTML=`<div class="pagehead"><div class="k">MAPPA LIVE</div><h2>Richieste disponibili</h2><p>Tocca un bersaglio: calcolo km e tempo. Le tappe restano in un pannello sopra la mappa, senza spostarla.</p></div><button class="gpsbtn" onclick="locateMe()">📍 Aggiorna la mia posizione</button><div class="map-shell"><div id="map"></div><button id="mapPlanChip" class="map-plan-chip hidden" onclick="expandMapPlanPanel()">🧭 Giro</button><div id="mapPlanPanel" class="map-plan-sheet hidden"></div></div>`;setTimeout(()=>{initMap();setTimeout(recalculateMapPlan,100)},100)}'''
if old_page not in s:
    raise SystemExit('renderMapPage block not found')
s = s.replace(old_page, new_page, 1)

pattern = re.compile(r"function renderMapPlanPanel\(routeData=MAP_PLAN_ROUTE,error=''\)\{.*?\n\}\nasync function recalculateMapPlan\(\)\{", re.S)
replacement = r'''function collapseMapPlanPanel(){
  let el=document.getElementById('mapPlanPanel'),chip=document.getElementById('mapPlanChip');if(el)el.classList.add('hidden');if(chip){chip.classList.remove('hidden');chip.textContent=`🧭 Giro · ${MAP_PLAN_IDS.length} ${MAP_PLAN_IDS.length===1?'tappa':'tappe'}`}
}
function expandMapPlanPanel(){
  let el=document.getElementById('mapPlanPanel'),chip=document.getElementById('mapPlanChip');if(el)el.classList.remove('hidden');if(chip)chip.classList.add('hidden');renderMapPlanPanel(MAP_PLAN_ROUTE)
}
function renderMapPlanPanel(routeData=MAP_PLAN_ROUTE,error=''){
  let el=document.getElementById('mapPlanPanel'),chip=document.getElementById('mapPlanChip');if(!el)return;let reqs=mapPlanRequests();
  if(!reqs.length){el.classList.add('hidden');el.innerHTML='';if(chip)chip.classList.add('hidden');return}
  el.classList.remove('hidden');if(chip)chip.classList.add('hidden');
  let arrivals=routeData?mapPlanArrivalInfo(routeData,reqs):[];
  let totalText=routeData?`${fmtDistance(routeData.distance)} · ${fmtDuration(routeData.duration)}`:'Calcolo percorso…';
  let total=routeData?`<div class="nav-summary"><div><b>${fmtDistance(routeData.distance)}</b><span>GIRO TOTALE</span></div><div><b>${fmtDuration(routeData.duration)}</b><span>TEMPO STIMATO</span></div></div>`:`<div class="notice">Calcolo percorso…</div>`;
  let rows=reqs.map((r,i)=>{let a=arrivals[i],warn=a?.late?' ⚠️ OLTRE LIMITE':'';return `<div class="req" style="margin-top:8px;padding:10px"><div class="reqhead"><span class="kind">TAPPA ${i+1}</span><button class="btn outline" style="padding:7px 10px" onclick="removeMapPlanStop('${r.id}')">✕ Togli</button></div><b>${esc(r.titolo)}</b><p style="margin:6px 0">${esc(r.ritiro_indirizzo)} → ${esc(cleanDeliveryAddress(r.consegna_indirizzo))}</p>${a?`<div class="meta"><span class="pill">🕒 Arrivo ~${a.arrival.toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'})}</span>${r.consegna_entro?`<span class="pill">⏰ Entro ${formatDateTime(r.consegna_entro)}${warn}</span>`:''}</div>`:''}</div>`}).join('');
  el.innerHTML=`<div class="map-plan-head"><div><b>🧭 Giro · ${reqs.length} ${reqs.length===1?'tappa':'tappe'}</b><small>${esc(totalText)}</small></div><button class="map-plan-collapse" onclick="collapseMapPlanPanel()">⌄</button></div>${error?`<div class="notice yellow">${esc(error)}</div>`:''}${total}${rows}<div class="rowbtn" style="margin-top:10px"><button class="btn outline" onclick="clearMapPlan()">Svuota giro</button><button class="btn teal" onclick="acceptMapPlan()">✓ Accetta giro (${reqs.length})</button></div>`
}
async function recalculateMapPlan(){'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('renderMapPlanPanel block not found')

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Map planner overlay layout fixed')
