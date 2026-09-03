from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

if 'TCV_MY_SOS_MANAGEMENT_V1' in s:
    print('already applied')
    raise SystemExit(0)

# Keep a private list returned by get-community-alerts for the signed-in user's own SOS.
old_decl = 'WALLET_ENTRIES=[],WALLET_YEAR_ROW=null,COMMUNITY_ALERTS=[];'
new_decl = 'WALLET_ENTRIES=[],WALLET_YEAR_ROW=null,COMMUNITY_ALERTS=[],MY_SOS=[];'
if old_decl not in s:
    raise SystemExit('global state anchor not found')
s = s.replace(old_decl, new_decl, 1)

# Read the private owner list alongside the public community alerts.
old_load = "COMMUNITY_ALERTS=Array.isArray(data?.alerts)?data.alerts:[];"
new_load = "COMMUNITY_ALERTS=Array.isArray(data?.alerts)?data.alerts:[];MY_SOS=Array.isArray(data?.my_sos)?data.my_sos:COMMUNITY_ALERTS.filter(a=>a.is_owner&&a.kind!=='hazard');"
if old_load not in s:
    raise SystemExit('community load anchor not found')
s = s.replace(old_load, new_load, 1)
s = s.replace("}catch(e){COMMUNITY_ALERTS=[];renderHomeCommunityAlarm();", "}catch(e){COMMUNITY_ALERTS=[];MY_SOS=[];renderHomeCommunityAlarm();", 1)

replacement = r'''function tcvFindMySos(id){return MY_SOS.find(x=>String(x.id)===String(id))||COMMUNITY_ALERTS.find(x=>String(x.id)===String(id)&&x.is_owner)}
function tcvMySosCard(a){
  const closed=!!a.owner_closed_at,resolved=!!a.resolved_at&&!closed,active=!a.resolved_at&&!closed,where=String(a.location_label||'').trim(),count=Math.min(3,Number(a.resolution_count||0)),note=String(a.resolution_note||'').trim();
  const state=closed?'✅ CHIUSO DA TE':resolved?'✅ SOS RISOLTO':'🆘 SOS ATTIVO';
  return `<article class="my-sos-card ${closed?'closed':resolved?'resolved':'active'}"><div class="my-sos-head"><span>${state}</span><small>${new Date(a.sent_at||a.created_at).toLocaleString('it-IT',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}</small></div><h3>${esc(a.message||'Richiesta urgente di aiuto')}</h3>${where?`<p>📍 ${esc(where)}</p>`:''}${active?`<div class="my-sos-count">Conferme risoluzione: <b>${count}/3</b></div>`:''}${note?`<div class="my-sos-note"><b>Com'è finita</b><br>${esc(note)}</div>`:''}${active?`<button class="my-sos-manage" onclick="tcvOpenManageMySos('${a.id}')">⚙️ GESTISCI SOS</button>`:resolved?`<button class="my-sos-view" onclick="openCommunityAlertDetail('${a.id}')">VEDI DETTAGLI</button>`:''}</article>`
}
function renderMySosSection(){
  const rows=[...MY_SOS].sort((a,b)=>new Date(b.sent_at||b.created_at)-new Date(a.sent_at||a.created_at));
  const active=rows.filter(a=>!a.resolved_at&&!a.owner_closed_at),recent=rows.filter(a=>a.resolved_at||a.owner_closed_at);
  return `<section class="my-sos-section"><div class="my-sos-title"><div><span>🆘 I MIEI SOS</span><h3>Gestisci emergenze</h3></div><b>${active.length} attiv${active.length===1?'o':'i'}</b></div>${active.length?active.map(tcvMySosCard).join(''):'<div class="notice green">✓ Non hai SOS attivi in questo momento.</div>'}${recent.length?`<div class="my-sos-recent">CHIUSI / RISOLTI NELLE ULTIME 24 ORE</div>${recent.map(tcvMySosCard).join('')}`:''}</section>`
}
function renderMyRequests(){
  let arr=REQUESTS.filter(r=>r.cliente_id===SESSION.user.id);
  myreq.innerHTML=`<div class="pagehead"><div class="k">LE MIE ATTIVITÀ</div><h2>Le mie</h2><p>Qui gestisci i tuoi SOS e le richieste che hai pubblicato.</p></div>${renderMySosSection()}<div class="sect"><h2>Le mie richieste</h2><span>${arr.length}</span></div>${arr.length?arr.map(card).join(''):'<div class="empty">Non hai ancora pubblicato richieste.</div>'}`
}'''

