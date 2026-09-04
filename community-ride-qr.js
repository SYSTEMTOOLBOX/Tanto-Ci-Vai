/* TCV_COMMUNITY_RIDE_QR_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_RIDE_QR_V1)return;
  window.TCV_COMMUNITY_RIDE_QR_V1=true;

  let STREAM=null,TIMER=null,ACTIVE_TOKEN='',EXPECTED_RIDE='';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmtTime=v=>{try{return new Date(v).toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'})}catch(e){return ''}};
  const fmtElapsed=s=>{s=Math.max(0,Number(s)||0);const h=Math.floor(s/3600),m=Math.floor((s%3600)/60),sec=s%60;return h?`${h} h ${m} min`:(m?`${m} min ${sec} s`:`${sec} s`)};

  function stop(){if(TIMER){clearTimeout(TIMER);TIMER=null}if(STREAM){try{STREAM.getTracks().forEach(t=>t.stop())}catch(e){}STREAM=null}const v=document.getElementById('tcvRideQrVideo');if(v)try{v.srcObject=null}catch(e){}}
  function baseUrl(){const u=new URL(location.href);u.search='';u.hash='';return u.toString()}
  function parse(raw){const t=String(raw||'').trim();if(t.startsWith('TCVR1:'))return t.slice(6).trim();try{const u=new URL(t,location.href);return String(u.searchParams.get('tcvride')||'').trim()}catch(e){return ''}}
  function img(row,size=104){if(row?.avatar_url)return `<img src="${esc(row.avatar_url)}" alt="Foto passeggero" style="width:${size}px;height:${size}px;border-radius:50%;object-fit:cover;border:3px solid #fff;box-shadow:0 8px 24px rgba(11,24,52,.18)">`;const n=String(row?.display_name||'Utente').trim();return `<div style="width:${size}px;height:${size}px;border-radius:50%;display:grid;place-items:center;background:#071a3d;color:#fff;font-size:28px;font-weight:950">${esc((n||'TC').slice(0,2).toUpperCase())}</div>`}

  async function latestMatched(){if(!window.db||!window.SESSION?.user?.id)return null;const {data,error}=await db.from('ride_requests').select('id,driver_id,status,from_label,to_label,departure_at,requester_display_name').eq('user_id',SESSION.user.id).eq('status','matched').order('created_at',{ascending:false}).limit(1);if(error)return null;return (data||[])[0]||null}

  window.tcvOpenMyBoardingQr=async function(rideId=''){
    stop();
    if(!window.db||!window.SESSION?.user?.id){alert('Accedi prima.');return}
    let ride=null;
    if(rideId){const q=await db.from('ride_requests').select('id,driver_id,status,from_label,to_label,departure_at').eq('id',rideId).eq('user_id',SESSION.user.id).maybeSingle();ride=q.data||null}else ride=await latestMatched();
    if(!ride){openSheet(`${head('PASSAGGIO COMMUNITY','🔳 QR di salita','Il QR compare quando il guidatore ha accettato la tua richiesta.')}<div class="notice yellow">Non hai un passaggio accettato in attesa di salita.</div>`);return}
    openSheet(`${head('PASSAGGIO COMMUNITY','🔳 Mostra questo QR al guidatore','Quando il guidatore lo scansiona, Tanto Ci Vai registra automaticamente che sei salito e avvia il viaggio.')}
      <div id="tcvRideQrBody" style="padding:14px;text-align:center"><div class="notice">Genero il QR di salita…</div></div>`);
    const body=document.getElementById('tcvRideQrBody');
    const {data,error}=await db.functions.invoke('community-ride-qr-svg',{body:{ride_request_id:ride.id,base_url:baseUrl()}});
    if(error||data?.error){if(body)body.innerHTML=`<div class="notice yellow">${esc(data?.error||error?.message||'Non riesco a generare il QR.')}</div>`;return}
    const exp=data?.expires_at?fmtTime(data.expires_at):'';
    if(body)body.innerHTML=`<div style="font-size:11px;font-weight:900;margin-bottom:10px">${esc(ride.from_label)} → ${esc(ride.to_label)}</div>
      <div style="display:flex;justify-content:center"><div style="background:#fff;padding:12px;border:1px solid #dfe8f4;border-radius:20px;max-width:330px;width:100%">${data.svg||''}</div></div>
      <div class="notice green" style="margin-top:12px"><b>QR di salita pronto</b><br>Valido ${exp?`fino alle ${esc(exp)}`:'per 10 minuti'} e utilizzabile una sola volta.</div>
      <div class="notice" style="margin-top:8px">Appena il guidatore lo scansiona, lo stato passa a <b>passeggero a bordo</b>. Non calcola tariffe a tempo: registra soltanto inizio e fine del passaggio.</div>
      <button class="btn primary full" style="margin-top:10px" onclick="tcvOpenMyBoardingQr('${esc(ride.id)}')">↻ GENERA NUOVO QR</button>`;
  };

  async function resolveToken(token,expected=''){
    ACTIVE_TOKEN=token;EXPECTED_RIDE=expected||'';
    const {data,error}=await db.rpc('tcv_resolve_ride_qr',{p_token:token});const row=Array.isArray(data)?data[0]:data;
    if(error||!row){openSheet(`${head('QR DI SALITA','⚠️ QR non valido','Il codice può essere scaduto, già usato oppure non appartenere a un tuo passeggero.')}<div class="notice yellow">${esc(error?.message||'QR non riconosciuto.')}</div><button class="btn primary full" style="margin-top:10px" onclick="tcvOpenRideQrScanner('${esc(expected||'')}')">RIPROVA</button>`);return}
    if(expected&&String(row.ride_request_id)!==String(expected)){openSheet(`${head('QR DI SALITA','⚠️ Passeggero sbagliato','Questo QR appartiene a un altro passaggio.')}<div class="notice yellow">Scansiona il QR del passeggero associato a questa richiesta.</div>`);return}
    const rating=Number(row.rating_count||0)?Number(row.rating_avg||0).toFixed(1):'Nuovo';
    openSheet(`${head('QR DI SALITA','👤 Controlla e fai salire','Confronta la foto con la persona davanti a te. La conferma avvia il passaggio.')}
      <div style="text-align:center;padding:16px;border:1px solid #dfe8f4;border-radius:22px;background:#f8fbff;margin:12px 0"><div style="display:flex;justify-content:center">${img(row)}</div><h2 style="margin:10px 0 5px">${esc(row.display_name||'Utente')}</h2><div style="font-size:10px;color:#69758d">🚘 ${Number(row.completed_rides||0)} viaggi · ⭐ ${esc(rating)}</div><div style="font-size:11px;font-weight:900;margin-top:9px">${esc(row.from_label)} → ${esc(row.to_label)}</div></div>
      <div class="notice green"><b>Scansione = salita</b><br>Premendo il pulsante registri l'orario di salita e il viaggio diventa attivo.</div>
      <button id="tcvRideBoardBtn" class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvBoardRideWithQr()">🚘 PASSEGGERO SALITO · AVVIA</button>
      <button class="btn outline full" style="margin-top:8px" onclick="tcvOpenRideQrScanner('${esc(expected||'')}')">NO · SCANSIONA DI NUOVO</button>`);
  }

  window.tcvBoardRideWithQr=async function(){if(!ACTIVE_TOKEN)return;const b=document.getElementById('tcvRideBoardBtn');if(b){b.disabled=true;b.textContent='AVVIO VIAGGIO…'}const {data,error}=await db.rpc('tcv_board_ride_with_qr',{p_token:ACTIVE_TOKEN});const row=Array.isArray(data)?data[0]:data;if(error||!row){if(b){b.disabled=false;b.textContent='🚘 PASSEGGERO SALITO · AVVIA'}alert(error?.message||'Non riesco ad avviare il viaggio.');return}ACTIVE_TOKEN='';try{await db.functions.invoke('send-community-ride-push',{body:{ride_id:row.ride_request_id,event:'onboard'}})}catch(e){}openSheet(`${head('VIAGGIO ATTIVO','🚘 Passeggero a bordo','La scansione del QR ha registrato la salita.')}<div class="notice green"><b>Partenza registrata alle ${esc(fmtTime(row.pickup_confirmed_at))}</b><br>Non è un tassametro: memorizziamo soltanto gli orari di salita e discesa.</div><button class="btn teal full" style="margin-top:10px" onclick="tcvFinishRideFromQr('${esc(row.ride_request_id)}')">👋 PASSEGGERO SCESO · TERMINA</button>`);setTimeout(patchDriverButtons,150)};

  window.tcvFinishRideFromQr=async function(rideId){if(!rideId)return;if(!confirm('Confermi che il passeggero è sceso e il passaggio è terminato?'))return;const {data,error}=await db.rpc('tcv_complete_ride',{p_ride_request_id:rideId});const row=Array.isArray(data)?data[0]:data;if(error||!row){alert(error?.message||'Non riesco a terminare il viaggio.');return}try{await db.functions.invoke('send-community-ride-push',{body:{ride_id:row.ride_request_id,event:'completed'}})}catch(e){}openSheet(`${head('PASSAGGIO COMPLETATO','🏁 Passeggero sceso','Il viaggio è stato chiuso correttamente.')}<div class="notice green"><b>Fine registrata alle ${esc(fmtTime(row.dropoff_confirmed_at))}</b><br>Durata del passaggio: ${esc(fmtElapsed(row.elapsed_seconds))}.</div><button class="btn primary full" style="margin-top:10px" onclick="closeSheet()">FATTO</button>`);setTimeout(patchDriverButtons,150)};

  window.tcvHandleRideQrText=async function(raw,expected=''){const token=parse(raw);if(!token){alert('Questo non è un QR di salita Tanto Ci Vai.');return}stop();await resolveToken(token,expected)};

  window.tcvOpenRideQrScanner=async function(expectedRideId=''){
    stop();EXPECTED_RIDE=expectedRideId||'';
    if(!navigator.mediaDevices?.getUserMedia||!('BarcodeDetector' in window)){openSheet(`${head('QR DI SALITA','📷 Usa la fotocamera del telefono','Inquadra il QR con la fotocamera normale e apri il link Tanto Ci Vai che compare.')}<div class="notice green">Il link torna direttamente nell'app e avvia la verifica del passeggero.</div>`);return}
    openSheet(`${head('QR DI SALITA','📷 Scansiona il passeggero','Inquadra il QR mostrato sul telefono del passeggero.')}
      <div style="position:relative;margin:12px 0;border-radius:20px;overflow:hidden;background:#071a3d;min-height:320px"><video id="tcvRideQrVideo" playsinline muted autoplay style="width:100%;height:320px;object-fit:cover;display:block"></video><div style="position:absolute;inset:52px;border:3px solid #08cdb0;border-radius:20px;box-shadow:0 0 0 999px rgba(5,17,39,.25)"></div></div><div id="tcvRideQrStatus" class="notice">Avvio fotocamera…</div>`);
    const video=document.getElementById('tcvRideQrVideo'),st=document.getElementById('tcvRideQrStatus');
    try{STREAM=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}}});video.srcObject=STREAM;await video.play();if(st)st.textContent='Inquadra il QR di salita.';const detector=new BarcodeDetector({formats:['qr_code']});const tick=async()=>{if(!STREAM)return;try{const codes=await detector.detect(video);if(codes?.[0]?.rawValue){const raw=codes[0].rawValue;if(parse(raw)){stop();await window.tcvHandleRideQrText(raw,EXPECTED_RIDE);return}}}catch(e){}TIMER=setTimeout(tick,350)};tick()}catch(e){stop();if(st)st.textContent='Fotocamera non disponibile. Usa la fotocamera normale del telefono.'}
  };

  function patchDriverButtons(){
    document.querySelectorAll('button').forEach(btn=>{
      const oc=btn.getAttribute('onclick')||'';
      let m=oc.match(/tcvDriverRideDecision\('([^']+)'\s*,\s*'onboard'\)/);
      if(m){const id=m[1];btn.textContent='📷 SCANSIONA QR PASSEGGERO';btn.setAttribute('onclick',`tcvOpenRideQrScanner('${id}')`);return}
      m=oc.match(/tcvDriverRideDecision\('([^']+)'\s*,\s*'completed'\)/);
      if(m){const id=m[1];btn.textContent='👋 PASSEGGERO SCESO · TERMINA';btn.setAttribute('onclick',`tcvFinishRideFromQr('${id}')`)}
    });
  }

  async function decoratePassengerProfile(){const card=document.getElementById('tcvPublicProfileCard');if(!card||document.getElementById('tcvBoardingQrAction'))return;const ride=await latestMatched();if(!ride)return;const box=document.createElement('div');box.id='tcvBoardingQrAction';box.style.marginTop='10px';box.innerHTML=`<div class="notice green"><b>Hai un passaggio accettato</b><br>${esc(ride.from_label)} → ${esc(ride.to_label)}</div><button class="btn teal full" style="margin-top:8px" onclick="tcvOpenMyBoardingQr('${esc(ride.id)}')">🔳 MOSTRA QR DI SALITA AL GUIDATORE</button>`;card.appendChild(box)}

  const observer=new MutationObserver(()=>{patchDriverButtons();decoratePassengerProfile()});
  observer.observe(document.documentElement,{childList:true,subtree:true});
  setInterval(()=>{patchDriverButtons();decoratePassengerProfile()},1200);

  setTimeout(()=>{
    const u=new URL(location.href);const token=String(u.searchParams.get('tcvride')||'').trim();
    if(token){u.searchParams.delete('tcvride');history.replaceState({},'',u.toString());setTimeout(()=>resolveToken(token,''),500)}
  },700);
})();