from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

css = r'''
/* RUNNER_WALLET_V1 */
.wallet-mini{margin:0 0 12px;padding:16px;border-radius:22px;background:linear-gradient(135deg,#071a3d,#0b66ff);color:#fff;box-shadow:0 14px 30px rgba(7,26,61,.18)}
.wallet-mini-top{display:flex;align-items:center;justify-content:space-between;gap:12px}.wallet-mini b{font-size:23px;letter-spacing:-.04em}.wallet-mini small{display:block;margin-top:3px;font-size:9px;opacity:.78}.wallet-mini .btn{margin-top:11px;background:#fff;color:#0b66ff}
.wallet-hero{padding:20px;border-radius:26px;background:linear-gradient(135deg,#071a3d,#0b66ff 62%,#08cdb0);color:#fff;box-shadow:0 18px 40px rgba(7,26,61,.2)}
.wallet-hero .eyebrow{opacity:.8}.wallet-total{font-size:42px;line-height:1;font-weight:1000;letter-spacing:-.055em;margin:9px 0 5px}.wallet-sub{font-size:11px;line-height:1.45;opacity:.85}
.wallet-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:15px}.wallet-stat{padding:12px;border-radius:16px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.12)}.wallet-stat b{display:block;font-size:19px}.wallet-stat span{font-size:8px;opacity:.8}
.wallet-progress-wrap{margin-top:16px}.wallet-progress-label{display:flex;justify-content:space-between;gap:10px;font-size:9px;font-weight:900;margin-bottom:7px}.wallet-progress{height:13px;border-radius:999px;background:rgba(255,255,255,.2);overflow:hidden}.wallet-progress>div{height:100%;border-radius:999px;background:#fff;transition:width .25s ease}
.wallet-alert{margin:11px 0 0;padding:11px 12px;border-radius:15px;font-size:10px;line-height:1.45;font-weight:750}.wallet-alert.good{background:#effff8;border:1px solid #cceedd;color:#286b54}.wallet-alert.watch{background:#fff9e7;border:1px solid #f7df9b;color:#755711}.wallet-alert.danger{background:#fff0f1;border:1px solid #f3c4ca;color:#923444}
.wallet-section{margin-top:15px;padding:15px;background:#fff;border:1px solid var(--line);border-radius:21px;box-shadow:0 8px 22px rgba(13,38,84,.06)}.wallet-section h3{margin:0 0 4px;font-size:16px}.wallet-section>p{margin:0;color:var(--muted);font-size:10px;line-height:1.5}
.wallet-entry{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center;padding:11px 0;border-bottom:1px solid #edf2f8}.wallet-entry:last-child{border-bottom:0}.wallet-entry b{display:block;font-size:12px}.wallet-entry small{display:block;color:var(--muted);font-size:8px;margin-top:3px}.wallet-entry strong{font-size:13px;color:#078b73}
.wallet-legal{margin-top:14px;padding:13px;border-radius:17px;background:#f6f8fc;border:1px solid var(--line);font-size:9px;line-height:1.55;color:#59677f}.wallet-legal b{color:var(--ink)}
'''
style_marker = '\n</style>\n</head>'
if '/* RUNNER_WALLET_V1 */' not in s:
    if style_marker not in s: raise SystemExit('style marker not found')
    s = s.replace(style_marker, '\n' + css + style_marker, 1)

old_mains = '<main id="missions" class="hidden"></main><main id="myreq" class="hidden"></main><main id="mapPage" class="hidden"></main><main id="profile" class="hidden"></main></div>'
new_mains = '<main id="missions" class="hidden"></main><main id="myreq" class="hidden"></main><main id="mapPage" class="hidden"></main><main id="wallet" class="hidden"></main><main id="profile" class="hidden"></main></div>'
if old_mains not in s: raise SystemExit('main pages block not found')
s = s.replace(old_mains, new_mains, 1)

old_state = 'DELIVERY_STREET_RESULTS=[],DELIVERY_TIMER=null,DELIVERY_CITY_POS=null;'
new_state = 'DELIVERY_STREET_RESULTS=[],DELIVERY_TIMER=null,DELIVERY_CITY_POS=null,WALLET_ENTRIES=[],WALLET_YEAR_ROW=null;'
if old_state not in s: raise SystemExit('state block not found')
s = s.replace(old_state, new_state, 1)

