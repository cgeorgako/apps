/* Service Worker για την εφαρμογή «Πινέζα Χάρτη» (PWA).
   Cache του app shell ώστε να ανοίγει και offline. Οι κλήσεις στο
   ArcGIS του Κτηματολογίου πάνε πάντα στο δίκτυο (network-first-για-τρίτους). */
'use strict';

const CACHE = 'maps-pin-v2';
const ASSETS = [
  './maps-pin.html',
  './maps-pin.webmanifest',
  './maps-pin-icon.svg'
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
  if (url.origin !== self.location.origin) return;

  // ΜΟΝΟ το app shell της Πινέζας διαχειρίζεται ο SW. Οτιδήποτε άλλο ίδιου
  // origin (index.html / dashboard, τα υπόλοιπα εργαλεία) πάει ΚΑΤΕΥΘΕΙΑΝ στο
  // δίκτυο — ώστε να μη «μένει» ποτέ παλιά έκδοση από cache.
  const isShell = /\/(maps-pin\.html|maps-pin\.webmanifest|maps-pin-icon\.svg)$/.test(url.pathname);
  if (!isShell) return; // default network handling από τον browser

  // Network-first για το shell: πάντα η φρέσκια έκδοση όταν υπάρχει δίκτυο,
  // με fallback στο cache όταν είμαστε offline.
  event.respondWith(
    fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match(req))
  );
});
