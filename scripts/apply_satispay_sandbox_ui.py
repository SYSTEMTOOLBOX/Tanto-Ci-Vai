from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
MARK = 'TCV_SATISPAY_SANDBOX_UI_V1'
if MARK in s:
    print('Satispay sandbox UI already applied')
    raise SystemExit(0)

css = r'''
/* TCV_SATISPAY_SANDBOX_UI_V1 */
.satispay-test-card{margin:18px 0 8px;padding:16px;border:2px solid #ef5b74;border-radius:22px;background:linear-gradient(145deg,#fff,#fff3f5);box-shadow:0 10px 26px rgba(190,39,68,.10)}
.satispay-test-head{display:flex;align-items:center;justify-content:space-between;gap:10px}.satispay-test-head b{font-size:17px;letter-spacing:-.025em}.satispay-test-badge{padding:6px 9px;border-radius:999px;background:#d92145;color:#fff;font-size:9px;font-weight:1000;letter-spacing:.08em}.satispay-test-card p{margin:7px 0 12px;color:#52647f;font-size:12px;line-height:1.45}.satispay-test-money{display:flex;align-items:end;justify-content:space-between;gap:10px;padding:11px 12px;border-radius:15px;background:#fff;border:1px solid #f2ccd3;margin-bottom:10px}.satispay-test-money strong{font-size:25px}.satispay-test-money span{font-size:10px;font-weight:950;color:#b3203c}.satispay-test-pay{width:100%;min-height:54px;border:0;border-radius:15px;background:#d92145;color:#fff;font-size:14px;font-weight:1000;box-shadow:0 8px 20px rgba(217,33,69,.22)}.satispay-test-pay:disabled{opacity:.55}.satispay-test-check{width:100%;min-height:46px;margin-top:8px;border:1px solid #e9b6c0;border-radius:14px;background:#fff;color:#9f1833;font-size:12px;font-weight:950}.satispay-test-status{margin-top:9px;padding:9px 10px;border-radius:12px;background:#fff;border:1px solid #f0d6db;color:#6b4250;font-size:11px;line-height:1.4}.satispay-result{padding:18px 4px;text-align:center}.satispay-result .big{font-size:52px}.satispay-result h2{font-size:25px;margin:7px 0}.satispay-result p{font-size:13px;line-height:1.5;color:#52647f}.satispay-result.accepted h2{color:#168653}.satispay-result.cancelled h2{color:#b21324}.satispay-result.pending h2{color:#a16b00}
'''
if '</style>' not in s:
    raise SystemExit('Missing </style>')
s = s.replace('</style>', css + '\n</style>', 1)

