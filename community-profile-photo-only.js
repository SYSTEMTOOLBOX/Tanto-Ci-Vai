/* TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V1)return;
  window.TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V1=true;

  const BUCKET='community-avatars';
  const MAX_BYTES=5*1024*1024;
  const TYPES=['image/jpeg','image/png','image/webp'];

  function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function bust(url){
    const base=String(url||'').split('#')[0];
    const sep=base.includes('?')?'&':'?';
    return `${base}${sep}v=${Date.now()}`;
  }

  function compactPhotoButton(){
    return document.querySelector('#tcvCompactCommunityProfile button[aria-label="Gestisci foto profilo"],#tcvCompactCommunityProfile button[aria-label="Cambia foto profilo"]');
  }

  function currentPhoto(){
    return compactPhotoButton()?.querySelector('img')?.src||document.querySelector('#avatar img')?.src||'';
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

  window.tcvOpenCompactPhotoOnly=function(){
    if(typeof window.openSheet!=='function')return;
    const photo=currentPhoto();
    openSheet(`${head('FOTO PROFILO','📷 Cambia foto','Qui modifichi esclusivamente la fotografia del tuo profilo Community.')}
      <div style="display:flex;justify-content:center;margin:16px 0 14px">
        <div id="tcvCompactPhotoPreview" style="width:128px;height:128px;border-radius:50%;overflow:hidden;display:grid;place-items:center;background:#eef5f1;border:4px solid #fff;box-shadow:0 10px 28px rgba(8,117,70,.18)">
          ${photo?`<img src="${esc(photo)}" alt="Foto attuale" style="width:100%;height:100%;object-fit:cover">`:'📷'}
        </div>
      </div>
      <div class="field">
        <label>NUOVA FOTO</label>
        <input id="tcvCompactPhotoInput" type="file" accept="image/jpeg,image/png,image/webp" capture="user" onchange="tcvPreviewCompactPhotoOnly(this)">
      </div>
      <div id="tcvCompactPhotoStatus" class="notice">JPG, PNG o WEBP · massimo 5 MB.</div>
      <button id="tcvCompactPhotoSave" class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvSaveCompactPhotoOnly()">📷 SALVA NUOVA FOTO</button>
      <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button>`);
  };

  window.tcvPreviewCompactPhotoOnly=function(input){
    const file=input?.files?.[0];
    const preview=document.getElementById('tcvCompactPhotoPreview');
    const st=document.getElementById('tcvCompactPhotoStatus');
    if(!file||!preview)return;
    if(!TYPES.includes(file.type)){
      if(st){st.className='notice yellow';st.textContent='Formato non supportato. Usa JPG, PNG o WEBP.'}
      return;
    }
    if(file.size>MAX_BYTES){
      if(st){st.className='notice yellow';st.textContent='Foto troppo grande: massimo 5 MB.'}
      return;
    }
    const url=URL.createObjectURL(file);
    preview.innerHTML=`<img src="${esc(url)}" alt="Anteprima nuova foto" style="width:100%;height:100%;object-fit:cover">`;
    if(st){st.className='notice green';st.textContent='Anteprima pronta. Premi “Salva nuova foto”.'}
  };

  window.tcvSaveCompactPhotoOnly=async function(){
    const input=document.getElementById('tcvCompactPhotoInput');
    const st=document.getElementById('tcvCompactPhotoStatus');
    const btn=document.getElementById('tcvCompactPhotoSave');
    const file=input?.files?.[0];
    const uid=window.SESSION?.user?.id;

    if(!uid||!window.db){
      if(st){st.className='notice yellow';st.textContent='Sessione non disponibile. Chiudi e riapri Tanto Ci Vai.'}
      return;
    }
    if(!file){
      if(st){st.className='notice yellow';st.textContent='Scegli prima una nuova fotografia.'}
      return;
    }
    if(!TYPES.includes(file.type)){
      if(st){st.className='notice yellow';st.textContent='Formato non supportato. Usa JPG, PNG o WEBP.'}
      return;
    }
    if(file.size>MAX_BYTES){
      if(st){st.className='notice yellow';st.textContent='Foto troppo grande: massimo 5 MB.'}
      return;
    }

    if(btn){btn.disabled=true;btn.textContent='SALVO LA FOTO…'}
    if(st){st.className='notice';st.textContent='Aggiorno la fotografia…'}

    try{
      const ext=file.type==='image/png'?'png':file.type==='image/webp'?'webp':'jpg';
      const path=`${uid}/avatar.${ext}`;
      const up=await db.storage.from(BUCKET).upload(path,file,{upsert:true,contentType:file.type,cacheControl:'60'});
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
      if(input)input.value='';
    }catch(e){
      console.warn('compact photo-only upload',e);
      if(st){st.className='notice yellow';st.textContent='Errore aggiornamento foto: '+(e?.message||e)}
    }finally{
      if(btn){btn.disabled=false;btn.textContent='📷 SALVA NUOVA FOTO'}
      setTimeout(wirePhotoButton,120);
    }
  };

  function install(){
    wirePhotoButton();
    const host=document.getElementById('profile');
    if(host)new MutationObserver(()=>setTimeout(wirePhotoButton,20)).observe(host,{childList:true,subtree:true});
    setInterval(wirePhotoButton,1000);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
  else install();
})();
