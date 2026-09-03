from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

old="""function renderHomeCommunityAlarm(){
  const host=document.getElementById('homeCommunityAlarm');if(!host)return;
  const helps=COMMUNITY_ALERTS.filter(a=>a.kind!=='hazard');
  const active=helps.filter(a=>!a.resolved_at).sort((a,b)=>new Date(b.sent_at||b.created_at)-new Date(a.sent_at||a.created_at));
  const resolved=helps.filter(a=>a.resolved_at).sort((a,b)=>new Date(b.resolved_at)-new Date(a.resolved_at));
  const a=active[0]||resolved[0];if(!a){host.innerHTML='';return}
  const isResolved=!!a.resolved_at,more=(isResolved?resolved:active).length-1;
  const where=String(a.location_label||'').trim();
  host.innerHTML=`<button class=\"home-community-alarm ${isResolved?'resolved':'active'}\" onclick=\"openCommunityAlertDetail('${a.id}')\"><div class=\"alarm-top\"><span class=\"alarm-icon\">${isResolved?'✅':'🆘'}</span><span class=\"alarm-title\">${isResolved?'SOS RISOLTO':'SOS ATTIVO'}</span></div><span class=\"alarm-sub\">${esc(a.sender_name||'Un utente')}${where?' · '+esc(where):''}${more>0?` · +${more} altro${more>1?'i':''}`:''}</span><span class=\"alarm-go\">${isResolved?'3 conferme · vedi dettagli':'TOCCA QUI · VAI DIRETTAMENTE ALL’SOS →'}</span></button>`;
}
"""

new="""function tcvSosDistanceKm(a){
  if(!USER_POS||!Number.isFinite(Number(a?.lat))||!Number.isFinite(Number(a?.lng)))return null;
  return distanceKm(USER_POS,{lat:Number(a.lat),lng:Number(a.lng)})
}
function tcvSortedActiveSos(){
  const rows=COMMUNITY_ALERTS.filter(a=>a.kind!=='hazard'&&!a.resolved_at);
  return rows.sort((a,b)=>{
    const da=tcvSosDistanceKm(a),db=tcvSosDistanceKm(b);
    if(da!=null&&db!=null)return da-db||new Date(b.sent_at||b.created_at)-new Date(a.sent_at||a.created_at);
    if(da!=null)return -1;if(db!=null)return 1;
    return new Date(b.sent_at||b.created_at)-new Date(a.sent_at||a.created_at)
  })
}
function tcvResolvedSosRows(){
  return COMMUNITY_ALERTS.filter(a=>a.kind!=='hazard'&&a.resolved_at).sort((a,b)=>new Date(b.resolved_at)-new Date(a.resolved_at))
}
function tcvSosDistanceLabel(a){const d=tcvSosDistanceKm(a);return d==null?'':(d<1?`${Math.max(10,Math.round(d*1000))} m`:`${d.toFixed(d<10?1:0)} km`)}
function renderHomeCommunityAlarm(){
  const host=document.getElementById('homeCommunityAlarm');if(!host)return;
  const active=tcvSortedActiveSos(),resolved=tcvResolvedSosRows();
  const a=active[0]||resolved[0];if(!a){host.innerHTML='';return}
  const isResolved=!!a.resolved_at,more=(isResolved?resolved:active).length-1;
  const where=String(a.location_label||'').trim(),dist=tcvSosDistanceLabel(a);
  const rank=!isResolved&&active.length>1?(dist?'SOS PIÙ VICINO':'SOS PIÙ RECENTE'):'';
  const allBtn=!isResolved&&active.length>1?`<button class=\"home-sos-all-btn\" onclick=\"event.stopPropagation();openAllCommunitySos()\">🆘 VEDI TUTTI GLI SOS ATTIVI · ${active.length}</button>`:'';
  host.innerHTML=`<button class=\"home-community-alarm ${isResolved?'resolved':'active'}\" onclick=\"openCommunityAlertDetail('${a.id}')\"><div class=\"alarm-top\"><span class=\"alarm-icon\">${isResolved?'✅':'🆘'}</span><span class=\"alarm-title\">${isResolved?'SOS RISOLTO':'SOS ATTIVO'}</span></div>${rank?`<span class=\"alarm-rank\">${rank}${dist?' · '+dist:''}</span>`:''}<span class=\"alarm-sub\">${esc(a.sender_name||'Un utente')}${where?' · '+esc(where):''}${more>0?` · +${more} altro${more>1?'i':''}`:''}</span><span class=\"alarm-go\">${isResolved?'3 conferme · vedi dettagli':'TOCCA QUI · APRI QUESTO SOS →'}</span></button>${allBtn}`;
}
async function tcvEnsureSosGps(){
  if(USER_POS)return true;
  try{
    let canTry=true;
    if(navigator.permissions?.query){try{const ps=await navigator.permissions.query({name:'geolocation'});canTry=ps.state==='granted'}catch(e){}}
    if(!canTry)return false;
    const p=await currentPosition();USER_POS={lat:Number(p.lat),lng:Number(p.lng)};renderHomeCommunityAlarm();return true
  }catch(e){return false}
}
function tcvSosListCard(a){
  const where=String(a.location_label||'').trim(),count=Math.min(3,Number(a.resolution_count||0)),dist=tcvSosDistanceLabel(a),resolved=!!a.resolved_at;
  return `<article class=\"sos-list-card ${resolved?'resolved':'active'}\"><div class=\"sos-list-head\"><div><span class=\"sos-list-state\">${resolved?'✅ RISOLTO':'🆘 SOS ATTIVO'}</span><h3>${esc(a.sender_name||'Un utente')}</h3></div>${dist?`<strong>${esc(dist)}</strong>`:''}</div><p>${esc(a.message||'Richiesta urgente di aiuto')}</p>${where?`<div class=\"sos-list-where\">📍 ${esc(where)}</div>`:'<div class=\"sos-list-where\">📍 Posizione non disponibile</div>'}<div class=\"sos-list-meta\">${resolved?'3/3 conferme':`${count}/3 conferme risoluzione`}${dist?' · distanza dal tuo telefono':''}</div><button class=\"sos-list-open\" onclick=\"openCommunityAlertDetail('${a.id}')\">${resolved?'APRI DETTAGLI':'APRI QUESTO SOS'}</button></article>`
}
async function openAllCommunitySos(tryGps=true){
  if(tryGps&&!USER_POS){await tcvEnsureSosGps()}
  const active=tcvSortedActiveSos(),resolved=tcvResolvedSosRows();
  const orderText=USER_POS?'Ordinati dal più vicino al tuo telefono.':'GPS non disponibile: ordinati dal più recente.';
  openSheet(`${head('SOS DELLA COMUNITÀ',`🆘 ${active.length} SOS attiv${active.length===1?'o':'i'}`,active.length?orderText:'Non risultano SOS attivi in questo momento.')}<div class=\"sos-list-summary\"><b>${active.length}</b><span>SOS ATTIVI</span>${USER_POS?'<small>📍 distanza calcolata dal tuo telefono</small>':'<button onclick=\"tcvForceSosGpsList()\">📍 ORDINA PER VICINANZA</button>'}</div>${active.length?`<div class=\"sos-list-grid\">${active.map(tcvSosListCard).join('')}</div>`:'<div class=\"empty\">Nessun SOS attivo.</div>'}${resolved.length?`<div class=\"sos-list-resolved-title\">✅ RISOLTI NELLE ULTIME 24 ORE</div><div class=\"sos-list-grid\">${resolved.map(tcvSosListCard).join('')}</div>`:''}<button class=\"btn outline full\" style=\"margin-top:12px\" onclick=\"closeSheet();page('home')\">🏠 Torna alla Home</button>`)
}
async function tcvForceSosGpsList(){
  try{const p=await currentPosition();USER_POS={lat:Number(p.lat),lng:Number(p.lng)};renderHomeCommunityAlarm();openAllCommunitySos(false)}catch(e){alert('Consenti la posizione al telefono per ordinare gli SOS dal più vicino.')}
}
"""

