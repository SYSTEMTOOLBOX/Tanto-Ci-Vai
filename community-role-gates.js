/* TCV_COMMUNITY_ROLE_GATES_V1
   Community-only members keep SOS/map/hazards/QR, but cannot request or offer rides.
*/
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_ROLE_GATES_V1)return;
  window.TCV_COMMUNITY_ROLE_GATES_V1=true;

  let cached=null;
  let cachedAt=0;

  async function ownRole(force=false){
    if(!window.db||!window.SESSION?.user?.id)return null;
    if(!force&&cached&&Date.now()-cachedAt<2500)return cached;
    const {data,error}=await db.from('community_public_profiles')
      .select('community_enabled,community_role,document_registered,document_kind')
      .eq('user_id',SESSION.user.id)
      .maybeSingle();
    if(error){console.warn('community role gate',error);return null}
    cached=data||null;cachedAt=Date.now();return cached;
  }

  function blockedSheet(kind){
    const passenger=kind==='passenger';
    const title=passenger?'🚘 Passaggi non attivi':'🚗 Guida non attiva';
    const text=passenger
      ?'Hai scelto di partecipare solo come Membro Community. Puoi usare SOS, mappa pericoli, segnalazioni e QR, ma non puoi chiedere o ricevere passaggi.'
      :'Hai scelto di partecipare solo come Membro Community. Puoi usare SOS, mappa pericoli, segnalazioni e QR, ma non puoi offrire passaggi.';
    if(typeof window.openSheet==='function'&&typeof window.head==='function'){
      openSheet(`${head('COMMUNITY',title,text)}
        <div class="notice green" style="margin-top:12px"><b>✓ Community sempre attiva</b><br>SOS, mappa pericoli, segnalazioni e QR restano disponibili.</div>
        <div class="notice" style="margin-top:9px">Per usare i passaggi devi prima scegliere il ruolo <b>Passeggero</b> oppure <b>Guidatore + passeggero</b>.</div>
        <button class="btn teal full" style="margin-top:10px" onclick="closeSheet();typeof tcvOpenCompactProfileManager==='function'?tcvOpenCompactProfileManager():page('profile')">✏️ GESTISCI PROFILO</button>
        <button class="btn outline full" style="margin-top:8px" onclick="closeSheet()">Chiudi</button>`);
    }else{
      alert(text);
    }
  }

  async function canPassenger(){
    const p=await ownRole(true);
    if(!p?.community_enabled){
      if(typeof window.tcvOpenCommunitySafetyProfile==='function')window.tcvOpenCommunitySafetyProfile();
      return false;
    }
    if(p.community_role==='passenger'||p.community_role==='driver_passenger')return true;
    blockedSheet('passenger');return false;
  }

  async function canDriver(){
    const p=await ownRole(true);
    if(!p?.community_enabled){
      if(typeof window.tcvOpenCommunitySafetyProfile==='function')window.tcvOpenCommunitySafetyProfile();
      return false;
    }
    if(p.community_role==='driver_passenger')return true;
    blockedSheet('driver');return false;
  }

  function wrap(name,guard){
    const original=window[name];
    if(typeof original!=='function'||original.__tcvRoleGate)return false;
    const wrapped=async function(...args){
      if(!(await guard()))return;
      return original.apply(this,args);
    };
    wrapped.__tcvRoleGate=true;
    wrapped.__tcvRoleGateOriginal=original;
    window[name]=wrapped;
    return true;
  }

  function install(){
    let n=0;
    n+=wrap('openRideRequest',canPassenger)?1:0;
    n+=wrap('publishRideRequest',canPassenger)?1:0;
    n+=wrap('openTripSearch',canDriver)?1:0;
    n+=wrap('tcvSaveCommunityTrip',canDriver)?1:0;
    n+=wrap('tcvToggleCommunityTrip',canDriver)?1:0;
    return n;
  }

  window.tcvRefreshCommunityRoleGate=function(){cached=null;cachedAt=0};
  let tries=0;
  const timer=setInterval(()=>{
    tries++;
    install();
    const passengerReady=typeof window.openRideRequest==='function'&&window.openRideRequest.__tcvRoleGate;
    const driverReady=typeof window.openTripSearch==='function'&&window.openTripSearch.__tcvRoleGate;
    if(passengerReady&&driverReady){clearInterval(timer)}
    else if(tries>120){clearInterval(timer)}
  },180);
})();
