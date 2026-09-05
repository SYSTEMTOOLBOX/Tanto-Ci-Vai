/* TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V2 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V2)return;
  window.TCV_COMMUNITY_PROFILE_PHOTO_ONLY_V2=true;

  const BUCKET='community-avatars';
  const MAX_BYTES=5*1024*1024;
  const TYPES=['image/jpeg','image/png','image/webp'];
  let SELECTED_FILE=null;

  function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]))}
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
    SELECTED_FILE=null;
    const photo=currentPhoto();
    openSheet(`${head('FOTO PROFILO','📷 Cambia foto','Scegli se scattare una nuova foto oppure prenderla dalla galleria.')}
      <div style="display:flex;justify-content:center;margin:16px 0 14px">
        <div id="tcvCompactPhotoPreview" style="width:128px;height:128px;border-radius:50%;overflow:hidden;display:grid;place-items:center;background:#eef5f1;border:4px solid #fff;box-shadow:0 10px 28px rgba(8,117,70,.18)">
          ${photo?`<img src="${esc(photo)}" alt="Foto attuale" style="width:100%;height:100%;object-fit:cover">`:'📷'}
        </div>
      </div>

      <input id="tcvCompactPhotoCamera" type="file" accept="image/jpeg,image/png,image/webp" capture="user" style="display:none" onchange="tcvPreviewCompactPhotoOnly(this,'camera')">
      <input id="tcvCompactPhotoGallery" type="file" accept="image/jpeg,image/png,image/webp" style="display:none" onchange="tcvPreviewCompactPhotoOnly(this,'gallery')">

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:6px">
        <button type="button" class="btn primary" style="min-height:72px;font-size:12px;border-radius:18px" onclick="document.getElementById('tcvCompactPhotoCamera')?.click()">📷<br><b>SCATTA FOTO</b></button>
        <button type="button" class="btn outline" style="min-height:72px;font-size:12px;border-radius:18px;background:#fff" onclick="document.getElementById('tcvCompactPhotoGallery')?.click()">🖼️<br><b>GALLERIA</b></button>
      </div>

      <div id="tcvCompactPhotoStatus" class="notice" style="margin-top:10px">JPG, PNG o WEBP · massimo 5 MB.</div>
      <button id="tcvCompactPhotoSave" class="btn teal full" style="margin-top:10px;padding:14px" onclick="tcvSaveCompactPhotoOnly()">📷 SALVA NUOVA FOTO</button>
      <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button>`);
  };

  window.tcvPreviewCompactPhotoOnly=function(input,source){
    const file=input?.files?.[0];
    const preview=document.getElementById('tcvCompactPhotoPreview');
    const st=document.getElementById('tcvCompactPhotoStatus');
    if(!file||!preview)return;
    if(!TYPES.includes(file.type)){
      SELECTED_FILE=null;
      if(st){st.className='notice yellow';st.textContent='Formato non supportato. Usa JPG, PNG o WEBP.'}
      return;
    }
    if(file.size>MAX_BYTES){
      SELECTED_FILE=null;
      if(st){st.className='notice yellow';st.textContent='Foto troppo grande: massimo 5 MB.'}
      return;
    }
    SELECTED_FILE=file;
    const otherId=source==='camera'?'tcvCompactPhotoGallery':'tcvCompactPhotoCamera';
    const other=document.getElementById(otherId);
    if(other)other.value='';
    const url=URL.createObjectURL(file);
    preview.innerHTML=`<img src="${esc(url)}" alt="Anteprima nuova foto" style="width:100%;height:100%;object-fit:cover">`;
    if(st){st.className='notice green';st.textContent=(source==='camera'?'Foto scattata':'Foto scelta dalla galleria')+'. Premi “Salva nuova foto”.'}
  };

  window.tcvSaveCompactPhotoOnly=async function(){
    const st=document.getElementById('tcvCompactPhotoStatus');
    const btn=document.getElementById('tcvCompactPhotoSave');
    const file=SELECTED_FILE;
    const uid=window.SESSION?.user?.id;

    if(!uid||!window.db){
      if(st){st.className='notice yellow';st.textContent='Sessione non disponibile. Chiudi e riapri Tanto Ci Vai.'}
      return;
    }
    if(!file){
      if(st){st.className='notice yellow';st.textContent='Scatta una foto oppure scegline una dalla galleria.'}
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
      SELECTED_FILE=null;
      const cam=document.getElementById('tcvCompactPhotoCamera');
      const gal=document.getElementById('tcvCompactPhotoGallery');
      if(cam)cam.value='';
      if(gal)gal.value='';
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
