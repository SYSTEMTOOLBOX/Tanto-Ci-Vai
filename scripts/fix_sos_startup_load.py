from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')

old="async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');let splashPromise=runStartupSplash(session);await ensureProfile();await loadRequests();await loadWallet();subscribeRealtime();renderAll();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000);await splashPromise;setTimeout(()=>tcvMaybeOfferPush(),350);setTimeout(()=>tcvOpenRequestFromUrl(),500)}"
new="async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');let splashPromise=runStartupSplash(session);await ensureProfile();await Promise.all([loadRequests(),loadWallet(),loadCommunityAlerts()]);subscribeRealtime();renderAll();renderHomeCommunityAlarm();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000);await splashPromise;setTimeout(()=>loadCommunityAlerts(),250);setTimeout(()=>tcvMaybeOfferPush(),350);setTimeout(()=>tcvOpenRequestFromUrl(),500)}"
if old not in s:
    raise SystemExit('afterLogin anchor not found')
s=s.replace(old,new,1)

# Never draw no-GPS SOS at coordinate 0,0 on the community map.
s=s.replace("COMMUNITY_ALERTS.forEach(a=>{const ll=[Number(a.lat),Number(a.lng)];pts.push(ll);L.marker(ll,{icon:communityAlertIcon(a),zIndexOffset:a.kind==='hazard'?700:1000}).addTo(MAP).bindPopup(communityAlertPopup(a),{maxWidth:290})});",
            "COMMUNITY_ALERTS.filter(a=>a.lat!=null&&a.lng!=null&&Number.isFinite(Number(a.lat))&&Number.isFinite(Number(a.lng))).forEach(a=>{const ll=[Number(a.lat),Number(a.lng)];pts.push(ll);L.marker(ll,{icon:communityAlertIcon(a),zIndexOffset:a.kind==='hazard'?700:1000}).addTo(MAP).bindPopup(communityAlertPopup(a),{maxWidth:290})});",1)

s=re.sub(r"sw\.js\?v=\d+","sw.js?v=13",s)
p.write_text(s,encoding='utf-8')
print('SOS alerts now load immediately during session restore')
