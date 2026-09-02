self.addEventListener('install',()=>self.skipWaiting());
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));

self.addEventListener('push',event=>{
  let data={};
  try{data=event.data?event.data.json():{}}catch(e){data={title:'Tanto Ci Vai',body:event.data?.text()||'Hai una nuova notifica'}}
  const title=data.title||'Tanto Ci Vai';
  const options={
    body:data.body||'Hai una nuova richiesta.',
    icon:'assets/tcv-splash-logo.jpg',
    badge:'assets/tcv-splash-logo.jpg',
    tag:data.tag||'tcv-push',
    renotify:true,
    silent:false,
    requireInteraction:true,
    timestamp:Date.now(),
    vibrate:[180,80,180],
    data:{url:data.url||'./',request_id:data.request_id||null}
  };
  event.waitUntil(self.registration.showNotification(title,options));
});

self.addEventListener('notificationclick',event=>{
  event.notification.close();
  const url=event.notification.data?.url||'./';
  const requestId=event.notification.data?.request_id||null;
  event.waitUntil((async()=>{
    const list=await self.clients.matchAll({type:'window',includeUncontrolled:true});
    for(const client of list){
      try{
        if('focus' in client){await client.focus();client.postMessage({type:'TCV_OPEN_REQUEST',request_id:requestId});return}
      }catch(e){}
    }
    if(self.clients.openWindow)await self.clients.openWindow(url);
  })());
});
