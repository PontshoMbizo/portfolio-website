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

echo "== health check =="
if curl -sf http://127.0.0.1/ >/dev/null; then
  echo "portfolio deploy: OK"
else
  echo "portfolio deploy: FAILED health check" >&2
  exit 1
fi