start = s.find('function renderMyRequests(){')
end = s.find('function renderProfile(){', start)
if start == -1 or end == -1:
    raise SystemExit('renderMyRequests anchors not found')
s = s[:start] + replacement + '\n' + s[end:]

start = s.find('async function tcvOwnerCloseSos(id){')
end = s.find('function tcvFocusCommunityAlert(id){', start)
if start == -1 or end == -1:
    raise SystemExit('owner close anchors not found')
owner_block = r'''function tcvOpenManageMySos(id){
  const a=tcvFindMySos(id);if(!a)return;
  if(a.owner_closed_at){return}
  if(a.resolved_at){openCommunityAlertDetail(id);return}
  const where=String(a.location_label||'').trim();
  openSheet(`${head('GESTISCI IL TUO SOS','🆘 SOS attivo','Da qui puoi controllare il tuo SOS oppure chiuderlo subito quando non serve più aiuto.')}<div class="sos-detail-state active">🆘 SOS ATTIVO · ${Math.min(3,Number(a.resolution_count||0))}/3 conferme</div><div class="notice" style="margin-top:10px"><b>${esc(a.message||'Richiesta urgente di aiuto')}</b>${where?`<br>📍 ${esc(where)}`:''}</div>${Number.isFinite(Number(a.lat))&&Number.isFinite(Number(a.lng))?`<button class="btn primary full" style="margin-top:10px" onclick="openCommunityAlertMaps(${Number(a.lat)},${Number(a.lng)})">🧭 VEDI POSIZIONE</button>`:''}<button class="sos-owner-close" style="margin-top:10px" onclick="tcvOpenOwnerCloseForm('${a.id}')">✓ HO RISOLTO · TOGLI SOS</button><button class="btn outline full" style="margin-top:8px" onclick="closeSheet();page('myreq')">← Torna a Le mie</button>`)
}
function tcvOwnerClosePreset(text){const el=document.getElementById('ownerCloseNote');if(el)el.value=text}
function tcvOpenOwnerCloseForm(id){
  const a=tcvFindMySos(id);if(!a)return;
  openSheet(`${head('CHIUSURA SOS','✅ Com’è finita?','Il tuo SOS sparirà subito dalla Home e dalla mappa. Puoi lasciare un breve messaggio su cosa è successo o ringraziare la comunità.')}<div class="owner-close-presets"><button onclick="tcvOwnerClosePreset('Risolto, grazie di cuore a tutti ❤️')">❤️ Grazie a tutti</button><button onclick="tcvOwnerClosePreset('Problema risolto, grazie a chi è intervenuto 🙏')">🙏 Risolto</button><button onclick="tcvOwnerClosePreset('Situazione rientrata, non serve più aiuto.')">✓ Tutto a posto</button></div><div class="field"><label>COM’È FINITA? · FACOLTATIVO</label><textarea id="ownerCloseNote" rows="4" maxlength="400" placeholder="Es. Ho risolto, grazie di cuore a chi mi ha aiutato."></textarea></div><div class="notice green">Il messaggio resta nel tuo storico SOS per 24 ore. L’allarme attivo invece viene tolto immediatamente.</div><button id="ownerCloseConfirm" class="sos-owner-close" style="margin-top:10px;background:#d92132;color:#fff" onclick="tcvSubmitOwnerClose('${id}')">✓ CHIUDI E TOGLI SOS ORA</button><button class="btn outline full" style="margin-top:8px" onclick="tcvOpenManageMySos('${id}')">← Indietro</button>`)
}
async function tcvSubmitOwnerClose(id){
  const note=document.getElementById('ownerCloseNote')?.value.trim()||'',btn=document.getElementById('ownerCloseConfirm');
  if(!confirm('Confermi che questo SOS è risolto? Verrà tolto subito dagli SOS attivi.'))return;
  if(btn){btn.disabled=true;btn.textContent='Chiusura SOS…'}
  try{
    const {data,error}=await db.functions.invoke('manage-help-alert',{body:{action:'owner_close',alert_id:id,resolution_note:note}});if(error)throw error;if(data?.error)throw new Error(data.error);
    closeSheet();await loadCommunityAlerts();renderMyRequests();renderHomeCommunityAlarm();if(!document.getElementById('mapPage')?.classList.contains('hidden'))renderMapPage();
    openSheet(`<div class="tcv-alert-success help"><div class="tcv-alert-success-icon" style="background:#20ad69">✓</div><div class="big-kicker">SOS CHIUSO</div><h2>Tutto risolto</h2><p>Il tuo SOS non è più visibile tra gli allarmi attivi.${note?`<br><br>“${esc(note)}”`:''}</p><button class="tcv-success-home" onclick="closeSheet();page('home')">🏠 VAI ALLA HOME</button><button class="tcv-success-map" onclick="closeSheet();page('myreq')">☷ I MIEI SOS</button></div>`)
  }catch(e){alert('Non riesco a chiudere il SOS: '+String(e?.message||e));if(btn){btn.disabled=false;btn.textContent='✓ CHIUDI E TOGLI SOS ORA'}}
}
function tcvOwnerCloseSos(id){tcvOpenOwnerCloseForm(id)}
'''
s = s[:start] + owner_block + '\n' + s[end:]

