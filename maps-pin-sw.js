/* Service Worker για την εφαρμογή «Πινέζα Χάρτη» (PWA).
   Cache του app shell ώστε να ανοίγει και offline. Οι κλήσεις στο
   ArcGIS του Κτηματολογίου πάνε πάντα στο δίκτυο (network-first-για-τρίτους). */
'use strict';

const CACHE = 'maps-pin-v1';
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
  // Μόνο το app shell (ίδιο origin) σερβίρεται από cache· τα υπόλοιπα (ArcGIS,
  // fonts) πάνε στο δίκτυο.
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(req).then(cached => cached || fetch(req).then(res => {
      // Ενημέρωση cache για μελλοντική offline χρήση
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
      return res;
    }).catch(() => cached))
  );
});
