from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

MARK = 'TCV_RIDE_REQUEST_ENTRY_V1'
if MARK in s:
    print('already applied')
    raise SystemExit(0)

# Dedicated Home action, clearly separate from "Mi serve una mano".
old_home = '<button class="home-clean-action trip" onclick="openTripSearch()"><span class="home-clean-ico">🚗</span><div><b>Sto già andando</b><small>Trova richieste sulla tua strada</small></div><span class="home-clean-arrow">→</span></button><button class="home-clean-action helpme" onclick="openNewRequest()"><span class="home-clean-ico">🙋</span><div><b>Mi serve una mano</b><small>Pubblica una richiesta</small></div><span class="home-clean-arrow">→</span></button>'
new_home = '<button class="home-clean-action trip" onclick="openTripSearch()"><span class="home-clean-ico">🚗</span><div><b>Sto già andando</b><small>Trova richieste sulla tua strada</small></div><span class="home-clean-arrow">→</span></button><button class="home-clean-action ride" onclick="openRideRequest()"><span class="home-clean-ico">🚘</span><div><b>Richiedi passaggio</b><small>Trova qualcuno che va nella tua direzione</small></div><span class="home-clean-arrow">→</span></button><button class="home-clean-action helpme" onclick="openNewRequest()"><span class="home-clean-ico">🙋</span><div><b>Mi serve una mano</b><small>Pubblica una richiesta</small></div><span class="home-clean-arrow">→</span></button>'
if old_home not in s:
    raise SystemExit('home action anchor not found')
s = s.replace(old_home, new_home, 1)

# State.
old_state = 'COMMUNITY_ALERTS=[],MY_SOS=[];'
new_state = 'COMMUNITY_ALERTS=[],MY_SOS=[],MY_RIDES=[];'
if old_state not in s:
    raise SystemExit('state anchor not found')
s = s.replace(old_state, new_state, 1)

# Load ride requests at startup.
old_login = 'await Promise.all([loadRequests(),loadWallet(),loadCommunityAlerts()]);'
new_login = 'await Promise.all([loadRequests(),loadWallet(),loadCommunityAlerts(),loadRideRequests()]);'
if old_login not in s:
    raise SystemExit('afterLogin anchor not found')
s = s.replace(old_login, new_login, 1)

# Add loader after normal requests loader.
anchor = "function subscribeRealtime(){"
idx = s.find(anchor)
if idx == -1:
    raise SystemExit('subscribe anchor not found')
loader = r'''async function loadRideRequests(){
  if(!SESSION){MY_RIDES=[];return}
  const {data,error}=await db.from('ride_requests').select('*').eq('user_id',SESSION.user.id).order('created_at',{ascending:false});
  if(error){console.warn('ride requests',error);MY_RIDES=[];return}
  MY_RIDES=data||[]
}
'''
s = s[:idx] + loader + s[idx:]

# Realtime also refreshes ride requests.
old_sub = "function subscribeRealtime(){if(CHANNEL)db.removeChannel(CHANNEL);CHANNEL=db.channel('tcv-consegne').on('postgres_changes',{event:'*',schema:'public',table:'consegne'},async()=>{syncBadge.textContent='● SYNC';await loadRequests();await loadWallet();renderAll();setTimeout(()=>syncBadge.textContent='● ONLINE',700)}).subscribe()}"
new_sub = "function subscribeRealtime(){if(CHANNEL)db.removeChannel(CHANNEL);CHANNEL=db.channel('tcv-live').on('postgres_changes',{event:'*',schema:'public',table:'consegne'},async()=>{syncBadge.textContent='● SYNC';await loadRequests();await loadWallet();renderAll();setTimeout(()=>syncBadge.textContent='● ONLINE',700)}).on('postgres_changes',{event:'*',schema:'public',table:'ride_requests'},async()=>{syncBadge.textContent='● SYNC';await loadRideRequests();renderAll();setTimeout(()=>syncBadge.textContent='● ONLINE',700)}).subscribe()}"
if old_sub not in s:
    raise SystemExit('subscribe exact anchor not found')
