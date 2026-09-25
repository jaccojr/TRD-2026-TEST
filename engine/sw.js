/* Event app engine service worker (v0.1-PRELIMINARY).
   Own cache name and own scope (/engine/), so it never touches v2.29's cache at the repo root.
   Rule carried over from TRD: bump CACHE whenever a same-named asset changes. */
const CACHE = "engine-trd2026-v0.1.1";
const CORE = ["./", "index.html", "event.json", "weather-keymap.json",
  "ui.en.json", "ui.nl.json", "sport-cycling.en.json", "sport-cycling.nl.json",
  "weather.en.json", "weather.nl.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith("engine-") && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;              // fonts, map tiles: browser default
  if (url.pathname.endsWith("compare.html")) return;        // test page, never cached
  const fresh = /\.(html|json)$/.test(url.pathname) || url.pathname.endsWith("/");
  if (fresh) {                                              // network first, cache as offline fallback
    e.respondWith(fetch(req, {cache: "no-store"}).then(r => {
      if (r.ok) { const cp = r.clone(); caches.open(CACHE).then(c => c.put(req, cp)); }
      return r;
    }).catch(() => caches.match(req, {ignoreSearch: true})));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {  // photos, logos: cache first
    if (r.ok) { const cp = r.clone(); caches.open(CACHE).then(c => c.put(req, cp)); }
    return r;
  })));
});
