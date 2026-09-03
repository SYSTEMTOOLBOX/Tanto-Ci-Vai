from pathlib import Path
import re

p = Path('community-routes.js')
s = p.read_text(encoding='utf-8')

# Keep the full point context (especially municipality) when the user picks a suggestion.
s = re.sub(
    r"  function featurePoint\(f\)\{const c=f\?\.geometry\?\.coordinates\|\|\[\];return \{lat:Number\(c\[1\]\),lng:Number\(c\[0\]\),label:featureLabel\(f\)\}\}\n",
    """  function featurePoint(f){\n    const c=f?.geometry?.coordinates||[],p=f?.properties||{};\n    const town=p.city||p.town||p.village||p.municipality||p.locality||'';\n    return {lat:Number(c[1]),lng:Number(c[0]),label:featureLabel(f),town}\n  }\n  function tcvAddressLike(q){return /^(via|viale|vicolo|piazza|piazzale|p\\.?le|corso|strada|borgata|frazione|largo|localita|località)\\b/i.test(String(q||'').trim())}\n  function tcvTownNorm(v){return String(v||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9]/g,'')}\n  function tcvTownFromPoint(pt){\n    if(pt?.town)return String(pt.town).trim();\n    const parts=String(pt?.label||'').split(',').map(x=>x.trim()).filter(Boolean);\n    if(parts.length>1&&tcvAddressLike(parts[0]))return parts[1];\n    return parts[0]||''\n  }\n  function tcvFeatureTown(f){const p=f?.properties||{};return p.city||p.town||p.village||p.municipality||p.locality||''}\n  function tcvPointDistanceKm(a,b){\n    if(!a||!b||!Number.isFinite(Number(a.lat))||!Number.isFinite(Number(a.lng))||!Number.isFinite(Number(b.lat))||!Number.isFinite(Number(b.lng)))return Infinity;\n    const R=6371,toRad=x=>Number(x)*Math.PI/180,dLat=toRad(Number(b.lat)-Number(a.lat)),dLng=toRad(Number(b.lng)-Number(a.lng));\n    const la1=toRad(a.lat),la2=toRad(b.lat),h=Math.sin(dLat/2)**2+Math.cos(la1)*Math.cos(la2)*Math.sin(dLng/2)**2;\n    return 2*R*Math.asin(Math.sqrt(h))\n  }\n""",
    s,
    count=1
)

start_marker = "  async function photon(q,limit=6){"
end_marker = "  async function reversePoint"
start = s.find(start_marker)
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('community photon block not found')
replacement = r'''  async function photon(q,limit=6,anchor=null){
    const query=String(q||'').trim();if(query.length<2)return [];
    const anchorTown=(!query.includes(',')&&tcvAddressLike(query))?tcvTownFromPoint(anchor):'';
    const searches=anchorTown?[`${query}, ${anchorTown}`,query]:[query];

    const localFilter=(fs,isLocal)=>{
      const rows=Array.isArray(fs)?fs.filter(Boolean):[];if(!isLocal||!anchorTown)return rows;
      const wanted=tcvTownNorm(anchorTown);
      const same=rows.filter(f=>{const got=tcvTownNorm(tcvFeatureTown(f));return got&&(got===wanted||got.includes(wanted)||wanted.includes(got))});
      if(same.length)return same;
      if(anchor){
        const near=rows.filter(f=>tcvPointDistanceKm(anchor,featurePoint(f))<=25);
        if(near.length)return near;
      }
      return [];
    };

    for(let attempt=0;attempt<searches.length;attempt++){
      const candidate=searches[attempt],isLocal=!!anchorTown&&attempt===0;

      // 1) Same Nominatim helper already proven in Farmacia/Altro.
      try{
        if(typeof nominatimDeliverySearch==='function'){
          const ns=await nominatimDeliverySearch(candidate,Math.max(limit,8));
          const fs=localFilter((Array.isArray(ns)?ns:[]).map(tcvNominatimFeature).filter(f=>Number.isFinite(f.geometry.coordinates[0])&&Number.isFinite(f.geometry.coordinates[1])),isLocal);
          if(fs.length)return fs.slice(0,limit);
        }
      }catch(e){console.warn('community nominatim app helper',e)}

      // 2) Same Photon helper used by the rest of the app.
      try{
        if(typeof photonSearch==='function'){
          const fs=localFilter(await photonSearch(`https://photon.komoot.io/api/?q=${encodeURIComponent(candidate)}&limit=${Math.max(limit,8)}`),isLocal);
          if(fs.length)return fs.slice(0,limit);
        }
      }catch(e){console.warn('community photon app helper',e)}

      // 3) Direct Nominatim fallback.
      try{
        const ctrl=typeof AbortController!=='undefined'?new AbortController():null;
        const timer=ctrl?setTimeout(()=>ctrl.abort(),6000):null;
        try{
          const r=await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=it&addressdetails=1&limit=${Math.max(limit,8)}&q=${encodeURIComponent(candidate)}`,
            ctrl?{signal:ctrl.signal,headers:{'Accept-Language':'it'}}:{headers:{'Accept-Language':'it'}});
          if(r.ok){
            const ns=await r.json();
            const fs=localFilter((Array.isArray(ns)?ns:[]).map(tcvNominatimFeature).filter(f=>Number.isFinite(f.geometry.coordinates[0])&&Number.isFinite(f.geometry.coordinates[1])),isLocal);
            if(fs.length)return fs.slice(0,limit);
          }
        }finally{if(timer)clearTimeout(timer)}
      }catch(e){console.warn('community nominatim direct',e)}

      // 4) Supabase proxy fallback.
      try{
        if(typeof db!=='undefined'&&db?.functions?.invoke){
          const {data,error}=await db.functions.invoke('community-place-search',{body:{q:candidate,limit:Math.max(limit,8)}});
          const fs=localFilter(!error&&Array.isArray(data?.features)?data.features:[],isLocal);
          if(fs.length)return fs.slice(0,limit);
        }
      }catch(e){console.warn('community place proxy',e)}

      // 5) Direct Photon last fallback.
      try{
        const ctrl=typeof AbortController!=='undefined'?new AbortController():null;
        const timer=ctrl?setTimeout(()=>ctrl.abort(),6000):null;
        try{
          const r=await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(candidate+', Italia')}&limit=${Math.max(limit,8)}&lang=it`,ctrl?{signal:ctrl.signal}:undefined);
          if(r.ok){const j=await r.json();const fs=localFilter(Array.isArray(j.features)?j.features:[],isLocal);if(fs.length)return fs.slice(0,limit)}
        }finally{if(timer)clearTimeout(timer)}
      }catch(e){console.warn('community photon direct',e)}
    }
    return [];
  }
'''
s = s[:start] + replacement + s[end:]

