#!/usr/bin/env bash
# One-command deploy to the Raspberry Pi: rsync the code, restart the services,
# and verify the dashboard is back up.
#
#   ./scripts/deploy.sh                 # uses the default target below
#   ./scripts/deploy.sh airmon@10.0.0.94
#   AQM_TARGET=airmon@10.0.0.94 ./scripts/deploy.sh
#
# NOTE: target the Pi by IP, not <host>.local — mDNS (.local) can transiently
# fail to resolve on the Mac, which makes rsync fail silently and leaves the Pi
# running old code.
set -euo pipefail

TARGET="${1:-${AQM_TARGET:-airmon@10.0.0.94}}"
PORT="${AQM_PORT:-8000}"

REMOTE_USER="${TARGET%@*}"
HOST="${TARGET#*@}"
REMOTE_DIR="/home/${REMOTE_USER}/air-quality-monitor"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Deploying ${REPO_ROOT}"
echo "    to ${TARGET}:${REMOTE_DIR}"

rsync -az --delete \
  --exclude '.venv' --exclude '__pycache__' --exclude '*.egg-info' \
  --exclude '*.db' --exclude '*.db-*' --exclude 'preview*.png' \
  --exclude 'config.yaml' --exclude '.git' --exclude '.DS_Store' \
  "${REPO_ROOT}/" "${TARGET}:${REMOTE_DIR}/"
echo "==> rsync complete"

echo "==> Restarting services"
ssh "${TARGET}" 'sudo systemctl restart aqm-collector aqm-web'

echo "==> Waiting for the web server (ARMv6 startup is slow)…"
if curl -fs --retry 15 --retry-connrefused --retry-delay 2 --max-time 60 \
     "http://${HOST}:${PORT}/healthz" >/dev/null; then
  ssh "${TARGET}" 'echo "    collector: $(systemctl is-active aqm-collector)  web: $(systemctl is-active aqm-web)"'
  echo "==> ✅ Live at http://${HOST}:${PORT}/"
else
  echo "!! Health check failed — check: ssh ${TARGET} 'journalctl -u aqm-web -n 30'" >&2
  exit 1
fi