css = r'''
/* TCV_MY_SOS_MANAGEMENT_V1 */
.my-sos-section{margin:4px 0 22px;padding:15px;border-radius:24px;background:#fff;border:1px solid var(--line);box-shadow:0 9px 24px rgba(13,38,84,.07)}
.my-sos-title{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:11px}.my-sos-title span{font-size:11px;font-weight:950;color:#b21324;letter-spacing:.08em}.my-sos-title h3{font-size:22px;margin:3px 0 0}.my-sos-title>b{padding:8px 10px;border-radius:999px;background:#fff0f1;color:#b21324;font-size:12px}
.my-sos-card{padding:14px;border-radius:18px;margin-top:9px;border:2px solid #e7edf5;background:#fff}.my-sos-card.active{border-color:#efb3ba;background:#fff7f8}.my-sos-card.resolved{border-color:#b9ebd2;background:#f3fff8}.my-sos-card.closed{border-color:#d7e4f2;background:#f8fbff}.my-sos-head{display:flex;justify-content:space-between;align-items:center;gap:8px}.my-sos-head span{font-size:12px;font-weight:950}.my-sos-head small{font-size:11px;color:var(--muted)}.my-sos-card h3{font-size:17px;margin:8px 0 4px}.my-sos-card p{font-size:13px;margin:5px 0;color:#52647f;line-height:1.4}.my-sos-count{font-size:12px;margin-top:7px}.my-sos-note{margin-top:9px;padding:10px;border-radius:13px;background:#fff;border:1px solid #dfe8f4;font-size:13px;line-height:1.45}.my-sos-manage,.my-sos-view{width:100%;min-height:50px;border:0;border-radius:14px;margin-top:10px;font-size:14px;font-weight:950}.my-sos-manage{background:#d92132;color:#fff}.my-sos-view{background:#20ad69;color:#fff}.my-sos-recent{margin:16px 2px 5px;font-size:10px;font-weight:950;color:#61708a;letter-spacing:.07em}.owner-close-presets{display:grid;grid-template-columns:1fr;gap:7px;margin:12px 0}.owner-close-presets button{border:1px solid #d7e4f2;background:#f8fbff;border-radius:14px;padding:12px;text-align:left;font-size:14px;font-weight:850;color:#10213d}
'''
if '</style>' not in s:
    raise SystemExit('style closing tag not found')
s = s.replace('</style>', css + '\n</style>', 1)

p.write_text(s, encoding='utf-8')
print('TCV_MY_SOS_MANAGEMENT_V1 applied')
# trigger: workflow is installed before this commit