old_after = "async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');let splashPromise=runStartupSplash(session);await ensureProfile();await loadRequests();subscribeRealtime();renderAll();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000);await splashPromise;setTimeout(()=>tcvMaybeOfferPush(),350);setTimeout(()=>tcvOpenRequestFromUrl(),500)}"
new_after = "async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');let splashPromise=runStartupSplash(session);await ensureProfile();await loadRequests();await loadWallet();subscribeRealtime();renderAll();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000);await splashPromise;setTimeout(()=>tcvMaybeOfferPush(),350);setTimeout(()=>tcvOpenRequestFromUrl(),500)}"
if old_after not in s: raise SystemExit('afterLogin block not found')
s = s.replace(old_after, new_after, 1)

old_rt = "function subscribeRealtime(){if(CHANNEL)db.removeChannel(CHANNEL);CHANNEL=db.channel('tcv-consegne').on('postgres_changes',{event:'*',schema:'public',table:'consegne'},async()=>{syncBadge.textContent='● SYNC';await loadRequests();renderAll();setTimeout(()=>syncBadge.textContent='● ONLINE',700)}).subscribe()}"
new_rt = "function subscribeRealtime(){if(CHANNEL)db.removeChannel(CHANNEL);CHANNEL=db.channel('tcv-consegne').on('postgres_changes',{event:'*',schema:'public',table:'consegne'},async()=>{syncBadge.textContent='● SYNC';await loadRequests();await loadWallet();renderAll();setTimeout(()=>syncBadge.textContent='● ONLINE',700)}).subscribe()}"
if old_rt not in s: raise SystemExit('realtime block not found')
s = s.replace(old_rt, new_rt, 1)

old_all = "function renderAll(){renderFeed();renderStats();if(!missions.classList.contains('hidden'))renderMissions();if(!myreq.classList.contains('hidden'))renderMyRequests();if(!profile.classList.contains('hidden'))renderProfile()}"
new_all = "function renderAll(){renderFeed();renderStats();if(!missions.classList.contains('hidden'))renderMissions();if(!myreq.classList.contains('hidden'))renderMyRequests();if(!document.getElementById('wallet').classList.contains('hidden'))renderWallet();if(!profile.classList.contains('hidden'))renderProfile()}"
if old_all not in s: raise SystemExit('renderAll block not found')
s = s.replace(old_all, new_all, 1)

old_status = "async function setStatus(id,status){let {data,error}=await db.rpc('aggiorna_stato_consegna',{p_consegna_id:id,p_stato:status});if(error){alert(error.message);return}if(!data){alert('Operazione non consentita o stato già cambiato.');return}await loadRequests();renderAll()}"
new_status = "async function setStatus(id,status){let before=status==='consegnata'?walletTrackedTotal():null;let {data,error}=await db.rpc('aggiorna_stato_consegna',{p_consegna_id:id,p_stato:status});if(error){alert(error.message);return}if(!data){alert('Operazione non consentita o stato già cambiato.');return}await loadRequests();if(status==='consegnata')await loadWallet();renderAll();if(status==='consegnata')tcvMaybeShowWalletMilestone(before,walletTrackedTotal())}"
if old_status not in s: raise SystemExit('setStatus block not found')
s = s.replace(old_status, new_status, 1)

old_page = "function page(p){['home','missions','myreq','mapPage','profile'].forEach(x=>{document.getElementById(x).classList.toggle('hidden',x!==p);document.querySelector(`[data-p=\"${x}\"]`)?.classList.toggle('active',x===p)});if(p==='missions')renderMissions();if(p==='myreq')renderMyRequests();if(p==='mapPage')renderMapPage();if(p==='profile')renderProfile();scrollTo(0,0)}"
new_page = "function page(p){['home','missions','myreq','mapPage','wallet','profile'].forEach(x=>{document.getElementById(x).classList.toggle('hidden',x!==p);document.querySelector(`[data-p=\"${x}\"]`)?.classList.toggle('active',x===p)});if(p==='missions')renderMissions();if(p==='myreq')renderMyRequests();if(p==='mapPage')renderMapPage();if(p==='wallet'){renderWallet();loadWallet().then(renderWallet).catch(e=>console.warn(e))}if(p==='profile')renderProfile();scrollTo(0,0)}"
if old_page not in s: raise SystemExit('page block not found')
s = s.replace(old_page, new_page, 1)

