/* TCV_COMMUNITY_UI_V2 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_UI_V2)return;
  window.TCV_COMMUNITY_UI_V2=true;

  function wireHeaderProfile(){
    const btn=document.getElementById('avatar');
    if(!btn)return;
    btn.title='Apri il mio profilo';
    btn.setAttribute('aria-label','Apri il mio profilo');
    btn.onclick=()=>page('profile');
  }

  function cleanMapProfileEditor(){
    document.getElementById('tcvMapSafetyBtn')?.remove();
  }

  function install(){
    wireHeaderProfile();
    const oldRenderMap=window.renderMapPage;
    if(typeof oldRenderMap==='function'&&!oldRenderMap.__tcvUiV2){
      const wrapped=function(...args){
        const out=oldRenderMap.apply(this,args);
        setTimeout(cleanMapProfileEditor,30);
        setTimeout(cleanMapProfileEditor,120);
        return out
      };
      wrapped.__tcvUiV2=true;
      window.renderMapPage=wrapped;
    }
    const mapPage=document.getElementById('mapPage');
    if(mapPage)new MutationObserver(cleanMapProfileEditor).observe(mapPage,{childList:true,subtree:true});
    setInterval(wireHeaderProfile,1500);
  }

  let tries=0;const timer=setInterval(()=>{
    tries++;
    if(typeof window.page==='function'&&typeof window.renderMapPage==='function'){
      clearInterval(timer);install()
    }else if(tries>80)clearInterval(timer)
  },200);
})();
