self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));

self.addEventListener('push',event=>{
  let data={};
  try{data=event.data?event.data.json():{}}catch(e){data={title:'Tanto Ci Vai',body:event.data?.text()||'Hai una nuova notifica'}}
  const title=data.title||'Tanto Ci Vai';
  const isHelp=data.event==='help_alert'||data.event==='hazard_alert';
  const options={
    body:data.body||'Hai una nuova richiesta.',
    icon:'assets/tcv-splash-logo.jpg?v=2',
    badge:'assets/tcv-splash-logo.jpg?v=2',
    tag:data.tag||'tcv-push',
    renotify:true,
    silent:false,
    requireInteraction:true,
    timestamp:Date.now(),
    vibrate:isHelp?[400,140,400,140,700]:[180,80,180],
    data:{
      url:data.url||'./',
      request_id:data.request_id||null,
      event:data.event||null,
      help_id:data.help_id||null,
      help_kind:data.help_kind||null,
      lat:data.lat??null,
      lng:data.lng??null
    }
  };
  event.waitUntil(self.registration.showNotification(title,options));
});

self.addEventListener('notificationclick',event=>{
  event.notification.close();
  const data=event.notification.data||{};
  const url=data.url||'./';
  const requestId=data.request_id||null;
  event.waitUntil((async()=>{
    if((data.event==='help_alert'||data.event==='hazard_alert')&&url&&url!=='./'){
      if(self.clients.openWindow)await self.clients.openWindow(url);
      return;
    }
    const list=await self.clients.matchAll({type:'window',includeUncontrolled:true});
    for(const client of list){
      try{
        if('focus' in client){await client.focus();client.postMessage({type:'TCV_OPEN_REQUEST',request_id:requestId});return}
      }catch(e){}
    }
    if(self.clients.openWindow)await self.clients.openWindow(url);
  })());
});
