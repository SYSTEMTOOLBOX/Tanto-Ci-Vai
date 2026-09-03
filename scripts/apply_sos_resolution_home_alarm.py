from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# 1) Home alarm host.
needle='<main id="home" class="home-clean"><div class="home-sos-wrap">'
if 'id="homeCommunityAlarm"' not in s:
    if needle not in s:
        raise SystemExit('Home anchor not found')
    s=s.replace(needle,'<main id="home" class="home-clean"><section id="homeCommunityAlarm"></section><div class="home-sos-wrap">',1)

# 2) CSS for active/resolved SOS and green map marker.
if '/* TCV_SOS_RESOLUTION_V1 */' not in s:
    css=r'''
/* TCV_SOS_RESOLUTION_V1 */
#homeCommunityAlarm:empty{display:none}.home-community-alarm{width:100%;border:0;border-radius:24px;padding:18px;margin:2px 0 16px;text-align:left;box-shadow:0 14px 34px rgba(7,26,61,.18);font-weight:900}.home-community-alarm.active{background:linear-gradient(135deg,#b90f22,#e42b3f);color:#fff;animation:tcvHomeAlarmPulse 1.2s infinite}.home-community-alarm.resolved{background:linear-gradient(135deg,#15854e,#22b56d);color:#fff}.home-community-alarm .alarm-top{display:flex;align-items:center;justify-content:space-between;gap:10px}.home-community-alarm .alarm-icon{font-size:42px}.home-community-alarm .alarm-title{font-size:25px;line-height:1;letter-spacing:-.04em}.home-community-alarm .alarm-sub{display:block;font-size:12px;line-height:1.35;margin-top:8px;opacity:.96}.home-community-alarm .alarm-go{display:inline-block;margin-top:12px;padding:8px 11px;border-radius:999px;background:rgba(255,255,255,.18);font-size:11px}.community-marker.resolved{background:#20ad69;color:#fff;animation:none}.map-key-dot.resolved{background:#20ad69}.sos-detail-state{padding:12px;border-radius:16px;margin:10px 0;font-size:12px;font-weight:900;text-align:center}.sos-detail-state.active{background:#fff0f1;color:#a51020;border:2px solid #efb3ba}.sos-detail-state.resolved{background:#eafff2;color:#176b45;border:2px solid #b9ebd2}.sos-resolution-progress{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:10px 0}.sos-resolution-progress i{height:9px;border-radius:99px;background:#e4e9f0}.sos-resolution-progress i.on{background:#20ad69}.sos-resolve-btn{width:100%;border:0;border-radius:16px;padding:14px;background:#20ad69;color:#fff;font-weight:950;font-size:13px}.sos-resolve-btn:disabled{opacity:.65}.sos-owner-close{width:100%;border:2px solid #d92132;border-radius:16px;padding:13px;background:#fff;color:#b21324;font-weight:950;font-size:13px;margin-top:8px}@keyframes tcvHomeAlarmPulse{0%,100%{transform:scale(1);box-shadow:0 14px 34px rgba(185,15,34,.25),0 0 0 0 rgba(217,33,50,.26)}50%{transform:scale(1.012);box-shadow:0 14px 34px rgba(185,15,34,.35),0 0 0 10px rgba(217,33,50,0)}}
'''
    s=s.replace('</style>',css+'\n</style>',1)