if old not in s:
    raise SystemExit('renderHomeCommunityAlarm block not found')
s=s.replace(old,new,1)

css="""
/* TCV_ALL_ACTIVE_SOS_LIST_V1 */
.home-sos-all-btn{width:100%;margin:-7px 0 16px;border:2px solid #d92132;border-radius:18px;padding:13px 12px;background:#fff;color:#b31426;font-size:14px;font-weight:1000;box-shadow:0 8px 20px rgba(185,15,34,.09)}
.home-sos-all-btn:active{transform:scale(.99)}
.home-community-alarm .alarm-rank{display:inline-block;margin-top:9px;padding:6px 9px;border-radius:999px;background:rgba(255,255,255,.2);font-size:11px;letter-spacing:.035em}
.sos-list-summary{margin:12px 0;padding:15px;border-radius:19px;background:#fff0f1;border:2px solid #f0bcc2;display:grid;grid-template-columns:auto 1fr;align-items:center;gap:4px 10px;color:#9e1827}.sos-list-summary b{font-size:31px;line-height:1}.sos-list-summary span{font-size:15px;font-weight:1000}.sos-list-summary small{grid-column:1/-1;color:#71464c;font-size:12px}.sos-list-summary button{grid-column:1/-1;border:1px solid #e2a8af;border-radius:13px;background:#fff;padding:10px;color:#9e1827;font-size:12px;font-weight:950}
.sos-list-grid{display:grid;gap:10px}.sos-list-card{border-radius:21px;padding:15px;background:#fff;border:2px solid #efb9c0;box-shadow:0 8px 20px rgba(16,38,74,.07)}.sos-list-card.resolved{border-color:#b9e6ce;background:#f3fff8}.sos-list-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.sos-list-state{font-size:11px;font-weight:1000;color:#b21324;letter-spacing:.035em}.sos-list-card.resolved .sos-list-state{color:#187047}.sos-list-head h3{margin:5px 0 0;font-size:21px;line-height:1.08}.sos-list-head strong{white-space:nowrap;border-radius:999px;background:#fff0f1;color:#a91525;padding:7px 10px;font-size:13px}.sos-list-card.resolved .sos-list-head strong{background:#e3f8ed;color:#187047}.sos-list-card p{margin:11px 0 6px;font-size:14px;line-height:1.45;font-weight:750}.sos-list-where{font-size:13px;line-height:1.4;color:#52647f}.sos-list-meta{margin-top:8px;font-size:11px;font-weight:850;color:#7d5960}.sos-list-open{width:100%;margin-top:11px;border:0;border-radius:15px;padding:13px;background:#d92132;color:#fff;font-size:14px;font-weight:1000}.sos-list-card.resolved .sos-list-open{background:#20ad69}.sos-list-resolved-title{margin:20px 2px 10px;font-size:12px;font-weight:1000;color:#20704a;letter-spacing:.05em}
"""
marker='</style>'
if 'TCV_ALL_ACTIVE_SOS_LIST_V1' not in s:
    s=s.replace(marker,css+'\n'+marker,1)

p.write_text(s,encoding='utf-8')
print('patched all active SOS list')
