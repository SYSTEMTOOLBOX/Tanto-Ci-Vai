from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
MARK='STARTUP_SPLASH_V1'
if MARK in s:
    print('startup splash already applied')
    raise SystemExit(0)

css=r'''
/* STARTUP_SPLASH_V1 */
.tcv-app-splash{position:fixed;inset:0;z-index:15000;background:#fff;display:grid;place-items:center;overflow:hidden;animation:tcvSplashIn .18s ease-out}
.tcv-app-splash.fade{animation:tcvSplashOut .22s ease-in forwards}
.tcv-app-splash video{width:100%;height:100%;object-fit:contain;background:#fff}
.tcv-app-splash-logo{width:min(82vw,430px);max-width:430px;max-height:72vh;object-fit:contain;filter:drop-shadow(0 14px 30px rgba(19,61,117,.10));animation:tcvLogoHello .9s ease both}
.tcv-splash-skip{position:absolute;right:18px;top:max(18px,env(safe-area-inset-top));min-height:44px;padding:10px 15px;border:1px solid rgba(15,43,82,.13);border-radius:999px;background:rgba(255,255,255,.88);color:#15345f;font-size:15px;font-weight:900;box-shadow:0 8px 20px rgba(18,51,92,.10);backdrop-filter:blur(10px)}
@keyframes tcvSplashIn{from{opacity:0}to{opacity:1}}
@keyframes tcvSplashOut{from{opacity:1}to{opacity:0}}
@keyframes tcvLogoHello{0%{opacity:0;transform:scale(.91)}55%{opacity:1;transform:scale(1.025)}100%{opacity:1;transform:scale(1)}}
'''
if '</style>' not in s: raise SystemExit('style close not found')
s=s.replace('</style>',css+'\n</style>',1)

old_signup="if(error)throw error;if(!data.session){authStatus.textContent='Registrazione creata. Controlla la tua email e conferma il link, poi torna qui e accedi.';return}await afterLogin(data.session)"
new_signup="if(error)throw error;try{localStorage.setItem('tcv_intro_pending_v1',email.toLowerCase())}catch(e){}if(!data.session){authStatus.textContent='Registrazione creata. Controlla la tua email e conferma il link, poi torna qui e accedi.';return}await afterLogin(data.session)"
if old_signup not in s: raise SystemExit('signup anchor not found')
s=s.replace(old_signup,new_signup,1)

old_after="async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');await ensureProfile();await loadRequests();subscribeRealtime();renderAll();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000)}"
new_after="async function afterLogin(session){SESSION=session;authView.classList.add('hidden');appView.classList.remove('hidden');bottomNav.classList.remove('hidden');let splashPromise=runStartupSplash(session);await ensureProfile();await loadRequests();subscribeRealtime();renderAll();if(!window.__tcvOfferTick)window.__tcvOfferTick=setInterval(()=>{if(SESSION)renderAll()},60000);await splashPromise}"
if old_after not in s: raise SystemExit('afterLogin anchor not found')
s=s.replace(old_after,new_after,1)

js=r'''
/* STARTUP_SPLASH_V1 */
const TCV_SPLASH_VIDEO='assets/tcv-welcome-5_5s.mp4?v=1';
const TCV_SPLASH_LOGO='assets/tcv-splash-logo.jpg?v=1';
function tcvIntroKey(session){return `tcv_intro_seen_v1_${session?.user?.id||'anon'}`}
function tcvIsFreshRegistration(session){
  try{
    const pending=(localStorage.getItem('tcv_intro_pending_v1')||'').toLowerCase();
    const email=(session?.user?.email||'').toLowerCase();
    return !!pending&&pending===email&&!localStorage.getItem(tcvIntroKey(session));
  }catch(e){return false}
}
function tcvMarkIntroSeen(session){
  try{localStorage.setItem(tcvIntroKey(session),'1');localStorage.removeItem('tcv_intro_pending_v1')}catch(e){}
}
function tcvRemoveStartupSplash(){document.getElementById('tcvAppSplash')?.remove()}
function tcvFadeAndRemove(wrap,resolve){
  if(!wrap||wrap.dataset.done==='1')return;
  wrap.dataset.done='1';wrap.classList.add('fade');
  setTimeout(()=>{wrap.remove();resolve?.()},220)
}
function runStartupSplash(session){
  tcvRemoveStartupSplash();
  return new Promise(resolve=>{
    const first=tcvIsFreshRegistration(session),wrap=document.createElement('div');
    wrap.id='tcvAppSplash';wrap.className='tcv-app-splash';
    if(first){
      wrap.innerHTML=`<video id="tcvWelcomeVideo" src="${TCV_SPLASH_VIDEO}" autoplay muted playsinline preload="auto"></video><button type="button" class="tcv-splash-skip">Salta ›</button>`;
      document.body.appendChild(wrap);
      const video=wrap.querySelector('video');
      const finish=()=>{tcvMarkIntroSeen(session);tcvFadeAndRemove(wrap,resolve)};
      video.addEventListener('ended',finish,{once:true});
      video.addEventListener('error',finish,{once:true});
      wrap.addEventListener('click',finish,{once:true});
      try{video.play()?.catch(()=>{})}catch(e){}
      setTimeout(finish,6500);
    }else{
      wrap.innerHTML=`<img class="tcv-app-splash-logo" src="${TCV_SPLASH_LOGO}" alt="Tanto ci vai?">`;
      document.body.appendChild(wrap);
      setTimeout(()=>tcvFadeAndRemove(wrap,resolve),1000);
    }
  })
}
'''
pos=s.rfind('</script>')
if pos<0: raise SystemExit('script close not found')
s=s[:pos]+js+'\n'+s[pos:]
p.write_text(s,encoding='utf-8')
print('startup splash applied')
