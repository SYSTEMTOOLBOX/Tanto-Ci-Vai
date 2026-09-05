/* TCV_COMMUNITY_QR_AUTH_FIX_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_QR_AUTH_FIX_V1)return;
  window.TCV_COMMUNITY_QR_AUTH_FIX_V1=true;

  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function qrBaseUrl(){
    const u=new URL(location.href);
    u.search='';
    u.hash='';
    return u.toString();
  }

  async function getAccessToken(forceRefresh){
    if(!window.db)return '';
    if(forceRefresh){
      const {data,error}=await db.auth.refreshSession();
      if(error)throw error;
      return String(data?.session?.access_token||'');
    }
    const {data,error}=await db.auth.getSession();
    if(error)throw error;
    let token=String(data?.session?.access_token||'');
    if(!token){
      const refreshed=await db.auth.refreshSession();
      if(refreshed.error)throw refreshed.error;
      token=String(refreshed.data?.session?.access_token||'');
    }
    return token;
  }

  function statusOf(error){
    return Number(error?.context?.status||error?.status||error?.statusCode||0);
  }

  async function invokeQr(){
    let token=await getAccessToken(false);
    if(!token)throw new Error('Sessione scaduta. Chiudi e riapri l’app.');

    let result=await db.functions.invoke('community-qr-svg',{
      body:{base_url:qrBaseUrl()},
      headers:{Authorization:`Bearer ${token}`}
    });

    const firstStatus=statusOf(result?.error);
    if(result?.error&&(firstStatus===401||firstStatus===403)){
      token=await getAccessToken(true);
      if(!token)throw new Error('Sessione scaduta. Accedi di nuovo.');
      result=await db.functions.invoke('community-qr-svg',{
        body:{base_url:qrBaseUrl()},
        headers:{Authorization:`Bearer ${token}`}
      });
    }
    return result;
  }

  function stopQrCamera(){
    const video=document.getElementById('tcvQrVideo');
    try{video?.srcObject?.getTracks?.().forEach(t=>t.stop())}catch(_e){}
    try{if(video)video.srcObject=null}catch(_e){}
  }

  window.tcvOpenMyProfileQr=async function(){
    stopQrCamera();
    if(!window.db||!window.SESSION?.user?.id){alert('Accedi prima al tuo profilo.');return}

    openSheet(`${head('PROFILO COMMUNITY','🔳 Il mio QR','Mostralo a un altro utente di Tanto Ci Vai. Il codice scade automaticamente dopo 10 minuti.')}
      <div id="tcvQrBody" style="padding:16px;text-align:center"><div class="notice">Genero un QR sicuro…</div></div>`);

    const body=document.getElementById('tcvQrBody');
    try{
      const {data,error}=await invokeQr();
      if(error||data?.error)throw error||new Error(data.error);

      const exp=data?.expires_at?new Date(data.expires_at):null;
      const expLabel=exp&&!isNaN(exp)?exp.toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'}):'tra 10 minuti';
      if(body)body.innerHTML=`<div style="display:flex;justify-content:center"><div style="background:#fff;padding:12px;border:1px solid #dfe8f4;border-radius:20px;box-shadow:0 8px 24px rgba(11,24,52,.08);max-width:330px;width:100%">${data?.svg||''}</div></div>
        <div class="notice green" style="margin-top:12px"><b>QR pronto</b><br>Valido fino alle ${esc(expLabel)}. È monouso: dopo una conferma non può essere riutilizzato.</div>
        <div style="font-size:10px;color:#69758d;line-height:1.5;margin:10px 4px">L'altra persona può usare <b>Scansiona QR</b> dentro Tanto Ci Vai oppure la fotocamera del telefono.</div>
        <button class="btn primary full" onclick="tcvOpenMyProfileQr()">↻ GENERA UN NUOVO QR</button>`;
    }catch(e){
      const msg=String(e?.message||e||'Riprova tra poco.');
      if(body)body.innerHTML=`<div class="notice yellow"><b>Non riesco a generare il QR.</b><br>${esc(msg)}</div>
        <button class="btn primary full" style="margin-top:10px" onclick="tcvOpenMyProfileQr()">↻ RIPROVA</button>
        <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">CHIUDI</button>`;
    }
  };
})();
