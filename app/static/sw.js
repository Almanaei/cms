const CACHE_NAME = 'cms-v1';
const ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/icons/icon-192x192.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

// Install Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return cache.addAll(ASSETS);
            })
    );
});

// Activate Service Worker
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        })
    );
});

// Fetch Event Strategy
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch new version
                return response || fetch(event.request)
                    .then(fetchResponse => {
                        // Cache new responses for static assets
                        if (event.request.url.match(/\.(css|js|png|jpg|jpeg|gif|ico)$/)) {
                            return caches.open(CACHE_NAME)
                                .then(cache => {
                                    cache.put(event.request, fetchResponse.clone());
                                    return fetchResponse;
                                });
                        }
                        return fetchResponse;
                    });
            })
            .catch(() => {
                // Return offline fallback for HTML requests
                if (event.request.mode === 'navigate') {
                    return caches.match('/offline.html');
                }
            })
    );
});
