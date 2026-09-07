#!/usr/bin/env bash
# Start RepoPulse and a public HTTPS tunnel (cloudflared trycloudflare).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"
export SUPPORT_EMAIL="${SUPPORT_EMAIL:-magnedinanevesdina@gmail.com}"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -r "$ROOT/requirements.txt"
fi

if [[ ! -x /tmp/cloudflared ]]; then
  curl -fsSL -o /tmp/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
  chmod +x /tmp/cloudflared
fi

mkdir -p /tmp/repopulse
"$ROOT/.venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 \
  >/tmp/repopulse/uvicorn.log 2>&1 &
echo $! >/tmp/repopulse/uvicorn.pid

for i in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null; then
    break
  fi
  sleep 0.3
done

/tmp/cloudflared tunnel --url http://127.0.0.1:8000 --no-autoupdate \
  >/tmp/repopulse/cloudflared.log 2>&1 &
echo $! >/tmp/repopulse/cloudflared.pid

PUBLIC=""
for i in $(seq 1 40); do
  PUBLIC="$(grep -oE 'https://[a-zA-Z0-9.-]+\.trycloudflare\.com' /tmp/repopulse/cloudflared.log | head -1 || true)"
  if [[ -n "$PUBLIC" ]]; then
    break
  fi
  sleep 0.5
done

echo "LOCAL  http://127.0.0.1:8000"
echo "PUBLIC ${PUBLIC:-pending — see /tmp/repopulse/cloudflared.log}"
echo "SETUP  ${PUBLIC}/setup"
echo "STATUS ${PUBLIC}/status"
echo "DEV    https://github.com/developer/register"
