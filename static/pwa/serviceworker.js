/**
 * Roomora PWA Service Worker
 * Version: 1.0.0
 * Handles offline caching, asset caching, and network resilience.
 */

const CACHE_NAME = 'roomora-pwa-v1';
const OFFLINE_URL = '/offline/';

// Critical static assets to pre-cache on install
const PRECACHE_ASSETS = [
    '/',
    OFFLINE_URL,
    '/manifest.json',
    '/static/pwa/icons/icon-192.png',
    '/static/pwa/icons/icon-512.png',
    '/static/pwa/icons/favicon-32.png',
    '/static/pwa/js/mobile-enhancements.js',
    '/static/landing/css/main.css',
    '/static/landing/js/accordion.js',
    'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap'
];

// Install Event - Pre-cache offline shell
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[Roomora SW] Pre-caching offline pages and assets');
            return cache.addAll(PRECACHE_ASSETS).catch((err) => {
                console.warn('[Roomora SW] Some precache assets failed:', err);
            });
        }).then(() => self.skipWaiting())
    );
});

// Activate Event - Clean up stale caches and claim clients immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((name) => {
                    if (name !== CACHE_NAME) {
                        console.log('[Roomora SW] Removing old cache:', name);
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch Event - Handle offline routing and caching
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // Bypass non-GET requests (POST, PUT, DELETE for bookings/payments must go straight to server)
    if (request.method !== 'GET') {
        return;
    }

    // Bypass API and WebSocket routes
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/') || url.pathname.startsWith('/admin/')) {
        return;
    }

    // HTML Navigation requests (pages) -> Network-first with offline fallback
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then((networkResponse) => {
                    // Update the cache with the latest page copy if valid response
                    if (networkResponse && networkResponse.status === 200) {
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseToCache);
                        });
                    }
                    return networkResponse;
                })
                .catch(async () => {
                    // If network fails, check cache first
                    const cachedResponse = await caches.match(request);
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // Otherwise return the dedicated offline fallback page
                    const offlinePage = await caches.match(OFFLINE_URL);
                    return offlinePage || new Response('You are offline', {
                        status: 503,
                        statusText: 'Service Unavailable',
                        headers: { 'Content-Type': 'text/html' }
                    });
                })
        );
        return;
    }

    // Static Assets (CSS, JS, Fonts, Images) -> Stale-while-revalidate / Cache-first
    if (
        url.pathname.startsWith('/static/') ||
        url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('fonts.gstatic.com') ||
        request.destination === 'style' ||
        request.destination === 'script' ||
        request.destination === 'image' ||
        request.destination === 'font'
    ) {
        event.respondWith(
            caches.match(request).then((cachedResponse) => {
                const fetchPromise = fetch(request).then((networkResponse) => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseToCache = networkResponse.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseToCache);
                        });
                    }
                    return networkResponse;
                }).catch(() => {
                    // Ignore background fetch errors if cached asset exists
                });

                return cachedResponse || fetchPromise;
            })
        );
        return;
    }

    // Default fallback to network
    event.respondWith(
        fetch(request).catch(() => caches.match(request))
    );
});

// Push Notification Event
self.addEventListener('push', (event) => {
    let payload = { title: 'Roomora Alert', body: 'You have a new update.' };
    if (event.data) {
        try {
            payload = event.data.json();
        } catch (e) {
            payload.body = event.data.text();
        }
    }

    const options = {
        body: payload.body,
        icon: '/static/pwa/icons/icon-192.png',
        badge: '/static/pwa/icons/favicon-32.png',
        vibrate: [100, 50, 100],
        data: {
            url: payload.url || '/'
        }
    };

    event.waitUntil(
        self.registration.showNotification(payload.title, options)
    );
});

// Notification Click Event
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const targetUrl = event.notification.data ? event.notification.data.url : '/';
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
            for (let client of windowClients) {
                if (client.url === targetUrl && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
