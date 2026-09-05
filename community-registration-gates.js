/* TCV_COMMUNITY_REGISTRATION_GATES_V1
   Identity document required for every Community member.
   Satispay remains optional. Community-only members can use safety features but not rides.
*/
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_REGISTRATION_GATES_V1)return;
  window.TCV_COMMUNITY_REGISTRATION_GATES_V1=true;

  let cachedState=null;
  let cachedAt=0;

  async function state(force=false,userId=''){
    if(!window.db)return null;
    const uid=userId||window.SESSION?.user?.id;
    if(!uid)return null;
    if(!userId&&!force&&cachedState&&Date.now()-cachedAt<1800)return cachedState;
    const {data,error}=await db.from('community_public_profiles')
      .select('user_id,display_name,avatar_url,community_enabled,community_role,document_registered,document_kind')
      .eq('user_id',uid).maybeSingle();
    if(error){console.warn('community registration state',error);return null}
    if(!userId){cachedState=data||null;cachedAt=Date.now()}
    return data||null;
  }

  function complete(p){
    return !!(p?.community_enabled&&p?.document_registered&&p?.avatar_url&&String(p?.display_name||'').trim());
  }

  function documentRequiredSheet(){
    if(typeof window.openSheet!=='function'||typeof window.head!=='function'){
      alert('Per usare la Community registra prima un documento e una foto riconoscibile.');return;
    }
    openSheet(`${head('SICUREZZA COMMUNITY','🪪 Registrazione necessaria','Per sapere sempre chi invia un SOS, ogni membro deve avere un documento registrato e una foto del volto riconoscibile. Satispay non è obbligatorio.')}
      <div class="notice green" style="margin-top:12px"><b>Puoi partecipare anche senza Satispay</b><br>Se vuoi solo SOS, mappa pericoli e segnalazioni scegli “Solo Community e sicurezza”.</div>
      <button class="btn teal full" style="margin-top:10px" onclick="closeSheet();tcvOpenCommunityDocumentSetup()">🪪 REGISTRA DOCUMENTO</button>
      <button class="btn outline full" style="margin-top:8px" onclick="closeSheet();page('profile')">👤 VAI AL PROFILO</button>
      <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button>`);
  }

  function selectCommunityOnly(){
    const hidden=document.getElementById('tcvDocRole');if(hidden)hidden.value='community_only';
    ['tcvDocRoleCommunityOnly','tcvDocRolePassenger','tcvDocRoleDriver'].forEach(id=>{
      const el=document.getElementById(id);if(!el)return;
      const on=id==='tcvDocRoleCommunityOnly';
      el.classList.toggle('selected',on);
      el.style.borderColor=on?'#78a8ff':'';
      el.style.background=on?'#eef5ff':'';
    });
    document.getElementById('tcvIdentityFields')?.classList.remove('hidden');
    document.getElementById('tcvLicenseFields')?.classList.add('hidden');
    const title=document.getElementById('tcvDocumentFilesTitle');if(title)title.textContent='FOTO CARTA D’IDENTITÀ';
    const hint=document.getElementById('tcvDocumentFilesHint');if(hint)hint.textContent='Carica fronte e retro della carta d’identità.';
    const elig=document.getElementById('tcvDriverEligibility');if(elig){elig.className='notice';elig.textContent='Come Membro Community usi la carta d’identità. Non puoi chiedere né offrire passaggi.'}
  }
  window.tcvSetCommunityOnlyRole=selectCommunityOnly;

  async function patchDocumentSheet(){
    const p=await state(true);
    const passenger=document.getElementById('tcvDocRolePassenger');
    const driver=document.getElementById('tcvDocRoleDriver');
    const choices=passenger?.parentElement;
    if(!choices||!passenger||!driver)return;
    choices.style.gridTemplateColumns='1fr';
    if(!document.getElementById('tcvDocRoleCommunityOnly')){
      const b=document.createElement('button');
      b.type='button';b.id='tcvDocRoleCommunityOnly';b.className='choice';
      b.onclick=selectCommunityOnly;
      b.innerHTML='<span class="em">🛡️</span><b>Solo Community e sicurezza</b><small>SOS, mappa pericoli, segnalazioni e QR. Carta d’identità obbligatoria. Nessun passaggio.</small>';
      choices.prepend(b);
    }
    const heading=choices.previousElementSibling;
    if(heading&&heading.textContent?.includes('COME VUOI USARE'))heading.textContent='COME VUOI PARTECIPARE A TANTO CI VAI?';
    passenger.querySelector('small').textContent='Puoi chiedere e ricevere passaggi. Carta d’identità obbligatoria.';
    driver.querySelector('small').textContent='Puoi offrire e ricevere passaggi. Patente obbligatoria e almeno 5 anni dalla categoria B.';
    if(p?.community_role==='community_only')selectCommunityOnly();
  }

  function patchSafetySheet(p){
    const docBtn=[...document.querySelectorAll('.sheet button')].find(b=>/VERIFICA DOCUMENTO|DOCUMENTO.*ATTIVAZIONE/i.test(b.textContent||''));
    if(docBtn){
      docBtn.disabled=false;docBtn.textContent='🪪 REGISTRA / GESTISCI DOCUMENTO';
      docBtn.onclick=()=>{closeSheet();tcvOpenCommunityDocumentSetup()};
    }
    const photoStatus=document.getElementById('tcvSafetyPhotoStatus');
    if(photoStatus)photoStatus.innerHTML='<b>Foto del volto obbligatoria.</b> Il viso deve essere ben visibile e riconoscibile; niente foto a figura intera. Max 5 MB.';
    const status=document.getElementById('tcvSafetyStatus');
    if(status&&!p?.document_registered){status.className='notice yellow';status.textContent='Prima di abilitare la Community devi registrare un documento.'}
    const notices=[...document.querySelectorAll('.sheet .notice.green')];
    const privacy=notices.find(n=>/Privacy by design/i.test(n.textContent||''));
    if(privacy)privacy.innerHTML='<b>🔒 Documento privato</b><br>Il documento non viene mostrato nella Community e non entra nel QR. In pubblico mostriamo solo il badge “Documento registrato”.';
    const enabled=document.getElementById('tcvSafetyEnabled');
    const label=enabled?.parentElement?.querySelector('span');
    if(label)label.innerHTML='<b>Attiva il mio Profilo Community</b><br>Nome, foto del volto e badge di sicurezza saranno visibili nella Community. Documento, telefono ed email restano privati.';
  }

  function installWrappers(){
    const openDoc=window.tcvOpenCommunityDocumentSetup;
    if(typeof openDoc==='function'&&!openDoc.__tcvRegistrationGate){
      const wrapped=async function(...args){const out=await openDoc.apply(this,args);setTimeout(patchDocumentSheet,30);return out};
      wrapped.__tcvRegistrationGate=true;window.tcvOpenCommunityDocumentSetup=wrapped;
    }

    const saveDoc=window.tcvSaveCommunityDocument;
    if(typeof saveDoc==='function'&&!saveDoc.__tcvRegistrationGate){
      const wrapped=async function(...args){const out=await saveDoc.apply(this,args);cachedState=null;cachedAt=0;setTimeout(()=>{window.tcvRefreshCommunityRoleGate?.();window.renderProfile?.()},180);return out};
      wrapped.__tcvRegistrationGate=true;window.tcvSaveCommunityDocument=wrapped;
    }

    const openSafety=window.tcvOpenCommunitySafetyProfile;
    if(typeof openSafety==='function'&&!openSafety.__tcvRegistrationGate){
      const wrapped=async function(...args){const out=await openSafety.apply(this,args);const p=await state(true);setTimeout(()=>patchSafetySheet(p),20);return out};
      wrapped.__tcvRegistrationGate=true;window.tcvOpenCommunitySafetyProfile=wrapped;
    }

    const saveSafety=window.tcvSaveCommunitySafetyProfile;
    if(typeof saveSafety==='function'&&!saveSafety.__tcvRegistrationGate){
      const wrapped=async function(...args){
        const wantsEnabled=!!document.getElementById('tcvSafetyEnabled')?.checked;
        if(wantsEnabled){const p=await state(true);if(!p?.document_registered){const st=document.getElementById('tcvSafetyStatus');if(st){st.className='notice yellow';st.textContent='Registra prima il documento: è obbligatorio per tutti i membri della Community.'}return}}
        const out=await saveSafety.apply(this,args);cachedState=null;cachedAt=0;return out;
      };
      wrapped.__tcvRegistrationGate=true;window.tcvSaveCommunitySafetyProfile=wrapped;
    }

    const help=window.openCommunityHelp;
    if(typeof help==='function'&&!help.__tcvRegistrationGate){
      const wrapped=async function(...args){const p=await state(true);if(!complete(p)){documentRequiredSheet();return}return help.apply(this,args)};
      wrapped.__tcvRegistrationGate=true;window.openCommunityHelp=wrapped;
    }

    const myPublic=window.tcvOpenMyCommunityPublicProfile;
    if(typeof myPublic==='function'&&!myPublic.__tcvRegistrationGate){
      const wrapped=async function(...args){const p=await state(true);if(!complete(p)){documentRequiredSheet();return}return myPublic.apply(this,args)};
      wrapped.__tcvRegistrationGate=true;window.tcvOpenMyCommunityPublicProfile=wrapped;
    }

    const publicUser=window.tcvOpenCommunityUserProfile;
    if(typeof publicUser==='function'&&!publicUser.__tcvRegistrationGate){
      const wrapped=async function(userId,...args){const p=await state(true,String(userId||''));if(!p?.community_enabled||!p?.document_registered||!p?.avatar_url){alert('Questo profilo Community non è ancora abilitato.');return}return publicUser.call(this,userId,...args)};
      wrapped.__tcvRegistrationGate=true;window.tcvOpenCommunityUserProfile=wrapped;
    }
  }

  let tries=0;
  const timer=setInterval(()=>{
    tries++;installWrappers();
    if(typeof window.tcvOpenCommunityDocumentSetup==='function'&&window.tcvOpenCommunityDocumentSetup.__tcvRegistrationGate&&typeof window.openCommunityHelp==='function'&&window.openCommunityHelp.__tcvRegistrationGate){clearInterval(timer)}
    else if(tries>150)clearInterval(timer);
  },160);
})();