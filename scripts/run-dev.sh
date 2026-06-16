#!/usr/bin/env bash
# Run the collector + web dashboard locally with the mock sensor. Ctrl-C stops both.
set -euo pipefail

[ -f config.yaml ] || cp config.example.yaml config.yaml

aqm-collect &
COLLECTOR=$!
trap 'kill "$COLLECTOR" 2>/dev/null || true' EXIT

aqm-web
