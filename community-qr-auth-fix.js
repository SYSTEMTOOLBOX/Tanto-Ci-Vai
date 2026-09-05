/* TCV_COMMUNITY_QR_AUTH_FIX_V4 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_QR_AUTH_FIX_V4)return;
  window.TCV_COMMUNITY_QR_AUTH_FIX_V4=true;

  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function qrBaseUrl(){
    const u=new URL(location.href);
    u.search='';
    u.hash='';
    return u;
  }

  function stopQrCamera(){
    const video=document.getElementById('tcvQrVideo');
    try{video?.srcObject?.getTracks?.().forEach(t=>t.stop())}catch(_e){}
    try{if(video)video.srcObject=null}catch(_e){}
  }

  function ensureLocalQr(){
    if(!window.TCVLocalQR?.toSvg)throw new Error('Generatore QR locale non caricato. Chiudi e riapri l’app.');
  }

  function clientUrl(){
    return String(window.db?.supabaseUrl||((typeof SUPABASE_URL!=='undefined')?SUPABASE_URL:'')).replace(/\/$/,'');
  }

  function clientKey(){
    return String(window.db?.supabaseKey||((typeof SUPABASE_KEY!=='undefined')?SUPABASE_KEY:''));
  }

  async function sessionToken(){
    const {data,error}=await db.auth.getSession();
    if(error)throw error;
    const token=String(data?.session?.access_token||'');
    if(!token)throw new Error('Sessione scaduta. Accedi di nuovo.');
    return token;
  }

  function xhrRpcCreateProfileQr(accessToken){
    return new Promise((resolve,reject)=>{
      const base=clientUrl();
      const key=clientKey();
      if(!base||!key){reject(new Error('Configurazione Supabase non disponibile.'));return}

      const xhr=new XMLHttpRequest();
      xhr.open('POST',`${base}/rest/v1/rpc/tcv_create_profile_qr`,true);
      xhr.timeout=12000;
      xhr.setRequestHeader('apikey',key);
      xhr.setRequestHeader('Authorization',`Bearer ${accessToken}`);
      xhr.setRequestHeader('Content-Type','application/json');
      xhr.setRequestHeader('Accept','application/json');

      xhr.onload=()=>{
        let parsed=null;
        try{parsed=xhr.responseText?JSON.parse(xhr.responseText):null}catch(_e){}
        if(xhr.status>=200&&xhr.status<300){
          const row=Array.isArray(parsed)?parsed[0]:parsed;
          if(row?.token){resolve(row);return}
          reject(new Error('Il server non ha restituito un token QR valido.'));
          return;
        }
        const msg=parsed?.message||parsed?.error||parsed?.hint||`Supabase HTTP ${xhr.status}`;
        reject(new Error(String(msg)));
      };
      xhr.onerror=()=>reject(new Error('Connessione Supabase non raggiungibile dal telefono.'));
      xhr.ontimeout=()=>reject(new Error('Connessione Supabase troppo lenta. Riprova.'));
      xhr.send('{}');
    });
  }

  async function createQrToken(retried=false){
    try{
      const {data,error}=await db.rpc('tcv_create_profile_qr');
      if(error){
        const msg=String(error?.message||error||'');
        if(!retried&&/jwt|session|auth|unauthor/i.test(msg)){
          try{
            const refreshed=await db.auth.refreshSession();
            if(!refreshed.error&&refreshed.data?.session)return createQrToken(true);
          }catch(_e){}
        }
        if(/failed to fetch|network|load failed/i.test(msg)){
          const token=await sessionToken();
          return await xhrRpcCreateProfileQr(token);
        }
        throw error;
      }
      const row=Array.isArray(data)?data[0]:data;
      if(!row?.token)throw new Error('Il server non ha restituito un token QR valido.');
      return row;
    }catch(e){
      const msg=String(e?.message||e||'');
      if(/failed to fetch|network|load failed/i.test(msg)){
        const token=await sessionToken();
        return await xhrRpcCreateProfileQr(token);
      }
      throw e;
    }
  }

  function renderQr(host,text){
    ensureLocalQr();
    host.innerHTML=window.TCVLocalQR.toSvg(text);
    const svg=host.querySelector('svg');
    if(svg){svg.style.maxWidth='100%';svg.style.height='auto';svg.style.display='block';svg.style.margin='0 auto'}
  }

  window.tcvOpenMyProfileQr=async function(){
    stopQrCamera();
    if(!window.db||!window.SESSION?.user?.id){alert('Accedi prima al tuo profilo.');return}

    openSheet(`${head('PROFILO COMMUNITY','🔳 Il mio QR','Mostralo a un altro utente di Tanto Ci Vai. Il codice scade automaticamente dopo 10 minuti.')}
      <div id="tcvQrBody" style="padding:16px;text-align:center"><div class="notice">Genero un QR sicuro…</div></div>`);

    const body=document.getElementById('tcvQrBody');
    try{
      ensureLocalQr();
      const row=await createQrToken();
      const target=qrBaseUrl();
      target.searchParams.set('tcvqr',String(row.token));

      const exp=row.expires_at?new Date(row.expires_at):null;
      const expLabel=exp&&!isNaN(exp)?exp.toLocaleTimeString('it-IT',{hour:'2-digit',minute:'2-digit'}):'tra 10 minuti';

      if(body){
        body.innerHTML=`<div style="display:flex;justify-content:center"><div style="background:#fff;padding:12px;border:1px solid #dfe8f4;border-radius:20px;box-shadow:0 8px 24px rgba(11,24,52,.08);max-width:330px;width:100%"><div id="tcvQrDirectHost" style="display:grid;place-items:center;min-height:280px"></div></div></div>
          <div class="notice green" style="margin-top:12px"><b>QR pronto</b><br>Valido fino alle ${esc(expLabel)}. È monouso: dopo una conferma non può essere riutilizzato.</div>
          <div style="font-size:10px;color:#69758d;line-height:1.5;margin:10px 4px">L'altra persona può usare <b>Scansiona QR</b> dentro Tanto Ci Vai oppure la fotocamera del telefono: il codice riapre direttamente l'app.</div>
          <button class="btn primary full" onclick="tcvOpenMyProfileQr()">↻ GENERA UN NUOVO QR</button>`;
        const host=document.getElementById('tcvQrDirectHost');
        if(!host)throw new Error('Area QR non disponibile.');
        renderQr(host,target.toString());
      }
    }catch(e){
      const msg=String(e?.message||e||'Riprova tra poco.');
      if(body)body.innerHTML=`<div class="notice yellow"><b>Non riesco a generare il QR.</b><br>${esc(msg)}</div>
        <button class="btn primary full" style="margin-top:10px" onclick="tcvOpenMyProfileQr()">↻ RIPROVA</button>
        <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">CHIUDI</button>`;
    }
  };
})();
