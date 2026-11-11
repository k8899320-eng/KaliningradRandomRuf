// Кэш игры: файлы отдаются сразу из кэша (мгновенный запуск), а свежая версия
// тихо скачивается в фоне и будет использована при следующем открытии.
const CACHE = "roofer-v12";
const FILES = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "vendor/three.game.min.js", "classic.html"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  if (url.origin !== self.location.origin) return; // Supabase и прочее — мимо кэша
  e.respondWith(caches.open(CACHE).then(async c => {
    const hit = await c.match(e.request, { ignoreSearch: true });
    const net = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; });
    if (hit) { e.waitUntil(net.catch(() => {})); return hit; }
    return net.catch(() => c.match("index.html"));
  }));
});