js = r'''
/* TCV_SATISPAY_SANDBOX_UI_V1 */
let TCV_SATISPAY_BUSY=false;
function tcvMountSatispaySandbox(){
  const home=document.getElementById('home');
  if(!home||document.getElementById('tcvSatispaySandbox'))return;
  const card=document.createElement('section');
  card.id='tcvSatispaySandbox';
  card.className='satispay-test-card';
  card.innerHTML=`<div class="satispay-test-head"><b>❤️ Satispay</b><span class="satispay-test-badge">SANDBOX</span></div><p>Banco prova dei pagamenti di Tanto Ci Vai. <b>Nessun denaro reale.</b></p><div class="satispay-test-money"><div><small>TEST PAGAMENTO</small><br><strong>€ 1,00</strong></div><span>SOLO PROVA</span></div><button id="tcvSatispayPayBtn" class="satispay-test-pay" onclick="tcvStartSatispayTest()">PAGA 1 € CON SATISPAY</button><button class="satispay-test-check" onclick="tcvCheckSatispayTest(true)">↻ Controlla ultimo pagamento</button><div id="tcvSatispayStatus" class="satispay-test-status">Sandbox Satispay collegata. Pronta per il primo test.</div>`;
  const actions=home.querySelector('.home-clean-actions');
  if(actions)actions.insertAdjacentElement('afterend',card);else home.appendChild(card);
}
function tcvSatispaySetStatus(t){const el=document.getElementById('tcvSatispayStatus');if(el)el.textContent=t}
async function tcvSatispayInvoke(body){
  const {data,error}=await db.functions.invoke('satispay-api',{body});
  if(error)throw error;
  if(data?.error)throw new Error(data.error);
  return data;
}
async function tcvStartSatispayTest(){
  if(TCV_SATISPAY_BUSY)return;
  const btn=document.getElementById('tcvSatispayPayBtn');
  TCV_SATISPAY_BUSY=true;if(btn)btn.disabled=true;
  try{
    tcvSatispaySetStatus('Creo il pagamento Sandbox da € 1,00…');
    const orderRef=`TCV-TEST-${Date.now()}`;
    const data=await tcvSatispayInvoke({action:'create',amount_unit:100,order_ref:orderRef});
    if(!data?.id||!data?.redirect_url)throw new Error('Satispay non ha restituito il link di pagamento');
    localStorage.setItem('tcv_satispay_payment_id',String(data.id));
    localStorage.setItem('tcv_satispay_order_ref',orderRef);
    tcvSatispaySetStatus('Pagamento creato. Apro Satispay Sandbox…');
    window.location.assign(String(data.redirect_url));
  }catch(e){
    tcvSatispaySetStatus('Errore Sandbox: '+(e?.message||e));
    TCV_SATISPAY_BUSY=false;if(btn)btn.disabled=false;
  }
}
function tcvSatispayResultSheet(data){
  const st=String(data?.status||'PENDING').toUpperCase();
  const accepted=st==='ACCEPTED',cancelled=st==='CANCELED'||st==='CANCELLED';
  const cls=accepted?'accepted':cancelled?'cancelled':'pending';
  const icon=accepted?'✅':cancelled?'❌':'⏳';
  const title=accepted?'PAGAMENTO RIUSCITO':cancelled?'PAGAMENTO ANNULLATO':'PAGAMENTO IN ATTESA';
  const msg=accepted?'Satispay Sandbox ha confermato il pagamento di prova da € 1,00. Nessun denaro reale è stato movimentato.':cancelled?'Il pagamento Sandbox è stato annullato. Puoi ripetere il test quando vuoi.':'Satispay non lo ha ancora confermato. Puoi controllare di nuovo tra qualche secondo.';
  openSheet(`<div class="satispay-result ${cls}"><div class="big">${icon}</div><h2>${title}</h2><p>${msg}</p><div class="notice ${accepted?'green':'yellow'}">Stato Satispay: <b>${esc(st)}</b></div>${!accepted&&!cancelled?'<button class="btn primary full" style="margin-top:12px" onclick="tcvCheckSatispayTest(true)">↻ CONTROLLA DI NUOVO</button>':''}<button class="btn outline full" style="margin-top:8px" onclick="closeSheet();page('home')">🏠 TORNA ALLA HOME</button></div>`);
}
async function tcvCheckSatispayTest(showResult=true){
  const id=localStorage.getItem('tcv_satispay_payment_id');
  if(!id){tcvSatispaySetStatus('Non c’è ancora un pagamento Sandbox da controllare.');return null}
  try{
    tcvSatispaySetStatus('Controllo lo stato reale su Satispay…');
    const data=await tcvSatispayInvoke({action:'get',payment_id:id});
    const st=String(data?.status||'PENDING').toUpperCase();
    tcvSatispaySetStatus(`Ultimo test: ${st}`);
    if(showResult)tcvSatispayResultSheet(data);
    return data;
  }catch(e){tcvSatispaySetStatus('Errore controllo: '+(e?.message||e));return null}
}
async function tcvHandleSatispayReturn(attempt=0){
  const isReturn=new URLSearchParams(location.search).get('satispay')==='return';
  if(!isReturn)return;
  if(!SESSION){if(attempt<20)setTimeout(()=>tcvHandleSatispayReturn(attempt+1),350);return}
  try{history.replaceState({},document.title,location.pathname+location.hash)}catch(e){}
  setTimeout(()=>tcvCheckSatispayTest(true),250);
}
setTimeout(()=>{tcvMountSatispaySandbox();tcvHandleSatispayReturn()},500);
window.addEventListener('pageshow',()=>{setTimeout(()=>{tcvMountSatispaySandbox();tcvHandleSatispayReturn()},250)});
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible'){setTimeout(()=>{tcvMountSatispaySandbox();if(localStorage.getItem('tcv_satispay_payment_id'))tcvCheckSatispayTest(false)},500)}});
'''
idx = s.rfind('</script>')
if idx < 0:
    raise SystemExit('Missing </script>')
s = s[:idx] + js + '\n' + s[idx:]

# bump service worker registration query if present
m = re.search(r'sw\.js\?v=(\d+)', s)
if m:
    old = int(m.group(1))
    s = s[:m.start()] + f'sw.js?v={old+1}' + s[m.end():]

p.write_text(s, encoding='utf-8')
print('Applied Satispay Sandbox UI')
