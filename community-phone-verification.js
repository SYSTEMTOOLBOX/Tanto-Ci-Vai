/* TCV_COMMUNITY_PHONE_VERIFICATION_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_PHONE_VERIFICATION_V1)return;
  window.TCV_COMMUNITY_PHONE_VERIFICATION_V1=true;

  let PENDING_PHONE='';
  let INJECTING=false;

  function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}

  function normalizePhone(raw){
    let s=String(raw||'').trim().replace(/[\s().-]/g,'');
    if(s.startsWith('00'))s='+'+s.slice(2);
    if(s.startsWith('+'))return /^\+[1-9]\d{7,14}$/.test(s)?s:'';
    s=s.replace(/\D/g,'');
    if(!s)return '';
    if(s.startsWith('39')&&s.length>=10)return '+'+s;
    return /^\d{8,13}$/.test(s)?'+39'+s:'';
  }
  window.tcvNormalizeCommunityPhone=normalizePhone;

  async function readState(){
    const uid=window.SESSION?.user?.id;
    if(!uid||!window.db)return {verified:false,profilePhone:'',authPhone:''};
    const [authRes,profileRes]=await Promise.all([
      db.auth.getUser(),
      db.from('profiles').select('telefono').eq('id',uid).maybeSingle()
    ]);
    if(authRes.error)throw authRes.error;
    const user=authRes.data?.user||null;
    const profilePhone=normalizePhone(profileRes.data?.telefono||window.PROFILE?.telefono||'');
    const authPhone=normalizePhone(user?.phone||'');
    const verified=!!(user?.phone_confirmed_at&&profilePhone&&authPhone&&profilePhone===authPhone);
    return {verified,profilePhone,authPhone,user};
  }

  async function syncPublicBadge(){
    const uid=window.SESSION?.user?.id;if(!uid)return false;
    const state=await readState();
    const upd=await db.from('community_public_profiles').update({phone_verified:state.verified}).eq('user_id',uid);
    if(upd.error)throw upd.error;
    return state.verified;
  }
  window.tcvSyncCommunityPhoneBadge=syncPublicBadge;

  function friendlyError(e){
    const msg=String(e?.message||e||'Errore sconosciuto');
    const low=msg.toLowerCase();
    if(low.includes('phone provider')||low.includes('sms provider')||low.includes('unsupported provider')||low.includes('sms not configured')){
      return 'L’invio SMS non è ancora configurato su Supabase. Va attivato Phone Auth e collegato un provider SMS.';
    }
    if(low.includes('rate limit'))return 'Hai richiesto troppi codici in poco tempo. Aspetta un minuto e riprova.';
    if(low.includes('invalid')&&low.includes('phone'))return 'Numero di telefono non valido. Inseriscilo con prefisso internazionale, ad esempio +39.';
    if(low.includes('token')||low.includes('otp'))return 'Codice non valido o scaduto. Controlla le 6 cifre oppure richiedi un nuovo SMS.';
    return msg;
  }

  window.tcvOpenPhoneVerification=async function(){
    if(!window.SESSION?.user?.id)return;
    let state={verified:false,profilePhone:normalizePhone(window.PROFILE?.telefono||'')};
    try{state=await readState()}catch(e){console.warn('phone state',e)}
    if(state.verified){
      try{await syncPublicBadge()}catch(e){}
      alert('✓ Questo numero di telefono è già verificato.');
      return;
    }
    const initial=state.profilePhone||'';
    openSheet(`${head('SICUREZZA COMMUNITY','📱 Verifica telefono','Ti inviamo un codice SMS per confermare che il numero appartiene davvero a te.')}
      <div class="notice green" style="margin-top:10px"><b>Perché serve?</b><br>Il numero non viene mostrato pubblicamente. Sul profilo comparirà soltanto “Telefono verificato”.</div>
      <div class="field"><label>NUMERO DI TELEFONO</label><input id="tcvPhoneVerifyNumber" inputmode="tel" autocomplete="tel" value="${esc(initial)}" placeholder="+39 333 1234567"></div>
      <div id="tcvPhoneSendStatus" class="notice">Inserisci il numero e premi INVIA CODICE.</div>
      <button id="tcvPhoneSendBtn" class="btn primary full" style="margin-top:9px;padding:14px" onclick="tcvSendPhoneOtp()">📩 INVIA CODICE SMS</button>
      <div id="tcvPhoneOtpStep" class="hidden" style="margin-top:12px">
        <div class="field"><label>CODICE SMS A 6 CIFRE</label><input id="tcvPhoneOtpCode" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="123456"></div>
        <div id="tcvPhoneOtpStatus" class="notice yellow">Inserisci il codice ricevuto via SMS.</div>
        <button id="tcvPhoneVerifyBtn" class="btn teal full" style="margin-top:9px;padding:14px" onclick="tcvVerifyPhoneOtp()">✅ VERIFICA NUMERO</button>
      </div>
      <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button>`);
  };

  window.tcvSendPhoneOtp=async function(){
    const input=document.getElementById('tcvPhoneVerifyNumber');
    const st=document.getElementById('tcvPhoneSendStatus');
    const btn=document.getElementById('tcvPhoneSendBtn');
    const phone=normalizePhone(input?.value||'');
    if(!phone){if(st){st.className='notice yellow';st.textContent='Inserisci un numero valido. Per l’Italia puoi scrivere 333… oppure +39 333…'}return}
    PENDING_PHONE=phone;
    if(input)input.value=phone;
    if(btn){btn.disabled=true;btn.textContent='Invio SMS…'}
    if(st){st.className='notice';st.textContent='Invio del codice in corso…'}
    try{
      const {error}=await db.auth.updateUser({phone});
      if(error)throw error;
      if(st){st.className='notice green';st.innerHTML='✓ Codice inviato a <b>'+esc(phone)+'</b>. Controlla gli SMS.'}
      document.getElementById('tcvPhoneOtpStep')?.classList.remove('hidden');
      setTimeout(()=>document.getElementById('tcvPhoneOtpCode')?.focus(),80);
    }catch(e){
      console.warn('send phone otp',e);
      if(st){st.className='notice yellow';st.textContent=friendlyError(e)}
    }finally{
      if(btn){btn.disabled=false;btn.textContent='📩 INVIA / REINVIA CODICE SMS'}
    }
  };

  window.tcvVerifyPhoneOtp=async function(){
    const token=String(document.getElementById('tcvPhoneOtpCode')?.value||'').replace(/\D/g,'').slice(0,6);
    const st=document.getElementById('tcvPhoneOtpStatus');
    const btn=document.getElementById('tcvPhoneVerifyBtn');
    const phone=PENDING_PHONE||normalizePhone(document.getElementById('tcvPhoneVerifyNumber')?.value||'');
    if(!phone){if(st)st.textContent='Numero non valido.';return}
    if(!/^\d{6}$/.test(token)){if(st)st.textContent='Inserisci tutte e 6 le cifre del codice SMS.';return}
    if(btn){btn.disabled=true;btn.textContent='Verifico…'}
    if(st){st.className='notice';st.textContent='Controllo del codice in corso…'}
    try{
      const {error}=await db.auth.verifyOtp({phone,token,type:'phone_change'});
      if(error)throw error;

      const uid=window.SESSION?.user?.id;
      const saved=await db.from('profiles').update({telefono:phone}).eq('id',uid);
      if(saved.error)throw saved.error;
      if(window.PROFILE)window.PROFILE.telefono=phone;

      await syncPublicBadge();
      const proof=await db.from('community_public_profiles').select('phone_verified').eq('user_id',uid).maybeSingle();
      if(proof.error)throw proof.error;
      if(!proof.data?.phone_verified)throw new Error('Il numero è stato confermato da Auth, ma il badge non si è ancora sincronizzato. Riprova tra un istante.');

      if(st){st.className='notice green';st.innerHTML='✅ <b>Telefono verificato.</b> Il badge Community è ora attivo.'}
      setTimeout(()=>{
        try{closeSheet()}catch(e){}
        if(typeof window.renderProfile==='function')window.renderProfile();
      },700);
    }catch(e){
      console.warn('verify phone otp',e);
      if(st){st.className='notice yellow';st.textContent=friendlyError(e)}
    }finally{
      if(btn){btn.disabled=false;btn.textContent='✅ VERIFICA NUMERO'}
    }
  };

  async function injectButton(){
    if(INJECTING)return;
    const card=document.getElementById('tcvPublicProfileCard');
    const uid=window.SESSION?.user?.id;
    if(!card||!uid)return;
    INJECTING=true;
    try{
      let verified=false;
      try{verified=await syncPublicBadge()}catch(e){console.warn('phone badge sync',e)}
      const old=document.getElementById('tcvPhoneVerifyAction');
      if(verified){old?.remove();return}
      if(old)return;
      const wrap=document.createElement('div');
      wrap.id='tcvPhoneVerifyAction';
      wrap.style.marginTop='8px';
      wrap.innerHTML='<button class="btn outline full" style="padding:12px" onclick="tcvOpenPhoneVerification()">📱 VERIFICA TELEFONO</button>';
      const qr=document.getElementById('tcvQrProfileActions');
      if(qr&&qr.parentElement===card)qr.insertAdjacentElement('beforebegin',wrap);else card.appendChild(wrap);
    }finally{INJECTING=false}
  }

  function install(){
    const profile=document.getElementById('profile');
    if(profile)new MutationObserver(()=>{
      if(!profile.classList.contains('hidden'))setTimeout(injectButton,80);
    }).observe(profile,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
    setInterval(()=>{if(!profile?.classList.contains('hidden'))injectButton()},1800);
    setTimeout(injectButton,200);
  }

  let tries=0;const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION&&typeof window.openSheet==='function'){
      clearInterval(timer);install();
    }else if(tries>100)clearInterval(timer)
  },200);
})();