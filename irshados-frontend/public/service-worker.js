/* eslint-disable no-restricted-globals */

importScripts("https://storage.googleapis.com/workbox-cdn/releases/6.6.0/workbox-sw.js")

const OFFLINE_FALLBACK_PAGE = "/offline.html"
const STATIC_CACHE_NAME = "irshados-static-v1"
const API_CACHE_NAME = "irshados-api-v1"
const BG_SYNC_QUEUE = "irshados-offline-post-queue"

if (self.workbox) {
    const { backgroundSync, cacheableResponse, core, expiration, precaching, routing, strategies } = self.workbox

    core.setCacheNameDetails({ prefix: "irshados" })

    const manifestEntries = self.__WB_MANIFEST
    const precacheManifest = Array.isArray(manifestEntries) ? [...manifestEntries] : []
    const appShellEntries = [
        { url: "/", revision: null },
        { url: "/manifest.json", revision: null },
        { url: "/favicon.svg", revision: null },
        { url: OFFLINE_FALLBACK_PAGE, revision: null },
    ]

    appShellEntries.forEach((entry) => {
        if (!precacheManifest.some((item) => item.url === entry.url)) {
            precacheManifest.push(entry)
        }
    })

    precaching.precacheAndRoute(precacheManifest)
    precaching.cleanupOutdatedCaches()

    routing.registerRoute(
        ({ request }) => request.mode === "navigate",
        new strategies.NetworkFirst({
            cacheName: "irshados-pages",
            networkTimeoutSeconds: 5,
            plugins: [
                new cacheableResponse.CacheableResponsePlugin({ statuses: [0, 200] }),
                new expiration.ExpirationPlugin({ maxEntries: 20, purgeOnQuotaError: true }),
            ],
        })
    )

    routing.registerRoute(
        ({ request }) =>
            request.destination === "style" || request.destination === "script" || request.destination === "worker",
        new strategies.StaleWhileRevalidate({
            cacheName: STATIC_CACHE_NAME,
            plugins: [
                new cacheableResponse.CacheableResponsePlugin({ statuses: [0, 200] }),
                new expiration.ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 30 * 24 * 60 * 60 }),
            ],
        })
    )

    routing.registerRoute(
        ({ request }) => request.destination === "image" || request.destination === "font",
        new strategies.CacheFirst({
            cacheName: "irshados-media",
            plugins: [
                new cacheableResponse.CacheableResponsePlugin({ statuses: [0, 200] }),
                new expiration.ExpirationPlugin({ maxEntries: 120, maxAgeSeconds: 60 * 24 * 60 * 60, purgeOnQuotaError: true }),
            ],
        })
    )

    routing.registerRoute(
        ({ url, request }) => url.origin === self.location.origin && url.pathname.startsWith("/api/") && request.method === "GET",
        new strategies.StaleWhileRevalidate({
            cacheName: API_CACHE_NAME,
            plugins: [
                new cacheableResponse.CacheableResponsePlugin({ statuses: [0, 200] }),
                new expiration.ExpirationPlugin({ maxEntries: 50, maxAgeSeconds: 5 * 60 }),
            ],
        })
    )

    const backgroundSyncPlugin = new backgroundSync.BackgroundSyncPlugin(BG_SYNC_QUEUE, {
        maxRetentionTime: 24 * 60,
    })

    routing.registerRoute(
        ({ url, request }) => url.origin === self.location.origin && request.method === "POST",
        new strategies.NetworkOnly({
            plugins: [backgroundSyncPlugin],
        }),
        "POST"
    )

    routing.setCatchHandler(async ({ event }) => {
        if (event.request.destination === "document") {
            const cachedPage = await caches.match(OFFLINE_FALLBACK_PAGE)
            return cachedPage ?? Response.error()
        }

        if (event.request.headers.get("accept")?.includes("application/json")) {
            return new Response(
                JSON.stringify({
                    error: "offline",
                    message: "This content is unavailable while you are offline.",
                }),
                {
                    status: 503,
                    headers: { "Content-Type": "application/json" },
                }
            )
        }

        return Response.error()
    })

    core.clientsClaim()
} else {
    console.warn("[PWA] Workbox failed to load. Offline support will be limited.")
}

self.addEventListener("message", (event) => {
    if (event.data?.type === "SKIP_WAITING") {
        self.skipWaiting()
    }
})
