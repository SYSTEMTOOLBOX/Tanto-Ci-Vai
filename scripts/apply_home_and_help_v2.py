from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s
marker = '/* TCV_HOME_ADDRESS_HELP_V2 */'
if marker in s:
    print('Home/help v2 already applied')
    raise SystemExit(0)

css = r'''
/* TCV_HOME_ADDRESS_HELP_V2 */
.urgent-help{width:100%;margin-top:12px;border:0;border-radius:23px;padding:16px 18px;background:linear-gradient(135deg,#c51f35,#e63b4f);color:#fff;display:flex;align-items:center;gap:14px;text-align:left;box-shadow:0 12px 28px rgba(197,31,53,.22)}
.urgent-help .sosico{width:54px;height:54px;border-radius:17px;background:rgba(255,255,255,.17);display:grid;place-items:center;font-size:28px;flex:0 0 auto}
.urgent-help b{display:block;font-size:20px;letter-spacing:-.03em}.urgent-help span{display:block;font-size:10px;line-height:1.4;opacity:.92;margin-top:3px}.urgent-help .sosarrow{margin-left:auto;font-size:24px;font-weight:950}
.delivery-choice-buttons{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:10px 0}.delivery-home-summary{padding:9px 10px;border-radius:13px;background:#effff8;border:1px solid #d5f4e8;color:#316b58;font-size:9px;line-height:1.4;margin:8px 0}
'''
if '</style>' not in s:
    raise SystemExit('style end not found')
s = s.replace('</style>', css + '</style>', 1)

home_anchor = '</button></section><div class="sect"><h2>Richieste disponibili</h2>'
if home_anchor not in s:
    raise SystemExit('home actions anchor not found')
help_button = '''</button></section><button class="urgent-help" onclick="openCommunityHelp()"><div class="sosico">🆘</div><div><b>AIUTO</b><span>Invia una richiesta urgente di aiuto alla comunità.</span></div><div class="sosarrow">→</div></button><div class="sect"><h2>Richieste disponibili</h2>'''
s = s.replace(home_anchor, help_button, 1)

smart_anchor = '<div class="delivery-smart"><div class="delivery-smart-title">📍 DOVE VA CONSEGNATO?</div>'
if smart_anchor not in s:
    raise SystemExit('delivery smart anchor not found')
smart_new = '''<div class="delivery-smart"><div class="delivery-smart-title">📍 DOVE VA CONSEGNATO?</div><div class="delivery-choice-buttons"><button type="button" class="btn teal" onclick="useSavedHome()">🏠 Casa</button><button type="button" class="btn outline" onclick="clearDeliveryForOther()">📦 Altra destinazione</button></div>${PROFILE?.home_city?`<div class="delivery-home-summary">🏠 Casa salvata: <b>${esc(PROFILE.home_label||canonicalDeliveryLabel([PROFILE.home_street,PROFILE.home_civic].filter(Boolean).join(' '),PROFILE.home_city))}</b></div>`:`<div class="notice">Non hai ancora una casa salvata. Inserisci l'indirizzo, premi <b>CERCA</b> e poi <b>Salva/aggiorna CASA</b>.</div>`}'''
s = s.replace(smart_anchor, smart_new, 1)

repls = [
    ('<input id="nrCity" value="" placeholder="Es. Lauriano"', '''<input id="nrCity" value="${esc(PROFILE?.home_city||'')}" placeholder="Es. Lauriano"'''),
    ('<input id="nrStreet" value="" placeholder="Es. Via Anselmina"', '''<input id="nrStreet" value="${esc(PROFILE?.home_street||'')}" placeholder="Es. Via Anselmina"'''),
    ('<input id="nrCivic" value="" placeholder="Es. 14/A"', '''<input id="nrCivic" value="${esc(PROFILE?.home_civic||'')}" placeholder="Es. 14/A"'''),
]
for old, new in repls:
    if old not in s:
        raise SystemExit('delivery input anchor not found: ' + old[:30])
    s = s.replace(old, new, 1)

civic_anchor = 'Mappa e GPS compilano il civico automaticamente quando disponibile.</div></div><div class="delivery-tools">'
if civic_anchor not in s:
    raise SystemExit('civic tools anchor not found')
civic_new = '''Dopo aver inserito il civico premi <b>CERCA</b>: il punto viene verificato prima di pubblicare.</div></div><button type="button" class="btn primary full" style="margin-top:8px;padding:14px;font-size:12px" onclick="searchDeliveryAddress()">🔎 CERCA INDIRIZZO</button><button type="button" class="btn outline full" style="margin-top:7px" onclick="saveDeliveryAsHome()">🏠 Salva / aggiorna CASA</button><div class="delivery-tools">'''
s = s.replace(civic_anchor, civic_new, 1)

