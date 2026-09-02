from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
MARK='REQUEST_SUCCESS_POPUP_V1'
if MARK in s:
    print('already applied')
    raise SystemExit(0)

old="alert('Richiesta pubblicata.')"
if old not in s:
    raise SystemExit('success alert anchor not found')
s=s.replace(old,'showRequestPublishedSuccess()',1)

css=r'''
/* REQUEST_SUCCESS_POPUP_V1 */
.tcv-success-overlay{position:fixed;inset:0;z-index:12000;display:grid;place-items:center;padding:22px;background:rgba(7,26,61,.42);backdrop-filter:blur(6px)}
.tcv-success-card{width:min(430px,100%);position:relative;overflow:hidden;text-align:center;background:linear-gradient(180deg,#effff6 0%,#ffffff 78%);border:1px solid #bfeeda;border-radius:32px;padding:28px 22px 22px;box-shadow:0 26px 70px rgba(7,39,35,.28);animation:tcvSuccessPop .28s cubic-bezier(.2,.85,.25,1.15)}
.tcv-success-card:before,.tcv-success-card:after{content:"";position:absolute;border-radius:50%;background:rgba(11,203,176,.12)}
.tcv-success-card:before{width:150px;height:150px;right:-70px;top:-75px}.tcv-success-card:after{width:110px;height:110px;left:-55px;bottom:-58px}
.tcv-success-check{width:84px;height:84px;margin:0 auto 16px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#22c878,#0bcbb0);color:#fff;font-size:43px;font-weight:1000;box-shadow:0 14px 30px rgba(19,184,125,.28);animation:tcvCheck .42s .08s both}
.tcv-success-card h2{position:relative;margin:0;color:#118c59;font-size:31px;line-height:1.05;letter-spacing:-.035em}
.tcv-success-card p{position:relative;margin:10px auto 21px;max-width:330px;color:#3c6657;font-size:17px;line-height:1.45;font-weight:650}
.tcv-success-btn{position:relative;width:100%;min-height:58px;border:0;border-radius:18px;background:linear-gradient(135deg,#1fbd70,#08b99f);color:#fff;font-size:18px;font-weight:950;box-shadow:0 10px 24px rgba(18,174,116,.22)}
@keyframes tcvSuccessPop{from{opacity:0;transform:translateY(22px) scale(.92)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes tcvCheck{0%{transform:scale(.45) rotate(-12deg);opacity:0}70%{transform:scale(1.12) rotate(2deg);opacity:1}100%{transform:scale(1) rotate(0)}}
'''
style_pos=s.rfind('</style>')
if style_pos<0: raise SystemExit('style close not found')
s=s[:style_pos]+css+'\n'+s[style_pos:]

js=r'''
/* REQUEST_SUCCESS_POPUP_V1 */
function tcvSuccessTone(){
  try{
    const AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;
    const ctx=new AC();
    const g=ctx.createGain();g.connect(ctx.destination);
    const now=ctx.currentTime;g.gain.setValueAtTime(.0001,now);g.gain.exponentialRampToValueAtTime(.14,now+.018);g.gain.exponentialRampToValueAtTime(.0001,now+.52);
    const o1=ctx.createOscillator();o1.type='sine';o1.frequency.setValueAtTime(880,now);o1.frequency.exponentialRampToValueAtTime(1174.66,now+.20);o1.connect(g);o1.start(now);o1.stop(now+.34);
    const o2=ctx.createOscillator();o2.type='sine';o2.frequency.setValueAtTime(1318.51,now+.16);o2.connect(g);o2.start(now+.16);o2.stop(now+.50);
    setTimeout(()=>ctx.close().catch(()=>{}),650);
  }catch(e){}
  try{navigator.vibrate?.(35)}catch(e){}
}
function closeRequestPublishedSuccess(){document.getElementById('tcvSuccessOverlay')?.remove()}
function showRequestPublishedSuccess(){
  closeRequestPublishedSuccess();
  const wrap=document.createElement('div');wrap.id='tcvSuccessOverlay';wrap.className='tcv-success-overlay';
  wrap.innerHTML=`<div class="tcv-success-card" role="dialog" aria-modal="true" aria-labelledby="tcvSuccessTitle"><div class="tcv-success-check">✓</div><h2 id="tcvSuccessTitle">Richiesta pubblicata!</h2><p>Perfetto! La tua richiesta è ora visibile ai runner della zona.</p><button type="button" class="tcv-success-btn" onclick="closeRequestPublishedSuccess()">Perfetto</button></div>`;
  wrap.addEventListener('click',e=>{if(e.target===wrap)closeRequestPublishedSuccess()});
  document.body.appendChild(wrap);tcvSuccessTone();
}
'''
script_pos=s.rfind('</script>')
if script_pos<0: raise SystemExit('script close not found')
s=s[:script_pos]+js+'\n'+s[script_pos:]

p.write_text(s,encoding='utf-8')
print('native success alert replaced with custom in-app popup')
