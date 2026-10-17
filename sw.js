/* OALE: con internet baja siempre la versión nueva; sin internet usa la guardada */
const C='oale-cache',F=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./icon-maskable-512.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(F)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim())});
self.addEventListener('fetch',e=>{
 if(e.request.method!=='GET'||new URL(e.request.url).origin!==location.origin)return;
 const u=new URL(e.request.url),key=u.origin+u.pathname;   /* se guarda sin lo que va después del ? para no llenar la memoria */
 const net=fetch(e.request,{cache:'no-cache'}).then(r=>{if(r&&r.ok){const cp=r.clone();caches.open(C).then(c=>c.put(key,cp))}return r});
 const wait=new Promise((_,no)=>setTimeout(no,4000));
 e.respondWith(Promise.race([net,wait]).catch(()=>caches.match(key).then(r=>r||caches.match('./index.html')||net)));
});
