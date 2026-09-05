/* TCV_COMMUNITY_PROFILE_COMPACT_V2 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_PROFILE_COMPACT_V2)return;
  window.TCV_COMMUNITY_PROFILE_COMPACT_V2=true;

  let EXPANDED=false;
  let BUSY=false;
  let LAST_STATE=null;

  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function avatarHtml(p){
    const name=String(p?.display_name||window.PROFILE?.nome||'Utente').trim();
    if(p?.avatar_url)return `<img src="${esc(p.avatar_url)}" alt="Foto profilo" style="width:86px;height:86px;border-radius:50%;object-fit:cover;border:4px solid #fff;box-shadow:0 10px 26px rgba(8,117,70,.22)">`;
    const init=(name||'TC').split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase()||'TC';
    return `<div style="width:86px;height:86px;border-radius:50%;display:grid;place-items:center;background:#0b1834;color:#fff;font-size:24px;font-weight:950;border:4px solid #fff">${esc(init)}</div>`;
  }

  async function loadState(){
    if(!window.db||!window.SESSION?.user?.id)return null;
    const uid=SESSION.user.id;
    const {data,error}=await db.from('community_public_profiles')
      .select('user_id,display_name,avatar_url,community_enabled,document_registered,document_kind,community_role,profile_confirmed,completed_rides,rating_avg,rating_count')
      .eq('user_id',uid).maybeSingle();
    if(error){console.warn('compact community profile',error);return null}
    return data||null;
  }

  function isEnabled(p){
    // Community base: nome + foto + profilo attivo. Satispay e documenti non sono requisiti.
    if(!p?.community_enabled||!p?.avatar_url||!String(p?.display_name||'').trim())return false;
    // Solo chi vuole guidare deve avere una patente registrata.
    if(p?.community_role==='driver_passenger'&&(!p?.document_registered||p?.document_kind!=='driving_license'))return false;
    return true;
  }

  function badge(text){return `<span style="display:inline-flex;align-items:center;padding:6px 9px;border-radius:999px;background:#fff;border:1px solid #cceedd;color:#087348;font-size:9px;font-weight:950;white-space:nowrap">${esc(text)}</span>`}

  function stateSignature(p){
    return JSON.stringify([
      p?.display_name||'',p?.avatar_url||'',!!p?.community_enabled,!!p?.document_registered,
      p?.document_kind||'',p?.community_role||'',!!p?.profile_confirmed,Number(p?.completed_rides||0),
      Number(p?.rating_avg||0),Number(p?.rating_count||0),!!window.PROFILE?.satispay_ready,EXPANDED
    ]);
  }

  function buildCard(p,sig){
    const name=String(p?.display_name||window.PROFILE?.nome||'Utente').trim();
    const role=String(p?.community_role||'');
    const isDriver=role==='driver_passenger';
    const isPassenger=role==='passenger';
    const roleText=isDriver?'🚗 Guidatore + passeggero':isPassenger?'🙋 Passeggero':'🛡️ Membro Community';
    const documentBadge=p?.document_registered
      ?(p?.document_kind==='driving_license'?'✅ Patente registrata':'✅ Documento registrato')
      :'';
    const satispay=!!window.PROFILE?.satispay_ready;
    const confirmed=!!p?.profile_confirmed;
    const rating=Number(p?.rating_count||0)>0?Number(p.rating_avg||0).toFixed(1):'—';
    const activityText=(isDriver||isPassenger)
      ?`${roleText} · ${Number(p?.completed_rides||0)} viaggi · ⭐ ${esc(rating)}`
      :`${roleText} · SOS e mappa pericoli attivi`;
    return `
      <section id="tcvCompactCommunityProfile" data-tcv-compact-signature="${esc(sig)}" style="margin:10px 0 16px;padding:18px;border-radius:28px;background:linear-gradient(150deg,#eafff4,#f8fffb 60%,#eef8ff);border:2px solid #8ee0b9;box-shadow:0 16px 38px rgba(8,117,70,.12)">
        <div style="display:flex;gap:14px;align-items:center">
          <button type="button" onclick="tcvOpenCompactProfileManager()" style="border:0;background:transparent;padding:0;position:relative;flex:0 0 auto" aria-label="Gestisci foto profilo">
            ${avatarHtml(p)}
            <span style="position:absolute;right:-2px;bottom:-2px;width:29px;height:29px;border-radius:50%;display:grid;place-items:center;background:#0aa86b;color:#fff;border:3px solid #fff;font-size:13px">📷</span>
          </button>
          <div style="min-width:0;flex:1">
            <div style="display:inline-flex;align-items:center;gap:6px;padding:6px 9px;border-radius:999px;background:#0aa86b;color:#fff;font-size:9px;font-weight:1000;letter-spacing:.08em">✓ UTENTE COMMUNITY ABILITATO</div>
            <h2 style="margin:7px 0 2px;font-size:26px;line-height:1;letter-spacing:-.045em;color:#083b2a">${esc(name)}</h2>
            <div style="font-size:10px;color:#4e7768;font-weight:800">${activityText}</div>
          </div>
        </div>

        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:13px">
          ${documentBadge?badge(documentBadge):''}
          ${satispay?badge('✅ Satispay collegato'):''}
          ${confirmed?badge('✅ Riconosciuto dalla Community'):''}
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:15px">
          <button class="btn primary" style="min-height:72px;font-size:14px;border-radius:18px" onclick="typeof tcvOpenMyProfileQr==='function'?tcvOpenMyProfileQr():alert('QR in caricamento. Riprova tra un istante.')">🔳<br><b>IL MIO QR</b></button>
          <button class="btn outline" style="min-height:72px;font-size:14px;border-radius:18px;background:#fff" onclick="typeof tcvOpenProfileQrScanner==='function'?tcvOpenProfileQrScanner():alert('Scanner QR in caricamento. Riprova tra un istante.')">📷<br><b>SCANSIONA QR</b></button>
        </div>

        <button class="btn teal full" style="margin-top:10px;padding:13px;border-radius:16px;font-size:11px" onclick="tcvOpenCompactProfileManager()">✏️ GESTISCI PROFILO</button>
        ${EXPANDED?'<button class="btn outline full" style="margin-top:7px;padding:12px;border-radius:16px" onclick="tcvReturnToCompactProfile()">← TORNA AL PROFILO SEMPLICE</button>':''}
      </section>`;
  }

  function setHidden(el,on){
    if(!el||el.id==='tcvCompactCommunityProfile')return;
    if(on){
      if(!el.dataset.tcvCompactOldDisplay)el.dataset.tcvCompactOldDisplay=el.style.display||'__empty__';
      el.style.display='none';
      el.dataset.tcvCompactHidden='1';
    }else if(el.dataset.tcvCompactHidden==='1'){
      el.style.display=el.dataset.tcvCompactOldDisplay==='__empty__'?'':el.dataset.tcvCompactOldDisplay;
      delete el.dataset.tcvCompactHidden;
      delete el.dataset.tcvCompactOldDisplay;
    }
  }

  function applyLayout(p){
    const host=document.getElementById('profile');
    if(!host||!isEnabled(p))return;
    const sig=stateSignature(p);
    let card=document.getElementById('tcvCompactCommunityProfile');

    if(!card||card.dataset.tcvCompactSignature!==sig){
      const tmp=document.createElement('div');tmp.innerHTML=buildCard(p,sig).trim();
      const next=tmp.firstElementChild;
      if(card)card.replaceWith(next);else host.prepend(next);
      card=next;
    }

    [...host.children].forEach(el=>setHidden(el,!EXPANDED));
    card.style.display='block';
    card.style.marginBottom=EXPANDED?'12px':'16px';
  }

  async function refresh(){
    if(BUSY)return;
    const host=document.getElementById('profile');
    if(!host||host.classList.contains('hidden'))return;
    BUSY=true;
    try{
      const p=await loadState();
      LAST_STATE=p;
      if(isEnabled(p))applyLayout(p);
      else{
        document.getElementById('tcvCompactCommunityProfile')?.remove();
        [...host.children].forEach(el=>setHidden(el,false));
      }
    }finally{BUSY=false}
  }

  window.tcvOpenCompactProfileManager=function(){
    if(typeof window.openSheet!=='function')return;
    openSheet(`${head('PROFILO COMMUNITY','⚙️ Gestisci profilo','Modifica solo ciò che ti serve. Il profilo principale resta semplice e ordinato.')}
      <div style="display:grid;gap:9px;margin-top:12px">
        <button class="btn teal full" style="padding:14px" onclick="closeSheet();typeof tcvOpenCommunitySafetyProfile==='function'?tcvOpenCommunitySafetyProfile():null">📷 CAMBIA FOTO E DATI</button>
        <button class="btn outline full" style="padding:14px" onclick="closeSheet();typeof tcvOpenCommunityDocumentSetup==='function'?tcvOpenCommunityDocumentSetup():null">🪪 DOCUMENTO / PATENTE · SE SERVE</button>
        <button class="btn outline full" style="padding:14px" onclick="closeSheet();tcvShowFullProfileSettings()">⚙️ ALTRE IMPOSTAZIONI</button>
      </div>
      <div class="notice green" style="margin-top:11px"><b>Community libera da pagamenti obbligatori</b><br>SOS, mappa pericoli, segnalazioni e QR Community funzionano anche senza Satispay. Patente e pagamenti servono solo per le funzioni che li richiedono.</div>
      <button class="btn outline full" style="margin-top:9px" onclick="closeSheet()">Chiudi</button>`);
  };

  window.tcvShowFullProfileSettings=function(){
    EXPANDED=true;
    const host=document.getElementById('profile');
    if(host)[...host.children].forEach(el=>setHidden(el,false));
    if(LAST_STATE)applyLayout(LAST_STATE);else refresh();
    setTimeout(()=>document.getElementById('tcvCompactCommunityProfile')?.scrollIntoView({block:'start',behavior:'smooth'}),50);
  };

  window.tcvReturnToCompactProfile=function(){
    EXPANDED=false;
    if(LAST_STATE)applyLayout(LAST_STATE);else refresh();
    window.scrollTo({top:0,behavior:'smooth'});
  };

  function install(){
    const host=document.getElementById('profile');
    if(host)new MutationObserver(()=>setTimeout(refresh,50)).observe(host,{childList:true,subtree:false,attributes:true,attributeFilter:['class']});

    const oldPage=window.page;
    if(typeof oldPage==='function'&&!oldPage.__tcvCompactProfile){
      const wrapped=function(which,...args){
        if(which!=='profile')EXPANDED=false;
        const out=oldPage.call(this,which,...args);
        if(which==='profile')setTimeout(refresh,90);
        return out;
      };
      wrapped.__tcvCompactProfile=true;
      window.page=wrapped;
    }

    const oldRender=window.renderProfile;
    if(typeof oldRender==='function'&&!oldRender.__tcvCompactProfile){
      const wrapped=function(...args){const out=oldRender.apply(this,args);setTimeout(refresh,90);return out};
      wrapped.__tcvCompactProfile=true;
      window.renderProfile=wrapped;
    }

    setInterval(()=>{
      if(!document.getElementById('profile')?.classList.contains('hidden'))refresh();
    },2500);
    setTimeout(refresh,140);
  }

  let tries=0;
  const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION&&typeof window.page==='function'&&typeof window.renderProfile==='function'){
      clearInterval(timer);install();
    }else if(tries>100)clearInterval(timer);
  },180);
})();