js_anchor = 'async function tcvSendLifecyclePush(requestId,event){'
if js_anchor not in s:
    raise SystemExit('lifecycle JS anchor not found')
js = r'''let COMMUNITY_HELP_SENDING=false;
function openCommunityHelp(){
  openSheet(`${head('AIUTO ALLA COMUNITÀ','🆘 Hai bisogno di aiuto?','Questo avviso viene inviato agli utenti di Tanto Ci Vai con le notifiche attive.')}<div class="notice yellow" style="margin-top:10px"><b>Pericolo immediato?</b> Chiama il <b>112</b>. Tanto Ci Vai è un aiuto tra persone e non sostituisce i servizi di emergenza.</div><div class="field"><label>COSA TI SERVE?</label><textarea id="communityHelpMessage" rows="3" maxlength="180" placeholder="Es. Auto in panne, sono bloccato e mi serve una mano"></textarea></div><div class="notice green">📍 Quando invii provo ad allegare la posizione del telefono. Se il GPS non è disponibile, l'avviso parte comunque.</div><div id="communityHelpStatus" class="notice" style="margin-top:8px">Nessun avviso è ancora stato inviato.</div><div class="rowbtn"><button class="btn outline" onclick="closeSheet()">Annulla</button><button id="communityHelpSend" class="btn danger" style="font-size:12px" onclick="sendCommunityHelp()">🆘 INVIA AIUTO</button></div>`)
}
async function sendCommunityHelp(){
  if(COMMUNITY_HELP_SENDING)return;
  let msg=document.getElementById('communityHelpMessage')?.value.trim()||'',st=document.getElementById('communityHelpStatus'),btn=document.getElementById('communityHelpSend');
  if(!confirm('Inviare questa richiesta di aiuto alla comunità?'))return;
  COMMUNITY_HELP_SENDING=true;if(btn){btn.disabled=true;btn.textContent='Invio…'}if(st)st.textContent='Cerco la tua posizione e invio l’avviso…';
  let pos=null;
  try{pos=await currentPosition();try{pos=await reverseGeocodePoint(pos)}catch(e){}}catch(e){}
  try{
    const {data,error}=await db.functions.invoke('send-help-push',{body:{message:msg,lat:pos?.lat??null,lng:pos?.lng??null,location_label:pos?.label||''}});
    if(error)throw error;if(data?.error)throw new Error(data.error);
    if(st)st.innerHTML=`✓ <b>Richiesta di aiuto inviata.</b> Notifiche recapitate: ${Number(data?.sent||0)}${pos?' · posizione allegata':''}.`;
    if(btn)btn.textContent='✓ INVIATO';setTimeout(()=>closeSheet(),1800)
  }catch(e){if(st)st.textContent='Non riesco a inviare l’avviso: '+(e?.message||e);if(btn){btn.disabled=false;btn.textContent='🆘 RIPROVA'}}finally{COMMUNITY_HELP_SENDING=false}
}
function useSavedHome(announce=true){
  if(!PROFILE?.home_city){let st=document.getElementById('nrStatus');if(st)st.textContent='Non hai ancora salvato CASA. Compila città, via e civico, premi CERCA e poi Salva CASA.';return false}
  let city=document.getElementById('nrCity'),street=document.getElementById('nrStreet'),civic=document.getElementById('nrCivic');
  if(city)city.value=PROFILE.home_city||'';if(street)street.value=PROFILE.home_street||'';if(civic)civic.value=PROFILE.home_civic||'';
  const full=[PROFILE.home_street||'',PROFILE.home_civic||''].filter(Boolean).join(' '),lat=+PROFILE.home_lat,lng=+PROFILE.home_lng;
  HOME_POS=Number.isFinite(lat)&&Number.isFinite(lng)?{lat,lng,label:PROFILE.home_label||canonicalDeliveryLabel(full,PROFILE.home_city),city:PROFILE.home_city,street:full,cityText:PROFILE.home_city,streetText:full,civicText:PROFILE.home_civic||''}:null;
  document.getElementById('deliveryCitySuggest')?.replaceChildren();document.getElementById('deliveryStreetSuggest')?.replaceChildren();
  if(HOME_POS){showPickedDelivery(HOME_POS);updateDeliveryMapMarker(HOME_POS);if(DELIVERY_MAP)DELIVERY_MAP.setView([lat,lng],18)}
  let st=document.getElementById('nrStatus');if(st&&announce)st.textContent='🏠 CASA impostata come destinazione.';return true
}
function clearDeliveryForOther(){
  for(const id of ['nrCity','nrStreet','nrCivic']){let el=document.getElementById(id);if(el)el.value=''}
  HOME_POS=null;DELIVERY_CITY_POS=null;document.getElementById('deliveryPicked')?.classList.add('hidden');document.getElementById('deliveryCitySuggest')?.replaceChildren();document.getElementById('deliveryStreetSuggest')?.replaceChildren();
  let st=document.getElementById('nrStatus');if(st)st.textContent='📦 Altra destinazione: inserisci città, via e civico, poi premi CERCA.';document.getElementById('nrCity')?.focus()
}
async function searchDeliveryAddress(showStatus=true){
  let city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',civic=document.getElementById('nrCivic')?.value.trim()||'',st=document.getElementById('nrStatus');
  if(!city){if(st)st.textContent='Inserisci prima città o frazione.';document.getElementById('nrCity')?.focus();return null}
  if(!street){if(st)st.textContent='Inserisci prima la via.';document.getElementById('nrStreet')?.focus();return null}
  if(!civic){if(st)st.textContent='Inserisci il numero civico e poi premi CERCA.';document.getElementById('nrCivic')?.focus();return null}
  const full=[street,civic].join(' ');if(st&&showStatus)st.textContent='🔎 Verifico città, via e numero civico…';
  try{
    const pt=await geocodeDeliveryAddress(city,full);
    HOME_POS={...pt,city,street:full,label:canonicalDeliveryLabel(full,city),cityText:city,streetText:full,civicText:civic};
    showPickedDelivery(HOME_POS);updateDeliveryMapMarker(HOME_POS);if(DELIVERY_MAP)DELIVERY_MAP.setView([pt.lat,pt.lng],18);
    if(st)st.innerHTML=`✓ Indirizzo trovato: <b>${esc(HOME_POS.label)}</b>`;return HOME_POS
  }catch(e){HOME_POS=null;if(st)st.textContent='Indirizzo non trovato bene: controlla il civico oppure usa Mappa/GPS.';return null}
}
async function saveDeliveryAsHome(){
  const pt=await searchDeliveryAddress(false);if(!pt)return;
  let city=document.getElementById('nrCity')?.value.trim()||'',street=document.getElementById('nrStreet')?.value.trim()||'',civic=document.getElementById('nrCivic')?.value.trim()||'',label=canonicalDeliveryLabel([street,civic].join(' '),city),st=document.getElementById('nrStatus');
  const row={home_city:city,home_street:street,home_civic:civic,home_lat:pt.lat,home_lng:pt.lng,home_label:label};
  const {error}=await db.from('profiles').update(row).eq('id',SESSION.user.id);if(error){if(st)st.textContent='Non riesco a salvare CASA: '+error.message;return}
  PROFILE={...PROFILE,...row};HOME_POS={...pt,city,street:[street,civic].join(' '),cityText:city,streetText:[street,civic].join(' '),civicText:civic,label};if(st)st.innerHTML=`🏠 <b>CASA salvata.</b> Da ora sarà già pronta nelle nuove richieste.`
}

'''
s = s.replace(js_anchor, js + js_anchor, 1)

