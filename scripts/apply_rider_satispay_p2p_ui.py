from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
MARK = 'TCV_RIDER_SATISPAY_P2P_UI_V1'
if MARK in s:
    print('Rider Satispay P2P UI already applied')
    raise SystemExit(0)

css = r'''
/* TCV_RIDER_SATISPAY_P2P_UI_V1 */
.satispay-profile-box{margin:10px 0;padding:13px;border:1px solid #f0ccd4;border-radius:16px;background:linear-gradient(145deg,#fff,#fff5f7)}
.satispay-profile-box h3{margin:0 0 4px;font-size:15px}.satispay-profile-box p{margin:0 0 9px;color:#52647f;font-size:10px;line-height:1.45}
.satispay-ready-row{display:flex;gap:9px;align-items:flex-start;padding:10px 11px;border:1px solid #f0d9de;background:#fff;border-radius:13px;font-size:10px;font-weight:850;line-height:1.35}.satispay-ready-row input{width:auto;margin:1px 0 0;transform:scale(1.12)}
.satispay-personal-btn{margin-top:10px;background:linear-gradient(135deg,#e51d46,#ff4d29)!important;color:#fff!important;box-shadow:0 8px 19px rgba(213,32,68,.18)}
.satispay-personal-sheet{text-align:center;padding:4px 1px 8px}.satispay-personal-sheet .heart{font-size:42px}.satispay-personal-sheet h2{font-size:24px;line-height:1.1;margin:6px 0}.satispay-personal-sheet>p{color:#52647f;font-size:12px;line-height:1.5;margin:5px 0 12px}
.satispay-p2p-amount{font-size:42px;font-weight:1000;letter-spacing:-.045em;margin:8px 0;color:#151a2b}.satispay-p2p-detail{text-align:left;margin:10px 0;padding:12px;border:1px solid #e6eaf0;border-radius:15px;background:#f8faff}.satispay-p2p-detail small{display:block;color:#6c7891;font-size:8px;font-weight:950;letter-spacing:.08em}.satispay-p2p-detail strong{display:block;font-size:18px;margin-top:3px;word-break:break-word}.satispay-p2p-steps{text-align:left;margin:10px 0;padding:12px 13px;border-radius:15px;background:#fff8df;border:1px solid #ffe49a;color:#5f4b12;font-size:10px;line-height:1.55}.satispay-p2p-state{margin:10px 0;padding:11px;border-radius:14px;background:#f3f6fa;border:1px solid #e0e7ef;font-size:11px;font-weight:850;line-height:1.4}.satispay-p2p-state.ok{background:#effff7;border-color:#c9ecd9;color:#21684a}
'''
if '</style>' not in s:
    raise SystemExit('Missing </style>')
s = s.replace('</style>', css + '\n</style>', 1)

# Beta: the app fee is not collected yet, so hide the old fee pill.
fee_pill = '${mine?`<span class="pill">Servizio app ${euro(r.commissione_app)}</span>`:``}'
if fee_pill in s:
    s = s.replace(fee_pill, '', 1)

# Add payment controls to completed requests/missions.
needle = "${assigned?missionButtons(r):''}${mine&&requestOpen(r)?"
replacement = "${assigned?missionButtons(r):''}${assigned&&r.stato==='consegnata'?tcvRiderP2pButton(r):''}${mine&&r.rider_id&&r.stato==='consegnata'?tcvClientP2pButton(r):''}${mine&&requestOpen(r)?"
if needle not in s:
    raise SystemExit('Could not find card action insertion point')
s = s.replace(needle, replacement, 1)

