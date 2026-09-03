from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
MARK = 'TCV_PAYMENT_LIFECYCLE_PUSH_V2'
if MARK in s:
    print('Payment lifecycle push V2 already applied')
    raise SystemExit(0)

old_status = "if(status==='ritirata')await tcvSendLifecyclePush(id,'picked_up');await loadRequests();if(status==='consegnata')await loadWallet();"
new_status = "if(status==='ritirata')await tcvSendLifecyclePush(id,'picked_up');if(status==='consegnata')await tcvSendLifecyclePush(id,'delivered');await loadRequests();if(status==='consegnata')await loadWallet();"
if old_status not in s:
    raise SystemExit('Could not find setStatus lifecycle hook')
s = s.replace(old_status, new_status, 1)

old_confirm = r'''async function tcvConfirmP2p(consegnaId,action){
  try{
    const {data,error}=await db.rpc('tcv_confirm_delivery_p2p_payment',{p_consegna_id:consegnaId,p_action:action});
    if(error)throw error;
    const p=await tcvLoadP2p(consegnaId);
    if(String(p.rider_id)===String(SESSION.user.id))await tcvOpenRiderP2p(consegnaId);else await tcvOpenClientP2p(consegnaId)
  }catch(e){alert('Conferma pagamento: '+(e?.message||e))}
}'''
new_confirm = r'''async function tcvConfirmP2p(consegnaId,action){
  try{
    const {data,error}=await db.rpc('tcv_confirm_delivery_p2p_payment',{p_consegna_id:consegnaId,p_action:action});
    if(error)throw error;
    if(action==='SENDER_PAID')await tcvSendLifecyclePush(consegnaId,'payment_sent');
    if(action==='RIDER_RECEIVED')await tcvSendLifecyclePush(consegnaId,'payment_received');
    const p=await tcvLoadP2p(consegnaId);
    if(String(p.rider_id)===String(SESSION.user.id))await tcvOpenRiderP2p(consegnaId);else await tcvOpenClientP2p(consegnaId)
  }catch(e){alert('Conferma pagamento: '+(e?.message||e))}
}
/* TCV_PAYMENT_LIFECYCLE_PUSH_V2 */'''
if old_confirm not in s:
    raise SystemExit('Could not find tcvConfirmP2p')
s = s.replace(old_confirm, new_confirm, 1)

p.write_text(s, encoding='utf-8')
print('Applied payment lifecycle push V2')