s = s.replace(old_sub, new_sub, 1)

# Ride request flow. parsePlace/geocode are function declarations and can be called before their textual location.
trip_anchor = 'function openTripSearch(){'
idx = s.find(trip_anchor)
if idx == -1:
    raise SystemExit('trip search anchor not found')
ride_code = r'''function tcvRideDefaultWhen(){
  const d=new Date(Date.now()+30*60000);d.setSeconds(0,0);d.setMinutes(Math.ceil(d.getMinutes()/5)*5);
  return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16)
}
function openRideRequest(){
  openSheet(`${head('RICHIEDI PASSAGGIO','🚘 Dove devi andare?','Questa richiesta è separata dalle commissioni: serve per trovare una persona che sta già andando nella tua direzione.')}<div class="ride-request-hero"><b>PASSAGGIO</b><span>Tu chiedi · chi passa di lì può offrirti un posto</span></div><div class="field"><label>DA DOVE PARTI</label><input id="rideFrom" placeholder="Es. Lauriano, Via Roma 10"></div><button class="gpsbtn" onclick="tcvUseGpsRideStart()">📍 Usa la mia posizione GPS</button><div class="field"><label>DOVE DEVI ANDARE</label><input id="rideTo" placeholder="Es. Torino Porta Susa"></div><div class="field"><label>QUANDO VUOI PARTIRE</label><input id="rideWhen" type="datetime-local" value="${tcvRideDefaultWhen()}"></div><div class="grid2"><div class="field"><label>FLESSIBILITÀ</label><select id="rideFlex"><option value="15">± 15 min</option><option value="30" selected>± 30 min</option><option value="60">± 1 ora</option><option value="120">± 2 ore</option></select></div><div class="field"><label>PERSONE</label><select id="ridePassengers"><option value="1">1 persona</option><option value="2">2 persone</option><option value="3">3 persone</option><option value="4">4 persone</option><option value="5">5 persone</option><option value="6">6 persone</option></select></div></div><div class="field"><label>NOTA · FACOLTATIVA</label><textarea id="rideNote" rows="3" maxlength="300" placeholder="Es. Ho un bambino, posso aspettare 20 minuti, ho una borsa..."></textarea></div><div id="rideStatus" class="notice green">La richiesta sarà visibile alle persone che stanno già andando lungo un percorso compatibile.</div><button id="ridePublishBtn" class="ride-publish full" onclick="publishRideRequest()">🚘 PUBBLICA RICHIESTA PASSAGGIO</button><button class="btn outline full" style="margin-top:8px" onclick="closeSheet();page('home')">← Torna alla Home</button>`)
}
function tcvUseGpsRideStart(){
  const st=document.getElementById('rideStatus');if(st)st.textContent='Cerco la tua posizione…';
  if(!navigator.geolocation){if(st)st.textContent='GPS non disponibile su questo dispositivo.';return}
  navigator.geolocation.getCurrentPosition(p=>{USER_POS={lat:p.coords.latitude,lng:p.coords.longitude};const el=document.getElementById('rideFrom');if(el)el.value=`${USER_POS.lat.toFixed(6)},${USER_POS.lng.toFixed(6)}`;if(st)st.textContent='✓ Partenza impostata con il GPS.'},()=>{if(st)st.textContent='Non riesco a leggere il GPS. Puoi scrivere la partenza a mano.'},{enableHighAccuracy:true,timeout:12000})
}
async function publishRideRequest(){
  const from=document.getElementById('rideFrom')?.value.trim()||'',to=document.getElementById('rideTo')?.value.trim()||'',when=document.getElementById('rideWhen')?.value||'',note=document.getElementById('rideNote')?.value.trim()||'';
  const flex=Math.max(0,Math.min(180,Number(document.getElementById('rideFlex')?.value||30))),passengers=Math.max(1,Math.min(6,Number(document.getElementById('ridePassengers')?.value||1))),st=document.getElementById('rideStatus'),btn=document.getElementById('ridePublishBtn');
  if(!from||!to||!when){if(st)st.textContent='Inserisci partenza, destinazione e quando vuoi partire.';return}
  const departure=new Date(when);if(!Number.isFinite(departure.getTime())||departure.getTime()<Date.now()+5*60000){if(st)st.textContent='Scegli un orario almeno 5 minuti nel futuro.';return}
  if(st)st.textContent='Verifico partenza e destinazione…';if(btn)btn.disabled=true;
  try{
    const [a,b]=await Promise.all([parsePlace(from),parsePlace(to)]);
    const payload={user_id:SESSION.user.id,from_label:a.label==='GPS'?'La mia posizione GPS':(a.label||from),from_lat:a.lat,from_lng:a.lng,to_label:b.label||to,to_lat:b.lat,to_lng:b.lng,departure_at:departure.toISOString(),flex_minutes:flex,passengers,note:note.slice(0,300),status:'open'};
    const {error}=await db.from('ride_requests').insert(payload);if(error)throw error;
    await loadRideRequests();closeSheet();page('myreq');
    setTimeout(()=>openSheet(`<div class="tcv-alert-success help"><div class="tcv-alert-success-icon" style="background:#4169e1">🚘</div><div class="big-kicker">PASSAGGIO PUBBLICATO</div><h2>Richiesta attiva</h2><p>Chi sta già andando lungo una strada compatibile potrà trovare la tua richiesta.</p><button class="tcv-success-home" onclick="closeSheet();page('home')">🏠 VAI ALLA HOME</button><button class="tcv-success-map" onclick="closeSheet();page('myreq')">☷ LE MIE RICHIESTE</button></div>`),80)
  }catch(e){if(st)st.textContent='Errore: '+String(e?.message||e);if(btn)btn.disabled=false}
}
async function cancelRideRequest(id){
  if(!confirm('Vuoi annullare questa richiesta di passaggio?'))return;
  const {error}=await db.from('ride_requests').update({status:'cancelled'}).eq('id',id).eq('user_id',SESSION.user.id);if(error){alert(error.message);return}
  await loadRideRequests();renderMyRequests()
}
'''
s = s[:idx] + ride_code + '\n' + s[idx:]