# Add rider Satispay configuration inside the existing profile card.
profile_needle = '<div class="field"><label>TELEFONO</label><input id="pfPhone" value="${esc(PROFILE.telefono||\'\')}"></div><button class="btn teal full" onclick="saveProfile()">Salva profilo</button>'
profile_replacement = r'''<div class="field"><label>TELEFONO</label><input id="pfPhone" value="${esc(PROFILE.telefono||'')}"></div><div class="satispay-profile-box"><h3>❤️ Satispay personale del rider</h3><p>Il compenso della consegna viene inviato dal cliente direttamente al tuo Satispay personale. Tanto Ci Vai non incassa questi soldi.</p><div class="field"><label>NUMERO COLLEGATO A SATISPAY</label><input id="pfSatispayPhone" inputmode="tel" autocomplete="tel" placeholder="Es. 3331234567" value="${esc(PROFILE.satispay_phone||PROFILE.telefono||'')}"></div><label class="satispay-ready-row"><input id="pfSatispayReady" type="checkbox" ${PROFILE.satispay_ready?'checked':''}><span>Questo numero è attivo su Satispay e voglio usarlo per ricevere i compensi delle consegne.</span></label><div class="notice green" style="margin-top:8px">Beta: commissione Tanto Ci Vai <b>0 €</b>. I 0,50 € verranno gestiti separatamente solo più avanti.</div></div><button class="btn teal full" onclick="saveProfile()">Salva profilo</button>'''
if profile_needle not in s:
    raise SystemExit('Could not find profile phone field')
s = s.replace(profile_needle, profile_replacement, 1)

# Replace profile save so the two Satispay fields are persisted too.
pat = re.compile(r"async function saveProfile\(\)\{[^\n]*\}\nasync function logout\(\)")
m = pat.search(s)
if not m:
    raise SystemExit('Could not find saveProfile')
new_save = r'''async function saveProfile(){
  let nome=document.getElementById('pfName')?.value.trim()||'',telefono=document.getElementById('pfPhone')?.value.trim()||'';
  let satispay_phone=document.getElementById('pfSatispayPhone')?.value.trim()||'',satispay_ready=!!document.getElementById('pfSatispayReady')?.checked;
  if(satispay_ready&&!satispay_phone){alert('Inserisci il numero collegato al tuo Satispay personale.');return}
  let {error}=await db.from('profiles').update({nome,telefono,satispay_phone,satispay_ready}).eq('id',SESSION.user.id);
  if(error){alert(error.message);return}
  PROFILE={...PROFILE,nome,telefono,satispay_phone,satispay_ready};await ensureProfile();renderProfile();
  alert(satispay_ready?'Profilo salvato. Satispay rider è pronto.':'Profilo salvato. Satispay rider non è ancora attivo.');
}
async function logout()'''
s = s[:m.start()] + new_save + s[m.end():]

