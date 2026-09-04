/* TCV_COMMUNITY_DOCUMENTS_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_DOCUMENTS_V1)return;
  window.TCV_COMMUNITY_DOCUMENTS_V1=true;

  const BUCKET='community-documents';
  const MAX_FILE_BYTES=8*1024*1024;
  const ACCEPTED_TYPES=['image/jpeg','image/png','image/webp'];
  let CURRENT_DOC=null;

  function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function todayLocal(){const d=new Date();return new Date(d.getFullYear(),d.getMonth(),d.getDate())}
  function parseDateOnly(v){if(!v)return null;const m=String(v).match(/^(\d{4})-(\d{2})-(\d{2})$/);if(!m)return null;const d=new Date(Number(m[1]),Number(m[2])-1,Number(m[3]));return Number.isFinite(d.getTime())?d:null}
  function fmtDate(v){const d=parseDateOnly(v);return d?d.toLocaleDateString('it-IT'):'—'}
  function dateInputValue(v){return v?String(v).slice(0,10):''}
  function fiveYearsAfter(d){const x=new Date(d.getFullYear()+5,d.getMonth(),d.getDate());return x}
  function splitName(v){const p=String(v||'').trim().replace(/\s+/g,' ').split(' ').filter(Boolean);return {first:p.shift()||'',last:p.join(' ')}}
  function typeLabel(t){return t==='driving_license'?'Patente di guida':'Carta d’identità'}

  function driverEligibility(bSince,expires){
    const b=parseDateOnly(bSince),exp=parseDateOnly(expires),today=todayLocal();
    if(!b)return {ok:false,reason:'Inserisci la data di conseguimento della categoria B.'};
    if(!exp)return {ok:false,reason:'Inserisci la data di scadenza della patente.'};
    if(exp<today)return {ok:false,reason:`Patente scaduta il ${fmtDate(expires)}. Puoi continuare a usare Tanto Ci Vai come passeggero, ma non come guidatore.`};
    const eligibleOn=fiveYearsAfter(b);
    if(eligibleOn>today)return {ok:false,reason:`Per offrire passaggi servono almeno 5 anni dalla categoria B. Potrai diventare guidatore dal ${eligibleOn.toLocaleDateString('it-IT')}.`};
    return {ok:true,reason:`✓ Requisito guida superato: categoria B dal ${fmtDate(bSince)} e patente valida fino al ${fmtDate(expires)}.`};
  }
  window.tcvCommunityDriverEligibility=driverEligibility;

  async function loadState(){
    if(!window.db||!window.SESSION?.user?.id)return {profile:null,doc:null};
    const uid=SESSION.user.id;
    const [pr,dr]=await Promise.all([
      db.from('community_public_profiles').select('user_id,display_name,community_role,community_enabled,identity_verified').eq('user_id',uid).maybeSingle(),
      db.from('community_identity_documents').select('user_id,document_type,first_name,last_name,front_path,back_path,license_category,license_b_since,license_expires_on,license_expiry_reminder,submitted_at,updated_at').eq('user_id',uid).maybeSingle()
    ]);
    if(pr.error)console.warn('community document profile read',pr.error);
    if(dr.error)console.warn('community document read',dr.error);
    CURRENT_DOC=dr.data||null;
    return {profile:pr.data||null,doc:CURRENT_DOC};
  }
  window.tcvLoadCommunityDocumentState=loadState;

  function currentRole(){return document.getElementById('tcvDocRole')?.value||'passenger'}
  function selectedDocType(){return currentRole()==='driver_passenger'?'driving_license':'identity_card'}

  function setRole(role){
    const safeRole=role==='driver_passenger'?'driver_passenger':'passenger';
    const hidden=document.getElementById('tcvDocRole');if(hidden)hidden.value=safeRole;
    const p=document.getElementById('tcvDocRolePassenger'),d=document.getElementById('tcvDocRoleDriver');
    [p,d].forEach(x=>{if(x){x.classList.remove('selected');x.style.borderColor='';x.style.background=''}});
    const on=safeRole==='driver_passenger'?d:p;if(on){on.classList.add('selected');on.style.borderColor='#78a8ff';on.style.background='#eef5ff'}
    document.getElementById('tcvIdentityFields')?.classList.toggle('hidden',safeRole!=='passenger');
    document.getElementById('tcvLicenseFields')?.classList.toggle('hidden',safeRole!=='driver_passenger');
    const title=document.getElementById('tcvDocumentFilesTitle');if(title)title.textContent=safeRole==='driver_passenger'?'FOTO PATENTE':'FOTO CARTA D’IDENTITÀ';
    const hint=document.getElementById('tcvDocumentFilesHint');if(hint)hint.textContent=safeRole==='driver_passenger'?'Carica fronte e retro della patente.':'Carica fronte e retro della carta d’identità.';
    updateEligibilityPreview();
  }
  window.tcvSetCommunityDocumentRole=setRole;

  function updateEligibilityPreview(){
    const box=document.getElementById('tcvDriverEligibility');if(!box)return;
    if(currentRole()!=='driver_passenger'){box.className='notice';box.textContent='Come passeggero userai la carta d’identità per registrare la tua identità nella Community.';return}
    const res=driverEligibility(document.getElementById('tcvLicenseBSince')?.value,document.getElementById('tcvLicenseExpires')?.value);
    box.className='notice '+(res.ok?'green':'yellow');box.textContent=res.reason;
  }
  window.tcvUpdateCommunityDriverEligibility=updateEligibilityPreview;

  function fileOk(file){
    if(!file)return {ok:false,msg:'Seleziona il file.'};
    if(file.size>MAX_FILE_BYTES)return {ok:false,msg:'File troppo grande: massimo 8 MB.'};
    if(!ACCEPTED_TYPES.includes(file.type))return {ok:false,msg:'Formato non supportato. Usa JPG, PNG o WEBP.'};
    return {ok:true,msg:''}
  }

  async function uploadFile(file,path){
    const check=fileOk(file);if(!check.ok)throw new Error(check.msg);
    const {error}=await db.storage.from(BUCKET).upload(path,file,{upsert:true,contentType:file.type,cacheControl:'3600'});
    if(error)throw error;
    return path
  }

  window.tcvOpenCommunityDocumentSetup=async function(){
    if(!window.SESSION?.user?.id){alert('Accedi prima di registrare il documento.');return}
    const {profile,doc}=await loadState();
    const guessed=splitName(window.PROFILE?.nome||'');
    const first=doc?.first_name||guessed.first||'';
    const last=doc?.last_name||guessed.last||'';
    const role=profile?.community_role==='driver_passenger'?'driver_passenger':'passenger';
    const sameType=doc?.document_type===(role==='driver_passenger'?'driving_license':'identity_card');
    const existing=doc?`<div class="notice green" style="margin-top:8px"><b>✓ ${esc(typeLabel(doc.document_type))} già caricata</b><br>Le immagini restano private. Ultimo aggiornamento: ${esc(new Date(doc.updated_at||doc.submitted_at).toLocaleString('it-IT'))}.</div>`:'';
    openSheet(`${head('DOCUMENTO COMMUNITY','🪪 Registrazione sicura','Il documento serve a rendere più sicuri gli incontri della Community. Non viene mostrato agli altri utenti e non entra nel QR.')}
      <div class="notice green" style="margin:10px 0"><b>🔒 Archivio privato</b><br>Fronte e retro vengono salvati in un’area Supabase privata accessibile solo al proprietario e ai processi amministrativi autorizzati. Nessun URL pubblico.</div>
      ${existing}
      <div style="margin-top:13px"><div style="font-size:8px;font-weight:950;letter-spacing:.1em;color:#0b66ff">COME VUOI USARE TANTO CI VAI?</div>
        <input id="tcvDocRole" type="hidden" value="${esc(role)}">
        <div class="choices" style="margin-top:7px">
          <button type="button" id="tcvDocRolePassenger" class="choice" onclick="tcvSetCommunityDocumentRole('passenger')"><span class="em">🙋</span><b>Voglio chiedere passaggi</b><small>Registrazione con carta d’identità.</small></button>
          <button type="button" id="tcvDocRoleDriver" class="choice" onclick="tcvSetCommunityDocumentRole('driver_passenger')"><span class="em">🚗</span><b>Voglio anche offrire passaggi</b><small>Patente obbligatoria e almeno 5 anni dalla categoria B.</small></button>
        </div>
      </div>
      <div class="grid2"><div class="field"><label>NOME SUL DOCUMENTO</label><input id="tcvDocFirstName" maxlength="80" autocomplete="given-name" value="${esc(first)}"></div><div class="field"><label>COGNOME SUL DOCUMENTO</label><input id="tcvDocLastName" maxlength="80" autocomplete="family-name" value="${esc(last)}"></div></div>
      <div id="tcvIdentityFields"><div class="notice">Per il profilo solo passeggero registriamo la carta d’identità. I dati e le immagini non compariranno nel profilo pubblico.</div></div>
      <div id="tcvLicenseFields" class="hidden">
        <div class="field"><label>CATEGORIA USATA PER I PASSAGGI</label><input id="tcvLicenseCategory" value="B" readonly></div>
        <div class="grid2"><div class="field"><label>CATEGORIA B CONSEGUITA IL</label><input id="tcvLicenseBSince" type="date" value="${esc(dateInputValue(doc?.document_type==='driving_license'?doc.license_b_since:''))}" onchange="tcvUpdateCommunityDriverEligibility()"></div><div class="field"><label>PATENTE VALIDA FINO AL</label><input id="tcvLicenseExpires" type="date" value="${esc(dateInputValue(doc?.document_type==='driving_license'?doc.license_expires_on:''))}" onchange="tcvUpdateCommunityDriverEligibility()"></div></div>
        <div id="tcvDriverEligibility" class="notice yellow"></div>
        <label style="display:flex;gap:9px;align-items:flex-start;margin:10px 0;padding:11px;border:1px solid #dfe8f4;border-radius:14px;font-size:10px;line-height:1.45"><input id="tcvLicenseReminder" type="checkbox" style="width:20px;height:20px;margin:0" ${doc?.document_type==='driving_license'&&doc.license_expiry_reminder?'checked':''}><span><b>🔔 Ricordami quando scade la patente</b><br>Salviamo la tua scelta. I promemoria automatici 30/7/1 giorni saranno collegati al sistema notifiche nello step dedicato.</span></label>
      </div>
      <div class="field"><label id="tcvDocumentFilesTitle">FOTO DOCUMENTO</label><div id="tcvDocumentFilesHint" style="font-size:9px;color:#6c7891;margin-bottom:7px">Carica fronte e retro.</div>
        <div class="grid2"><div><label style="font-size:8px;font-weight:900">FRONTE</label><input id="tcvDocFront" type="file" accept="image/jpeg,image/png,image/webp" capture="environment"></div><div><label style="font-size:8px;font-weight:900">RETRO</label><input id="tcvDocBack" type="file" accept="image/jpeg,image/png,image/webp" capture="environment"></div></div>
        <div class="notice" style="margin-top:7px">JPG, PNG o WEBP · massimo 8 MB per immagine.${sameType?' Se il documento non è cambiato puoi lasciare vuoti i file già caricati.':''}</div>
      </div>
      <div id="tcvDocumentStatus" class="notice yellow">Documento non ancora salvato in questa sessione.</div>
      <button id="tcvDocumentSave" class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvSaveCommunityDocument()">🔒 SALVA DOCUMENTO</button>
      <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button>`);
    setTimeout(()=>setRole(role),0)
  };

  window.tcvSaveCommunityDocument=async function(){
    const st=document.getElementById('tcvDocumentStatus'),btn=document.getElementById('tcvDocumentSave');
    const uid=window.SESSION?.user?.id;if(!uid){if(st)st.textContent='Sessione scaduta.';return}
    const role=currentRole(),docType=selectedDocType();
    const first=String(document.getElementById('tcvDocFirstName')?.value||'').trim();
    const last=String(document.getElementById('tcvDocLastName')?.value||'').trim();
    if(!first||!last){if(st)st.textContent='Inserisci nome e cognome come compaiono sul documento.';return}

    let bSince=null,expires=null,reminder=false;
    if(role==='driver_passenger'){
      bSince=document.getElementById('tcvLicenseBSince')?.value||null;
      expires=document.getElementById('tcvLicenseExpires')?.value||null;
      reminder=!!document.getElementById('tcvLicenseReminder')?.checked;
      const eligible=driverEligibility(bSince,expires);
      if(!eligible.ok){if(st){st.className='notice yellow';st.textContent=eligible.reason}return}
    }

    const frontFile=document.getElementById('tcvDocFront')?.files?.[0]||null;
    const backFile=document.getElementById('tcvDocBack')?.files?.[0]||null;
    const sameType=CURRENT_DOC?.document_type===docType;
    if(!sameType&&(!frontFile||!backFile)){if(st)st.textContent=`Per registrare ${typeLabel(docType).toLowerCase()} servono fronte e retro.`;return}
    if(frontFile){const c=fileOk(frontFile);if(!c.ok){if(st)st.textContent='Fronte: '+c.msg;return}}
    if(backFile){const c=fileOk(backFile);if(!c.ok){if(st)st.textContent='Retro: '+c.msg;return}}

    if(btn)btn.disabled=true;if(st){st.className='notice';st.textContent='Salvataggio sicuro del documento…'}
    const old=CURRENT_DOC?{...CURRENT_DOC}:null;
    try{
      let frontPath=sameType?CURRENT_DOC?.front_path:null;
      let backPath=sameType?CURRENT_DOC?.back_path:null;
      if(frontFile)frontPath=await uploadFile(frontFile,`${uid}/${docType}/front`);
      if(backFile)backPath=await uploadFile(backFile,`${uid}/${docType}/back`);
      if(!frontPath||!backPath)throw new Error('Mancano fronte o retro del documento.');

      const row={
        user_id:uid,
        document_type:docType,
        first_name:first,
        last_name:last,
        front_path:frontPath,
        back_path:backPath,
        license_category:docType==='driving_license'?'B':null,
        license_b_since:docType==='driving_license'?bSince:null,
        license_expires_on:docType==='driving_license'?expires:null,
        license_expiry_reminder:docType==='driving_license'?reminder:false,
        updated_at:new Date().toISOString()
      };
      const saved=await db.from('community_identity_documents').upsert(row,{onConflict:'user_id'});
      if(saved.error)throw saved.error;
      const roleSave=await db.from('community_public_profiles').update({community_role:role}).eq('user_id',uid);
      if(roleSave.error)throw roleSave.error;

      if(old&&old.document_type!==docType){
        const stale=[old.front_path,old.back_path].filter(Boolean);
        if(stale.length){const rem=await db.storage.from(BUCKET).remove(stale);if(rem.error)console.warn('old community document cleanup',rem.error)}
      }
      const fresh=await loadState();
      if(st){st.className='notice green';st.innerHTML=`✓ <b>${esc(typeLabel(docType))} registrata.</b><br>Le immagini sono private e non sono state pubblicate.${docType==='driving_license'?'<br>✓ Requisito minimo di 5 anni e scadenza controllati.':''}`}
      setTimeout(()=>{injectProfileCard(true);wireSafetyButton()},120)
      return fresh.doc
    }catch(e){console.warn('community document save',e);if(st){st.className='notice yellow';st.textContent='Errore salvataggio documento: '+(e?.message||e)}}finally{if(btn)btn.disabled=false}
  };

  async function passengerDocumentReady(){
    const {doc}=await loadState();
    return !!(doc&&doc.front_path&&doc.back_path&&(doc.document_type==='identity_card'||doc.document_type==='driving_license'))
  }

  async function driverDocumentReady(){
    const {profile,doc}=await loadState();
    if(profile?.community_role!=='driver_passenger')return {ok:false,reason:'Per offrire passaggi scegli “Voglio anche offrire passaggi” e registra la patente.'};
    if(!doc||doc.document_type!=='driving_license'||!doc.front_path||!doc.back_path)return {ok:false,reason:'Per offrire passaggi devi prima registrare fronte e retro della patente.'};
    return driverEligibility(doc.license_b_since,doc.license_expires_on)
  }
  window.tcvCommunityPassengerDocumentReady=passengerDocumentReady;
  window.tcvCommunityDriverDocumentReady=driverDocumentReady;

  async function requirePassengerDocument(){
    if(await passengerDocumentReady())return true;
    await window.tcvOpenCommunityDocumentSetup();
    const st=document.getElementById('tcvDocumentStatus');if(st)st.textContent='Prima di richiedere un passaggio registra il tuo documento Community.';
    return false
  }
  async function requireDriverDocument(){
    const check=await driverDocumentReady();if(check.ok)return true;
    await window.tcvOpenCommunityDocumentSetup();
    const st=document.getElementById('tcvDocumentStatus');if(st){st.className='notice yellow';st.textContent=check.reason}
    return false
  }

  function installGuards(){
    if(typeof window.publishRideRequest==='function'&&!window.publishRideRequest.__tcvDocumentsV1){
      const original=window.publishRideRequest;
      const wrapped=async function(...args){if(!(await requirePassengerDocument()))return;return original.apply(this,args)};
      wrapped.__tcvDocumentsV1=true;window.publishRideRequest=wrapped;
    }
    if(typeof window.tcvSaveCommunityTrip==='function'&&!window.tcvSaveCommunityTrip.__tcvDocumentsV1){
      const original=window.tcvSaveCommunityTrip;
      const wrapped=async function(...args){if(!(await requireDriverDocument()))return;return original.apply(this,args)};
      wrapped.__tcvDocumentsV1=true;window.tcvSaveCommunityTrip=wrapped;
    }
    if(typeof window.tcvToggleCommunityTrip==='function'&&!window.tcvToggleCommunityTrip.__tcvDocumentsV1){
      const original=window.tcvToggleCommunityTrip;
      const wrapped=async function(id,on,...args){if(on&&!(await requireDriverDocument()))return;return original.call(this,id,on,...args)};
      wrapped.__tcvDocumentsV1=true;window.tcvToggleCommunityTrip=wrapped;
    }
  }

  function wireSafetyButton(){
    const sheet=document.querySelector('.sheet');if(!sheet)return;
    [...sheet.querySelectorAll('button')].forEach(btn=>{
      const text=String(btn.textContent||'').toUpperCase();
      if(text.includes('VERIFICA DOCUMENTO')||text.includes('DOCUMENTO · IN ATTIVAZIONE')){
        btn.disabled=false;btn.className='btn teal full';btn.style.marginTop='8px';btn.textContent='🪪 REGISTRA DOCUMENTO COMMUNITY';btn.onclick=()=>window.tcvOpenCommunityDocumentSetup();
      }
    })
  }

  async function injectProfileCard(force=false){
    const host=document.getElementById('profile');if(!host||host.classList.contains('hidden')||!window.SESSION?.user?.id)return;
    if(force)document.getElementById('tcvCommunityDocumentCard')?.remove();
    if(document.getElementById('tcvCommunityDocumentCard'))return;
    const {profile,doc}=await loadState();
    const card=document.createElement('section');card.id='tcvCommunityDocumentCard';card.className='req';card.style.margin='0 0 12px';
    let body='Documento non ancora registrato.';let good=false;
    if(doc){
      if(doc.document_type==='driving_license'){
        const chk=driverEligibility(doc.license_b_since,doc.license_expires_on);good=chk.ok;
        body=`Patente registrata · B dal ${esc(fmtDate(doc.license_b_since))} · scadenza ${esc(fmtDate(doc.license_expires_on))}.<br>${esc(chk.reason)}`;
      }else{good=true;body='Carta d’identità registrata. Le immagini sono conservate nell’area privata.'}
    }
    card.innerHTML=`<div style="font-size:9px;color:#0b66ff;font-weight:950;letter-spacing:.1em">DOCUMENTO COMMUNITY</div><h3 style="margin:4px 0 5px;font-size:17px">🪪 ${doc?esc(typeLabel(doc.document_type)):'Registrazione documento'}</h3><p style="font-size:9px;color:#69758d;line-height:1.5;margin:0">${body}</p><div class="notice ${doc&&good?'green':'yellow'}" style="margin-top:9px">${doc?'✓ Documento caricato in archivio privato.':'Per richiedere o offrire passaggi devi prima registrare il documento previsto per il tuo ruolo.'}</div><button class="btn ${doc?'outline':'teal'} full" style="margin-top:9px" onclick="tcvOpenCommunityDocumentSetup()">🪪 ${doc?'GESTISCI DOCUMENTO':'REGISTRA DOCUMENTO'}</button>`;
    const main=document.getElementById('tcvMainCommunityProfileCard')||document.getElementById('tcvPublicProfileCard');
    if(main)main.insertAdjacentElement('afterend',card);else{const h=host.querySelector('.pagehead');if(h)h.insertAdjacentElement('afterend',card);else host.prepend(card)}
  }

  function install(){
    installGuards();wireSafetyButton();injectProfileCard();
    const sheet=document.getElementById('sheet');if(sheet)new MutationObserver(wireSafetyButton).observe(sheet,{childList:true,subtree:true});
    const profile=document.getElementById('profile');if(profile)new MutationObserver(()=>{if(!profile.classList.contains('hidden'))setTimeout(()=>injectProfileCard(),60)}).observe(profile,{attributes:true,attributeFilter:['class'],childList:true});
    setInterval(()=>{installGuards();wireSafetyButton()},1200)
  }

  let tries=0;const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION&&typeof window.openSheet==='function'){
      clearInterval(timer);install()
    }else if(tries>100)clearInterval(timer)
  },200)
})();