old_missions = "function renderMissions(){let arr=REQUESTS.filter(r=>r.rider_id===SESSION.user.id&&r.stato!=='annullata');missions.innerHTML=`<div class=\"pagehead\"><div class=\"k\">LE TUE ATTIVITÀ</div><h2>Missioni</h2><p>Commissioni che hai accettato.</p></div>${arr.length?arr.map(card).join(''):'<div class=\"empty\">Non hai ancora missioni assegnate.</div>'}` }"
# Existing source has no space before final }, handle exact actual form below.
actual_missions = "function renderMissions(){let arr=REQUESTS.filter(r=>r.rider_id===SESSION.user.id&&r.stato!=='annullata');missions.innerHTML=`<div class=\"pagehead\"><div class=\"k\">LE TUE ATTIVITÀ</div><h2>Missioni</h2><p>Commissioni che hai accettato.</p></div>${arr.length?arr.map(card).join(''):'<div class=\"empty\">Non hai ancora missioni assegnate.</div>'}`}"
new_missions = "function renderMissions(){let arr=REQUESTS.filter(r=>r.rider_id===SESSION.user.id&&r.stato!=='annullata');missions.innerHTML=`<div class=\"pagehead\"><div class=\"k\">LE TUE ATTIVITÀ</div><h2>Missioni</h2><p>Commissioni che hai accettato.</p></div>${walletMiniCard()}${arr.length?arr.map(card).join(''):'<div class=\"empty\">Non hai ancora missioni assegnate.</div>'}`}"
if actual_missions not in s: raise SystemExit('renderMissions block not found')
s = s.replace(actual_missions, new_missions, 1)

old_profile = "function renderProfile(){let pushState=tcvPushStatusText();profile.innerHTML=`<div class=\"pagehead\"><div class=\"k\">PROFILO</div><h2>${esc(PROFILE.nome||'Profilo')}</h2><p>${esc(SESSION.user.email||'')}</p></div><div class=\"req\"><div class=\"field\"><label>NOME</label><input id=\"pfName\" value=\"${esc(PROFILE.nome||'')}\"></div><div class=\"field\"><label>TELEFONO</label><input id=\"pfPhone\" value=\"${esc(PROFILE.telefono||'')}\"></div><button class=\"btn teal full\" onclick=\"saveProfile()\">Salva profilo</button><button class=\"btn outline full\" style=\"margin-top:8px\" onclick=\"logout()\">Esci dall'account</button></div><div class=\"req\" style=\"margin-top:10px\"><h3>🔔 Notifiche richieste</h3><p id=\"pushProfileStatus\">${esc(pushState)}</p><button class=\"btn primary full\" style=\"margin-top:9px\" onclick=\"tcvEnablePush(true)\">Attiva notifiche</button><button class=\"btn outline full\" style=\"margin-top:7px\" onclick=\"tcvDisablePush()\">Disattiva su questo telefono</button></div><div class=\"notice green\" style=\"margin-top:10px\">✓ Profilo, richieste e missioni sono salvati online in modo sicuro.</div>`}"
new_profile = "function renderProfile(){let pushState=tcvPushStatusText();profile.innerHTML=`<div class=\"pagehead\"><div class=\"k\">PROFILO</div><h2>${esc(PROFILE.nome||'Profilo')}</h2><p>${esc(SESSION.user.email||'')}</p></div>${walletMiniCard()}<div class=\"req\"><div class=\"field\"><label>NOME</label><input id=\"pfName\" value=\"${esc(PROFILE.nome||'')}\"></div><div class=\"field\"><label>TELEFONO</label><input id=\"pfPhone\" value=\"${esc(PROFILE.telefono||'')}\"></div><button class=\"btn teal full\" onclick=\"saveProfile()\">Salva profilo</button><button class=\"btn outline full\" style=\"margin-top:8px\" onclick=\"logout()\">Esci dall'account</button></div><div class=\"req\" style=\"margin-top:10px\"><h3>🔔 Notifiche richieste</h3><p id=\"pushProfileStatus\">${esc(pushState)}</p><button class=\"btn primary full\" style=\"margin-top:9px\" onclick=\"tcvEnablePush(true)\">Attiva notifiche</button><button class=\"btn outline full\" style=\"margin-top:7px\" onclick=\"tcvDisablePush()\">Disattiva su questo telefono</button></div><div class=\"notice green\" style=\"margin-top:10px\">✓ Profilo, richieste e missioni sono salvati online in modo sicuro.</div>`}"
if old_profile not in s: raise SystemExit('renderProfile block not found')
s = s.replace(old_profile, new_profile, 1)

