from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

helper = """async function tcvSendLifecyclePush(requestId,event){\n  try{\n    const {error}=await db.functions.invoke('send-request-push',{body:{request_id:requestId,event}});\n    if(error)console.warn('Lifecycle push failed',event,error)\n  }catch(e){console.warn('Lifecycle push failed',event,e)}\n}\n"""
marker = "async function acceptRequest(id){"
if 'async function tcvSendLifecyclePush(requestId,event)' not in s:
    if marker not in s:
        raise SystemExit('acceptRequest marker not found')
    s = s.replace(marker, helper + marker, 1)

old = """async function acceptRequest(id){\n  if(!confirm('Vuoi prendere questa commissione?'))return;\n  let {data,error}=await db.rpc('accetta_consegna',{p_consegna_id:id});\n  if(error){alert(error.message);return}if(!data){alert('Questa richiesta è già stata presa oppure il tempo massimo di consegna è scaduto.');return}\n  await loadRequests();renderAll();closeSheet();page('missions')\n}"""
new = """async function acceptRequest(id){\n  if(!confirm('Vuoi prendere questa commissione?'))return;\n  let {data,error}=await db.rpc('accetta_consegna',{p_consegna_id:id});\n  if(error){alert(error.message);return}if(!data){alert('Questa richiesta è già stata presa oppure il tempo massimo di consegna è scaduto.');return}\n  await tcvSendLifecyclePush(id,'accepted');\n  await loadRequests();renderAll();closeSheet();page('missions')\n}"""
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('acceptRequest block not found')

old = """async function confirmPickupEta(id){\n  let r=REQUESTS.find(x=>x.id===id),el=document.getElementById('pickupEta'),eta=el?.value;if(!eta){alert('Imposta la consegna prevista.');return}\n  let when=new Date(eta);if(!Number.isFinite(when.getTime())||when.getTime()<=Date.now()){alert('Scegli un orario futuro.');return}\n  let deadline=r?.consegna_entro?new Date(r.consegna_entro):null;\n  if(deadline&&deadline.getTime()>Date.now()&&when.getTime()>deadline.getTime()){alert('La consegna prevista non può superare il limite richiesto dal mittente: '+formatDateTime(deadline));return}\n  let {data,error}=await db.rpc('segna_ritiro_con_eta',{p_consegna_id:id,p_consegna_prevista:when.toISOString()});\n  if(error){alert(error.message);return}if(!data){alert('Non posso confermare il ritiro: controlla stato e orario massimo richiesto.');return}\n  await loadRequests();renderAll();closeSheet();page('missions')\n}"""
new = """async function confirmPickupEta(id){\n  let r=REQUESTS.find(x=>x.id===id),el=document.getElementById('pickupEta'),eta=el?.value;if(!eta){alert('Imposta la consegna prevista.');return}\n  let when=new Date(eta);if(!Number.isFinite(when.getTime())||when.getTime()<=Date.now()){alert('Scegli un orario futuro.');return}\n  let deadline=r?.consegna_entro?new Date(r.consegna_entro):null;\n  if(deadline&&deadline.getTime()>Date.now()&&when.getTime()>deadline.getTime()){alert('La consegna prevista non può superare il limite richiesto dal mittente: '+formatDateTime(deadline));return}\n  let {data,error}=await db.rpc('segna_ritiro_con_eta',{p_consegna_id:id,p_consegna_prevista:when.toISOString()});\n  if(error){alert(error.message);return}if(!data){alert('Non posso confermare il ritiro: controlla stato e orario massimo richiesto.');return}\n  await tcvSendLifecyclePush(id,'picked_up');\n  await loadRequests();renderAll();closeSheet();page('missions')\n}"""
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('confirmPickupEta block not found')

old = """async function setStatus(id,status){let before=status==='consegnata'?walletTrackedTotal():null;let {data,error}=await db.rpc('aggiorna_stato_consegna',{p_consegna_id:id,p_stato:status});if(error){alert(error.message);return}if(!data){alert('Operazione non consentita o stato già cambiato.');return}await loadRequests();if(status==='consegnata')await loadWallet();renderAll();if(status==='consegnata')tcvMaybeShowWalletMilestone(before,walletTrackedTotal())}"""
new = """async function setStatus(id,status){let before=status==='consegnata'?walletTrackedTotal():null;let {data,error}=await db.rpc('aggiorna_stato_consegna',{p_consegna_id:id,p_stato:status});if(error){alert(error.message);return}if(!data){alert('Operazione non consentita o stato già cambiato.');return}if(status==='ritirata')await tcvSendLifecyclePush(id,'picked_up');await loadRequests();if(status==='consegnata')await loadWallet();renderAll();if(status==='consegnata')tcvMaybeShowWalletMilestone(before,walletTrackedTotal())}"""
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('setStatus block not found')

old = """async function acceptMapPlan(){\n  let ids=[...MAP_PLAN_IDS];if(!ids.length)return;if(!confirm(`Accettare ${ids.length} richieste di questo giro?`))return;\n  let ok=0,failed=0;\n  for(let id of ids){let r=REQUESTS.find(x=>x.id===id);if(!r||!requestOpen(r)){failed++;continue}let {data,error}=await db.rpc('accetta_consegna',{p_consegna_id:id});if(error||!data)failed++;else ok++}\n  await loadRequests();renderAll();MAP_PLAN_IDS=[];MAP_PLAN_ROUTE=null;MAP_PLAN_START=USER_POS?{...USER_POS}:MAP_PLAN_START;if(MAP_PLAN_ROUTE_LAYER&&MAP){MAP.removeLayer(MAP_PLAN_ROUTE_LAYER);MAP_PLAN_ROUTE_LAYER=null}\n  alert(failed?`${ok} richieste accettate. ${failed} non erano più disponibili.`:`${ok} richieste accettate.`);page('missions')\n}"""
new = """async function acceptMapPlan(){\n  let ids=[...MAP_PLAN_IDS];if(!ids.length)return;if(!confirm(`Accettare ${ids.length} richieste di questo giro?`))return;\n  let ok=0,failed=0,acceptedIds=[];\n  for(let id of ids){let r=REQUESTS.find(x=>x.id===id);if(!r||!requestOpen(r)){failed++;continue}let {data,error}=await db.rpc('accetta_consegna',{p_consegna_id:id});if(error||!data)failed++;else{ok++;acceptedIds.push(id)}}\n  await Promise.allSettled(acceptedIds.map(id=>tcvSendLifecyclePush(id,'accepted')));\n  await loadRequests();renderAll();MAP_PLAN_IDS=[];MAP_PLAN_ROUTE=null;MAP_PLAN_START=USER_POS?{...USER_POS}:MAP_PLAN_START;if(MAP_PLAN_ROUTE_LAYER&&MAP){MAP.removeLayer(MAP_PLAN_ROUTE_LAYER);MAP_PLAN_ROUTE_LAYER=null}\n  alert(failed?`${ok} richieste accettate. ${failed} non erano più disponibili.`:`${ok} richieste accettate.`);page('missions')\n}"""
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('acceptMapPlan block not found')

s = s.replace('<h3>🔔 Notifiche richieste</h3>', '<h3>🔔 Notifiche attività</h3>', 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Requester lifecycle push patch applied')
