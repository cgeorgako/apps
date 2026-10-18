/* Service Worker για την εφαρμογή «Σημειώσεις .md → Drive» (PWA).
   Cache του app shell ώστε να ανοίγει και offline (η σύνθεση δουλεύει offline,
   το upload στο Drive προφανώς χρειάζεται δίκτυο). Οτιδήποτε εκτός του shell
   (Google APIs, υπόλοιπα εργαλεία ίδιου origin) πάει κατευθείαν στο δίκτυο. */
'use strict';

const CACHE = 'notes-md-v1';
const ASSETS = [
  './notes-md.html',
  './notes-md.webmanifest',
  './notes-md-icon.svg'
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
  if (url.origin !== self.location.origin) return; // Google APIs κ.λπ. → δίκτυο

  // ΜΟΝΟ το app shell διαχειρίζεται ο SW. Οτιδήποτε άλλο ίδιου origin
  // (index.html / dashboard, τα υπόλοιπα εργαλεία) πάει κατευθείαν στο δίκτυο.
  const isShell = /\/(notes-md\.html|notes-md\.webmanifest|notes-md-icon\.svg)$/.test(url.pathname);
  if (!isShell) return;

  // Network-first για το shell: φρέσκια έκδοση όταν υπάρχει δίκτυο,
  // με fallback στο cache όταν είμαστε offline.
  event.respondWith(
    fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match(req))
  );
});
