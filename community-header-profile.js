/* TCV_COMMUNITY_HEADER_PROFILE_V2 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_HEADER_PROFILE_V2)return;
  window.TCV_COMMUNITY_HEADER_PROFILE_V2=true;

  function forceProfilePage(){
    const profile=document.getElementById('profile');

    // Se il Profilo è già aperto, non richiamare page('profile'):
    // il rerender del profilo legacy può riapparire sopra al profilo compatto.
    if(profile&&!profile.classList.contains('hidden')){
      try{
        if(typeof window.tcvRefreshCompactCommunityProfile==='function'){
          window.tcvRefreshCompactCommunityProfile();
        }
      }catch(_e){}
      return;
    }

    try{
      if(typeof window.closeSheet==='function')window.closeSheet();
    }catch(_e){}

    if(typeof window.page==='function'){
      window.page('profile');
    }else{
      const ids=['home','available','missions','myreq','mapPage','wallet','profile'];
      ids.forEach(id=>document.getElementById(id)?.classList.toggle('hidden',id!=='profile'));
      if(typeof window.renderProfile==='function')window.renderProfile();
      window.scrollTo(0,0);
    }

    // Safety net: se un altro wrapper cambia pagina subito dopo, ripristina Profilo.
    setTimeout(()=>{
      const p=document.getElementById('profile');
      if(!p||!p.classList.contains('hidden'))return;
      ['home','available','missions','myreq','mapPage','wallet','profile'].forEach(id=>{
        document.getElementById(id)?.classList.toggle('hidden',id!=='profile');
      });
      try{if(typeof window.renderProfile==='function')window.renderProfile()}catch(_e){}
      window.scrollTo(0,0);
    },40);
  }

  function onAvatarClick(e){
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    forceProfilePage();
    return false;
  }

  function wire(){
    const btn=document.getElementById('avatar');
    if(!btn)return;
    btn.title='Apri il mio profilo';
    btn.setAttribute('aria-label','Apri il mio profilo');
    btn.style.position='relative';
    btn.style.zIndex='50';
    btn.style.pointerEvents='auto';
    if(btn.__tcvHeaderProfileV2)return;
    btn.__tcvHeaderProfileV2=true;
    btn.addEventListener('click',onAvatarClick,true);
  }

  const observer=new MutationObserver(wire);
  observer.observe(document.documentElement,{childList:true,subtree:true});
  setInterval(wire,1000);
  wire();
})();