# My rides section in "Le mie".
my_anchor = 'function renderMyRequests(){'
idx = s.find(my_anchor)
if idx == -1:
    raise SystemExit('renderMyRequests anchor not found')
my_code = r'''function tcvRideStatusLabel(r){return r.status==='open'?'🚘 PASSAGGIO CERCATO':r.status==='matched'?'🤝 PASSAGGIO TROVATO':r.status==='completed'?'✅ PASSAGGIO COMPLETATO':'✕ RICHIESTA ANNULLATA'}
function renderMyRideSection(){
  const rows=[...MY_RIDES].sort((a,b)=>new Date(b.created_at)-new Date(a.created_at)),active=rows.filter(r=>r.status==='open'||r.status==='matched');
  if(!rows.length)return `<section class="my-rides-section"><div class="my-rides-title"><div><span>🚘 PASSAGGI</span><h3>I miei passaggi</h3></div><b>0 attivi</b></div><div class="empty">Non hai ancora richiesto un passaggio.</div><button class="ride-publish full" style="margin-top:10px" onclick="openRideRequest()">+ RICHIEDI PASSAGGIO</button></section>`;
  return `<section class="my-rides-section"><div class="my-rides-title"><div><span>🚘 PASSAGGI</span><h3>I miei passaggi</h3></div><b>${active.length} attiv${active.length===1?'o':'i'}</b></div>${rows.map(r=>`<article class="my-ride-card ${r.status}"><div class="my-ride-head"><strong>${tcvRideStatusLabel(r)}</strong><small>${new Date(r.departure_at).toLocaleString('it-IT',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}</small></div><h3>${esc(r.from_label)} → ${esc(r.to_label)}</h3><p>👥 ${Number(r.passengers||1)} · flessibilità ±${Number(r.flex_minutes||0)} min${r.note?`<br>💬 ${esc(r.note)}`:''}</p>${r.status==='open'?`<button class="btn danger full" style="margin-top:9px" onclick="cancelRideRequest('${r.id}')">ANNULLA RICHIESTA PASSAGGIO</button>`:''}</article>`).join('')}<button class="ride-publish full" style="margin-top:10px" onclick="openRideRequest()">+ NUOVO PASSAGGIO</button></section>`
}
'''
s = s[:idx] + my_code + s[idx:]

