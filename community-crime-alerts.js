/* TCV_COMMUNITY_CRIME_ALERTS_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_CRIME_ALERTS_V1)return;
  window.TCV_COMMUNITY_CRIME_ALERTS_V1=true;

  function mountCrimeHazards(){
    const host=document.querySelector('.hazard-presets');
    if(!host||host.querySelector('[data-tcv-crime-hazard]'))return;

    const attempted=document.createElement('button');
    attempted.className='hazard-preset';
    attempted.type='button';
    attempted.dataset.tcvCrimeHazard='attempted-theft';
    attempted.innerHTML='🕵️<b>Tentato furto</b>';
    attempted.onclick=function(){window.tcvHazardCrimePreset('Tentato furto',attempted,false)};

    const active=document.createElement('button');
    active.className='hazard-preset';
    active.type='button';
    active.dataset.tcvCrimeHazard='theft-in-progress';
    active.innerHTML='🚨<b>Furto in corso</b>';
    active.onclick=function(){window.tcvHazardCrimePreset('Furto in corso',active,true)};

    host.append(attempted,active);
  }

  window.tcvHazardCrimePreset=function(text,btn,isActiveCrime){
    if(typeof window.tcvHazardPreset==='function')window.tcvHazardPreset(text,btn);
    const st=document.getElementById('hazardStatus');
    if(!st)return;
    if(isActiveCrime){
      st.className='notice yellow';
      st.innerHTML='<b>🚨 Furto in corso:</b> non intervenire e non avvicinarti. Se il fatto sta avvenendo adesso, chiama subito il <b>112</b>. La segnalazione in Tanto Ci Vai è un avviso Community e non sostituisce una chiamata o denuncia ufficiale.';
    }else{
      st.className='notice yellow';
      st.innerHTML='<b>🕵️ Tentato furto:</b> indica il punto e invia l’avviso alla Community. Se hai bisogno delle Forze dell’ordine, usa i canali ufficiali.';
    }
  };

  const observer=new MutationObserver(mountCrimeHazards);
  observer.observe(document.documentElement,{childList:true,subtree:true});
  setInterval(mountCrimeHazards,1200);
  mountCrimeHazards();
})();
