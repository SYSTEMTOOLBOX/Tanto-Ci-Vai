from pathlib import Path
import re

p=Path('index.html')
s=p.read_text(encoding='utf-8')
MARK='TCV_KM_FUND_LOCK_CHECKOUT_V1'
if MARK in s:
    print('KM fund-lock checkout already applied')
    raise SystemExit(0)

# Only funded new requests are visible to riders. Existing rows remain LEGACY.
old="const requestOpen=r=>r.stato==='disponibile'&&offerExpiresAt(r)>Date.now()&&(!r.consegna_entro||new Date(r.consegna_entro).getTime()>Date.now());"
new="const requestOpen=r=>r.stato==='disponibile'&&['LEGACY','READY'].includes(String(r.payment_state||'LEGACY'))&&offerExpiresAt(r)>Date.now()&&(!r.consegna_entro||new Date(r.consegna_entro).getTime()>Date.now());"
if old not in s: raise SystemExit('requestOpen not found')
s=s.replace(old,new,1)

# Replace manual compensation picker with the automatic tariff description.
old_pay='''<div class="field"><label>COMPENSO RIDER</label><select id="nrPay"><option value="3.5">€ 3,50</option><option value="4" selected>€ 4,00</option><option value="5">€ 5,00</option><option value="6">€ 6,00</option></select></div>'''
new_pay='''<div class="field"><label>TARIFFA AUTOMATICA</label><div class="notice green" style="font-size:11px"><b>Rider: € 0,50/km</b> sulla distanza stradale reale.<br><b>Tanto Ci Vai: € 0,50</b> di servizio, addebitati subito.<br><span id="nrPricingPreview">Il totale viene calcolato automaticamente prima di aprire Satispay.</span></div></div>'''
if old_pay not in s: raise SystemExit('nrPay UI not found')
s=s.replace(old_pay,new_pay,1)

# Remove the old manual pay variable.
old_decl="deadlineValue=document.getElementById('nrDeadline')?.value||'',offerHours=+(document.getElementById('nrOfferHours')?.value||3),pay=+nrPay.value;"
new_decl="deadlineValue=document.getElementById('nrDeadline')?.value||'',offerHours=+(document.getElementById('nrOfferHours')?.value||3);"
if old_decl not in s: raise SystemExit('publish declaration not found')
s=s.replace(old_decl,new_decl,1)

# Price by real road distance, create hidden-until-funded request, then start Satispay checkout.
old_block="""    let deliveryLabel=canonicalDeliveryLabel(street,city);
    let {data:created,error}=await db.from('consegne').insert({cliente_id:SESSION.user.id,categoria:REQUEST_CATEGORY,titolo:title,descrizione:fullDesc,ritiro_indirizzo:a.label,ritiro_lat:a.lat,ritiro_lng:a.lng,consegna_indirizzo:deliveryLabel,consegna_lat:b.lat,consegna_lng:b.lng,consegna_entro:deadline.toISOString(),offerta_scade_il:offerExpires.toISOString(),compenso_rider:pay}).select('id,numero_ordine').single();if(error)throw error;try{await db.functions.invoke('send-request-push',{body:{request_id:created.id}})}catch(pushErr){console.warn('Push send failed',pushErr)}
    await loadRequests();renderAll();closeSheet();SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;DELIVERY_CITY_POS=null;if(DELIVERY_MAP){DELIVERY_MAP.remove();DELIVERY_MAP=null;DELIVERY_MARKER=null}showRequestPublishedSuccess(created.numero_ordine)"""
