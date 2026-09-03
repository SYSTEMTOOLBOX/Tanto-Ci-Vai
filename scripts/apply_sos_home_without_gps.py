from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

old="COMMUNITY_ALERTS=Array.isArray(data?.alerts)?data.alerts.filter(a=>Number.isFinite(+a.lat)&&Number.isFinite(+a.lng)):[];"
new="COMMUNITY_ALERTS=Array.isArray(data?.alerts)?data.alerts:[];"
if old in s:
    s=s.replace(old,new,1)

old_map="COMMUNITY_ALERTS.forEach(a=>{const ll=[Number(a.lat),Number(a.lng)];pts.push(ll);L.marker(ll,{icon:communityAlertIcon(a),zIndexOffset:a.kind==='hazard'?700:1000}).addTo(MAP).bindPopup(communityAlertPopup(a),{maxWidth:290})});"
new_map="COMMUNITY_ALERTS.forEach(a=>{if(!Number.isFinite(Number(a.lat))||!Number.isFinite(Number(a.lng)))return;const ll=[Number(a.lat),Number(a.lng)];pts.push(ll);L.marker(ll,{icon:communityAlertIcon(a),zIndexOffset:a.kind==='hazard'?700:(a.resolved_at?850:1000)}).addTo(MAP).bindPopup(communityAlertPopup(a),{maxWidth:290})});"
if old_map not in s:
    raise SystemExit('Map alert anchor not found')
s=s.replace(old_map,new_map,1)

old_detail="const resolved=!!a.resolved_at,count=Math.min(3,Number(a.resolution_count||0)),where=String(a.location_label||'').trim();"
new_detail="const resolved=!!a.resolved_at,count=Math.min(3,Number(a.resolution_count||0)),where=String(a.location_label||'').trim(),hasPoint=Number.isFinite(Number(a.lat))&&Number.isFinite(Number(a.lng));"
if old_detail not in s:
    raise SystemExit('Detail anchor not found')
s=s.replace(old_detail,new_detail,1)

old_sheet="openSheet(`${head(resolved?'SOS RISOLTO':'ASSISTENZA IMMEDIATA',resolved?'✅ Situazione risolta':'🆘 Richiesta SOS',resolved?'Tre persone hanno confermato la risoluzione. Rimarrà verde per 24 ore.':'Serve assistenza: verifica la situazione prima di segnalarla come risolta.')}${state}<div class=\"notice\" style=\"margin-top:10px\"><b>${esc(a.message||'Richiesta urgente di aiuto')}</b>${where?`<br>📍 ${esc(where)}`:''}<br>Segnalato da ${esc(a.sender_name||'un utente')}</div><button class=\"btn primary full\" style=\"margin-top:10px\" onclick=\"openCommunityAlertMaps(${Number(a.lat)},${Number(a.lng)})\">🧭 VAI AL PUNTO SOS</button>${vote}${owner}<button class=\"btn outline full\" style=\"margin-top:8px\" onclick=\"tcvFocusCommunityAlert('${a.id}')\">⌖ VEDI SULLA MAPPA</button>`)"
new_sheet="openSheet(`${head(resolved?'SOS RISOLTO':'ASSISTENZA IMMEDIATA',resolved?'✅ Situazione risolta':'🆘 Richiesta SOS',resolved?'Tre persone hanno confermato la risoluzione. Rimarrà verde per 24 ore.':'Serve assistenza: verifica la situazione prima di segnalarla come risolta.')}${state}<div class=\"notice\" style=\"margin-top:10px\"><b>${esc(a.message||'Richiesta urgente di aiuto')}</b>${where?`<br>📍 ${esc(where)}`:(hasPoint?'':'<br>📍 Posizione GPS non disponibile')}<br>Segnalato da ${esc(a.sender_name||'un utente')}</div>${hasPoint?`<button class=\"btn primary full\" style=\"margin-top:10px\" onclick=\"openCommunityAlertMaps(${Number(a.lat)},${Number(a.lng)})\">🧭 VAI AL PUNTO SOS</button>`:''}${vote}${owner}${hasPoint?`<button class=\"btn outline full\" style=\"margin-top:8px\" onclick=\"tcvFocusCommunityAlert('${a.id}')\">⌖ VEDI SULLA MAPPA</button>`:''}`)"
if old_sheet not in s:
    raise SystemExit('SOS detail sheet anchor not found')
s=s.replace(old_sheet,new_sheet,1)

s=re.sub(r"sw\.js\?v=\d+","sw.js?v=12",s)
p.write_text(s,encoding='utf-8')
print('SOS Home alerts no longer depend on GPS coordinates')
