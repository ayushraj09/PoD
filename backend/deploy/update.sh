#!/usr/bin/env bash
# Pull the latest main and rebuild/restart the backend. Run on the server:
#   ~/PoD/backend/deploy/update.sh
set -euo pipefail
cd "$(dirname "$0")"
git -C ../.. pull --ff-only origin main
docker compose up -d --build
docker image prune -f >/dev/null
docker compose ps
echo "health: $(curl -s -m 10 "https://$(grep -E '^API_DOMAIN=' .env | cut -d= -f2)/health" || echo 'not reachable yet')"
