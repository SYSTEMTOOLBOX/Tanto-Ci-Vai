/* TCV_COMMUNITY_ACCOUNT_CONFIRMATION_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_ACCOUNT_CONFIRMATION_V1)return;
  window.TCV_COMMUNITY_ACCOUNT_CONFIRMATION_V1=true;

  let INJECTING=false;
  let LAST_PROFILE_USER='';

  async function publicState(userId){
    if(!window.db||!userId)return {confirmed:false};
    const {data,error}=await db.from('community_public_profiles')
      .select('account_confirmed,account_confirmed_at')
      .eq('user_id',userId).maybeSingle();
    if(error)throw error;
    return {confirmed:!!data?.account_confirmed,confirmedAt:data?.account_confirmed_at||null};
  }

  function decorateAccountBadge(root,confirmed){
    if(!root)return;
    const candidates=[...root.querySelectorAll('span,div')];
    for(const el of candidates){
      const t=String(el.textContent||'').trim();
      if(t==='📱 Telefono verificato'||t==='📱 Telefono non verificato'||t==='✅ Account confermato'||t==='Account non confermato'){
        el.textContent=confirmed?'✅ Account confermato':'Account non confermato';
        el.style.background=confirmed?'#eafff5':'#f5f7fb';
        el.style.color=confirmed?'#08785f':'#69758d';
      }
    }
  }

  async function decorateOwnProfile(){
    const uid=window.SESSION?.user?.id;if(!uid)return;
    try{const s=await publicState(uid);decorateAccountBadge(document.getElementById('profile'),s.confirmed)}catch(e){console.warn('account badge',e)}
  }

  async function edgeErrorDetail(error){
    let detail=String(error?.message||error||'Errore Edge Function');
    const ctx=error?.context;
    if(!ctx)return detail;
    try{
      const response=typeof ctx.clone==='function'?ctx.clone():ctx;
      if(typeof response.text==='function'){
        const text=await response.text();
        if(text){
          try{
            const payload=JSON.parse(text);
            detail=String(payload?.error||payload?.message||text);
          }catch(_){detail=String(text)}
        }
      }
    }catch(_){ }
    return detail.slice(0,300);
  }

  async function invoke(action){
    const {data:{session},error:sessionError}=await db.auth.getSession();
    if(sessionError||!session?.access_token)throw new Error('Sessione scaduta. Chiudi e riapri Tanto Ci Vai.');

    let result;
    try{
      result=await db.functions.invoke('satispay-account',{body:{action}});
    }catch(e){
      throw new Error('Connessione al servizio Satispay non riuscita: '+String(e?.message||e));
    }

    const data=result?.data;
    const error=result?.error;
    if(error){
      const detail=await edgeErrorDetail(error);
      throw new Error(detail);
    }
    if(data?.error)throw new Error(String(data.error));
    return data||{};
  }

  window.tcvOpenAccountConfirmation=async function(){
    if(!window.SESSION?.user?.id)return;
    let state={confirmed:false};
    try{state=await publicState(SESSION.user.id)}catch(e){}
    if(state.confirmed){alert('✅ Il tuo account è già confermato con Satispay.');return}
    openSheet(`${head('SICUREZZA COMMUNITY','✅ Conferma account','Conferma il tuo account tramite Satispay. Il tuo numero di telefono resta privato e non viene mostrato alla Community.')}
      <div class="notice green" style="margin-top:10px"><b>Cosa vedranno gli altri?</b><br>Solo il badge “Account confermato”. Nessun numero di telefono, email o dato Satispay viene pubblicato.</div>
      <div id="tcvAccountConfirmStatus" class="notice" style="margin-top:10px">Premi il pulsante e completa la conferma nell’app o nella pagina Satispay.</div>
      <button id="tcvAccountConfirmBtn" class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvStartAccountConfirmation()">❤️ CONFERMA CON SATISPAY</button>
      <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button>`);
  };

  window.tcvStartAccountConfirmation=async function(){
    const st=document.getElementById('tcvAccountConfirmStatus'),btn=document.getElementById('tcvAccountConfirmBtn');
    if(btn){btn.disabled=true;btn.textContent='Apro Satispay…'}
    if(st)st.textContent='Creo la conferma sicura con Satispay…';
    try{
      const data=await invoke('create');
      if(data.confirmed){if(st)st.innerHTML='✅ <b>Account già confermato.</b>';setTimeout(()=>{closeSheet();renderProfile?.()},600);return}
      if(!data.redirect_url)throw new Error('Satispay non ha restituito il link di conferma.');
      try{localStorage.setItem('tcv_satispay_account_pending','1')}catch(e){}
      window.location.assign(String(data.redirect_url));
    }catch(e){
      console.warn('Satispay account create',e);
      if(st){st.className='notice yellow';st.textContent='Non riesco ad aprire la conferma Satispay: '+(e?.message||e)}
      if(btn){btn.disabled=false;btn.textContent='❤️ RIPROVA CON SATISPAY'}
    }
  };

  async function refreshAfterReturn(){
    if(!window.SESSION?.user?.id)return;
    try{
      const data=await invoke('status');
      try{localStorage.removeItem('tcv_satispay_account_pending')}catch(e){}
      try{history.replaceState({},document.title,location.pathname+location.hash)}catch(e){}
      if(typeof window.renderProfile==='function')window.renderProfile();
      setTimeout(decorateOwnProfile,120);
      if(data.confirmed)openSheet(`${head('SICUREZZA COMMUNITY','✅ Account confermato','La conferma Satispay è riuscita.')}
        <div class="notice green" style="margin-top:10px"><b>Account confermato.</b><br>Nel profilo pubblico compare solo il badge. Il tuo numero di telefono resta privato.</div>
        <button class="btn teal full" style="margin-top:10px" onclick="closeSheet();page('profile')">VAI AL PROFILO</button>`);
      else openSheet(`${head('SICUREZZA COMMUNITY','⏳ Conferma in attesa','Satispay non ha ancora confermato l’operazione.')}
        <div class="notice yellow" style="margin-top:10px">Puoi riprovare la conferma dal Profilo.</div>
        <button class="btn outline full" style="margin-top:10px" onclick="closeSheet();page('profile')">TORNA AL PROFILO</button>`);
    }catch(e){console.warn('Satispay account status',e)}
  }

  async function injectButton(){
    if(INJECTING)return;
    const card=document.getElementById('tcvPublicProfileCard');
    const uid=window.SESSION?.user?.id;
    if(!card||!uid)return;
    INJECTING=true;
    try{
      const s=await publicState(uid);
      decorateAccountBadge(card,s.confirmed);
      document.getElementById('tcvPhoneVerifyAction')?.remove();
      let wrap=document.getElementById('tcvAccountConfirmAction');
      if(s.confirmed){wrap?.remove();return}
      if(!wrap){
        wrap=document.createElement('div');wrap.id='tcvAccountConfirmAction';wrap.style.marginTop='8px';
        wrap.innerHTML='<button class="btn outline full" style="padding:12px" onclick="tcvOpenAccountConfirmation()">✅ CONFERMA ACCOUNT CON SATISPAY</button>';
        card.appendChild(wrap);
      }
    }catch(e){console.warn('account confirm button',e)}finally{INJECTING=false}
  }

  function wrapPublicProfile(){
    if(typeof window.tcvOpenCommunityUserProfile!=='function'||window.tcvOpenCommunityUserProfile.__tcvAccountConfirm)return;
    const original=window.tcvOpenCommunityUserProfile;
    const wrapped=async function(userId,...args){
      LAST_PROFILE_USER=String(userId||'');
      const out=await original.call(this,userId,...args);
      try{const s=await publicState(userId);setTimeout(()=>decorateAccountBadge(document.getElementById('sheet'),s.confirmed),30);setTimeout(()=>decorateAccountBadge(document.getElementById('sheet'),s.confirmed),160)}catch(e){}
      return out;
    };
    wrapped.__tcvAccountConfirm=true;
    window.tcvOpenCommunityUserProfile=wrapped;
  }

  function install(){
    wrapPublicProfile();decorateOwnProfile();injectButton();
    const profile=document.getElementById('profile');
    if(profile)new MutationObserver(()=>{if(!profile.classList.contains('hidden')){setTimeout(decorateOwnProfile,30);setTimeout(injectButton,80)}}).observe(profile,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
    const sheet=document.getElementById('sheet');
    if(sheet)new MutationObserver(()=>{if(LAST_PROFILE_USER)publicState(LAST_PROFILE_USER).then(s=>decorateAccountBadge(sheet,s.confirmed)).catch(()=>{});wrapPublicProfile()}).observe(sheet,{childList:true,subtree:true});
    setInterval(()=>{if(!profile?.classList.contains('hidden'))injectButton();wrapPublicProfile()},1800);

    const q=new URLSearchParams(location.search);
    let pending=false;try{pending=localStorage.getItem('tcv_satispay_account_pending')==='1'}catch(e){}
    if(q.get('satispay')==='account-return'||pending)setTimeout(refreshAfterReturn,350);
  }

  let tries=0;const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION&&typeof window.openSheet==='function'){
      clearInterval(timer);install();
    }else if(tries>100)clearInterval(timer)
  },200);
})();
