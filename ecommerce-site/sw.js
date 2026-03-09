// Service Worker for Push Notifications
const CACHE_NAME = 'cali-clear-admin-v1';

// Install event
self.addEventListener('install', (event) => {
    console.log('Service Worker installing.');
    self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
    console.log('Service Worker activated.');
    event.waitUntil(clients.claim());
});

// Push event - when notification is received
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    
    const title = data.title || 'Cali Clear Admin';
    const options = {
        body: data.body || 'New notification',
        icon: '/assets/images/logo.png',
        badge: '/assets/images/logo.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/admin.html'
        },
        actions: [
            { action: 'open', title: 'Open' },
            { action: 'dismiss', title: 'Dismiss' }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'dismiss') {
        return;
    }
    
    const url = event.notification.data.url || '/admin.html';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // If a window is already open, focus it
                for (const client of clientList) {
                    if (client.url.includes('admin.html') && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Otherwise, open a new window
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

// Background sync for offline support
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-orders') {
        console.log('Background sync for orders');
    }
});