old = r'''const _tcvPublishRequest=publishRequest;
publishRequest=async function(){
  const st=document.getElementById('nrStreet'),cv=document.getElementById('nrCivic'),status=document.getElementById('nrStatus');
  const base=st?.value.trim()||'',civic=cv?.value.trim()||'';
  if(!civic){if(status)status.textContent='Inserisci il numero civico di consegna.';cv?.focus();return}
  if(st)st.value=[base,civic].filter(Boolean).join(' ');
  try{return await _tcvPublishRequest()}finally{if(st)st.value=base}
};'''
new = r'''const _tcvPublishRequest=publishRequest;
publishRequest=async function(){
  const st=document.getElementById('nrStreet'),cv=document.getElementById('nrCivic'),cityEl=document.getElementById('nrCity'),status=document.getElementById('nrStatus');
  const base=st?.value.trim()||'',civic=cv?.value.trim()||'',city=cityEl?.value.trim()||'',full=[base,civic].filter(Boolean).join(' ');
  if(!civic){if(status)status.textContent='Inserisci il numero civico di consegna e premi CERCA.';cv?.focus();return}
  if(!HOME_POS||HOME_POS.cityText!==city||HOME_POS.streetText!==full){const verified=await searchDeliveryAddress(false);if(!verified)return}
  if(st)st.value=full;
  try{return await _tcvPublishRequest()}finally{if(st)st.value=base}
};'''
if old not in s:
    raise SystemExit('publish wrapper anchor not found')
s = s.replace(old, new, 1)

if s == original:
    raise SystemExit('No changes applied')
p.write_text(s, encoding='utf-8')
print('Saved home + community help v2 patch applied')
