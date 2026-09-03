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
replacement = r'''  async function photon(q,limit=6){
    const query=String(q||'').trim();if(query.length<2)return [];
    // Prima passa dal proxy Supabase: evita i blocchi/limitazioni del browser mobile
    // verso Photon e mantiene la ricerca identica su Android/PWA.
    try{
      if(typeof db!=='undefined'&&db?.functions?.invoke){
        const {data,error}=await db.functions.invoke('community-place-search',{body:{q:query,limit}});
        if(!error&&Array.isArray(data?.features))return data.features;
      }
    }catch(e){console.warn('community place proxy',e)}
    // Fallback diretto: se il proxy non è raggiungibile proviamo comunque Photon.
    const ctrl=typeof AbortController!=='undefined'?new AbortController():null;
    const timer=ctrl?setTimeout(()=>ctrl.abort(),6500):null;
    try{
      const r=await fetch(`https://photon.komoot.io/api/?q=${encodeURIComponent(query+', Italia')}&limit=${limit}&lang=it`,ctrl?{signal:ctrl.signal}:undefined);
      if(!r.ok)throw new Error('Ricerca luogo non disponibile');
      const j=await r.json();return Array.isArray(j.features)?j.features:[]
    }finally{if(timer)clearTimeout(timer)}
  }
'''
s = s[:start] + replacement + s[end:]
p.write_text(s, encoding='utf-8')

idx = Path('index.html')
html = idx.read_text(encoding='utf-8')
html2 = re.sub(r'community-routes\.js\?v=\d+', 'community-routes.js?v=2', html, count=1)
if html2 == html and 'community-routes.js?v=2' not in html:
    raise SystemExit('community-routes script tag not found')
idx.write_text(html2, encoding='utf-8')

print('Community place search now uses Supabase proxy with direct fallback; cache version bumped')