new_block="""    let deliveryLabel=canonicalDeliveryLabel(street,city);
    nrStatus.textContent='Calcolo i km reali su strada…';
    let pricingRoute=await route([a,b]),routeKm=Math.max(0.01,Number(pricingRoute.distance||0)/1000);
    let pay=Math.round(routeKm*50)/100,appFee=.50,total=Math.round((pay+appFee)*100)/100;
    let preview=document.getElementById('nrPricingPreview');if(preview)preview.innerHTML=`${routeKm.toFixed(1)} km × € 0,50 = <b>${euro(pay)}</b> rider + <b>€ 0,50</b> servizio · totale <b>${euro(total)}</b>`;
    nrStatus.textContent=`Totale ${euro(total)}. Apro Satispay Sandbox…`;
    let {data:created,error}=await db.from('consegne').insert({cliente_id:SESSION.user.id,categoria:REQUEST_CATEGORY,titolo:title,descrizione:fullDesc,ritiro_indirizzo:a.label,ritiro_lat:a.lat,ritiro_lng:a.lng,consegna_indirizzo:deliveryLabel,consegna_lat:b.lat,consegna_lng:b.lng,consegna_entro:deadline.toISOString(),offerta_scade_il:offerExpires.toISOString(),route_km:+routeKm.toFixed(2),tariffa_km:.50,compenso_rider:pay,commissione_app:.50,payment_state:'PAYMENT_REQUIRED'}).select('id,numero_ordine').single();if(error)throw error;
    await loadRequests();renderAll();closeSheet();SELECTED_PLACE=null;SEARCH_POS=null;HOME_POS=null;DELIVERY_CITY_POS=null;if(DELIVERY_MAP){DELIVERY_MAP.remove();DELIVERY_MAP=null;DELIVERY_MARKER=null}
    await tcvStartDeliveryPayment(created.id)"""
if old_block not in s: raise SystemExit('publish insert block not found')
s=s.replace(old_block,new_block,1)

# Keep old P2P only for legacy deliveries. New paid deliveries use fund lock.
old_actions="${assigned&&r.stato==='consegnata'?tcvRiderP2pButton(r):''}${mine&&r.rider_id&&r.stato==='consegnata'?tcvClientP2pButton(r):''}"
new_actions="${assigned&&r.stato==='consegnata'&&r.payment_state==='LEGACY'?tcvRiderP2pButton(r):''}${mine&&r.rider_id&&r.stato==='consegnata'&&r.payment_state==='LEGACY'?tcvClientP2pButton(r):''}${mine?tcvDeliveryPaymentButton(r):''}${assigned?tcvRiderLockedPaymentButton(r):''}"
if old_actions not in s: raise SystemExit('legacy P2P actions not found')
s=s.replace(old_actions,new_actions,1)

# Add km + fee to the first request card meta row.
old_meta='<span class="pill money">Compenso ${euro(r.compenso_rider)}</span>${r.offerta_scade_il?'
new_meta='<span class="pill money">Compenso rider ${euro(r.compenso_rider)}</span>${r.route_km!=null?`<span class="pill">🚗 ${Number(r.route_km).toFixed(1)} km × € 0,50</span>`:``}${mine&&r.payment_state!==\'LEGACY\'?`<span class="pill">Servizio € 0,50</span>`:``}${r.offerta_scade_il?'
if old_meta not in s: raise SystemExit('card meta not found')
s=s.replace(old_meta,new_meta,1)

# Update the profile wording: personal Satispay remains the intended final payout destination.
s=s.replace('Il compenso della consegna viene inviato dal cliente direttamente al tuo Satispay personale. Tanto Ci Vai non incassa questi soldi.','Il compenso viene bloccato quando il cliente paga e si sblocca solo dopo “Consegnato”. Il tuo numero Satispay resta associato al profilo per il payout finale del rider.',1)
s=s.replace('Beta: commissione Tanto Ci Vai <b>0 €</b>. I 0,50 € verranno gestiti separatamente solo più avanti.','Sandbox: commissione Tanto Ci Vai <b>€ 0,50</b>, pagata subito dal cliente. Il compenso rider resta invece bloccato fino alla consegna.',1)