wallet_code = r'''const WALLET_THRESHOLD=5000;
function walletYear(){return new Date().getFullYear()}
function walletYearBounds(){let y=walletYear();return {start:new Date(y,0,1).toISOString(),end:new Date(y+1,0,1).toISOString()}}
async function loadWallet(){
  if(!SESSION)return;let y=walletYear(),b=walletYearBounds(),uid=SESSION.user.id;
  let [entriesRes,yearRes]=await Promise.all([
    db.from('runner_wallet_entries').select('*').eq('rider_id',uid).gte('earned_at',b.start).lt('earned_at',b.end).order('earned_at',{ascending:false}),
    db.from('runner_wallet_years').select('*').eq('user_id',uid).eq('year',y).maybeSingle()
  ]);
  if(entriesRes.error)throw entriesRes.error;if(yearRes.error)throw yearRes.error;
  WALLET_ENTRIES=entriesRes.data||[];WALLET_YEAR_ROW=yearRes.data||{user_id:uid,year:y,external_gross:0}
}
function walletAppTotal(){return WALLET_ENTRIES.reduce((sum,x)=>sum+Number(x.amount||0),0)}
function walletExternalTotal(){return Number(WALLET_YEAR_ROW?.external_gross||0)}
function walletTrackedTotal(){return walletAppTotal()+walletExternalTotal()}
function walletMonthTotal(){let n=new Date(),m=n.getMonth(),y=n.getFullYear();return WALLET_ENTRIES.filter(x=>{let d=new Date(x.earned_at);return d.getFullYear()===y&&d.getMonth()===m}).reduce((sum,x)=>sum+Number(x.amount||0),0)}
function walletThresholdInfo(total=walletTrackedTotal()){
  let pct=Math.max(0,total/WALLET_THRESHOLD*100),left=Math.max(0,WALLET_THRESHOLD-total);
  if(total>=WALLET_THRESHOLD)return {cls:'danger',pct:100,text:`⚠️ Hai raggiunto o superato € 5.000 di compensi monitorati. Verifica subito la tua posizione previdenziale/fiscale e l’inquadramento dell’attività.`};
  if(total>=4500)return {cls:'watch',pct:Math.min(100,pct),text:`⚠️ Sei molto vicino alla soglia previdenziale indicativa: mancano ${euro(left)} a € 5.000.`};
  if(total>=3500)return {cls:'watch',pct:Math.min(100,pct),text:`🔔 Hai superato il 70% della soglia previdenziale indicativa. Mancano ${euro(left)}.`};
  return {cls:'good',pct:Math.min(100,pct),text:`✓ Compensi monitorati: ${euro(total)}. Mancano ${euro(left)} alla soglia previdenziale indicativa di € 5.000.`}
}
function walletMiniCard(){let app=walletAppTotal(),total=walletTrackedTotal(),info=walletThresholdInfo(total);return `<section class="wallet-mini"><div class="wallet-mini-top"><div><small>PORTAFOGLIO RUNNER · ${walletYear()}</small><b>${euro(total)}</b><small>${euro(app)} maturati con Tanto Ci Vai</small></div><div style="font-size:30px">👛</div></div><button class="btn full" onclick="page('wallet')">Apri portafoglio</button></section>`}
function renderWallet(){
  let el=document.getElementById('wallet');if(!el)return;let app=walletAppTotal(),external=walletExternalTotal(),total=walletTrackedTotal(),month=walletMonthTotal(),info=walletThresholdInfo(total),pct=Math.min(100,info.pct);
  let rows=WALLET_ENTRIES.length?WALLET_ENTRIES.map(x=>`<div class="wallet-entry"><div><b>${esc(x.title||'Consegna completata')}</b><small>${new Date(x.earned_at).toLocaleDateString('it-IT',{day:'2-digit',month:'2-digit',year:'numeric'})} · ${esc(x.category||'commissione')}</small></div><strong>+ ${euro(x.amount)}</strong></div>`).join(''):'<div class="empty" style="margin-top:10px">Le consegne completate compariranno qui automaticamente.</div>';
  el.innerHTML=`<div class="pagehead"><div class="k">GUADAGNI RUNNER</div><h2>Portafoglio</h2><p>Riepilogo dei compensi maturati. Non è un conto di pagamento e non custodisce denaro.</p></div><section class="wallet-hero"><div class="eyebrow">COMPENSI MONITORATI · ${walletYear()}</div><div class="wallet-total">${euro(total)}</div><div class="wallet-sub">Somma dei compensi registrati su Tanto Ci Vai + eventuali compensi occasionali esterni che inserisci tu.</div><div class="wallet-grid"><div class="wallet-stat"><b>${euro(app)}</b><span>TANTO CI VAI</span></div><div class="wallet-stat"><b>${euro(month)}</b><span>QUESTO MESE</span></div></div><div class="wallet-progress-wrap"><div class="wallet-progress-label"><span>0 €</span><span>Soglia indicativa 5.000 €</span></div><div class="wallet-progress"><div style="width:${pct.toFixed(1)}%"></div></div></div></section><div class="wallet-alert ${info.cls}">${info.text}</div><section class="wallet-section"><h3>Altri compensi occasionali ${walletYear()}</h3><p>Se hai percepito compensi occasionali fuori da Tanto Ci Vai, inseriscili qui per rendere l’avviso più utile.</p><div class="field"><label>TOTALE ESTERNO LORDO</label><input id="walletExternal" inputmode="decimal" value="${Number(external).toFixed(2).replace('.',',')}" placeholder="0,00"></div><button class="btn teal full" onclick="saveWalletExternal()">Salva importo esterno</button></section><section class="wallet-section"><h3>Storico consegne pagate</h3><p>Le voci vengono create automaticamente quando una missione passa a “consegnata”.</p>${rows}</section><div class="wallet-legal"><b>Importante:</b> il riferimento a € 5.000 è un indicatore previdenziale per il lavoro autonomo occasionale, non una soglia generale di esenzione fiscale e non rende automaticamente “occasionale” un’attività svolta con abitualità. Il contatore è uno strumento informativo: per l’inquadramento personale vanno considerate anche le attività svolte fuori dall’app e la situazione del singolo runner.</div><button class="btn outline full" style="margin-top:11px" onclick="page('missions')">← Torna alle missioni</button>`
}
async function saveWalletExternal(){
  let raw=(document.getElementById('walletExternal')?.value||'0').trim().replace(',','.'),value=Number(raw);if(!Number.isFinite(value)||value<0){alert('Inserisci un importo valido.');return}
  let row={user_id:SESSION.user.id,year:walletYear(),external_gross:Math.round(value*100)/100,updated_at:new Date().toISOString()};let {error}=await db.from('runner_wallet_years').upsert(row,{onConflict:'user_id,year'});if(error){alert(error.message);return}await loadWallet();renderWallet();alert('Importo esterno aggiornato.')
}
function tcvMaybeShowWalletMilestone(before,after){
  if(before==null||after==null||after<=before)return;let hit=[5000,4500,3500].find(t=>before<t&&after>=t);if(!hit)return;
  let title=hit===5000?'Soglia raggiunta':hit===4500?'Sei vicino a € 5.000':'Portafoglio al 70%';
  let text=hit===5000?'Hai raggiunto o superato € 5.000 di compensi monitorati. Questo non blocca automaticamente l’app, ma è il momento di verificare posizione previdenziale, fiscale e carattere occasionale dell’attività.':hit===4500?'Hai superato € 4.500 di compensi monitorati. Controlla il portafoglio e considera anche eventuali compensi occasionali esterni.':'Hai superato € 3.500 di compensi monitorati. Da qui il portafoglio ti avviserà con maggiore evidenza mentre ti avvicini a € 5.000.';
  openSheet(`${head('PORTAFOGLIO RUNNER',title,text)}<div class="wallet-alert ${hit===5000?'danger':'watch'}" style="margin-top:11px"><b>Totale monitorato: ${euro(after)}</b></div><button class="btn primary full" style="margin-top:10px" onclick="closeSheet();page('wallet')">Apri portafoglio</button>`)
}

'''
marker = 'function mapPlanRequests(extraId=null){'
if 'const WALLET_THRESHOLD=5000;' not in s:
    if marker not in s: raise SystemExit('wallet insertion marker not found')
    s = s.replace(marker, wallet_code + marker, 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Runner wallet UI patch applied')