old_my = '${renderMySosSection()}<div class="sect"><h2>Le mie richieste</h2>'
new_my = '${renderMySosSection()}${renderMyRideSection()}<div class="sect"><h2>Le mie richieste</h2>'
if old_my not in s:
    raise SystemExit('Le mie composition anchor not found')
s = s.replace(old_my, new_my, 1)

# Styling.
css = r'''
/* TCV_RIDE_REQUEST_ENTRY_V1 */
.home-clean-action.ride{border:2px solid #b8c9ff;background:linear-gradient(135deg,#ffffff,#f0f3ff)}
.home-clean-action.ride .home-clean-ico{background:linear-gradient(135deg,#e7ecff,#d7e0ff);box-shadow:inset 0 0 0 1px #c7d2ff}
.home-clean-action.ride b{color:#233f9f;font-size:19px}
.ride-request-hero{margin:12px 0;padding:14px 15px;border-radius:18px;background:linear-gradient(135deg,#244cc8,#697fee);color:#fff;display:grid;gap:3px;box-shadow:0 10px 24px rgba(54,82,183,.2)}
.ride-request-hero b{font-size:11px;letter-spacing:.12em}.ride-request-hero span{font-size:14px;font-weight:850;line-height:1.35}
.ride-publish{border:0;border-radius:15px;min-height:54px;padding:13px 14px;background:linear-gradient(135deg,#244cc8,#627ced);color:#fff;font-size:14px;font-weight:1000;box-shadow:0 9px 22px rgba(54,82,183,.2);margin-top:11px}
.ride-publish:disabled{opacity:.55}
.my-rides-section{margin:0 0 22px;padding:15px;border-radius:24px;background:#fff;border:1px solid #dce4ff;box-shadow:0 9px 24px rgba(13,38,84,.07)}
.my-rides-title{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px}.my-rides-title span{font-size:11px;font-weight:950;color:#2946a5;letter-spacing:.08em}.my-rides-title h3{margin:3px 0 0;font-size:22px}.my-rides-title>b{padding:8px 10px;border-radius:999px;background:#edf1ff;color:#2946a5;font-size:12px}
.my-ride-card{margin-top:9px;padding:14px;border:2px solid #dce4ff;border-radius:18px;background:#f8f9ff}.my-ride-card.cancelled{opacity:.7;background:#f7f7f8;border-color:#e5e7eb}.my-ride-card.completed{background:#f2fff8;border-color:#c7ead7}.my-ride-card.matched{background:#f2fff9;border-color:#aee4c9}.my-ride-head{display:flex;justify-content:space-between;gap:8px;align-items:center}.my-ride-head strong{font-size:11px;color:#2946a5}.my-ride-head small{font-size:11px;color:var(--muted)}.my-ride-card h3{font-size:16px;margin:8px 0 5px;line-height:1.35}.my-ride-card p{font-size:12px;color:#52647f;line-height:1.45;margin:0}
'''
if '</style>' not in s:
    raise SystemExit('style closing tag not found')
s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
print(MARK, 'applied')