# Replace setStatus so delivery completion captures the authorized fund lock automatically.
pat=re.compile(r"async function setStatus\(id,status\)\{let before=status==='consegnata'\?walletTrackedTotal\(\):null;.*?tcvMaybeShowWalletMilestone\(before,walletTrackedTotal\(\)\)\}")
m=pat.search(s)
if not m: raise SystemExit('setStatus not found')
new_status=r'''async function setStatus(id,status){
  let before=status==='consegnata'?walletTrackedTotal():null,req=REQUESTS.find(x=>x.id===id);
  let {data,error}=await db.rpc('aggiorna_stato_consegna',{p_consegna_id:id,p_stato:status});
  if(error){alert(error.message);return}if(!data){alert('Operazione non consentita o stato già cambiato.');return}
  if(status==='ritirata')await tcvSendLifecyclePush(id,'picked_up');
  if(status==='consegnata'){
    await tcvSendLifecyclePush(id,'delivered');
    if(req&&String(req.payment_state||'LEGACY')!=='LEGACY')await tcvCaptureDeliveryFunds(id,true);
  }
  if(status==='annullata'&&req&&String(req.payment_state||'LEGACY')!=='LEGACY')await tcvCancelDeliveryHold(id);
  await loadRequests();if(status==='consegnata')await loadWallet();renderAll();if(status==='consegnata')tcvMaybeShowWalletMilestone(before,walletTrackedTotal())
}'''
s=s[:m.start()]+new_status+s[m.end():]

css=r'''
/* TCV_KM_FUND_LOCK_CHECKOUT_V1 */
.tcv-pay-state{margin-top:9px;padding:10px 11px;border-radius:13px;background:#f4f7fb;border:1px solid #dfe7f0;font-size:10px;line-height:1.45;color:#4c5d75}.tcv-pay-state.ok{background:#effff7;border-color:#c8ecd8;color:#246b4d}.tcv-pay-state.warn{background:#fff8df;border-color:#ffe39a;color:#6b5110}.tcv-pay-button{margin-top:9px;background:linear-gradient(135deg,#e51d46,#ff4d29)!important;color:#fff!important}.tcv-price-big{font-size:34px;font-weight:1000;letter-spacing:-.04em;margin:8px 0}.tcv-checkout-lines{display:grid;gap:7px;margin:12px 0}.tcv-checkout-line{display:flex;justify-content:space-between;gap:12px;padding:10px 11px;border:1px solid #e4eaf1;border-radius:13px;background:#fff;font-size:11px}.tcv-checkout-line b{white-space:nowrap}
'''
s=s.replace('</style>',css+'\n</style>',1)

