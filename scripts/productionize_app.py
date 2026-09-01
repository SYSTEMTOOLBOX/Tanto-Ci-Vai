from pathlib import Path

p = Path('index.html')
s = p.read_text()

replacements = {
    'Beta territoriale collegata al database reale. Accedi oppure crea il profilo per pubblicare e prendere commissioni.': 'Accedi oppure crea il profilo per chiedere una mano o prendere una commissione.',
    '<span>📍 Beta territoriale</span>': '<span id="liveLocation">📍 Rilevo posizione…</span>',
    '<div class="eyebrow">DATABASE REALE ATTIVO</div>': '<div class="eyebrow">TANTO CI VAI?</div>',
    'Le richieste pubblicate qui sono condivise fra i telefoni registrati nella beta e vengono aggiornate in tempo reale.': 'Le richieste vengono condivise e aggiornate in tempo reale.',
    '<div class="sect"><h2>Cosa vuoi fare?</h2><span>Backend Supabase</span></div>': '<div class="sect"><h2>Cosa vuoi fare?</h2><span>Servizio attivo</span></div>',
    '<div class="sect"><h2>Richieste vicino a te</h2><span id="feedStatus">Sincronizzate</span></div>': '<div class="sect"><h2>Richieste disponibili</h2><span id="feedStatus">Sincronizzate</span></div>',
    "authStatus.textContent=m==='login'?'Accedi alla beta con email e password.':'Il nome e il telefono verranno salvati nel tuo profilo Supabase.'": "authStatus.textContent=m==='login'?'Accedi con email e password.':'Il nome e il telefono verranno salvati nel tuo profilo.'",
    'PROFILO SUPABASE': 'PROFILO',
    '✓ Profilo, richieste e missioni sono ora salvati online e protetti dalle regole RLS del database.': '✓ Profilo, richieste e missioni sono salvati online in modo sicuro.'
}
for a, b in replacements.items():
    s = s.replace(a, b)

old = "async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');await ensureProfile();await loadRequests();subscribeRealtime();renderAll()}"
new = "async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');await ensureProfile();initLiveGps();await loadRequests();subscribeRealtime();renderAll()}"
if old in s:
    s = s.replace(old, new, 1)

anchor = 'async function ensureProfile(){'
gps = """async function initLiveGps(){
  let el=document.getElementById('liveLocation');if(!el)return;
  if(!navigator.geolocation){el.textContent='📍 GPS non disponibile';return}
  el.textContent='📍 Rilevo posizione…';
  try{
    let p=await currentPosition();USER_POS={lat:p.lat,lng:p.lng};
    let rp=await reverseGeocodePoint({lat:p.lat,lng:p.lng});
    let label=rp.area||(rp.label?rp.label.split(',')[0]:'Posizione rilevata');
    el.textContent='📍 '+label;
  }catch(e){el.textContent='📍 Attiva posizione'}
}
"""
if 'function initLiveGps()' not in s:
    s = s.replace(anchor, gps + anchor, 1)

s = s.replace('alla beta', 'al servizio').replace('della beta', 'del servizio').replace('Beta territoriale', 'Posizione GPS')
p.write_text(s)
