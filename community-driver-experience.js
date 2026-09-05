/* TCV_COMMUNITY_DRIVER_EXPERIENCE_V1
   Shows how long a Community driver has held a category B licence.
   The exact document and licence number remain private.
*/
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_DRIVER_EXPERIENCE_V1)return;
  window.TCV_COMMUNITY_DRIVER_EXPERIENCE_V1=true;

  function parseDateOnly(v){
    if(!v)return null;
    const m=String(v).match(/^(\d{4})-(\d{2})-(\d{2})/);
    if(!m)return null;
    const d=new Date(Number(m[1]),Number(m[2])-1,Number(m[3]));
    return Number.isFinite(d.getTime())?d:null;
  }

  function experienceText(v){
    const d=parseDateOnly(v);
    if(!d)return '';
    const now=new Date();
    const today=new Date(now.getFullYear(),now.getMonth(),now.getDate());
    if(d>today)return '';
    let months=(today.getFullYear()-d.getFullYear())*12+(today.getMonth()-d.getMonth());
    if(today.getDate()<d.getDate())months--;
    months=Math.max(0,months);
    if(months===0)return 'Patente da meno di 1 mese';
    if(months<12)return `Patente da ${months} ${months===1?'mese':'mesi'}`;
    const years=Math.floor(months/12),rem=months%12;
    const y=`${years} ${years===1?'anno':'anni'}`;
    if(!rem)return `Patente da ${y}`;
    return `Patente da ${y} e ${rem} ${rem===1?'mese':'mesi'}`;
  }
  window.tcvDriverExperienceText=experienceText;

  async function getProfile(userId){
    if(!window.db||!userId)return null;
    const {data,error}=await db.from('community_public_profiles')
      .select('user_id,community_role,document_registered,document_kind,driver_license_since')
      .eq('user_id',userId).maybeSingle();
    if(error){console.warn('driver experience profile read',error);return null}
    return data||null;
  }

  function decorate(root,p){
    if(!root)return;
    root.querySelectorAll('.tcv-driver-experience-badge').forEach(el=>el.remove());
    if(p?.community_role!=='driver_passenger'||!p?.document_registered||p?.document_kind!=='driving_license')return;
    const text=experienceText(p?.driver_license_since);
    if(!text)return;
    const anchor=[...root.querySelectorAll('span')].find(el=>String(el.textContent||'').trim()==='✅ Patente registrata');
    if(!anchor||!anchor.parentElement)return;
    const badge=document.createElement('span');
    badge.className='tcv-driver-experience-badge';
    badge.style.cssText='display:inline-flex;align-items:center;padding:6px 9px;border-radius:999px;background:#eef5ff;border:1px solid #cfe0ff;color:#215b9b;font-size:9px;font-weight:950;white-space:nowrap';
    badge.textContent='🕒 '+text;
    anchor.insertAdjacentElement('afterend',badge);
  }

  async function decorateOwn(){
    const uid=window.SESSION?.user?.id;if(!uid)return;
    const p=await getProfile(uid);if(!p)return;
    decorate(document.getElementById('profile'),p);
  }

  function wrapPublicProfile(){
    const fn=window.tcvOpenCommunityUserProfile;
    if(typeof fn!=='function'||fn.__tcvDriverExperience)return false;
    const wrapped=async function(userId,...args){
      const out=await fn.call(this,userId,...args);
      const p=await getProfile(userId);
      setTimeout(()=>decorate(document.getElementById('sheet')||document,p),90);
      setTimeout(()=>decorate(document.getElementById('sheet')||document,p),240);
      return out;
    };
    wrapped.__tcvDriverExperience=true;
    window.tcvOpenCommunityUserProfile=wrapped;
    return true;
  }

  function install(){
    wrapPublicProfile();
    decorateOwn();
    const profile=document.getElementById('profile');
    if(profile)new MutationObserver(()=>{
      if(!profile.classList.contains('hidden'))setTimeout(decorateOwn,70);
    }).observe(profile,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
    const sheet=document.getElementById('sheet');
    if(sheet)new MutationObserver(()=>wrapPublicProfile()).observe(sheet,{childList:true,subtree:true});
    setInterval(()=>{wrapPublicProfile();if(!document.getElementById('profile')?.classList.contains('hidden'))decorateOwn()},1800);
  }

  let tries=0;
  const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION){clearInterval(timer);install()}
    else if(tries>100)clearInterval(timer);
  },180);
})();