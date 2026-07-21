const CACHE='pushup-v21';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./icon-maskable-512.png','./vendor/fonts/fonts.css','./assets/coach-layma-fox-v1.png','./assets/coach-lime-fox-v1.png','./assets/hero-man-pushup-v1.png','./assets/technique-gym-bg-v1.png'];
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS).catch(()=>{})));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const req=e.request; if(req.method!=='GET')return;
  e.respondWith(caches.match(req).then(r=>r||fetch(req).then(res=>{
    if(res.ok&&new URL(req.url).origin===self.location.origin){try{const copy=res.clone();caches.open(CACHE).then(c=>c.put(req,copy).catch(()=>{}));}catch(_){}}
    return res;
  }).catch(()=>req.mode==='navigate'?caches.match('./index.html'):Response.error())));
});
self.addEventListener('notificationclick',e=>{
  e.notification.close();
  e.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(cl=>{
    for(const c of cl){ if('focus' in c) return c.focus(); }
    if(self.clients.openWindow) return self.clients.openWindow('./');
  }));
});
