/* TCV_COMMUNITY_CRIME_ALERTS_V2 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_CRIME_ALERTS_V2)return;
  window.TCV_COMMUNITY_CRIME_ALERTS_V2=true;

  function mountCrimeHazards(){
    const host=document.querySelector('.hazard-presets');
    if(!host||host.querySelector('[data-tcv-crime-hazard]'))return;

    const attempted=document.createElement('button');
    attempted.className='hazard-preset';
    attempted.type='button';
    attempted.dataset.tcvCrimeHazard='attempted-theft';
    attempted.innerHTML='🕵️<b>Tentato furto / persone sospette</b>';
    attempted.onclick=function(){window.tcvHazardCrimePreset('Tentato furto / persone non autorizzate',attempted,false)};

    const active=document.createElement('button');
    active.className='hazard-preset';
    active.type='button';
    active.dataset.tcvCrimeHazard='theft-in-progress';
    active.innerHTML='🚨<b>Furto in corso</b>';
    active.onclick=function(){window.tcvHazardCrimePreset('Furto in corso',active,true)};

    host.append(attempted,active);
  }

  function mountCrimeSosPreset(){
    const host=document.querySelector('.sos-presets');
    if(!host||host.querySelector('[data-tcv-crime-sos]'))return;

    const btn=document.createElement('button');
    btn.className='sos-preset';
    btn.type='button';
    btn.dataset.tcvCrimeSos='intruders';
    btn.innerHTML='🚨<b>Ladri / intrusi</b>';
    btn.onclick=function(){window.tcvSosCrimePreset(btn)};
    host.appendChild(btn);
  }

  window.tcvHazardCrimePreset=function(text,btn,isActiveCrime){
    if(typeof window.tcvHazardPreset==='function')window.tcvHazardPreset(text,btn);
    const st=document.getElementById('hazardStatus');
    if(!st)return;
    st.className='notice yellow';
    if(isActiveCrime){
      st.innerHTML='<b>🚨 Furto in corso:</b> se sei un vicino o un testimone, metti il pin <b>sulla casa o sul luogo dove sta avvenendo il fatto</b>, non sulla tua posizione. Non intervenire e non avvicinarti: chiama subito il <b>112</b>. La segnalazione in Tanto Ci Vai è un avviso Community e non sostituisce una chiamata o denuncia ufficiale.';
    }else{
      st.innerHTML='<b>🕵️ Tentato furto / persone sospette:</b> metti il pin <b>sulla casa o sul luogo interessato</b>. Questa segnalazione serve ad avvisare la Community; se ritieni che sia in corso un reato o ci sia pericolo, chiama il <b>112</b>.';
    }
  };

  window.tcvSosCrimePreset=function(btn){
    const text='Ci sono ladri / intrusi in casa';
    const st=document.getElementById('sosStatus');
    if(st){
      st.className='notice yellow';
      st.innerHTML='<b>🚨 Ladri / intrusi:</b> l’SOS viene inviato subito dalla tua posizione. Non affrontare le persone presenti. Se puoi farlo in sicurezza, chiama anche il <b>112</b>.';
    }
    if(typeof window.tcvSosPreset==='function')window.tcvSosPreset(text,btn);
  };

  function mount(){
    mountCrimeHazards();
    mountCrimeSosPreset();
  }

  const observer=new MutationObserver(mount);
  observer.observe(document.documentElement,{childList:true,subtree:true});
  setInterval(mount,1200);
  mount();
})();
