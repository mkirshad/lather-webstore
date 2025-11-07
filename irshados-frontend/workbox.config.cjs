module.exports = {
  globDirectory: "build",
  globPatterns: [
    "**/*.{html,js,css,png,jpg,jpeg,svg,webp,ico,json,woff2,woff}"
  ],
  swSrc: "public/service-worker.js",
  swDest: "build/service-worker.js",
  additionalManifestEntries: [
    { url: "/", revision: null },
    { url: "/manifest.json", revision: null },
    { url: "/favicon.svg", revision: null },
    { url: "/offline.html", revision: null }
  ],
  maximumFileSizeToCacheInBytes: 5 * 1024 * 1024
}
