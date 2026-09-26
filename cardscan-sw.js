/* Service Worker για την εφαρμογή «CardScan» (PWA) της CG apps.
   Cache του app shell ώστε να ανοίγει και offline. Η βιβλιοθήκη OCR
   (Tesseract.js) και τα γλωσσικά δεδομένα φορτώνονται από CDN με
   στρατηγική "network-first, fallback σε cache" ώστε να δουλεύουν και
   offline μετά την πρώτη χρήση. */
'use strict';

const CACHE = 'cardscan-v1';
const ASSETS = [
  './cardscan.html',
  './cardscan.webmanifest',
  './cardscan-icon.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
      .catch(() => {})
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // App shell (ίδιο origin, μόνο τα αρχεία της CardScan): network-first ώστε να
  // παίρνουμε πάντα φρέσκια έκδοση όταν υπάρχει δίκτυο, με fallback στο cache.
  const isShell = /\/(cardscan\.html|cardscan\.webmanifest|cardscan-icon\.svg)$/.test(url.pathname);
  if (url.origin === self.location.origin) {
    if (!isShell) return; // ό,τι άλλο ίδιου origin -> κατευθείαν στο δίκτυο
    event.respondWith(
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }

  // Τρίτα origins (CDN για Tesseract.js / γλωσσικά αρχεία): stale-while-cache.
  // Προσπάθησε δίκτυο, αποθήκευσε στο cache, αλλιώς σέρβιρε από cache όταν offline.
  event.respondWith(
    fetch(req).then(res => {
      if (res && res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      }
      return res;
    }).catch(() => caches.match(req))
  );
});
