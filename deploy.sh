#!/bin/bash
# Redeploy portfolio-website from origin/main. Invoked by GitHub Actions over the
# restricted gha_deploy SSH key (same key used by nikaVSimulator/stmVSimulator —
# see ~/bin/gha-deploy-dispatch.sh), or run by hand.
#
# Static site, no build step: just pull and copy index.html into nginx's root.
set -euo pipefail
cd ~/apps/portfolio-website

echo "== fetching origin/main =="
git fetch origin main
git reset --hard origin/main

echo "== publishing index.html =="
cp index.html /var/www/pontsho-mbizo/index.html

echo "== publishing cv.pdf =="
cp cv.pdf /var/www/pontsho-mbizo/cv.pdf

echo "== publishing content.json (git is the source of truth) =="
cp content.json /var/www/pontsho-mbizo/content.json

echo "== publishing favico.png and images/ =="
cp favico.png /var/www/pontsho-mbizo/favico.png
if [ -d images ]; then
  rm -rf /var/www/pontsho-mbizo/images
  cp -r images /var/www/pontsho-mbizo/images
fi

echo "== removing old /admin (no longer part of the site) =="
rm -rf /var/www/pontsho-mbizo/admin

echo "== health check =="
# Ask nginx for the real site on this machine: HTTPS first (pinned to
# 127.0.0.1 so it never leaves the VM), then plain HTTP with the Host header.
SITE=pontsho-mbizo.co.za
if curl -sfk -o /dev/null --resolve "$SITE:443:127.0.0.1" "https://$SITE/content.json" \
   || curl -sf -o /dev/null -H "Host: $SITE" "http://127.0.0.1/content.json"; then
  echo "portfolio deploy: OK"
else
  echo "portfolio deploy: FAILED health check" >&2
  curl -sk -o /dev/null -w "https: %{http_code}\n" --resolve "$SITE:443:127.0.0.1" "https://$SITE/content.json" >&2 || true
  curl -s -o /dev/null -w "http:  %{http_code}\n" -H "Host: $SITE" "http://127.0.0.1/content.json" >&2 || true
  exit 1
fi