js=r'''
/* TCV_KM_FUND_LOCK_CHECKOUT_V1 */
function tcvDeliveryPaymentButton(r){
  const st=String(r.payment_state||'LEGACY');
  if(st==='LEGACY'||st==='READY'||st==='ASSIGNED'||st==='CAPTURED_PENDING_PAYOUT')return '';
  if(['FEE_CANCELED','HOLD_CANCELED'].includes(st))return `<div class="tcv-pay-state warn">Pagamento non completato.</div><button class="btn full tcv-pay-button" onclick="tcvRestartDeliveryPayment('${r.id}')">❤️ RIPROVA PAGAMENTO</button>`;
  return `<div class="tcv-pay-state warn">Richiesta non ancora visibile ai rider: completa Satispay.</div><button class="btn full tcv-pay-button" onclick="tcvResumeDeliveryPayment('${r.id}',false)">❤️ COMPLETA PAGAMENTO</button>`
}
function tcvRiderLockedPaymentButton(r){
  const st=String(r.payment_state||'');
  if(r.stato!=='consegnata'||st==='LEGACY')return '';
  if(st==='CAPTURED_PENDING_PAYOUT')return `<div class="tcv-pay-state ok">🔓 Fondo rider sbloccato dopo “Consegnato” (Sandbox).</div>`;
  return `<button class="btn teal full" style="margin-top:9px" onclick="tcvCaptureDeliveryFunds('${r.id}',true)">🔓 SBLOCCA COMPENSO</button>`
}
async function tcvDeliveryPayInvoke(action,deliveryId){
  const {data,error}=await db.functions.invoke('satispay-api',{body:{action,delivery_id:deliveryId}});if(error)throw error;if(data?.error)throw new Error(data.error);return data
}
function tcvRememberDeliveryPayment(id){try{localStorage.setItem('tcv_delivery_payment_id',String(id))}catch(e){}}
function tcvForgetDeliveryPayment(){try{localStorage.removeItem('tcv_delivery_payment_id')}catch(e){}}
async function tcvStartDeliveryPayment(deliveryId){
  tcvRememberDeliveryPayment(deliveryId);
  try{
    const r=REQUESTS.find(x=>x.id===deliveryId),fee=.50,rider=Number(r?.compenso_rider||0),total=rider+fee;
    openSheet(`<div class="satispay-personal-sheet"><div class="heart">❤️</div><h2>Pagamento prima della pubblicazione</h2><p>Il rider vedrà la richiesta solo quando il pagamento è garantito.</p><div class="tcv-price-big">${euro(total)}</div><div class="tcv-checkout-lines"><div class="tcv-checkout-line"><span>Servizio Tanto Ci Vai · subito</span><b>€ 0,50</b></div><div class="tcv-checkout-line"><span>Compenso rider · bloccato</span><b>${euro(rider)}</b></div></div><div class="notice yellow">Sandbox: Satispay richiede prima il pagamento dei € 0,50 e poi l'autorizzazione del blocco fondi rider.</div><button class="btn full tcv-pay-button" style="margin-top:10px" onclick="tcvBeginDeliveryFee('${deliveryId}')">CONTINUA CON SATISPAY</button><button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Non ora</button></div>`)
  }catch(e){alert('Pagamento: '+(e?.message||e))}
}
async function tcvBeginDeliveryFee(deliveryId){
  try{const data=await tcvDeliveryPayInvoke('create_delivery_fee',deliveryId);if(!data?.redirect_url)throw new Error('Link Satispay non disponibile');window.location.assign(String(data.redirect_url))}catch(e){alert('Commissione Satispay: '+(e?.message||e))}
}
async function tcvResumeDeliveryPayment(deliveryId,fromReturn=true){
  tcvRememberDeliveryPayment(deliveryId);
  try{
    const {data:d,error}=await db.from('consegne').select('*').eq('id',deliveryId).maybeSingle();if(error)throw error;if(!d)throw new Error('Richiesta non trovata');
    // If fee is missing or not accepted, create/reopen fee first.
    if(!d.app_fee_payment_id||String(d.app_fee_status||'')!=='ACCEPTED'){
      const fee=await tcvDeliveryPayInvoke('create_delivery_fee',deliveryId);
      if(String(fee.status||'').toUpperCase()==='ACCEPTED'){
        // continue below
      }else if(fee.redirect_url){window.location.assign(String(fee.redirect_url));return}
      else{openSheet(`<div class="satispay-result pending"><div class="big">⏳</div><h2>Commissione in attesa</h2><p>Completa i € 0,50 su Satispay.</p><button class="btn primary full" onclick="tcvResumeDeliveryPayment('${deliveryId}',false)">RIPROVA</button></div>`);return}
    }
    const {data:fresh,error:freshErr}=await db.from('consegne').select('*').eq('id',deliveryId).maybeSingle();if(freshErr)throw freshErr;
    if(!fresh.rider_fund_lock_payment_id){const hold=await tcvDeliveryPayInvoke('create_delivery_fund_lock',deliveryId);if(!hold?.redirect_url)throw new Error('Link blocco fondi non disponibile');window.location.assign(String(hold.redirect_url));return}
    const final=await tcvDeliveryPayInvoke('finalize_delivery_payment',deliveryId);
    if(final.ready){
      tcvForgetDeliveryPayment();try{history.replaceState({},document.title,location.pathname+location.hash)}catch(e){}
      await loadRequests();renderAll();
      try{await db.functions.invoke('send-request-push',{body:{request_id:deliveryId,event:'new_request'}})}catch(e){console.warn('new request push',e)}
      const rr=REQUESTS.find(x=>x.id===deliveryId);showRequestPublishedSuccess(rr?.numero_ordine);return
    }
    if(final.hold_status==='PENDING'){
      openSheet(`<div class="satispay-result pending"><div class="big">🔒</div><h2>Autorizza il blocco fondi</h2><p>Il compenso rider deve risultare AUTHORIZED prima di pubblicare la richiesta.</p><div class="notice yellow">Stato: ${esc(final.hold_status)}</div><button class="btn primary full" style="margin-top:10px" onclick="tcvResumeDeliveryPayment('${deliveryId}',false)">CONTROLLA DI NUOVO</button></div>`);return
    }
    throw new Error(`Pagamento non completato: servizio ${final.fee_status}, fondo rider ${final.hold_status}`)
  }catch(e){openSheet(`<div class="satispay-result cancelled"><div class="big">⚠️</div><h2>Pagamento da completare</h2><p>${esc(e?.message||e)}</p><button class="btn primary full" onclick="tcvRestartDeliveryPayment('${deliveryId}')">RIPROVA</button><button class="btn outline full" style="margin-top:8px" onclick="closeSheet();page('myreq')">LE MIE RICHIESTE</button></div>`)}
}
async function tcvRestartDeliveryPayment(deliveryId){
  try{const {data:d}=await db.from('consegne').select('app_fee_status,rider_fund_lock_status').eq('id',deliveryId).maybeSingle();if(d?.rider_fund_lock_status==='CANCELED'){alert('Il blocco fondi precedente è annullato. Per ora crea una nuova richiesta: evitiamo doppi addebiti della commissione in Sandbox.');return}await tcvResumeDeliveryPayment(deliveryId,false)}catch(e){alert(e?.message||e)}
}
async function tcvCaptureDeliveryFunds(deliveryId,show=false){
  try{
    const data=await tcvDeliveryPayInvoke('capture_delivery',deliveryId);await loadRequests();renderAll();
    if(show)openSheet(`<div class="satispay-result accepted"><div class="big">🔓</div><h2>FONDO SBLOCCATO</h2><p>Satispay Sandbox ha catturato ${euro((Number(data.amount_unit)||0)/100)} solo dopo “Consegnato”.</p><div class="notice green">Il meccanismo blocco → consegna → cattura funziona.</div><div class="notice yellow" style="margin-top:8px">Per il trasferimento automatico dal merchant al Satispay personale del rider serve una funzione marketplace/payout non presente nell'API pubblica.</div><button class="btn outline full" style="margin-top:9px" onclick="closeSheet();page('missions')">CHIUDI</button></div>`);
    return data
  }catch(e){if(show)alert('Sblocco compenso: '+(e?.message||e));return null}
}
async function tcvCancelDeliveryHold(deliveryId){try{return await tcvDeliveryPayInvoke('cancel_delivery_hold',deliveryId)}catch(e){console.warn('cancel delivery hold',e);return null}}

// Delivery checkout takes priority over the old €1 generic Satispay sandbox return handler.
const _tcvOldSatispayReturnHandler=tcvHandleSatispayReturn;
tcvHandleSatispayReturn=async function(attempt=0){
  let deliveryId='';try{deliveryId=localStorage.getItem('tcv_delivery_payment_id')||''}catch(e){}
  const isReturn=new URLSearchParams(location.search).get('satispay')==='return';
  if(deliveryId&&isReturn){if(!SESSION){if(attempt<20)setTimeout(()=>tcvHandleSatispayReturn(attempt+1),350);return}try{history.replaceState({},document.title,location.pathname+location.hash)}catch(e){}setTimeout(()=>tcvResumeDeliveryPayment(deliveryId,true),250);return}
  return _tcvOldSatispayReturnHandler(attempt)
};
'''
idx=s.rfind('</script>')
if idx<0: raise SystemExit('Missing script close')
s=s[:idx]+js+'\n'+s[idx:]

# Refresh service worker query.
m=re.search(r'sw\.js\?v=(\d+)',s)
if m:
    n=int(m.group(1))+1
    s=s[:m.start()]+f'sw.js?v={n}'+s[m.end():]

p.write_text(s,encoding='utf-8')
print('Applied km pricing + Satispay fund lock checkout')
