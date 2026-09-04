/* TCV_COMMUNITY_SAFETY_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_SAFETY_V1)return;
  window.TCV_COMMUNITY_SAFETY_V1=true;

  let SELF=null;
  let PUBLIC_BY_ID={};
  let DRIVER_REQUESTS=[];

  function s(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function firstName(v){const x=String(v||'').trim().replace(/\s+/g,' ');return x?x.split(' ')[0]:'Utente'}
  function initials(v){return firstName(v).slice(0,2).toUpperCase()||'TC'}
  function euro(v){return new Intl.NumberFormat('it-IT',{style:'currency',currency:'EUR'}).format(Number(v)||0)}
  function fmtDate(v){try{return new Date(v).toLocaleString('it-IT',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'})}catch(e){return ''}}
  function ready(p){return !!(p&&p.community_enabled&&String(p.display_name||'').trim()&&String(p.avatar_url||'').trim())}
  function badgeLine(p){
    const id=p?.identity_verified?'✅ Identità verificata':'🪪 Identità non ancora verificata';
    const ph=p?.phone_verified?'✅ Telefono verificato':'📱 Telefono non verificato';
    return `${id}<br>${ph}`
  }
  function avatarHtml(p,size=56){
    const name=p?.display_name||'Utente';
    return p?.avatar_url
      ?`<img src="${s(p.avatar_url)}" alt="Foto profilo" style="width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;border:2px solid #fff;box-shadow:0 4px 14px rgba(11,24,52,.16)">`
      :`<div style="width:${size}px;height:${size}px;border-radius:50%;display:grid;place-items:center;background:#0b1834;color:#fff;font-weight:950">${s(initials(name))}</div>`
  }

  async function getOwn(){
    if(!window.db||!window.SESSION?.user?.id)return null;
    const uid=SESSION.user.id;
    let {data,error}=await db.from('community_public_profiles').select('*').eq('user_id',uid).limit(1);
    if(error){console.warn('community safety profile read',error);return null}
    let row=Array.isArray(data)?data[0]:data;
    if(!row){
      const display=firstName(window.PROFILE?.nome||SESSION.user.email?.split('@')[0]||'Utente');
      const ins=await db.from('community_public_profiles').insert({user_id:uid,display_name:display,community_enabled:false});
      if(ins.error){console.warn('community safety profile create',ins.error);return null}
      ({data,error}=await db.from('community_public_profiles').select('*').eq('user_id',uid).limit(1));
      row=Array.isArray(data)?data[0]:data;
    }
    SELF=row||null;
    return SELF;
  }
  window.tcvLoadOwnSafetyProfile=getOwn;

  async function loadPublicForTrips(){
    const trips=Array.isArray(window.TCV_COMMUNITY_TRIPS)?window.TCV_COMMUNITY_TRIPS:[];
    const ids=[...new Set(trips.map(t=>String(t.user_id||'')).filter(Boolean))];
    if(!ids.length||!window.db)return PUBLIC_BY_ID;
    const {data,error}=await db.from('community_public_profiles')
      .select('user_id,display_name,avatar_url,community_enabled,identity_verified,phone_verified,completed_rides,rating_avg,rating_count')
      .in('user_id',ids);
    if(!error){PUBLIC_BY_ID={};(data||[]).forEach(p=>PUBLIC_BY_ID[String(p.user_id)]=p)}
    return PUBLIC_BY_ID;
  }

  window.tcvOpenCommunitySafetyProfile=async function(){
    const p=await getOwn();
    if(!p){alert('Profilo sicurezza non disponibile. Riprova tra poco.');return}
    const enabled=!!p.community_enabled;
    openSheet(`${head('SICUREZZA COMMUNITY','🛡️ Il tuo profilo di viaggio','Sulla mappa mostriamo solo le informazioni necessarie. Telefono, indirizzo di casa e documenti non vengono pubblicati.')}
      <div style="display:flex;gap:12px;align-items:center;padding:13px;border:1px solid #dfe8f4;border-radius:18px;background:#f8fbff;margin:12px 0">
        <div id="tcvSafetyAvatarPreview">${avatarHtml(p,70)}</div>
        <div style="flex:1"><b style="font-size:15px">${s(p.display_name||'Utente')}</b><div style="font-size:9px;line-height:1.6;color:#5f6e87;margin-top:4px">${badgeLine(p)}<br>🚘 ${Number(p.completed_rides||0)} viaggi completati${Number(p.rating_count||0)?` · ⭐ ${Number(p.rating_avg||0).toFixed(1)}`:''}</div></div>
      </div>
      <div class="field"><label>NOME VISIBILE NELLA COMMUNITY</label><input id="tcvSafetyDisplayName" maxlength="60" value="${s(p.display_name||firstName(PROFILE?.nome))}" placeholder="Es. Loris"></div>
      <div class="field"><label>FOTO REALE DEL PROFILO</label><input id="tcvSafetyPhoto" type="file" accept="image/jpeg,image/png,image/webp" capture="user"><div id="tcvSafetyPhotoStatus" class="notice" style="margin-top:6px">La foto serve al guidatore/passeggero per riconoscere la persona che sale a bordo. Max 5 MB.</div></div>
      <div class="notice green"><b>Privacy by design</b><br>In pubblico: nome, foto, badge, valutazione e viaggi completati. Mai telefono, documento, indirizzo di casa o posizione GPS continua. Il documento d'identità, quando collegheremo il provider di verifica, non verrà salvato nell'app: conserveremo solo l'esito “verificato / non verificato”.</div>
      <label style="display:flex;gap:9px;align-items:flex-start;margin:12px 0;padding:11px;border:1px solid #dfe8f4;border-radius:14px;font-size:10px;line-height:1.45"><input id="tcvSafetyEnabled" type="checkbox" style="width:20px;height:20px;margin:0" ${enabled?'checked':''}><span><b>Attiva il mio Profilo Community</b><br>Accetto che nome visibile, foto e badge di sicurezza siano mostrati agli utenti della Community quando pubblico o richiedo un passaggio.</span></label>
      <div id="tcvSafetyStatus" class="notice ${ready(p)?'green':'yellow'}">${ready(p)?'✓ Profilo pronto per viaggiare.':'Aggiungi una foto e attiva il profilo per usare i passaggi Community.'}</div>
      <button class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvSaveCommunitySafetyProfile()">SALVA PROFILO SICUREZZA</button>
      <button class="btn outline full" style="margin-top:8px" disabled>🪪 VERIFICA DOCUMENTO · IN ATTIVAZIONE</button>`);
    setTimeout(()=>{const f=document.getElementById('tcvSafetyPhoto');if(f)f.addEventListener('change',window.tcvUploadCommunitySafetyPhoto)},0)
  };

  window.tcvUploadCommunitySafetyPhoto=async function(){
    const input=document.getElementById('tcvSafetyPhoto'),st=document.getElementById('tcvSafetyPhotoStatus');
    const file=input?.files?.[0];if(!file)return;
    if(file.size>5*1024*1024){if(st)st.textContent='Foto troppo grande: massimo 5 MB.';return}
    if(!['image/jpeg','image/png','image/webp'].includes(file.type)){if(st)st.textContent='Formato non supportato. Usa JPG, PNG o WEBP.';return}
    if(st)st.textContent='Carico la foto in modo sicuro…';
    const uid=SESSION?.user?.id;if(!uid){if(st)st.textContent='Sessione scaduta.';return}
    const ext=file.type==='image/png'?'png':file.type==='image/webp'?'webp':'jpg';
    const path=`${uid}/avatar.${ext}`;
    const up=await db.storage.from('community-avatars').upload(path,file,{upsert:true,contentType:file.type,cacheControl:'3600'});
    if(up.error){console.warn('avatar upload',up.error);if(st)st.textContent='Errore caricamento foto: '+up.error.message;return}
    const pub=db.storage.from('community-avatars').getPublicUrl(path);
    const url=pub?.data?.publicUrl||'';
    if(!url){if(st)st.textContent='Foto caricata ma URL non disponibile.';return}
    const {error}=await db.from('community_public_profiles').update({avatar_url:url}).eq('user_id',uid);
    if(error){if(st)st.textContent='Errore salvataggio foto: '+error.message;return}
    SELF=await getOwn();
    const prev=document.getElementById('tcvSafetyAvatarPreview');if(prev)prev.innerHTML=avatarHtml(SELF,70);
    if(st)st.textContent='✓ Foto caricata. Ora salva il profilo.';
  };

  window.tcvSaveCommunitySafetyProfile=async function(){
    const st=document.getElementById('tcvSafetyStatus'),name=String(document.getElementById('tcvSafetyDisplayName')?.value||'').trim(),enabled=!!document.getElementById('tcvSafetyEnabled')?.checked;
    if(!name){if(st)st.textContent='Inserisci il nome visibile.';return}
    const current=await getOwn();
    if(enabled&&!current?.avatar_url){if(st)st.textContent='Per attivare la Community serve una foto reale.';return}
    const {error}=await db.from('community_public_profiles').update({display_name:firstName(name),community_enabled:enabled}).eq('user_id',SESSION.user.id);
    if(error){if(st)st.textContent='Errore: '+error.message;return}
    SELF=await getOwn();
    if(st){st.className='notice '+(ready(SELF)?'green':'yellow');st.textContent=ready(SELF)?'✓ Profilo sicurezza attivo. Ora puoi pubblicare o richiedere passaggi.':'Profilo salvato ma Community non attiva.'}
  };

  async function ensureReady(action){
    const p=await getOwn();
    if(ready(p))return true;
    await window.tcvOpenCommunitySafetyProfile();
    const st=document.getElementById('tcvSafetyStatus');if(st)st.textContent=`Prima di ${action||'usare i passaggi'} completa foto e attiva il Profilo Community.`;
    return false;
  }
  window.tcvEnsureCommunitySafetyReady=ensureReady;

  async function loadDriverRequests(){
    if(!SESSION?.user?.id||!window.db)return [];
    const {data,error}=await db.from('ride_requests')
      .select('id,user_id,community_trip_id,from_label,to_label,departure_at,passengers,status,distance_km,contribution_per_person,platform_fee,requester_display_name,requester_avatar_url,requester_identity_verified,requester_phone_verified,requester_completed_rides,requester_rating_avg,created_at')
      .eq('driver_id',SESSION.user.id)
      .in('status',['open','matched','onboard'])
      .order('created_at',{ascending:false});
    if(error){console.warn('driver ride requests',error);return DRIVER_REQUESTS}
    DRIVER_REQUESTS=data||[];return DRIVER_REQUESTS
  }

  function requestCard(r){
    const p={display_name:r.requester_display_name||'Utente',avatar_url:r.requester_avatar_url,identity_verified:r.requester_identity_verified,phone_verified:r.requester_phone_verified,completed_rides:r.requester_completed_rides,rating_avg:r.requester_rating_avg,rating_count:Number(r.requester_completed_rides||0)>0?1:0};
    const total=Number(r.contribution_per_person||0)*Math.max(1,Number(r.passengers||1));
    let actions='';
    if(r.status==='open')actions=`<div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:9px"><button class="btn teal" onclick="tcvDriverRideDecision('${r.id}','matched')">✓ ACCETTA</button><button class="btn danger" onclick="tcvDriverRideDecision('${r.id}','declined')">RIFIUTA</button></div>`;
    else if(r.status==='matched')actions=`<button class="btn primary full" style="margin-top:9px" onclick="tcvDriverRideDecision('${r.id}','onboard')">🚘 PASSEGGERO A BORDO</button>`;
    else if(r.status==='onboard')actions=`<button class="btn teal full" style="margin-top:9px" onclick="tcvDriverRideDecision('${r.id}','completed')">🏁 ARRIVATI</button>`;
    return `<article style="border:1px solid #dfe8f4;border-radius:17px;padding:12px;background:#fff;margin-top:8px"><div style="display:flex;gap:10px;align-items:center">${avatarHtml(p,54)}<div style="min-width:0;flex:1"><b style="font-size:13px">${s(p.display_name)}</b><div style="font-size:8px;color:#69758d;line-height:1.5">${p.identity_verified?'✅ Identità verificata':'🪪 Identità non verificata'} · ${p.phone_verified?'📱 verificato':'📱 non verificato'}<br>🚘 ${Number(p.completed_rides||0)} viaggi${Number(p.requester_completed_rides||0)>0?` · ⭐ ${Number(p.rating_avg||0).toFixed(1)}`:''}</div></div><span style="font-size:8px;font-weight:900;padding:5px 7px;border-radius:999px;background:#eef4ff;color:#0b66ff">${s(String(r.status).toUpperCase())}</span></div><div style="font-size:9px;line-height:1.55;margin-top:9px;color:#51617e"><b>${s(r.from_label)} → ${s(r.to_label)}</b><br>🕒 ${fmtDate(r.departure_at)} · 👥 ${Number(r.passengers||1)}<br>💶 ${euro(r.contribution_per_person)} a persona${Number(r.passengers||1)>1?` · ${euro(total)} totali`:''}</div>${actions}<div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:7px"><button class="btn outline" onclick="tcvOpenSafetyReport('${r.id}','${r.user_id}')">⚠️ SEGNALA</button><button class="btn outline" onclick="tcvBlockCommunityUser('${r.user_id}','${r.id}')">🚫 BLOCCA</button></div></article>`
  }

  async function injectDriverPanel(tripId=''){
    const sheet=document.querySelector('.sheet');if(!sheet)return;
    const old=document.getElementById('tcvDriverSafetyPanel');if(old)old.remove();
    const rows=(await loadDriverRequests()).filter(r=>!tripId||String(r.community_trip_id)===String(tripId));
    const panel=document.createElement('div');panel.id='tcvDriverSafetyPanel';panel.style.margin='12px 0';
    panel.innerHTML=`<div style="display:flex;justify-content:space-between;align-items:end;gap:8px"><div><div style="font-size:8px;color:#0b66ff;font-weight:950;letter-spacing:.12em">SICUREZZA PASSEGGERI</div><h3 style="margin:3px 0;font-size:17px">Chi vuole salire a bordo</h3></div><button class="btn outline" onclick="tcvOpenCommunitySafetyProfile()">🛡️ MIO PROFILO</button></div>${rows.length?rows.map(requestCard).join(''):'<div class="notice" style="margin-top:8px">Nessuna richiesta in attesa per i tuoi percorsi.</div>'}`;
    const anchor=sheet.querySelector('.tcv-route-hero');if(anchor)anchor.insertAdjacentElement('afterend',panel);else sheet.prepend(panel)
  }

  window.tcvDriverRideDecision=async function(id,status){
    const allowed=['matched','declined','onboard','completed'];if(!allowed.includes(status))return;
    const {error}=await db.from('ride_requests').update({status}).eq('id',id).eq('driver_id',SESSION.user.id);
    if(error){alert(error.message);return}
    await injectDriverPanel('');
  };

  window.tcvBlockCommunityUser=async function(userId,rideId=''){
    if(!confirm('Bloccare questo utente? Non potrà più creare richieste di viaggio con te.'))return;
    if(rideId){try{await db.from('ride_requests').update({status:'declined'}).eq('id',rideId).eq('driver_id',SESSION.user.id)}catch(e){}}
    const {error}=await db.from('community_user_blocks').upsert({blocker_id:SESSION.user.id,blocked_id:userId});
    if(error){alert(error.message);return}
    alert('Utente bloccato.');await injectDriverPanel('')
  };

  window.tcvOpenSafetyReport=function(rideId,userId){
    openSheet(`${head('SICUREZZA','⚠️ Segnala un comportamento','La segnalazione resta privata e non viene mostrata pubblicamente all’utente segnalato.')}
      <div class="field"><label>MOTIVO</label><select id="tcvSafetyReportCategory"><option value="behavior">Comportamento inappropriato</option><option value="harassment">Molestie / minacce</option><option value="unsafe_driving">Guida pericolosa</option><option value="fraud">Tentativo di frode</option><option value="identity">Problema di identità</option><option value="other">Altro</option></select></div>
      <div class="field"><label>DETTAGLI</label><textarea id="tcvSafetyReportDetails" maxlength="1000" rows="5" placeholder="Descrivi solo fatti concreti e utili alla verifica."></textarea></div>
      <div id="tcvSafetyReportStatus" class="notice yellow">Non inserire diagnosi, dati sanitari o accuse non verificabili. La segnalazione serve solo alla sicurezza della piattaforma.</div>
      <button class="btn danger full" style="margin-top:9px" onclick="tcvSubmitSafetyReport('${rideId}','${userId}')">INVIA SEGNALAZIONE</button>`)
  };

  window.tcvSubmitSafetyReport=async function(rideId,userId){
    const cat=document.getElementById('tcvSafetyReportCategory')?.value||'other',details=String(document.getElementById('tcvSafetyReportDetails')?.value||'').trim(),st=document.getElementById('tcvSafetyReportStatus');
    if(!details){if(st)st.textContent='Scrivi cosa è successo.';return}
    const {error}=await db.from('community_safety_reports').insert({reporter_id:SESSION.user.id,reported_user_id:userId,ride_request_id:rideId||null,category:cat,details:details.slice(0,1000)});
    if(error){if(st)st.textContent='Errore: '+error.message;return}
    if(st){st.className='notice green';st.textContent='✓ Segnalazione inviata in modo riservato.'}
  };

  function installWrappers(){
    if(window.__TCV_SAFETY_WRAPPED)return;window.__TCV_SAFETY_WRAPPED=true;

    const origOpenTrip=window.openTripSearch;
    if(typeof origOpenTrip==='function')window.openTripSearch=async function(...args){const out=await origOpenTrip.apply(this,args);setTimeout(()=>injectDriverPanel(args[0]||''),30);return out};

    const origSave=window.tcvSaveCommunityTrip;
    if(typeof origSave==='function')window.tcvSaveCommunityTrip=async function(...args){if(!await ensureReady('pubblicare un percorso'))return;let oldName=null;if(window.PROFILE){oldName=PROFILE.nome;PROFILE.nome=firstName(PROFILE.nome)}try{return await origSave.apply(this,args)}finally{if(window.PROFILE&&oldName!==null)PROFILE.nome=oldName}};

    const origPublish=window.publishRideRequest;
    if(typeof origPublish==='function')window.publishRideRequest=async function(...args){if(!await ensureReady('richiedere un passaggio'))return;return origPublish.apply(this,args)};

    const origOpenRide=window.openRideRequest;
    if(typeof origOpenRide==='function')window.openRideRequest=function(tripId='',...rest){if(!tripId){openSheet(`${head('PASSAGGI COMMUNITY','🗺️ Scegli prima un percorso','Il guidatore pubblica il proprio tragitto. Tu lo raggiungi nel punto di salita concordato: non deve venirti a prendere a casa.')}<div class="notice green"><b>Come funziona</b><br>Apri la mappa → tocca una linea di un pendolare → scegli “Richiedi un posto”. Solo allora invii i tuoi dati al guidatore di quel percorso.</div><button class="btn primary full" style="margin-top:10px" onclick="closeSheet();page('mapPage')">🗺️ APRI MAPPA COMMUNITY</button><button class="btn outline full" style="margin-top:8px" onclick="tcvOpenCommunitySafetyProfile()">🛡️ PROFILO SICUREZZA</button>`);return}return origOpenRide.call(this,tripId,...rest)};

    const origRenderMap=window.renderMapPage;
    if(typeof origRenderMap==='function')window.renderMapPage=function(...args){const out=origRenderMap.apply(this,args);setTimeout(()=>{const mp=document.getElementById('mapPage');if(!mp||document.getElementById('tcvMapSafetyBtn'))return;const b=document.createElement('button');b.id='tcvMapSafetyBtn';b.className='btn outline full';b.style.margin='0 0 9px';b.innerHTML='🛡️ Profilo sicurezza Community';b.onclick=window.tcvOpenCommunitySafetyProfile;const gps=mp.querySelector('.gpsbtn');if(gps)gps.insertAdjacentElement('beforebegin',b);else mp.prepend(b)},0);return out};

    const origInitMap=window.initMap;
    if(typeof origInitMap==='function')window.initMap=async function(...args){await loadPublicForTrips();const trips=Array.isArray(window.TCV_COMMUNITY_TRIPS)?window.TCV_COMMUNITY_TRIPS:[];trips.forEach(t=>{const p=PUBLIC_BY_ID[String(t.user_id)]||null;const n=firstName(p?.display_name||t.driver_name||'Utente');t.driver_name=n+(p?.identity_verified?' ✓':'')});return origInitMap.apply(this,args)};
  }

  let tries=0;const boot=setInterval(async()=>{tries++;if(window.db&&window.SESSION&&typeof window.openTripSearch==='function'){clearInterval(boot);installWrappers();await getOwn()}else if(tries>80)clearInterval(boot)},250);
})();
