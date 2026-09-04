/* TCV_COMMUNITY_NOTIFICATIONS_V1 */
(function(){
  'use strict';
  if(window.TCV_COMMUNITY_NOTIFICATIONS_V1)return;
  window.TCV_COMMUNITY_NOTIFICATIONS_V1=true;

  async function latestOwnRide(){
    if(!window.db||!window.SESSION?.user?.id)return null;
    const {data,error}=await db.from('ride_requests')
      .select('id,created_at,status,community_trip_id')
      .eq('user_id',SESSION.user.id)
      .order('created_at',{ascending:false})
      .limit(1)
      .maybeSingle();
    if(error){console.warn('latest Community ride',error);return null}
    return data||null
  }

  async function sendRidePush(rideId,eventType){
    if(!rideId||!eventType||!window.db?.functions?.invoke)return null;
    try{
      const {data,error}=await db.functions.invoke('send-community-ride-push',{body:{ride_id:rideId,event:eventType}});
      if(error)throw error;
      console.log('Community push',eventType,data);
      return data
    }catch(e){
      console.warn('Community push failed',eventType,e);
      return null
    }
  }
  window.tcvSendCommunityRidePush=sendRidePush;

  function install(){
    if(window.__TCV_COMMUNITY_PUSH_WRAPPED)return;
    window.__TCV_COMMUNITY_PUSH_WRAPPED=true;

    const oldPublish=window.publishRideRequest;
    if(typeof oldPublish==='function'){
      window.publishRideRequest=async function(...args){
        const before=await latestOwnRide();
        const out=await oldPublish.apply(this,args);
        const after=await latestOwnRide();
        if(after?.id&&String(after.id)!==String(before?.id||'')){
          await sendRidePush(after.id,'requested');
        }
        return out
      }
    }

    const oldDecision=window.tcvDriverRideDecision;
    if(typeof oldDecision==='function'){
      window.tcvDriverRideDecision=async function(id,status){
        const out=await oldDecision.apply(this,arguments);
        const eventType={matched:'accepted',declined:'declined',onboard:'onboard',completed:'completed'}[status];
        if(eventType)await sendRidePush(id,eventType);
        return out
      }
    }
  }

  let tries=0;const timer=setInterval(()=>{
    tries++;
    if(window.db&&window.SESSION&&typeof window.publishRideRequest==='function'&&typeof window.tcvDriverRideDecision==='function'){
      clearInterval(timer);install()
    }else if(tries>100)clearInterval(timer)
  },200)
})();
