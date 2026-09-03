from pathlib import Path
import re

p = Path('community-routes.js')
s = p.read_text(encoding='utf-8')

if 'TCV_TOWN_PREFIX_FIX_V1' not in s:
    s = s.replace('TCV_CAP_CONSISTENCY_V1', 'TCV_CAP_CONSISTENCY_V1\n   TCV_TOWN_PREFIX_FIX_V1', 1)

anchor = r'''  function tcvTownRows(fs,q){
    const wanted=tcvTownNorm(q),seen=new Set(),out=[];
    for(const f of (Array.isArray(fs)?fs:[])){
      const raw=tcvFeatureTown(f)||String(featureLabel(f)||'').split(',')[0]||'',town=String(raw).trim();if(!town)continue;
      const norm=tcvTownNorm(town);if(wanted&&!(norm.includes(wanted)||wanted.includes(norm)))continue;if(seen.has(norm))continue;seen.add(norm);
      const p=featurePoint(f);if(!Number.isFinite(p.lat)||!Number.isFinite(p.lng))continue;p.town=town;p.label=town;
      out.push({f,p,town,postcode:String(f?.properties?.postcode||''),sub:featureSub(f)});if(out.length>=8)break
    }
    return out
  }
'''

replacement = r'''  function tcvTownRows(fs,q){
    const wanted=tcvTownNorm(q),seen=new Set(),out=[];
    for(const f of (Array.isArray(fs)?fs:[])){
      const props=f?.properties||{};
      const candidates=[tcvFeatureTown(f),props.name,props.city,props.town,props.village,props.municipality,String(featureLabel(f)||'').split(',')[0]].filter(Boolean);
      const town=String(candidates.find(v=>{const n=tcvTownNorm(v);return !wanted||n.startsWith(wanted)||n.includes(wanted)||wanted.includes(n)})||candidates[0]||'').trim();
      if(!town)continue;
      const norm=tcvTownNorm(town);if(wanted&&!(norm.startsWith(wanted)||norm.includes(wanted)||wanted.includes(norm)))continue;if(seen.has(norm))continue;seen.add(norm);
      const p=featurePoint(f);if(!Number.isFinite(p.lat)||!Number.isFinite(p.lng))continue;p.town=town;p.label=town;
      out.push({f,p,town,postcode:String(props.postcode||''),sub:featureSub(f)});if(out.length>=8)break
    }
    return out
  }
  async function tcvTownSearch(q){
    const query=String(q||'').trim();if(query.length<2)return [];
    let rows=[];
    try{rows=tcvTownRows(await photon(query,20,null),query);if(rows.length)return rows}catch(e){console.warn('town generic search',e)}
    try{
      const ctrl=typeof AbortController!=='undefined'?new AbortController():null,timer=ctrl?setTimeout(()=>ctrl.abort(),6000):null;
      try{
        const r=await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=it&addressdetails=1&limit=20&q=${encodeURIComponent(query+', Italia')}`,ctrl?{signal:ctrl.signal,headers:{'Accept-Language':'it'}}:{headers:{'Accept-Language':'it'}});
        if(r.ok){const data=await r.json();rows=tcvTownRows((Array.isArray(data)?data:[]).map(tcvNominatimFeature),query);if(rows.length)return rows}
      }finally{if(timer)clearTimeout(timer)}
    }catch(e){console.warn('town nominatim fallback',e)}
    try{
      const ctrl=typeof AbortController!=='undefined'?new AbortController():null,timer=ctrl?setTimeout(()=>ctrl.abort(),6000):null;
      try{
        const r=await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(query+', Italia')}&limit=20&lang=it`,ctrl?{signal:ctrl.signal}:undefined);
        if(r.ok){const data=await r.json();rows=tcvTownRows(Array.isArray(data?.features)?data.features:[],query);if(rows.length)return rows}
      }finally{if(timer)clearTimeout(timer)}
    }catch(e){console.warn('town photon fallback',e)}
    try{
      if(typeof db!=='undefined'&&db?.functions?.invoke){
        const {data,error}=await db.functions.invoke('community-place-search',{body:{q:query+', Italia',limit:20}});
        if(!error){rows=tcvTownRows(Array.isArray(data?.features)?data.features:[],query);if(rows.length)return rows}
      }
    }catch(e){console.warn('town proxy fallback',e)}
    return []
  }
'''

if anchor not in s:
    raise SystemExit('tcvTownRows anchor not found')
s = s.replace(anchor, replacement, 1)

old = "          const rows=tcvTownRows(await photon(q,14,null),q);\n"
new = "          const rows=await tcvTownSearch(q);\n"
if old not in s:
    raise SystemExit('town autocomplete search call not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')

idx = Path('index.html')
html = idx.read_text(encoding='utf-8')
html2 = re.sub(r'community-routes\\.js\\?v=\\d+', 'community-routes.js?v=7', html, count=1)
if html2 == html and 'community-routes.js?v=7' not in html:
    raise SystemExit('community-routes script tag not found')
idx.write_text(html2, encoding='utf-8')

print('Community municipality autocomplete now retries dedicated prefix searches')
