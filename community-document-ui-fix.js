/* TCV_COMMUNITY_DOCUMENT_UI_FIX_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_DOCUMENT_UI_FIX_V1)return;
  window.TCV_COMMUNITY_DOCUMENT_UI_FIX_V1=true;

  function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function badgeLabel(p){
    if(p?.identity_verified)return '✅ Identità verificata';
    if(p?.document_registered){
      return p.document_kind==='driving_license'?'✅ Patente registrata':'✅ Documento registrato';
    }
    return '🪪 Documento non registrato';
  }

  async function getProfile(userId){
    if(!window.db||!userId)return null;
    const {data,error}=await db.from('community_public_profiles')
      .select('user_id,identity_verified,document_registered,document_kind,community_role,avatar_url')
      .eq('user_id',userId).maybeSingle();
    if(error){console.warn('document badge profile read',error);return null}
    return data||null
  }

  function styleRegistered(el,on){
    if(!el)return;
    if(on){
      el.style.background='#eafff5';
      el.style.color='#08785f';
    }
  }

  function decorateIdentityText(root,p){
    if(!root||!p)return;
    const label=badgeLabel(p);
    const candidates=[...root.querySelectorAll('span,div')];
    for(const el of candidates){
      const t=String(el.textContent||'').trim();
      if(t==='🪪 Identità non verificata'||t==='🪪 Identità non ancora verificata'||t==='✅ Identità verificata'||t==='🪪 Documento non registrato'||t==='✅ Patente registrata'||t==='✅ Documento registrato'){
        el.textContent=label;
        styleRegistered(el,!!(p.identity_verified||p.document_registered));
      }
    }
  }

  async function decorateOwnProfile(){
    const uid=window.SESSION?.user?.id;if(!uid)return;
    const p=await getProfile(uid);if(!p)return;
    const host=document.getElementById('profile');
    if(host)decorateIdentityText(host,p);
  }

  function bust(url){
    const base=String(url||'').replace(/([?&])v=\d+(&|$)/g,(m,a,b)=>b?a:'').replace(/[?&]$/,'');
    return `${base}${base.includes('?')?'&':'?'}v=${Date.now()}`;
  }

  async function installAvatarUploadFix(){
    if(typeof window.tcvUploadCommunitySafetyPhoto!=='function'||window.tcvUploadCommunitySafetyPhoto.__tcvAvatarCacheFix)return false;
    const fixed=async function(){
      const input=document.getElementById('tcvSafetyPhoto'),st=document.getElementById('tcvSafetyPhotoStatus');
      const file=input?.files?.[0];if(!file)return;
      if(file.size>5*1024*1024){if(st)st.textContent='Foto troppo grande: massimo 5 MB.';return}
      if(!['image/jpeg','image/png','image/webp'].includes(file.type)){if(st)st.textContent='Formato non supportato. Usa JPG, PNG o WEBP.';return}
      const uid=window.SESSION?.user?.id;if(!uid){if(st)st.textContent='Sessione scaduta.';return}
      if(st)st.textContent='Aggiorno la foto…';
      try{
        const ext=file.type==='image/png'?'png':file.type==='image/webp'?'webp':'jpg';
        const path=`${uid}/avatar.${ext}`;
        const up=await db.storage.from('community-avatars').upload(path,file,{upsert:true,contentType:file.type,cacheControl:'60'});
        if(up.error)throw up.error;
        const pub=db.storage.from('community-avatars').getPublicUrl(path);
        const base=pub?.data?.publicUrl||'';
        if(!base)throw new Error('URL foto non disponibile.');
        const url=bust(base);
        const saved=await db.from('community_public_profiles').update({avatar_url:url}).eq('user_id',uid);
        if(saved.error)throw saved.error;

        const preview=document.getElementById('tcvSafetyAvatarPreview');
        if(preview)preview.innerHTML=`<img src="${esc(url)}" alt="Foto profilo" style="width:70px;height:70px;border-radius:50%;object-fit:cover;border:2px solid #fff;box-shadow:0 4px 14px rgba(11,24,52,.16)">`;
        document.querySelectorAll('#tcvPublicProfileCard img,#tcvMainCommunityProfileCard img,#avatar img').forEach(img=>img.src=url);
        if(typeof window.tcvRefreshHeaderCommunityAvatar==='function')await window.tcvRefreshHeaderCommunityAvatar();
        if(st)st.textContent='✓ Foto aggiornata. La nuova immagine è già attiva.';
      }catch(e){
        console.warn('community avatar cache fix',e);
        if(st)st.textContent='Errore aggiornamento foto: '+(e?.message||e);
      }
    };
    fixed.__tcvAvatarCacheFix=true;
    window.tcvUploadCommunitySafetyPhoto=fixed;
    return true
  }

  function wrapPublicProfile(){
    if(typeof window.tcvOpenCommunityUserProfile!=='function'||window.tcvOpenCommunityUserProfile.__tcvDocumentBadgeFix)return;
    const original=window.tcvOpenCommunityUserProfile;
    const wrapped=async function(userId,...args){
      const out=await original.call(this,userId,...args);
      const p=await getProfile(userId);
      setTimeout(()=>decorateIdentityText(document.getElementById('sheet')||document,p),30);
      setTimeout(()=>decorateIdentityText(document.getElementById('sheet')||document,p),160);
      return out
    };
    wrapped.__tcvDocumentBadgeFix=true;
    window.tcvOpenCommunityUserProfile=wrapped;
  }

  function install(){
    installAvatarUploadFix();
    wrapPublicProfile();
    decorateOwnProfile();

    const profile=document.getElementById('profile');
    if(profile)new MutationObserver(()=>{
      if(!profile.classList.contains('hidden'))setTimeout(decorateOwnProfile,40);
    }).observe(profile,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});

    const sheet=document.getElementById('sheet');
    if(sheet)new MutationObserver(()=>{
      const uid=window.SESSION?.user?.id;
      if(uid)setTimeout(async()=>decorateIdentityText(sheet,await getProfile(uid)),50);
      installAvatarUploadFix();wrapPublicProfile();
    }).observe(sheet,{childList:true,subtree:true});

    setInterval(()=>{installAvatarUploadFix();wrapPublicProfile()},1200);
  }

  let tries=0;const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION){clearInterval(timer);install()}
    else if(tries>100)clearInterval(timer)
  },200);
})();
