/* TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V5 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V5)return;
  window.TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V5=true;

  const BUCKET='community-avatars';
  const MAX_BYTES=5*1024*1024;
  const TYPES=['image/jpeg','image/png','image/webp'];
  const EXT_RE=/\.(jpe?g|png|webp)$/i;
  let SELECTED_FILE=null;
  let CAMERA_STREAM=null;
  let CAMERA_OPENING=false;

  function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function bust(url){
    const base=String(url||'').split('#')[0];
    const sep=base.includes('?')?'&':'?';
    return `${base}${sep}v=${Date.now()}`;
  }
  function fileOk(file){return !!file && (TYPES.includes(file.type)||(!file.type&&EXT_RE.test(file.name||'')))}
  function normalizedType(file){
    if(TYPES.includes(file?.type))return file.type;
    const n=(file?.name||'').toLowerCase();
    if(n.endsWith('.png'))return 'image/png';
    if(n.endsWith('.webp'))return 'image/webp';
    return 'image/jpeg';
  }
  function wait(ms){return new Promise(r=>setTimeout(r,ms))}
  function timeoutPromise(ms,label){return new Promise((_,reject)=>setTimeout(()=>reject(new Error(label||'Timeout')),ms))}

  function compactPhotoButton(){
    return document.querySelector('#tcvCompactCommunityProfile button[aria-label="Gestisci foto profilo"],#tcvCompactCommunityProfile button[aria-label="Cambia foto profilo"]');
  }
  function currentPhoto(){
    return compactPhotoButton()?.querySelector('img')?.src||document.querySelector('#avatar img')?.src||'';
  }
  function setStatus(text,type){
    const st=document.getElementById('tcvCompactPhotoStatus');
    if(!st)return;
    st.className='notice'+(type?` ${type}`:'');
    st.textContent=text;
  }
  function stopCamera(){
    CAMERA_OPENING=false;
    if(CAMERA_STREAM){
      try{CAMERA_STREAM.getTracks().forEach(t=>t.stop())}catch(_e){}
      CAMERA_STREAM=null;
    }
    const video=document.getElementById('tcvCompactLiveCamera');
    if(video){
      try{video.pause()}catch(_e){}
      try{video.srcObject=null}catch(_e){}
    }
  }
  function wirePhotoButton(){
    const btn=compactPhotoButton();
    if(!btn)return;
    btn.setAttribute('aria-label','Cambia foto profilo');
    btn.setAttribute('title','Cambia foto');
    if(btn.__tcvPhotoOnly)return;
    btn.__tcvPhotoOnly=true;
    btn.onclick=function(e){
      if(e){e.preventDefault();e.stopPropagation()}
      window.tcvOpenCompactPhotoOnly();
      return false;
    };
  }

  function useSelectedFile(file,source){
    stopCamera();
    const capture=document.getElementById('tcvCompactCaptureNow');
    if(capture)capture.style.display='none';
    const preview=document.getElementById('tcvCompactPhotoPreview');
    if(!file||!preview)return false;
    if(!fileOk(file)){
      SELECTED_FILE=null;
      setStatus('Formato non supportato. Usa JPG, PNG o WEBP.','yellow');
      return false;
    }
    if(file.size>MAX_BYTES){
      SELECTED_FILE=null;
      setStatus('Foto troppo grande: massimo 5 MB.','yellow');
      return false;
    }
    SELECTED_FILE=file;
    const url=URL.createObjectURL(file);
    preview.innerHTML=`<img src="${esc(url)}" alt="Anteprima nuova foto" style="width:100%;height:100%;object-fit:cover">`;
    setStatus((source==='camera'?'Foto scattata':'Foto scelta dalla galleria')+'. Premi “Salva nuova foto”.','green');
    return true;
  }

  window.tcvOpenCompactPhotoOnly=function(){
    if(typeof window.openSheet!=='function')return;
    stopCamera();
    SELECTED_FILE=null;
    const photo=currentPhoto();
    openSheet(`${head('FOTO PROFILO','📷 Cambia foto','Scatta una nuova foto oppure scegline una dalla galleria.')}
      <div style="display:flex;justify-content:center;margin:16px 0 14px">
        <div id="tcvCompactPhotoPreview" style="width:170px;height:170px;border-radius:50%;overflow:hidden;display:grid;place-items:center;background:#eef5f1;border:4px solid #fff;box-shadow:0 10px 28px rgba(8,117,70,.18)">
          ${photo?`<img src="${esc(photo)}" alt="Foto attuale" style="width:100%;height:100%;object-fit:cover">`:'📷'}
        </div>
      </div>

      <input id="tcvCompactPhotoGallery" type="file" accept=".jpg,.jpeg,.png,.webp" style="display:none" onchange="tcvPreviewCompactPhotoOnly(this,'gallery')">

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:6px">
        <button id="tcvCompactStartCamera" type="button" class="btn primary" style="min-height:72px;font-size:12px;border-radius:18px" onclick="tcvStartCompactCamera()">📷<br><b>SCATTA FOTO</b></button>
        <button type="button" class="btn outline" style="min-height:72px;font-size:12px;border-radius:18px;background:#fff" onclick="tcvChooseCompactGallery()">🖼️<br><b>GALLERIA</b></button>
      </div>

      <button id="tcvCompactCaptureNow" type="button" class="btn teal full" style="display:none;margin-top:10px;padding:14px" onclick="tcvCaptureCompactCamera()">📸 SCATTA ADESSO</button>
      <div id="tcvCompactPhotoStatus" class="notice" style="margin-top:10px">La fotocamera può chiedere il consenso la prima volta.</div>
      <button id="tcvCompactPhotoSave" class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvSaveCompactPhotoOnly()">✓ SALVA NUOVA FOTO</button>
      <button class="btn outline full" style="margin-top:8px" onclick="tcvCloseCompactPhotoOnly()">Chiudi</button>`);
  };

  window.tcvChooseCompactGallery=async function(){
    stopCamera();
    const capture=document.getElementById('tcvCompactCaptureNow');
    if(capture)capture.style.display='none';
    setStatus('Apro la galleria…','');

    if(typeof window.showOpenFilePicker==='function'){
      try{
        const handles=await window.showOpenFilePicker({
          multiple:false,
          excludeAcceptAllOption:true,
          types:[{description:'Foto',accept:{'image/jpeg':['.jpg','.jpeg'],'image/png':['.png'],'image/webp':['.webp']}}]
        });
        const file=handles?.[0]?await handles[0].getFile():null;
        if(file)useSelectedFile(file,'gallery');
        return;
      }catch(e){
        if(e?.name==='AbortError'){setStatus('Selezione annullata.','');return}
        console.warn('gallery picker fallback',e);
      }
    }

    const input=document.getElementById('tcvCompactPhotoGallery');
    if(!input)return;
    input.removeAttribute('capture');
    input.setAttribute('accept','.jpg,.jpeg,.png,.webp');
    input.value='';
    try{
      if(typeof input.showPicker==='function')input.showPicker();
      else input.click();
    }catch(_e){input.click()}
  };

  window.tcvStartCompactCamera=async function(){
    if(CAMERA_OPENING)return;
    stopCamera();
    SELECTED_FILE=null;
    CAMERA_OPENING=true;

    const preview=document.getElementById('tcvCompactPhotoPreview');
    const capture=document.getElementById('tcvCompactCaptureNow');
    const start=document.getElementById('tcvCompactStartCamera');
    if(!preview){CAMERA_OPENING=false;return}

    if(!navigator.mediaDevices?.getUserMedia){
      CAMERA_OPENING=false;
      setStatus('Fotocamera diretta non disponibile su questo telefono. Usa Galleria.','yellow');
      return;
    }

    if(start){start.disabled=true;start.innerHTML='📷<br><b>APRO…</b>'}
    if(capture)capture.style.display='none';
    setStatus('Apro la fotocamera… Se richiesto, premi Consenti.','');

    try{
      const mediaPromise=navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});
      const stream=await Promise.race([mediaPromise,timeoutPromise(9000,'La fotocamera non risponde.')]);
      if(!CAMERA_OPENING){try{stream.getTracks().forEach(t=>t.stop())}catch(_e){};return}
      CAMERA_STREAM=stream;

      preview.innerHTML='<video id="tcvCompactLiveCamera" autoplay playsinline muted style="width:100%;height:100%;object-fit:cover;transform:scaleX(-1);background:#111"></video>';
      const video=document.getElementById('tcvCompactLiveCamera');
      if(!video)throw new Error('Anteprima fotocamera non disponibile.');
      video.srcObject=stream;

      const ready=new Promise((resolve,reject)=>{
        let done=false;
        const ok=()=>{if(done)return;done=true;resolve()};
        video.onloadedmetadata=ok;
        video.oncanplay=ok;
        video.onerror=()=>{if(done)return;done=true;reject(new Error('Anteprima fotocamera non disponibile.'))};
      });
      try{await video.play()}catch(_e){}
      await Promise.race([ready,timeoutPromise(5000,'La fotocamera si è avviata ma il video non risponde.')]);
      await wait(150);

      if(!video.videoWidth||!video.videoHeight)throw new Error('Il video della fotocamera non è pronto.');
      if(capture)capture.style.display='block';
      setStatus('Fotocamera pronta. Inquadrati e premi “Scatta adesso”.','green');
    }catch(e){
      stopCamera();
      const denied=e?.name==='NotAllowedError'||e?.name==='PermissionDeniedError';
      const busy=e?.name==='NotReadableError'||e?.name==='TrackStartError';
      if(denied)setStatus('Permesso fotocamera negato. Consenti la fotocamera oppure usa Galleria.','yellow');
      else if(busy)setStatus('La fotocamera è occupata da un’altra app. Chiudila e riprova.','yellow');
      else setStatus((e?.message||'Non riesco ad aprire la fotocamera.')+' Puoi comunque usare Galleria.','yellow');
      if(capture)capture.style.display='none';
    }finally{
      CAMERA_OPENING=false;
      if(start){start.disabled=false;start.innerHTML='📷<br><b>SCATTA FOTO</b>'}
    }
  };

  window.tcvCaptureCompactCamera=function(){
    const video=document.getElementById('tcvCompactLiveCamera');
    const preview=document.getElementById('tcvCompactPhotoPreview');
    const capture=document.getElementById('tcvCompactCaptureNow');
    if(!video||!preview||video.readyState<2||!video.videoWidth||!video.videoHeight){
      setStatus('La fotocamera non è ancora pronta. Riprova tra un istante.','yellow');
      return;
    }
    if(capture){capture.disabled=true;capture.textContent='📸 SCATTO…'}
    const size=Math.min(video.videoWidth,video.videoHeight);
    const sx=(video.videoWidth-size)/2;
    const sy=(video.videoHeight-size)/2;
    const canvas=document.createElement('canvas');
    canvas.width=720;canvas.height=720;
    const ctx=canvas.getContext('2d');
    ctx.translate(720,0);ctx.scale(-1,1);
    ctx.drawImage(video,sx,sy,size,size,0,0,720,720);
    canvas.toBlob(blob=>{
      if(capture){capture.disabled=false;capture.textContent='📸 SCATTA ADESSO'}
      if(!blob){setStatus('Non riesco a creare la foto. Riprova.','yellow');return}
      const file=new File([blob],`profilo-${Date.now()}.jpg`,{type:'image/jpeg'});
      useSelectedFile(file,'camera');
    },'image/jpeg',0.88);
  };

  window.tcvPreviewCompactPhotoOnly=function(input,source){useSelectedFile(input?.files?.[0],source)};

  window.tcvSaveCompactPhotoOnly=async function(){
    const st=document.getElementById('tcvCompactPhotoStatus');
    const btn=document.getElementById('tcvCompactPhotoSave');
    const file=SELECTED_FILE;
    const uid=window.SESSION?.user?.id;
    stopCamera();

    if(!uid||!window.db){setStatus('Sessione non disponibile. Chiudi e riapri Tanto Ci Vai.','yellow');return}
    if(!file){setStatus('Scatta una foto oppure scegline una dalla galleria.','yellow');return}
    if(!fileOk(file)){setStatus('Formato non supportato. Usa JPG, PNG o WEBP.','yellow');return}
    if(file.size>MAX_BYTES){setStatus('Foto troppo grande: massimo 5 MB.','yellow');return}

    if(btn){btn.disabled=true;btn.textContent='SALVO LA FOTO…'}
    if(st){st.className='notice';st.textContent='Aggiorno la fotografia…'}

    try{
      const mime=normalizedType(file);
      const ext=mime==='image/png'?'png':mime==='image/webp'?'webp':'jpg';
      const path=`${uid}/avatar.${ext}`;
      const up=await db.storage.from(BUCKET).upload(path,file,{upsert:true,contentType:mime,cacheControl:'60'});
      if(up.error)throw up.error;

      const pub=db.storage.from(BUCKET).getPublicUrl(path);
      const base=pub?.data?.publicUrl||'';
      if(!base)throw new Error('URL foto non disponibile.');
      const url=bust(base);

      const saved=await db.from('community_public_profiles').update({avatar_url:url}).eq('user_id',uid);
      if(saved.error)throw saved.error;

      document.querySelectorAll('#tcvCompactCommunityProfile img,#tcvPublicProfileCard img,#tcvMainCommunityProfileCard img,#avatar img').forEach(img=>{img.src=url});
      const preview=document.getElementById('tcvCompactPhotoPreview');
      if(preview)preview.innerHTML=`<img src="${esc(url)}" alt="Nuova foto profilo" style="width:100%;height:100%;object-fit:cover">`;
      if(typeof window.tcvRefreshHeaderCommunityAvatar==='function')await window.tcvRefreshHeaderCommunityAvatar();
      if(st){st.className='notice green';st.textContent='✓ Foto aggiornata. È già attiva nel tuo profilo Community.'}
      SELECTED_FILE=null;
      const gal=document.getElementById('tcvCompactPhotoGallery');
      if(gal)gal.value='';
    }catch(e){
      console.warn('compact photo-only upload',e);
      if(st){st.className='notice yellow';st.textContent='Errore aggiornamento foto: '+(e?.message||e)}
    }finally{
      if(btn){btn.disabled=false;btn.textContent='✓ SALVA NUOVA FOTO'}
      setTimeout(wirePhotoButton,120);
    }
  };

  window.tcvCloseCompactPhotoOnly=function(){stopCamera();if(typeof window.closeSheet==='function')closeSheet()};

  function install(){
    wirePhotoButton();
    const host=document.getElementById('profile');
    if(host)new MutationObserver(()=>setTimeout(wirePhotoButton,20)).observe(host,{childList:true,subtree:true});
    document.addEventListener('visibilitychange',()=>{if(document.hidden)stopCamera()});
    window.addEventListener('pagehide',stopCamera);
    setInterval(()=>{wirePhotoButton();if(CAMERA_STREAM&&!document.getElementById('tcvCompactLiveCamera'))stopCamera()},800);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
  else install();
})();
