#!/bin/sh
# Copies the web app into native/www so Capacitor can bundle it. Run from anywhere.
set -e
cd "$(dirname "$0")"
rm -rf www && mkdir www
for f in ../basketball.html ../games.js ../logos.js ../stats.js ../ovr.js ../bh.js ../fonts.css ../logo.png ../manifest.webmanifest; do cp "$f" www/; done
# the app opens the live website (launcher.html is the bundle's index.html); the bundled copy of the app is app.html, used when offline
cp ../index.html www/app.html
cp launcher.html www/index.html
cp -r ../fonts ../icons ../vendor ../ads www/
# the service worker is for the website only; the app bundles its own files
echo "www ready: $(du -sh www | cut -f1)"