# 3) Replace alert-loading / icon / detail helpers.
pat=re.compile(r"async function loadCommunityAlerts\(\)\{.*?\n\}\nfunction communityAlertIcon\(kind\)\{.*?\n\}\nfunction openCommunityAlertMaps\(lat,lng\)\{.*?\n\}\nfunction communityAlertPopup\(a\)\{.*?\n\}",re.S)
new=r'''async function loadCommunityAlerts(){
  const st=document.getElementById('mapAlertStatus');
  try{
    if(st)st.textContent='Aggiorno pericoli e richieste di aiuto…';
    const {data,error}=await db.functions.invoke('get-community-alerts',{body:{}});if(error)throw error;if(data?.error)throw new Error(data.error);
    COMMUNITY_ALERTS=Array.isArray(data?.alerts)?data.alerts.filter(a=>Number.isFinite(+a.lat)&&Number.isFinite(+a.lng)):[];
    const hazards=COMMUNITY_ALERTS.filter(a=>a.kind==='hazard').length;
    const active=COMMUNITY_ALERTS.filter(a=>a.kind!=='hazard'&&!a.resolved_at).length;
    const resolved=COMMUNITY_ALERTS.filter(a=>a.kind!=='hazard'&&a.resolved_at).length;
    if(st)st.innerHTML=`Aggiornata ora · <b>${hazards}</b> pericoli · <b>${active}</b> SOS attivi · <b>${resolved}</b> risolti`;
    renderHomeCommunityAlarm();
  }catch(e){COMMUNITY_ALERTS=[];renderHomeCommunityAlarm();if(st)st.textContent='Ritiri aggiornati. Avvisi comunità momentaneamente non disponibili.';console.warn('Community alerts map',e)}
}
function renderHomeCommunityAlarm(){
  const host=document.getElementById('homeCommunityAlarm');if(!host)return;
  const helps=COMMUNITY_ALERTS.filter(a=>a.kind!=='hazard');
  const active=helps.filter(a=>!a.resolved_at).sort((a,b)=>new Date(b.sent_at||b.created_at)-new Date(a.sent_at||a.created_at));
  const resolved=helps.filter(a=>a.resolved_at).sort((a,b)=>new Date(b.resolved_at)-new Date(a.resolved_at));
  const a=active[0]||resolved[0];if(!a){host.innerHTML='';return}
  const isResolved=!!a.resolved_at,more=(isResolved?resolved:active).length-1;
  const where=String(a.location_label||'').trim();
  host.innerHTML=`<button class="home-community-alarm ${isResolved?'resolved':'active'}" onclick="openCommunityAlertDetail('${a.id}')"><div class="alarm-top"><span class="alarm-icon">${isResolved?'✅':'🆘'}</span><span class="alarm-title">${isResolved?'SOS RISOLTO':'SOS ATTIVO'}</span></div><span class="alarm-sub">${esc(a.sender_name||'Un utente')}${where?' · '+esc(where):''}${more>0?` · +${more} altro${more>1?'i':''}`:''}</span><span class="alarm-go">${isResolved?'3 conferme · vedi dettagli':'TOCCA QUI · VAI DIRETTAMENTE ALL’SOS →'}</span></button>`;
}
function communityAlertIcon(a){
  const hazard=a.kind==='hazard',resolved=!hazard&&!!a.resolved_at;
  return L.divIcon({className:'community-marker-wrap',html:`<div class="community-marker ${hazard?'hazard':(resolved?'resolved':'help')}">${hazard?'⚠':(resolved?'✓':'🆘')}</div>`,iconSize:[46,46],iconAnchor:[23,23],popupAnchor:[0,-25]})
}
function openCommunityAlertMaps(lat,lng){
  const url=`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${lat},${lng}`)}&dir_action=navigate`;
  window.open(url,'_blank')
}
function communityAlertPopup(a){
  const hazard=a.kind==='hazard',resolved=!hazard&&!!a.resolved_at;
  const title=hazard?'⚠️ PERICOLO SEGNALATO':(resolved?'✅ SOS RISOLTO':'🆘 ASSISTENZA IMMEDIATA');
  const msg=String(a.message||'').trim()||(hazard?'Pericolo segnalato dalla comunità':'Richiesta urgente di aiuto');
  const where=String(a.location_label||'').trim();
  const votes=!hazard?`<div class="where">Conferme risoluzione: ${Math.min(3,Number(a.resolution_count||0))}/3</div>`:'';
  return `<div class="community-popup"><b>${title}</b><div class="msg">${esc(msg)}</div>${where?`<div class="where">📍 ${esc(where)}</div>`:''}<div class="where">Segnalato da ${esc(a.sender_name||'un utente')}</div>${votes}<button onclick="openCommunityAlertDetail('${a.id}')">APRI SOS</button><button onclick="openCommunityAlertMaps(${Number(a.lat)},${Number(a.lng)})">🧭 INDICAZIONI</button></div>`
}
function sosResolutionBars(n){n=Math.max(0,Math.min(3,Number(n||0)));return `<div class="sos-resolution-progress">${[1,2,3].map(i=>`<i class="${i<=n?'on':''}"></i>`).join('')}</div>`}
function openCommunityAlertDetail(id){
  const a=COMMUNITY_ALERTS.find(x=>String(x.id)===String(id));if(!a)return;
  if(a.kind==='hazard'){openCommunityAlertMaps(a.lat,a.lng);return}
  const resolved=!!a.resolved_at,count=Math.min(3,Number(a.resolution_count||0)),where=String(a.location_label||'').trim();
  const state=`<div class="sos-detail-state ${resolved?'resolved':'active'}">${resolved?'✅ SOS RISOLTO':'🆘 SOS ATTIVO'} · ${count}/3 conferme</div>${sosResolutionBars(count)}`;
  const vote=resolved?'':`<button class="sos-resolve-btn" ${a.viewer_voted?'disabled':''} onclick="tcvVoteSosResolved('${a.id}')">${a.viewer_voted?'✓ HAI GIÀ SEGNALATO RISOLTO':'✓ SEGNALA SOS RISOLTO'}</button>`;
  const owner=a.is_owner?`<button class="sos-owner-close" onclick="tcvOwnerCloseSos('${a.id}')">✕ TOGLI IL MIO SOS SUBITO</button>`:'';
  openSheet(`${head(resolved?'SOS RISOLTO':'ASSISTENZA IMMEDIATA',resolved?'✅ Situazione risolta':'🆘 Richiesta SOS',resolved?'Tre persone hanno confermato la risoluzione. Rimarrà verde per 24 ore.':'Serve assistenza: verifica la situazione prima di segnalarla come risolta.')}${state}<div class="notice" style="margin-top:10px"><b>${esc(a.message||'Richiesta urgente di aiuto')}</b>${where?`<br>📍 ${esc(where)}`:''}<br>Segnalato da ${esc(a.sender_name||'un utente')}</div><button class="btn primary full" style="margin-top:10px" onclick="openCommunityAlertMaps(${Number(a.lat)},${Number(a.lng)})">🧭 VAI AL PUNTO SOS</button>${vote}${owner}<button class="btn outline full" style="margin-top:8px" onclick="tcvFocusCommunityAlert('${a.id}')">⌖ VEDI SULLA MAPPA</button>`)
}
async function tcvVoteSosResolved(id){
  try{
    const {data,error}=await db.functions.invoke('manage-help-alert',{body:{action:'vote_resolved',alert_id:id}});if(error)throw error;if(data?.error)throw new Error(data.error);
    await loadCommunityAlerts();if(!document.getElementById('mapPage')?.classList.contains('hidden'))renderMapPage();
    const a=COMMUNITY_ALERTS.find(x=>String(x.id)===String(id));
    if(data?.resolved)alert('✅ Tre persone hanno confermato: SOS RISOLTO.');
    if(a)openCommunityAlertDetail(id);else closeSheet();
  }catch(e){alert('Non riesco a registrare la conferma: '+String(e?.message||e))}
}
async function tcvOwnerCloseSos(id){
  if(!confirm('Togliere subito questo SOS? Sparirà immediatamente dalla comunità.'))return;
  try{
    const {data,error}=await db.functions.invoke('manage-help-alert',{body:{action:'owner_close',alert_id:id}});if(error)throw error;if(data?.error)throw new Error(data.error);
    closeSheet();await loadCommunityAlerts();if(!document.getElementById('mapPage')?.classList.contains('hidden'))renderMapPage();alert('✓ SOS rimosso subito.');
  }catch(e){alert('Non riesco a rimuovere il SOS: '+String(e?.message||e))}
}
function tcvFocusCommunityAlert(id){
  const a=COMMUNITY_ALERTS.find(x=>String(x.id)===String(id));if(!a)return;closeSheet();page('mapPage');setTimeout(()=>{if(MAP){MAP.setView([Number(a.lat),Number(a.lng)],16)}},500)
}
'''
s2,n=pat.subn(new,s,count=1)
if n!=1: raise SystemExit(f'Alert helper block not replaced: {n}')
s=s2

