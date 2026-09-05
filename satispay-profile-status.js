/* TCV_SATISPAY_PROFILE_STATUS_V1 */
(function(){
  'use strict';
  if(window.TCV_SATISPAY_PROFILE_STATUS_V1)return;
  window.TCV_SATISPAY_PROFILE_STATUS_V1=true;

  function isReady(){
    try{return typeof PROFILE!=='undefined'&&!!PROFILE?.satispay_ready}catch(_){return false}
  }

  function decorate(){
    const root=document.getElementById('profile');
    const box=root?.querySelector('.satispay-profile-box');
    if(!box)return;

    box.querySelector('#tcvSatispayReadyHero')?.remove();
    const title=box.querySelector('h3');

    if(!isReady()){
      box.style.background='';
      box.style.border='';
      box.style.boxShadow='';
      box.style.borderRadius='';
      box.style.padding='';
      if(title)title.style.display='';
      return;
    }

    box.style.background='linear-gradient(145deg,#effff7,#d9f8e9)';
    box.style.border='2px solid #27b96f';
    box.style.boxShadow='0 12px 28px rgba(39,185,111,.16)';
    box.style.borderRadius='22px';
    box.style.padding='16px';
    if(title)title.style.display='none';

    const hero=document.createElement('div');
    hero.id='tcvSatispayReadyHero';
    hero.style.cssText='display:flex;align-items:center;gap:13px;margin-bottom:12px;padding:13px 14px;border-radius:18px;background:#ffffff;border:1px solid #bdebd3;';
    hero.innerHTML=`
      <div style="width:58px;height:58px;flex:0 0 58px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(145deg,#18a85f,#31c979);color:white;font-size:34px;font-weight:1000;box-shadow:0 8px 18px rgba(24,168,95,.24)">✓</div>
      <div style="min-width:0">
        <div style="font-size:10px;letter-spacing:.12em;font-weight:950;color:#087a46">COLLEGAMENTO PAGAMENTI</div>
        <div style="font-size:21px;line-height:1.05;font-weight:1000;color:#075d37;margin-top:3px">SATISPAY ABILITATO</div>
        <div style="font-size:10px;line-height:1.4;color:#42705a;margin-top:5px">Il tuo Satispay personale è pronto per essere usato nell’app.</div>
      </div>`;
    box.prepend(hero);
  }

  function wrapRenderProfile(){
    if(typeof window.renderProfile!=='function'||window.renderProfile.__tcvSatispayReadyVisual)return;
    const original=window.renderProfile;
    const wrapped=function(...args){
      const out=original.apply(this,args);
      setTimeout(decorate,0);
      return out;
    };
    wrapped.__tcvSatispayReadyVisual=true;
    window.renderProfile=wrapped;
  }

  function install(){
    wrapRenderProfile();
    decorate();
    const profile=document.getElementById('profile');
    if(profile)new MutationObserver(()=>setTimeout(decorate,20)).observe(profile,{childList:true,subtree:true});
    setInterval(()=>{wrapRenderProfile();if(!profile?.classList.contains('hidden'))decorate()},1600);
  }

  let tries=0;
  const timer=setInterval(()=>{
    tries++;
    if(typeof window.renderProfile==='function'&&document.getElementById('profile')){
      clearInterval(timer);install();
    }else if(tries>100)clearInterval(timer);
  },150);
})();