start_marker = "  function bindAutocomplete(inputId,boxId,key,target='trip'){"
end_marker = "  async function resolveInput"
start = s.find(start_marker)
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('community autocomplete block not found')
replacement = r'''  function bindAutocomplete(inputId,boxId,key,target='trip'){
    const input=document.getElementById(inputId);if(!input)return;
    input.setAttribute('autocomplete','off');
    input.addEventListener('input',()=>{
      const state=target==='trip'?draft:rideDraft,anchor=state[key==='from'?'to':'from'];
      state[key]=null;
      clearTimeout(searchTimers[inputId]);
      const q=input.value.trim();if(q.length<2){clearBox(boxId);return}
      searchTimers[inputId]=setTimeout(async()=>{
        const box=document.getElementById(boxId);if(!box)return;
        const anchorTown=(!q.includes(',')&&tcvAddressLike(q))?tcvTownFromPoint(anchor):'';
        box.innerHTML=`<div class="notice">${anchorTown?`Cerco prima nel comune di <b>${safe(anchorTown)}</b>…`:'Cerco città, via, piazza e luogo…'}</div>`;
        try{
          const fs=await photon(q,7,anchor);
          box.innerHTML=fs.length?fs.map((f,i)=>`<button type="button" class="tcv-autoitem" data-i="${i}"><b>${safe(featureLabel(f)||q)}</b><small>${safe(featureSub(f))}</small></button>`).join(''):'<div class="notice yellow">Nessun luogo trovato. Se vuoi un altro paese scrivi anche il comune, per esempio “Piazza …, Chivasso”.</div>';
          box.querySelectorAll('button[data-i]').forEach(btn=>btn.addEventListener('pointerdown',(ev)=>{ev.preventDefault();
            const f=fs[Number(btn.dataset.i)],p=featurePoint(f);if(!Number.isFinite(p.lat)||!Number.isFinite(p.lng))return;
            input.value=p.label||q;state[key]=p;clearBox(boxId);
            if(target==='trip')tcvMaybeAutoPreview();else tcvMaybeRidePreview()
          }))
        }catch(e){console.warn('community autocomplete',e);box.innerHTML='<div class="notice yellow">Ricerca momentaneamente lenta: continua a scrivere città, via o piazza.</div>'}
      },250)
    })
  }

'''
s = s[:start] + replacement + s[end:]

start_marker = "  async function resolveInput(inputId,key,target='trip'){"
end_marker = "  async function routeDetails"
start = s.find(start_marker)
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('community resolveInput block not found')
replacement = r'''  async function resolveInput(inputId,key,target='trip'){
    const state=target==='trip'?draft:rideDraft;
    if(state[key]&&Number.isFinite(state[key].lat))return state[key];
    const val=document.getElementById(inputId)?.value.trim()||'';if(!val)throw new Error('Inserisci partenza e destinazione.');
    const gps=val.match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
    if(gps){const p=await reversePoint(Number(gps[1]),Number(gps[2]));state[key]=p;document.getElementById(inputId).value=p.label;return p}
    const anchor=state[key==='from'?'to':'from'];
    const fs=await photon(val,1,anchor);if(!fs.length)throw new Error(`Non trovo “${val}”. Scrivi anche il comune.`);
    const p=featurePoint(fs[0]);state[key]=p;document.getElementById(inputId).value=p.label;return p
  }

'''
s = s[:start] + replacement + s[end:]

p.write_text(s, encoding='utf-8')

# Hard cache bust so Android/PWA gets the new municipality-aware autocomplete.
idx = Path('index.html')
html = idx.read_text(encoding='utf-8')
html2 = re.sub(r'community-routes\.js\?v=\d+', 'community-routes.js?v=4', html, count=1)
if html2 == html and 'community-routes.js?v=4' not in html:
    raise SystemExit('community-routes script tag not found')
idx.write_text(html2, encoding='utf-8')

print('Community autocomplete now searches generic streets/squares in the selected nearby municipality first')
