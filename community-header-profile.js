/* TCV_COMMUNITY_HEADER_PROFILE_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_HEADER_PROFILE_V1)return;
  window.TCV_COMMUNITY_HEADER_PROFILE_V1=true;

  function forceProfilePage(){
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

    // Safety net: if another runtime wrapper changed page immediately, restore Profile.
    setTimeout(()=>{
      const profile=document.getElementById('profile');
      if(!profile||!profile.classList.contains('hidden'))return;
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
    if(btn.__tcvHeaderProfileV1)return;
    btn.__tcvHeaderProfileV1=true;
    btn.addEventListener('click',onAvatarClick,true);
  }

  const observer=new MutationObserver(wire);
  observer.observe(document.documentElement,{childList:true,subtree:true});
  setInterval(wire,1000);
  wire();
})();
