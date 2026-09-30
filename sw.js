// Theogonia service worker: keeps the app usable offline and picks up new versions.
const CACHE = "theogonia-1f66d3cc1c";
const CORE = ["./", "index.html", "desktop.html", "manifest.webmanifest",
  "icons/icon-192.png", "icons/icon-512.png", "icons/icon-maskable-512.png", "icons/apple-touch-icon.png", "icons/favicon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k.startsWith("theogonia-")).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const req = e.request; if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    if (req.mode === "navigate") {   // pages: try the network first so updates arrive, fall back offline
      e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(k => k.put(req, c)); return r; })
        .catch(() => caches.match(req, {ignoreSearch: true}).then(r => r || caches.match("index.html"))));
    } else {
      e.respondWith(caches.match(req).then(r => r || fetch(req).then(n => { const c = n.clone(); caches.open(CACHE).then(k => k.put(req, c)); return n; })));
    }
  } else if (/fonts\.(googleapis|gstatic)\.com$/.test(url.hostname)) {   // fonts: serve cached, refresh in background
    e.respondWith(caches.open(CACHE + "-fonts").then(c => c.match(req).then(hit => {
      const net = fetch(req).then(r => { c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net; })));
  }
});
