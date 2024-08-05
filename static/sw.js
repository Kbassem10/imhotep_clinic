const CACHE_NAME = 'flask-app-cache-v1';
const urlsToCache = [
    '/',
    '/static/kbclinic.png',
    '/static/kbclinic.ico',
    '/static/manifest.json',
    '/static/app.css'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                return response || fetch(event.request);
            })
    );
});
