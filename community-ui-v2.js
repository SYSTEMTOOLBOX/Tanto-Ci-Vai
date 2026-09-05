/* TCV_COMMUNITY_UI_V3 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_UI_V3)return;
  window.TCV_COMMUNITY_UI_V3=true;

  function loadCommunityDocumentsModule(){
    if(window.TCV_COMMUNITY_DOCUMENTS_V1||document.querySelector('script[data-tcv-community-documents]'))return;
    const s=document.createElement('script');
    s.src='./community-documents.js?v=1';
    s.async=true;
    s.dataset.tcvCommunityDocuments='1';
    document.head.appendChild(s)
  }

  function loadCommunityDocumentUiFix(){
    if(window.TCV_COMMUNITY_DOCUMENT_UI_FIX_V1||document.querySelector('script[data-tcv-community-document-ui-fix]'))return;
    const s=document.createElement('script');
    s.src='./community-document-ui-fix.js?v=1';
    s.async=true;
    s.dataset.tcvCommunityDocumentUiFix='1';
    document.head.appendChild(s)
  }

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

  function cleanProfileWallet(){
    const host=document.getElementById('profile');
    if(!host)return;
    host.querySelectorAll('.wallet-mini').forEach(el=>el.remove());
  }

  function openCommunityProfileEditor(){
    if(typeof window.tcvOpenCommunitySafetyProfile==='function'){
      window.tcvOpenCommunitySafetyProfile();
      return;
    }
    alert('Profilo Community in caricamento. Chiudi e riapri il Profilo tra un istante.');
  }
  window.tcvOpenCommunityProfileFromMainProfile=openCommunityProfileEditor;

  async function injectMainProfileCommunityCard(){
    const host=document.getElementById('profile');
    if(!host||host.classList.contains('hidden')||!window.SESSION?.user?.id)return;
    if(document.getElementById('tcvCommunityProfileMainCard')||document.getElementById('tcvMainCommunityProfileCard'))return;

    let p=null;
    try{
      if(window.db){
        const {data}=await db.from('community_public_profiles')
          .select('display_name,avatar_url,community_enabled,identity_verified,phone_verified,completed_rides,rating_avg,rating_count')
          .eq('user_id',SESSION.user.id).maybeSingle();
        p=data||null;
      }
    }catch(e){console.warn('Community profile card',e)}

    const name=String(p?.display_name||window.PROFILE?.nome||'Il tuo profilo').trim();
    const ready=!!(p?.community_enabled&&p?.avatar_url&&name);
    const initials=(name||'TC').split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase();
    const avatar=p?.avatar_url
      ?`<img src="${String(p.avatar_url).replace(/"/g,'&quot;')}" alt="Foto profilo" style="width:78px;height:78px;border-radius:50%;object-fit:cover;border:3px solid #fff;box-shadow:0 8px 22px rgba(11,24,52,.15)">`
      :`<div style="width:78px;height:78px;border-radius:50%;display:grid;place-items:center;background:#0b1834;color:#fff;font-size:22px;font-weight:950">${initials||'TC'}</div>`;

    const card=document.createElement('section');
    card.id='tcvMainCommunityProfileCard';
    card.className='req';
    card.style.margin='0 0 12px';
    card.style.border=ready?'1px solid #bfead9':'2px solid #87b8ff';
    card.style.background=ready?'linear-gradient(180deg,#f2fff9,#fff)':'linear-gradient(180deg,#eef6ff,#fff)';
    card.innerHTML=`
      <div style="display:flex;gap:13px;align-items:center">
        <div>${avatar}</div>
        <div style="min-width:0;flex:1">
          <div style="font-size:9px;color:#0b66ff;font-weight:950;letter-spacing:.1em">PROFILO COMMUNITY</div>
          <h3 style="margin:4px 0 3px;font-size:18px">${name.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</h3>
          <p style="margin:0;font-size:10px;color:#69758d;line-height:1.45">${ready?'Questo è il profilo che vedono guidatori e passeggeri.':'Qui registri chi sei e carichi la tua fotografia reale.'}</p>
        </div>
      </div>
      <div class="notice ${ready?'green':'yellow'}" style="margin-top:11px">${ready?'✓ Profilo Community attivo e visibile agli altri utenti.':'📸 Per usare i passaggi Community devi aggiungere una foto reale e attivare il profilo.'}</div>
      <button class="btn ${ready?'teal':'primary'} full" style="margin-top:10px;padding:14px;font-size:12px" onclick="tcvOpenCommunityProfileFromMainProfile()">📸 ${ready?'MODIFICA FOTO E PROFILO':'CREA PROFILO CON FOTO'}</button>
      ${ready&&typeof window.tcvOpenMyCommunityPublicProfile==='function'?'<button class="btn outline full" style="margin-top:7px" onclick="tcvOpenMyCommunityPublicProfile()">👁️ VEDI COME MI VEDONO GLI ALTRI</button>':''}
    `;
    const head=host.querySelector('.pagehead');
    if(head)head.insertAdjacentElement('afterend',card);
    else host.prepend(card);
  }

  function scheduleProfileInjection(){
    const run=()=>{cleanProfileWallet();injectMainProfileCommunityCard()};
    setTimeout(run,0);
    setTimeout(run,120);
    setTimeout(run,500);
  }

  function install(){
    loadCommunityDocumentsModule();
    loadCommunityDocumentUiFix();
    wireHeaderProfile();

    const oldPage=window.page;
    if(typeof oldPage==='function'&&!oldPage.__tcvProfileUiV3){
      const wrappedPage=function(which,...args){
        const out=oldPage.call(this,which,...args);
        if(which==='profile')scheduleProfileInjection();
        return out;
      };
      wrappedPage.__tcvProfileUiV3=true;
      window.page=wrappedPage;
    }

    const oldRenderMap=window.renderMapPage;
    if(typeof oldRenderMap==='function'&&!oldRenderMap.__tcvUiV3){
      const wrapped=function(...args){
        const out=oldRenderMap.apply(this,args);
        setTimeout(cleanMapProfileEditor,30);
        setTimeout(cleanMapProfileEditor,120);
        return out;
      };
      wrapped.__tcvUiV3=true;
      window.renderMapPage=wrapped;
    }

    const profile=document.getElementById('profile');
    if(profile)new MutationObserver(()=>{
      if(!profile.classList.contains('hidden'))scheduleProfileInjection();
    }).observe(profile,{attributes:true,attributeFilter:['class'],childList:true,subtree:false});

    const mapPage=document.getElementById('mapPage');
    if(mapPage)new MutationObserver(cleanMapProfileEditor).observe(mapPage,{childList:true,subtree:true});

    setInterval(wireHeaderProfile,1500);
    if(!document.getElementById('profile')?.classList.contains('hidden'))scheduleProfileInjection();
  }

  let tries=0;const timer=setInterval(()=>{
    tries++;
    if(typeof window.page==='function'&&typeof window.renderMapPage==='function'){
      clearInterval(timer);install()
    }else if(tries>80)clearInterval(timer)
  },200);
})();