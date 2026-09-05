/* TCV_COMMUNITY_PUBLIC_PROFILE_READONLY_V1
   Public Community profiles opened from the map/people views are read-only.
   Editing remains available only from the signed-in user's private Profile page.
*/
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_PUBLIC_PROFILE_READONLY_V1)return;
  window.TCV_COMMUNITY_PUBLIC_PROFILE_READONLY_V1=true;

  function cleanPublicProfileSheet(){
    const sheet=document.getElementById('sheet')||document.querySelector('.sheet');
    if(!sheet)return;
    const text=String(sheet.textContent||'');
    if(!text.includes('PROFILO COMMUNITY')||!text.includes('Dati privati protetti'))return;

    [...sheet.querySelectorAll('button')].forEach(btn=>{
      const label=String(btn.textContent||'').trim().toUpperCase();
      if(label.includes('MODIFICA FOTO E PROFILO')||label.includes('MODIFICA FOTO E DATI')||label.includes('CREA PROFILO CON FOTO')){
        btn.remove();
      }
    });
  }

  function install(){
    const fn=window.tcvOpenCommunityUserProfile;
    if(typeof fn!=='function'||fn.__tcvPublicProfileReadonly)return false;

    const wrapped=async function(...args){
      const out=await fn.apply(this,args);
      cleanPublicProfileSheet();
      setTimeout(cleanPublicProfileSheet,30);
      setTimeout(cleanPublicProfileSheet,180);
      return out;
    };
    wrapped.__tcvPublicProfileReadonly=true;
    // Preserve markers from wrappers that may already be installed.
    if(fn.__tcvDriverExperience)wrapped.__tcvDriverExperience=true;
    if(fn.__tcvDocumentBadgeFix)wrapped.__tcvDocumentBadgeFix=true;
    if(fn.__tcvRegistrationGate)wrapped.__tcvRegistrationGate=true;
    window.tcvOpenCommunityUserProfile=wrapped;
    return true;
  }

  let tries=0;
  const timer=setInterval(()=>{
    tries++;
    if(install())clearInterval(timer);
    else if(tries>120)clearInterval(timer);
  },150);

  const sheet=document.getElementById('sheet');
  if(sheet)new MutationObserver(()=>setTimeout(cleanPublicProfileSheet,0)).observe(sheet,{childList:true,subtree:true});
})();