# 4) Map icon now receives the whole alert object; add green legend.
s=s.replace('communityAlertIcon(a.kind)','communityAlertIcon(a)')
s=s.replace('<span><i class="map-key-dot help"></i> Assistenza immediata</span>','<span><i class="map-key-dot help"></i> SOS attivo</span><span><i class="map-key-dot resolved"></i> SOS risolto</span>',1)

# 5) Refresh alerts every time Home is opened.
old="function page(p){['home','available','missions','myreq','mapPage','wallet','profile'].forEach(x=>{document.getElementById(x).classList.toggle('hidden',x!==p);document.querySelector(`[data-p=\"${x}\"]`)?.classList.toggle('active',x===p)});if(p==='available')renderFeed();"
newp="function page(p){['home','available','missions','myreq','mapPage','wallet','profile'].forEach(x=>{document.getElementById(x).classList.toggle('hidden',x!==p);document.querySelector(`[data-p=\"${x}\"]`)?.classList.toggle('active',x===p)});if(p==='home')loadCommunityAlerts();if(p==='available')renderFeed();"
if old not in s: raise SystemExit('page() anchor not found')
s=s.replace(old,newp,1)

# 6) While Home stays open, refresh SOS state periodically.
if 'TCV_HOME_SOS_POLL_V1' not in s:
    anchor='function renderHomeCommunityAlarm(){'
    s=s.replace(anchor,"/* TCV_HOME_SOS_POLL_V1 */\nsetInterval(()=>{if(SESSION&&!document.getElementById('home')?.classList.contains('hidden'))loadCommunityAlerts()},12000);\n"+anchor,1)

# 7) Force service worker refresh.
s=re.sub(r"sw\.js\?v=\d+","sw.js?v=11",s)

p.write_text(s,encoding='utf-8')
print('Applied SOS resolution voting, green resolved state and prominent Home alarm')