js = r'''
/* TCV_RIDER_SATISPAY_P2P_UI_V1 */
function tcvClientP2pButton(r){
  return `<button class="btn full satispay-personal-btn" onclick="tcvOpenClientP2p('${r.id}')">❤️ PAGA IL RIDER CON SATISPAY</button>`
}
function tcvRiderP2pButton(r){
  return `<button class="btn full satispay-personal-btn" onclick="tcvOpenRiderP2p('${r.id}')">❤️ PAGAMENTO SATISPAY</button>`
}
function tcvP2pMoney(unit){
  return new Intl.NumberFormat('it-IT',{style:'currency',currency:'EUR'}).format((Number(unit)||0)/100)
}
async function tcvLoadP2p(consegnaId){
  const {data,error}=await db.from('delivery_p2p_payments').select('consegna_id,cliente_id,rider_id,rider_display_name,rider_satispay_phone,amount_unit,currency,status,sender_confirmed_at,receiver_confirmed_at,platform_fee_unit,platform_fee_status').eq('consegna_id',consegnaId).maybeSingle();
  if(error)throw error;
  if(!data)throw new Error('Dati del pagamento rider non trovati.');
  return data
}
async function tcvCopyP2p(text,label='Dato'){
  try{await navigator.clipboard.writeText(String(text));alert(label+' copiato.')}catch(e){prompt('Copia questo valore:',String(text))}
}
function tcvP2pOrderLabel(id){
  const r=REQUESTS.find(x=>String(x.id)===String(id));
  return r&&r.numero_ordine!=null?`Ordine #${orderCode(r)}`:'Consegna Tanto Ci Vai'
}
async function tcvOpenClientP2p(consegnaId){
  try{
    const p=await tcvLoadP2p(consegnaId),amount=tcvP2pMoney(p.amount_unit),status=String(p.status||'AWAITING_PAYMENT').toUpperCase();
    const sent=status==='SENDER_CONFIRMED'||status==='RECEIVED',received=status==='RECEIVED';
    let state=received?'<div class="satispay-p2p-state ok">✅ Il rider ha confermato di aver ricevuto il pagamento.</div>':sent?'<div class="satispay-p2p-state">⏳ Hai confermato l’invio. Ora attendiamo la conferma del rider.</div>':'<div class="satispay-p2p-state">Da pagare direttamente al rider sul suo Satispay personale.</div>';
    let action=received?'':sent?'':`<button class="btn primary full" style="margin-top:8px" onclick="tcvConfirmP2p('${consegnaId}','SENDER_PAID')">✅ HO INVIATO ${esc(amount)}</button>`;
    openSheet(`<div class="satispay-personal-sheet"><div class="heart">❤️</div><h2>Paga direttamente ${esc(p.rider_display_name||'il rider')}</h2><p>${esc(tcvP2pOrderLabel(consegnaId))}. Il denaro non passa da Tanto Ci Vai.</p><div class="satispay-p2p-amount">${esc(amount)}</div><div class="satispay-p2p-detail"><small>NUMERO SATISPAY DEL RIDER</small><strong>${esc(p.rider_satispay_phone||'')}</strong></div><button class="btn outline full" onclick="tcvCopyP2p('${esc(String(p.rider_satispay_phone||'')).replace(/'/g,"\\'")}','Numero Satispay')">📋 COPIA NUMERO</button><div class="satispay-p2p-steps"><b>Come pagare:</b><br>1. Apri la tua app Satispay personale.<br>2. Vai su Contatti e cerca il numero qui sopra.<br>3. Invia esattamente <b>${esc(amount)}</b>.<br>4. Torna qui e premi “Ho inviato”.</div>${state}${action}<button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button></div>`)
  }catch(e){alert('Pagamento rider: '+(e?.message||e))}
}
async function tcvOpenRiderP2p(consegnaId){
  try{
    const p=await tcvLoadP2p(consegnaId),amount=tcvP2pMoney(p.amount_unit),status=String(p.status||'AWAITING_PAYMENT').toUpperCase();
    let state='',action='';
    if(status==='RECEIVED')state='<div class="satispay-p2p-state ok">✅ Hai confermato la ricezione del pagamento.</div>';
    else if(status==='SENDER_CONFIRMED'){
      state=`<div class="satispay-p2p-state">💸 Il cliente ha dichiarato di aver inviato <b>${esc(amount)}</b>. Controlla il tuo Satispay personale prima di confermare.</div>`;
      action=`<button class="btn teal full" style="margin-top:8px" onclick="tcvConfirmP2p('${consegnaId}','RIDER_RECEIVED')">✅ HO RICEVUTO ${esc(amount)}</button>`;
    }else state=`<div class="satispay-p2p-state">⏳ Il cliente deve ancora confermare l’invio di <b>${esc(amount)}</b>.</div>`;
    openSheet(`<div class="satispay-personal-sheet"><div class="heart">❤️</div><h2>Pagamento della consegna</h2><p>${esc(tcvP2pOrderLabel(consegnaId))}. Ricevi tutto direttamente sul tuo Satispay personale.</p><div class="satispay-p2p-amount">${esc(amount)}</div>${state}${action}<div class="notice green" style="margin-top:10px">Commissione app nella beta: <b>0 €</b>.</div><button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button></div>`)
  }catch(e){alert('Pagamento rider: '+(e?.message||e))}
}
async function tcvConfirmP2p(consegnaId,action){
  try{
    const {data,error}=await db.rpc('tcv_confirm_delivery_p2p_payment',{p_consegna_id:consegnaId,p_action:action});
    if(error)throw error;
    const p=await tcvLoadP2p(consegnaId);
    if(String(p.rider_id)===String(SESSION.user.id))await tcvOpenRiderP2p(consegnaId);else await tcvOpenClientP2p(consegnaId)
  }catch(e){alert('Conferma pagamento: '+(e?.message||e))}
}
'''
idx = s.rfind('</script>')
if idx < 0:
    raise SystemExit('Missing </script>')
s = s[:idx] + js + '\n' + s[idx:]

# Force clients to refresh the service worker after deployment.
m = re.search(r'sw\.js\?v=(\d+)', s)
if m:
    old = int(m.group(1))
    s = s[:m.start()] + f'sw.js?v={old+1}' + s[m.end():]

p.write_text(s, encoding='utf-8')
print('Applied rider personal Satispay P2P UI')
