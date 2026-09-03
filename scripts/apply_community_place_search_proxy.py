from pathlib import Path
import re

p = Path('community-routes.js')
s = p.read_text(encoding='utf-8')
start_marker = "  async function photon(q,limit=6){"
end_marker = "  async function reversePoint"
start = s.find(start_marker)
end = s.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('community place-search block not found')

replacement = r'''  function tcvNominatimFeature(x){
    const a=x?.address||{};
    const city=a.city||a.town||a.village||a.municipality||a.hamlet||a.locality||'';
    const street=a.road||a.pedestrian||a.residential||a.footway||a.path||'';
    const name=x?.name||street||city||String(x?.display_name||'').split(',')[0]||'';
    return {
      type:'Feature',
      properties:{
        name,
        street,
        housenumber:a.house_number||'',
        city,
        town:a.town||'',
        village:a.village||'',
        locality:a.locality||a.suburb||a.neighbourhood||'',
        county:a.county||'',
        state:a.state||'',
        postcode:a.postcode||'',
        country:a.country||'Italia',
        countrycode:'IT'
      },
      geometry:{type:'Point',coordinates:[Number(x?.lon),Number(x?.lat)]}
    };
  }

  async function photon(q,limit=6){
    const query=String(q||'').trim();if(query.length<2)return [];

    // Usa PRIMA gli stessi motori già collaudati nella compilazione Farmacia/Altro.
    // Così Community non ha più un sistema di indirizzi diverso dal resto dell'app.
    try{
      if(typeof nominatimDeliverySearch==='function'){
        const ns=await nominatimDeliverySearch(query,limit);
        const fs=(Array.isArray(ns)?ns:[]).map(tcvNominatimFeature).filter(f=>Number.isFinite(f.geometry.coordinates[0])&&Number.isFinite(f.geometry.coordinates[1]));
        if(fs.length)return fs;
      }
    }catch(e){console.warn('community nominatim app helper',e)}

    try{
      if(typeof photonSearch==='function'){
        const fs=await photonSearch(`https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=${limit}`);
        if(Array.isArray(fs)&&fs.length)return fs;
      }
    }catch(e){console.warn('community photon app helper',e)}

    // Secondo fallback: Nominatim diretto, identico alla geocodifica già usata dall'app.
    try{
      const ctrl=typeof AbortController!=='undefined'?new AbortController():null;
      const timer=ctrl?setTimeout(()=>ctrl.abort(),6000):null;
      try{
        const r=await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=it&addressdetails=1&limit=${limit}&q=${encodeURIComponent(query)}`,
          ctrl?{signal:ctrl.signal,headers:{'Accept-Language':'it'}}:{headers:{'Accept-Language':'it'}});
        if(r.ok){
          const ns=await r.json();
          const fs=(Array.isArray(ns)?ns:[]).map(tcvNominatimFeature).filter(f=>Number.isFinite(f.geometry.coordinates[0])&&Number.isFinite(f.geometry.coordinates[1]));
          if(fs.length)return fs;
        }
      }finally{if(timer)clearTimeout(timer)}
    }catch(e){console.warn('community nominatim direct',e)}

    // Terzo fallback: proxy Supabase.
    try{
      if(typeof db!=='undefined'&&db?.functions?.invoke){
        const {data,error}=await db.functions.invoke('community-place-search',{body:{q:query,limit}});
        if(!error&&Array.isArray(data?.features)&&data.features.length)return data.features;
      }
    }catch(e){console.warn('community place proxy',e)}

    // Ultimo tentativo Photon diretto. Se anche questo non va, restituiamo [] e
    // l'interfaccia invita a continuare a scrivere invece di mostrare un errore tecnico.
    try{
      const ctrl=typeof AbortController!=='undefined'?new AbortController():null;
      const timer=ctrl?setTimeout(()=>ctrl.abort(),6000):null;
      try{
        const r=await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(query+', Italia')}&limit=${limit}&lang=it`,ctrl?{signal:ctrl.signal}:undefined);
        if(r.ok){const j=await r.json();if(Array.isArray(j.features))return j.features}
      }finally{if(timer)clearTimeout(timer)}
    }catch(e){console.warn('community photon direct',e)}
    return [];
  }
'''

s = s[:start] + replacement + s[end:]

# Mobile: la tastiera può mangiare il click. Usiamo pointerdown come già fa
# l'autocomplete Farmacia/Altro.
old = "box.querySelectorAll('button[data-i]').forEach(btn=>btn.addEventListener('click',()=>{"
new = "box.querySelectorAll('button[data-i]').forEach(btn=>btn.addEventListener('pointerdown',(ev)=>{ev.preventDefault();"
if old in s:
    s = s.replace(old, new, 1)

# Non mostrare più l'errore tecnico all'utente: l'autocomplete deve degradare
# come Farmacia/Altro e permettere di continuare a scrivere.
s = s.replace("}catch(e){box.innerHTML=`<div class=\"notice yellow\">${safe(e.message)}</div>`}",
              "}catch(e){console.warn('community autocomplete',e);box.innerHTML='<div class=\"notice yellow\">Ricerca momentaneamente lenta: continua a scrivere città, via o piazza.</div>'}", 1)

p.write_text(s, encoding='utf-8')

idx = Path('index.html')
html = idx.read_text(encoding='utf-8')
html2 = re.sub(r'community-routes\.js\?v=\d+', 'community-routes.js?v=3', html, count=1)
if html2 == html and 'community-routes.js?v=3' not in html:
    raise SystemExit('community-routes script tag not found')
idx.write_text(html2, encoding='utf-8')

print('Community autocomplete now reuses Pharmacy/Other search stack + Nominatim fallback; mobile pointer selection fixed; cache v3')
