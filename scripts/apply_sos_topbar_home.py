from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')

# Force fresh service worker registration reference.
s=s.replace("navigator.serviceWorker.register('./sw.js?v=7', { scope: './' })", "navigator.serviceWorker.register('./sw.js?v=8', { scope: './' })")

css_anchor=".sos-stop-top:active{transform:scale(.985)}"
css_add=""".sos-stop-top:active{transform:scale(.985)}
/* TCV_SOS_TOPBAR_HOME_V1 */
.sos-topbar{position:sticky;top:-10px;z-index:15;display:grid;grid-template-columns:.78fr 1.22fr;gap:8px;margin:-2px -2px 12px;padding:8px 2px 10px;background:linear-gradient(180deg,#fff 82%,rgba(255,255,255,.92));border-bottom:1px solid #edf1f6}
.sos-topbar .sos-stop-top{margin:0;padding:14px 10px;font-size:14px;min-height:58px}
.sos-home-top{border:2px solid #cdd9ea;border-radius:18px;background:#fff;color:#071a3d;font-size:14px;font-weight:950;min-height:58px;padding:12px 8px;box-shadow:0 7px 18px rgba(7,26,61,.08)}
.sos-home-top:active{transform:scale(.985)}
@media(max-width:380px){.sos-topbar{grid-template-columns:.7fr 1.3fr}.sos-topbar .sos-stop-top,.sos-home-top{font-size:13px}}
"""
if 'TCV_SOS_TOPBAR_HOME_V1' not in s:
    if css_anchor not in s: raise SystemExit('CSS anchor not found')
    s=s.replace(css_anchor,css_add,1)

old='''<div class="sos-panel"><div class="sos-kicker">SOS DELLA COMUNITÀ</div><h2 class="sos-title">🆘 AIUTO SUBITO</h2><p class="sos-copy">Non devi compilare niente. Da questo momento l'SOS è attivo: se non lo annulli, tra 30 secondi viene inviata la tua posizione agli utenti con le notifiche attive.</p><div class="notice yellow" style="margin-top:10px"><b>Emergenza medica o pericolo immediato?</b> Chiama sempre il <b>112</b>. Tanto Ci Vai non sostituisce i soccorsi ufficiali.</div><button type="button" class="sos-stop-top" onclick="tcvPauseSosForReport()">✋ FERMA SUBITO IL COUNTDOWN</button><div class="sos-countdown">'''
new='''<div class="sos-panel"><div class="sos-topbar"><button type="button" class="sos-home-top" onclick="tcvCancelSosAndHome()">🏠 HOME</button><button type="button" class="sos-stop-top" onclick="tcvPauseSosForReport()">✋ STOP SOS</button></div><div class="sos-kicker">SOS DELLA COMUNITÀ</div><h2 class="sos-title">🆘 AIUTO SUBITO</h2><p class="sos-copy">Non devi compilare niente. Da questo momento l'SOS è attivo: se non lo annulli, tra 30 secondi viene inviata la tua posizione agli utenti con le notifiche attive.</p><div class="notice yellow" style="margin-top:10px"><b>Emergenza medica o pericolo immediato?</b> Chiama sempre il <b>112</b>. Tanto Ci Vai non sostituisce i soccorsi ufficiali.</div><div class="sos-countdown">'''
if 'class="sos-topbar"' not in s:
    if old not in s: raise SystemExit('SOS render anchor not found')
    s=s.replace(old,new,1)

fn_anchor="function tcvLockSosOverlay(lock){"
fn='''async function tcvCancelSosAndHome(){
  if(TCV_SOS_SENDING)return;
  const st=document.getElementById('sosStatus');if(st)st.textContent='🏠 Annullamento SOS e ritorno alla Home…';
  TCV_SOS_PAUSING=true;clearInterval(TCV_SOS_TIMER);TCV_SOS_TIMER=null;
  try{
    if(!TCV_SOS_ALERT_ID&&TCV_SOS_ARMED){
      for(let i=0;i<25&&!TCV_SOS_ALERT_ID&&TCV_SOS_PAUSING;i++)await new Promise(r=>setTimeout(r,100));
      if(!TCV_SOS_PAUSING){TCV_SOS_ARMED=false;TCV_SOS_SENDING=false;tcvLockSosOverlay(false);closeSheet();page('home');return}
    }
    if(TCV_SOS_ALERT_ID){
      const {data,error}=await db.functions.invoke('send-help-push',{body:{action:'cancel',alert_id:TCV_SOS_ALERT_ID}});if(error)throw error;if(data?.error)throw new Error(data.error);if(data?.cancelled===false)throw new Error('L’SOS non è più annullabile');
    }else if(TCV_SOS_PAUSING){
      throw new Error('Sto ancora collegando l’SOS al server. Premi HOME di nuovo tra un istante.');
    }
    TCV_SOS_PAUSING=false;TCV_SOS_ARMED=false;TCV_SOS_ALERT_ID=null;TCV_SOS_SENDING=false;tcvLockSosOverlay(false);closeSheet();page('home')
  }catch(e){
    TCV_SOS_PAUSING=false;TCV_SOS_ARMED=true;clearInterval(TCV_SOS_TIMER);TCV_SOS_TIMER=setInterval(tcvSosTick,250);
    if(st)st.innerHTML=`⚠️ Non posso tornare alla Home finché non confermo l'annullamento dell'SOS: ${esc(e?.message||String(e))}`
  }
}

'''
if 'async function tcvCancelSosAndHome()' not in s:
    if fn_anchor not in s: raise SystemExit('Function anchor not found')
    s=s.replace(fn_anchor,fn+fn_anchor,1)

p.write_text(s,encoding='utf-8')
print('SOS topbar + safe Home button applied')
