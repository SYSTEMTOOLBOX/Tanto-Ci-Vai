/* TCV_COMMUNITY_QR_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_QR_V1)return;
  window.TCV_COMMUNITY_QR_V1=true;

  let QR_STREAM=null;
  let QR_TIMER=null;
  let SCANNED_TOKEN='';
  let PUBLIC_PROFILE_WRAPPED=false;
  let CLOSE_WRAPPED=false;

  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));

  function profileImage(p,size=96){
    const name=String(p?.display_name||'Utente').trim();
    if(p?.avatar_url)return `<img src="${esc(p.avatar_url)}" alt="Foto profilo" style="width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;border:3px solid #fff;box-shadow:0 8px 24px rgba(11,24,52,.18)">`;
    const init=(name||'TC').slice(0,2).toUpperCase();
    return `<div style="width:${size}px;height:${size}px;border-radius:50%;display:grid;place-items:center;background:#071a3d;color:#fff;font-size:${Math.round(size*.28)}px;font-weight:950">${esc(init)}</div>`;
  }

  function stopScanner(){
    if(QR_TIMER){clearTimeout(QR_TIMER);QR_TIMER=null}
    if(QR_STREAM){
      try{QR_STREAM.getTracks().forEach(t=>t.stop())}catch(e){}
      QR_STREAM=null;
    }
    const video=document.getElementById('tcvQrVideo');
    if(video)try{video.srcObject=null}catch(e){}
  }

  function parseQrToken(raw){
    const text=String(raw||'').trim();
    if(text.startsWith('TCV1:'))return text.slice(5).trim();
    try{
      const u=new URL(text,location.href);
      return String(u.searchParams.get('tcvqr')||'').trim();
    }catch(e){return ''}
  }

  async function loadConfirmation(userId){
    if(!window.db||!userId)return null;
    const {data,error}=await db.from('community_public_profiles')
      .select('user_id,profile_confirmed,profile_confirmation_count,profile_confirmed_at')
      .eq('user_id',userId).maybeSingle();
    if(error){console.warn('community qr confirmation',error);return null}
    return data||null;
  }

  function confirmationBadge(p){
    const count=Number(p?.profile_confirmation_count||0);
    if(p?.profile_confirmed){
      return `<div style="display:inline-flex;align-items:center;gap:6px;padding:8px 10px;border-radius:999px;background:#eafff5;color:#08785f;font-size:10px;font-weight:950">✅ Profilo confermato dalla Community${count?` · ${count}`:''}</div>`;
    }
    return `<div style="display:inline-flex;align-items:center;gap:6px;padding:8px 10px;border-radius:999px;background:#fff8e8;color:#795d1c;font-size:10px;font-weight:950">🔳 Profilo non ancora confermato</div>`;
  }

  async function decorateOwnProfileCard(){
    const card=document.getElementById('tcvPublicProfileCard');
    if(!card||card.querySelector('#tcvQrProfileActions')||!window.SESSION?.user?.id)return;
    const p=await loadConfirmation(SESSION.user.id);
    const box=document.createElement('div');
    box.id='tcvQrProfileActions';
    box.style.marginTop='10px';
    box.innerHTML=`<div id="tcvQrOwnBadge" style="margin-bottom:8px">${confirmationBadge(p||{})}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
        <button class="btn primary" onclick="tcvOpenMyProfileQr()">🔳 IL MIO QR</button>
        <button class="btn outline" onclick="tcvOpenProfileQrScanner()">📷 SCANSIONA QR</button>
      </div>
      <div class="notice" style="margin-top:8px">Nessun documento viene caricato: il QR serve solo a confermare dal vivo che la persona davanti a te corrisponde al profilo.</div>`;
    card.appendChild(box);
  }

  async function decoratePublicProfile(userId){
    if(!userId||!window.db)return;
    const p=await loadConfirmation(userId);
    if(!p)return;
    setTimeout(()=>{
      const sheet=document.getElementById('sheet');
      if(!sheet||sheet.classList.contains('hidden'))return;
      document.getElementById('tcvQrPublicBadge')?.remove();
      const host=sheet.querySelector('#sc')||sheet;
      const badge=document.createElement('div');
      badge.id='tcvQrPublicBadge';
      badge.style.cssText='display:flex;justify-content:center;margin:10px 0 4px';
      badge.innerHTML=confirmationBadge(p);
      const firstNotice=host.querySelector('.notice');
      if(firstNotice)firstNotice.insertAdjacentElement('beforebegin',badge);else host.appendChild(badge);
    },0);
  }

  function replaceDocumentPlaceholder(){
    const sheet=document.getElementById('sheet');
    if(!sheet||sheet.classList.contains('hidden'))return;
    const buttons=[...sheet.querySelectorAll('button')];
    const old=buttons.find(b=>/VERIFICA DOCUMENTO/i.test(b.textContent||''));
    if(!old||document.getElementById('tcvQrSafetyActions'))return;
    const wrap=document.createElement('div');
    wrap.id='tcvQrSafetyActions';
    wrap.innerHTML=`<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">
        <button class="btn primary" onclick="tcvOpenMyProfileQr()">🔳 IL MIO QR</button>
        <button class="btn outline" onclick="tcvOpenProfileQrScanner()">📷 SCANSIONA QR</button>
      </div>
      <div class="notice green" style="margin-top:8px"><b>Conferma profilo gratuita</b><br>Il QR dura 10 minuti e non contiene documento, telefono o indirizzo. Un altro utente vede foto e nome, poi conferma dal vivo.</div>`;
    old.replaceWith(wrap);
  }

  function bindProfileWrapper(){
    if(PUBLIC_PROFILE_WRAPPED||typeof window.tcvOpenCommunityUserProfile!=='function')return;
    PUBLIC_PROFILE_WRAPPED=true;
    const original=window.tcvOpenCommunityUserProfile;
    window.tcvOpenCommunityUserProfile=async function(userId){
      const out=await original.apply(this,arguments);
      decoratePublicProfile(userId);
      return out;
    };
  }

  function bindCloseWrapper(){
    if(CLOSE_WRAPPED||typeof window.closeSheet!=='function')return;
    CLOSE_WRAPPED=true;
    const original=window.closeSheet;
    window.closeSheet=function(){stopScanner();return original.apply(this,arguments)};
  }

  function qrBaseUrl(){
    const u=new URL(location.href);
    u.search='';u.hash='';
    return u.toString();
  }

  window.tcvOpenMyProfileQr=async function(){
    stopScanner();
    if(!window.db||!window.SESSION?.user?.id){alert('Accedi prima al tuo profilo.');return}
    openSheet(`${head('PROFILO COMMUNITY','🔳 Il mio QR','Mostralo a un altro utente di Tanto Ci Vai. Il codice scade automaticamente dopo 10 minuti.')}
      <div id="tcvQrBody" style="padding:16px;text-align:center"><div class="notice">Genero un QR sicuro…</div></div>`);
    const body=document.getElementById('tcvQrBody');
    const {data,error}=await db.functions.invoke('community-qr-svg',{body:{base_url:qrBaseUrl()}});
    if(error||data?.error){
      if(body)body.innerHTML=`<div class="notice yellow"><b>Non riesco a generare il QR.</b><br>${esc(data?.error||error?.message||'Riprova tra poco.')}</div><button class="btn outline full" style="margin-top:10px" onclick="tcvOpenCommunitySafetyProfile()">APRI PROFILO COMMUNITY</button>`;
      return;
    }
    const exp=data?.expires_at?new Date(data.expires_at):null;
    const expLabel=exp&&!isNaN(exp)?exp.toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'}):'tra 10 minuti';
    if(body)body.innerHTML=`<div style="display:flex;justify-content:center"><div style="background:#fff;padding:12px;border:1px solid #dfe8f4;border-radius:20px;box-shadow:0 8px 24px rgba(11,24,52,.08);max-width:330px;width:100%">${data.svg||''}</div></div>
      <div class="notice green" style="margin-top:12px"><b>QR pronto</b><br>Valido fino alle ${esc(expLabel)}. È monouso: dopo una conferma non può essere riutilizzato.</div>
      <div style="font-size:10px;color:#69758d;line-height:1.5;margin:10px 4px">L'altra persona può usare <b>Scansiona QR</b> dentro Tanto Ci Vai oppure la fotocamera del telefono: il QR riapre direttamente l'app.</div>
      <button class="btn primary full" onclick="tcvOpenMyProfileQr()">↻ GENERA UN NUOVO QR</button>`;
  };

  async function showResolvedProfile(token){
    SCANNED_TOKEN=token;
    const {data,error}=await db.rpc('tcv_resolve_profile_qr',{p_token:token});
    const row=Array.isArray(data)?data[0]:data;
    if(error||!row){
      openSheet(`${head('QR COMMUNITY','⚠️ QR non valido','Il codice potrebbe essere scaduto, già usato oppure appartenere al tuo stesso profilo.')}
        <div class="notice yellow">${esc(error?.message||'Non riesco a leggere questo QR.')}</div>
        <button class="btn primary full" style="margin-top:10px" onclick="tcvOpenProfileQrScanner()">RIPROVA</button>`);
      return;
    }
    const rating=Number(row.rating_count||0)>0?Number(row.rating_avg||0).toFixed(1):'Nuovo';
    openSheet(`${head('QR COMMUNITY','👤 È questa la persona?','Confronta la foto con la persona davanti a te. Conferma solo se corrisponde davvero.')}
      <div style="text-align:center;padding:16px;border:1px solid #dfe8f4;border-radius:22px;background:#f8fbff;margin:12px 0">
        <div style="display:flex;justify-content:center">${profileImage(row,112)}</div>
        <h2 style="margin:10px 0 4px;font-size:24px">${esc(row.display_name||'Utente')}</h2>
        <div style="margin:8px 0">${confirmationBadge(row)}</div>
        <div style="font-size:10px;color:#69758d">🚘 ${Number(row.completed_rides||0)} viaggi · ⭐ ${esc(rating)}</div>
      </div>
      <div class="notice yellow"><b>Controllo umano, non documento d'identità.</b><br>Premendo conferma dichiari soltanto che la persona presente corrisponde alla foto e al profilo mostrati.</div>
      <button id="tcvQrConfirmBtn" class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvConfirmScannedProfile()">✅ CONFERMO CHE È LEI/LUI</button>
      <button class="btn outline full" style="margin-top:8px" onclick="tcvOpenProfileQrScanner()">NO · SCANSIONA DI NUOVO</button>`);
  }

  window.tcvConfirmScannedProfile=async function(){
    if(!SCANNED_TOKEN)return;
    const btn=document.getElementById('tcvQrConfirmBtn');
    if(btn){btn.disabled=true;btn.textContent='CONFERMO…'}
    const {data,error}=await db.rpc('tcv_confirm_profile_qr',{p_token:SCANNED_TOKEN});
    const row=Array.isArray(data)?data[0]:data;
    if(error||!row){
      if(btn){btn.disabled=false;btn.textContent='✅ CONFERMO CHE È LEI/LUI'}
      alert(error?.message||'Non riesco a confermare il profilo.');
      return;
    }
    SCANNED_TOKEN='';
    openSheet(`${head('PROFILO CONFERMATO','✅ Conferma registrata','Tanto Ci Vai ha registrato che un altro membro della Community ha riconosciuto questa persona dal vivo.')}
      <div style="text-align:center;padding:18px;border:1px solid #d5f4e8;border-radius:22px;background:#effff8;margin:12px 0">
        <div style="display:flex;justify-content:center">${profileImage(row,100)}</div>
        <h2 style="margin:10px 0 5px">${esc(row.display_name||'Utente')}</h2>
        <div>${confirmationBadge(row)}</div>
      </div>
      <div class="notice"><b>Cosa significa</b><br>È una conferma della Community basata su foto + incontro dal vivo. Non equivale a verifica di documento, fedina penale o identità legale.</div>
      <button class="btn primary full" style="margin-top:10px" onclick="closeSheet()">FATTO</button>`);
    setTimeout(()=>{document.getElementById('tcvQrProfileActions')?.remove();decorateOwnProfileCard()},100);
  };

  window.tcvHandleQrText=async function(raw){
    const token=parseQrToken(raw);
    if(!token){
      alert('Questo non è un QR di Tanto Ci Vai.');
      return;
    }
    stopScanner();
    await showResolvedProfile(token);
  };

  window.tcvOpenProfileQrScanner=async function(){
    stopScanner();
    if(!window.db||!window.SESSION?.user?.id){alert('Accedi prima al tuo profilo.');return}
    if(!navigator.mediaDevices?.getUserMedia){
      openSheet(`${head('SCANSIONA QR','📷 Fotocamera non disponibile','Puoi comunque usare la fotocamera normale del telefono: inquadra il QR e apri il link Tanto Ci Vai che compare.')}
        <div class="notice">Il browser attuale non permette l'accesso diretto alla fotocamera.</div>`);
      return;
    }
    if(!('BarcodeDetector' in window)){
      openSheet(`${head('SCANSIONA QR','📷 Usa la fotocamera del telefono','Su questo dispositivo lo scanner interno non è disponibile. Inquadra il QR con la fotocamera normale e apri il link Tanto Ci Vai.')}
        <div class="notice green">Non serve nessun servizio esterno: il link torna direttamente a Tanto Ci Vai e verrà riconosciuto dall'app.</div>`);
      return;
    }

    openSheet(`${head('SCANSIONA QR','📷 Inquadra il QR Community','Tieni il QR dentro il riquadro. La lettura avviene sul telefono.')}
      <div style="position:relative;margin:12px 0;border-radius:20px;overflow:hidden;background:#071a3d;min-height:320px">
        <video id="tcvQrVideo" playsinline muted autoplay style="width:100%;height:320px;object-fit:cover;display:block"></video>
        <div style="position:absolute;inset:52px;border:3px solid #08cdb0;border-radius:20px;box-shadow:0 0 0 999px rgba(5,17,39,.25)"></div>
      </div>
      <div id="tcvQrScanStatus" class="notice">Avvio fotocamera…</div>`);

    const video=document.getElementById('tcvQrVideo');
    const st=document.getElementById('tcvQrScanStatus');
    try{
      QR_STREAM=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
      if(!video){stopScanner();return}
      video.srcObject=QR_STREAM;
      await video.play();
      const supported=typeof BarcodeDetector.getSupportedFormats==='function'?await BarcodeDetector.getSupportedFormats():['qr_code'];
      if(Array.isArray(supported)&&!supported.includes('qr_code'))throw new Error('QR non supportato dal browser');
      const detector=new BarcodeDetector({formats:['qr_code']});
      if(st)st.textContent='Fotocamera pronta. Inquadra il QR.';
      const scan=async()=>{
        if(!QR_STREAM||!document.getElementById('tcvQrVideo'))return;
        try{
          if(video.readyState>=2){
            const codes=await detector.detect(video);
            if(codes?.length){
              const raw=codes[0].rawValue||'';
              stopScanner();
              await window.tcvHandleQrText(raw);
              return;
            }
          }
        }catch(e){console.warn('qr detect',e)}
        QR_TIMER=setTimeout(scan,250);
      };
      scan();
    }catch(e){
      stopScanner();
      if(st)st.innerHTML=`<b>Non riesco ad aprire la fotocamera.</b><br>${esc(e?.message||'Controlla il permesso Fotocamera.')}`;
    }
  };

  async function handleIncomingUrlQr(){
    const token=new URL(location.href).searchParams.get('tcvqr');
    if(!token||!window.SESSION?.user?.id)return;
    try{
      const u=new URL(location.href);u.searchParams.delete('tcvqr');history.replaceState({},'',u.pathname+(u.search||'')+(u.hash||''));
    }catch(e){}
    await showResolvedProfile(token);
  }

  function install(){
    bindCloseWrapper();
    bindProfileWrapper();
    const sheet=document.getElementById('sheet');
    if(sheet)new MutationObserver(()=>{replaceDocumentPlaceholder();decorateOwnProfileCard()}).observe(sheet,{childList:true,subtree:true});
    const profile=document.getElementById('profile');
    if(profile)new MutationObserver(()=>decorateOwnProfileCard()).observe(profile,{childList:true,subtree:true});
    setTimeout(()=>{replaceDocumentPlaceholder();decorateOwnProfileCard();handleIncomingUrlQr()},250);
  }

  let tries=0;
  const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION&&typeof window.openSheet==='function'&&typeof window.head==='function'){
      clearInterval(timer);install();
    }else if(tries>120)clearInterval(timer);
  },200);
})();
