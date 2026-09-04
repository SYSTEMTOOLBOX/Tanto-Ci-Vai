/* TCV_COMMUNITY_PROFILE_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_PROFILE_V1)return;
  window.TCV_COMMUNITY_PROFILE_V1=true;

  function escHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function firstName(v){const x=String(v||'').trim().replace(/\s+/g,' ');return x?x.split(' ')[0]:'Utente'}
  function initials(v){return firstName(v).slice(0,2).toUpperCase()||'TC'}
  function memberSince(v){
    if(!v)return '';
    try{return new Date(v).toLocaleDateString('it-IT',{month:'long',year:'numeric'})}catch(e){return ''}
  }
  function profileReady(p){return !!(p&&p.community_enabled&&p.display_name&&p.avatar_url)}
  function profileAvatar(p,size=84){
    const name=p?.display_name||'Utente';
    return p?.avatar_url
      ?`<img src="${escHtml(p.avatar_url)}" alt="Foto profilo" style="width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;border:3px solid #fff;box-shadow:0 8px 22px rgba(11,24,52,.18)">`
      :`<div style="width:${size}px;height:${size}px;border-radius:50%;display:grid;place-items:center;background:#0b1834;color:#fff;font-size:${Math.round(size*.28)}px;font-weight:950">${escHtml(initials(name))}</div>`
  }
  function verificationHtml(p){
    return `<span style="display:inline-flex;align-items:center;gap:4px;padding:6px 8px;border-radius:999px;background:${p?.identity_verified?'#eafff5':'#f5f7fb'};color:${p?.identity_verified?'#08785f':'#69758d'};font-size:9px;font-weight:900">${p?.identity_verified?'✅ Identità verificata':'🪪 Identità non verificata'}</span>
      <span style="display:inline-flex;align-items:center;gap:4px;padding:6px 8px;border-radius:999px;background:${p?.phone_verified?'#eef5ff':'#f5f7fb'};color:${p?.phone_verified?'#0b66ff':'#69758d'};font-size:9px;font-weight:900">${p?.phone_verified?'📱 Telefono verificato':'📱 Telefono non verificato'}</span>`
  }

  async function fetchProfile(userId){
    if(!window.db||!userId)return null;
    const {data,error}=await db.from('community_public_profiles')
      .select('user_id,display_name,avatar_url,community_enabled,identity_verified,phone_verified,completed_rides,rating_avg,rating_count,created_at')
      .eq('user_id',userId).maybeSingle();
    if(error){console.warn('public community profile',error);return null}
    return data||null
  }

  window.tcvOpenCommunityUserProfile=async function(userId){
    const own=String(userId||'')===String(window.SESSION?.user?.id||'');
    const p=await fetchProfile(userId);
    if(!p||(!p.community_enabled&&!own)){
      alert('Questo profilo Community non è disponibile.');
      return
    }
    const rating=Number(p.rating_count||0)>0?`${Number(p.rating_avg||0).toFixed(1)} / 5`:'Nuovo';
    const since=memberSince(p.created_at);
    openSheet(`${head('PROFILO COMMUNITY',`👤 ${escHtml(p.display_name||'Utente')}`,'Qui vedi solo le informazioni che servono per riconoscere e valutare la persona con cui viaggi.')}
      <div style="text-align:center;padding:18px 12px;border:1px solid #dfe8f4;border-radius:22px;background:linear-gradient(180deg,#f7fbff,#fff);margin:12px 0">
        <div style="display:flex;justify-content:center">${profileAvatar(p,112)}</div>
        <h2 style="margin:10px 0 4px;font-size:25px;letter-spacing:-.04em">${escHtml(p.display_name||'Utente')}</h2>
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:6px;margin-top:8px">${verificationHtml(p)}</div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-top:14px">
          <div style="padding:11px 7px;border:1px solid #e2eaf5;border-radius:14px;background:#fff"><b style="display:block;font-size:17px">${Number(p.completed_rides||0)}</b><span style="font-size:8px;color:#69758d">VIAGGI</span></div>
          <div style="padding:11px 7px;border:1px solid #e2eaf5;border-radius:14px;background:#fff"><b style="display:block;font-size:17px">${escHtml(rating)}</b><span style="font-size:8px;color:#69758d">VALUTAZIONE</span></div>
          <div style="padding:11px 7px;border:1px solid #e2eaf5;border-radius:14px;background:#fff"><b style="display:block;font-size:12px;margin-top:2px">${escHtml(since||'—')}</b><span style="font-size:8px;color:#69758d">NELLA COMMUNITY</span></div>
        </div>
      </div>
      <div class="notice green"><b>🔒 Dati privati protetti</b><br>Telefono, email, indirizzo di casa e documento d'identità non sono visibili qui.</div>
      ${own?`<button class="btn teal full" style="margin-top:10px;padding:14px" onclick="closeSheet();tcvOpenCommunitySafetyProfile()">📸 MODIFICA FOTO E PROFILO</button>`:''}
      <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button>`)
  };

  window.tcvOpenMyCommunityPublicProfile=async function(){
    const uid=window.SESSION?.user?.id;
    if(!uid)return;
    const p=await fetchProfile(uid);
    if(!p){if(typeof window.tcvOpenCommunitySafetyProfile==='function')window.tcvOpenCommunitySafetyProfile();return}
    if(!profileReady(p)){
      if(typeof window.tcvOpenCommunitySafetyProfile==='function')window.tcvOpenCommunitySafetyProfile();
      return
    }
    return window.tcvOpenCommunityUserProfile(uid)
  };

  async function refreshHeaderAvatar(){
    if(!window.SESSION?.user?.id)return;
    const p=await fetchProfile(SESSION.user.id);
    const btn=document.getElementById('avatar');if(!btn)return;
    btn.title='Apri il mio profilo';btn.setAttribute('aria-label','Apri il mio profilo');
    if(p?.avatar_url){
      btn.innerHTML=`<img src="${escHtml(p.avatar_url)}" alt="La tua foto" style="width:100%;height:100%;border-radius:50%;object-fit:cover;display:block">`;
      btn.style.padding='0';btn.style.overflow='hidden';btn.style.background='#fff';
    }else{
      btn.textContent=initials(window.PROFILE?.nome||p?.display_name||'TC');btn.style.padding='';btn.style.overflow='';btn.style.background=''
    }
  }
  window.tcvRefreshHeaderCommunityAvatar=refreshHeaderAvatar;

  async function injectOwnProfileCard(){
    const host=document.getElementById('profile');if(!host||host.classList.contains('hidden')||!window.SESSION?.user?.id)return;
    document.getElementById('tcvPublicProfileCard')?.remove();
    const p=await fetchProfile(SESSION.user.id);
    const card=document.createElement('div');card.id='tcvPublicProfileCard';card.className='req';card.style.margin='0 0 10px';
    const ready=profileReady(p);
    card.innerHTML=`<div style="display:flex;gap:12px;align-items:center">
      <div>${profileAvatar(p||{display_name:window.PROFILE?.nome},72)}</div>
      <div style="min-width:0;flex:1"><div style="font-size:9px;color:#0b66ff;font-weight:950;letter-spacing:.1em">PROFILO PUBBLICO COMMUNITY</div><h3 style="margin:4px 0 3px;font-size:17px">${escHtml(p?.display_name||firstName(window.PROFILE?.nome)||'Il tuo profilo')}</h3><p style="margin:0;font-size:9px;color:#69758d;line-height:1.45">${ready?'Gli altri utenti possono riconoscerti prima di viaggiare con te.':'Aggiungi una foto reale e attiva il profilo Community.'}</p></div>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px">${verificationHtml(p||{})}</div>
    <div class="notice ${ready?'green':'yellow'}" style="margin-top:10px">${ready?'✓ Profilo pubblico attivo.':'Profilo pubblico non ancora completo.'}</div>
    <button class="btn teal full" style="margin-top:9px" onclick="tcvOpenCommunitySafetyProfile()">📸 ${ready?'MODIFICA FOTO E DATI':'CREA PROFILO CON FOTO'}</button>
    ${ready?'<button class="btn outline full" style="margin-top:7px" onclick="tcvOpenMyCommunityPublicProfile()">👁️ VEDI COME MI VEDONO GLI ALTRI</button>':''}`;
    const headEl=host.querySelector('.pagehead');if(headEl)headEl.insertAdjacentElement('afterend',card);else host.prepend(card);
    await refreshHeaderAvatar()
  }

  function decoratePassengerCards(){
    const sheet=document.getElementById('sheet');if(!sheet)return;
    sheet.querySelectorAll('article').forEach(card=>{
      if(card.querySelector('.tcv-open-user-profile'))return;
      const block=card.querySelector('button[onclick*="tcvBlockCommunityUser"]');
      const code=block?.getAttribute('onclick')||'';
      const m=code.match(/tcvBlockCommunityUser\('([^']+)'/);if(!m)return;
      const row=block.parentElement;if(!row)return;
      const b=document.createElement('button');b.className='btn outline tcv-open-user-profile';b.textContent='👤 PROFILO';b.onclick=()=>window.tcvOpenCommunityUserProfile(m[1]);
      row.style.gridTemplateColumns='repeat(3,1fr)';row.prepend(b)
    })
  }

  function install(){
    if(window.__TCV_PUBLIC_PROFILE_INSTALLED)return;window.__TCV_PUBLIC_PROFILE_INSTALLED=true;
    if(typeof window.renderProfile==='function'){
      const original=window.renderProfile;
      window.renderProfile=function(...args){const out=original.apply(this,args);setTimeout(injectOwnProfileCard,0);return out}
    }
    const oldSave=window.tcvSaveCommunitySafetyProfile;
    if(typeof oldSave==='function')window.tcvSaveCommunitySafetyProfile=async function(...args){const out=await oldSave.apply(this,args);setTimeout(()=>{refreshHeaderAvatar();if(!document.getElementById('profile')?.classList.contains('hidden'))injectOwnProfileCard()},120);return out};
    const oldUpload=window.tcvUploadCommunitySafetyPhoto;
    if(typeof oldUpload==='function')window.tcvUploadCommunitySafetyPhoto=async function(...args){const out=await oldUpload.apply(this,args);setTimeout(refreshHeaderAvatar,120);return out};
    const sheet=document.getElementById('sheet');if(sheet)new MutationObserver(()=>decoratePassengerCards()).observe(sheet,{childList:true,subtree:true});
    setTimeout(()=>{refreshHeaderAvatar();if(!document.getElementById('profile')?.classList.contains('hidden'))injectOwnProfileCard()},100)
  }

  let tries=0;const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION&&typeof window.renderProfile==='function'&&typeof window.tcvOpenCommunitySafetyProfile==='function'){
      clearInterval(timer);install()
    }else if(tries>100)clearInterval(timer)
  },200)
})();
