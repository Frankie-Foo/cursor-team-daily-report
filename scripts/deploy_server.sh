#!/usr/bin/env bash
# One-shot server deploy (Linux). Run ON the server after git clone.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PUBLIC_URL="${1:-https://global-pdca.vertu.cn}"
PORT="${API_PORT:-8080}"

echo "=== Cursor Team Daily Report - Server Deploy ==="

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env - EDIT DB_PASSWORD"
fi

if [[ ! -f config/api_tokens.json ]]; then
  echo "Missing config/api_tokens.json - copy from laptop"
  exit 1
fi

echo "[1/5] pip install..."
python3 -m pip install -r requirements.txt

echo "[2/5] public URL..."
python3 scripts/set_production_url.py --public-url "${PUBLIC_URL%/}"

echo "[3/5] DB schema..."
python3 scripts/db_schema.py --create-db || true

echo "[4/5] local health..."
python3 -m uvicorn api.server:app --host 127.0.0.1 --port "$PORT" &
PID=$!
sleep 3
if curl -sf "http://127.0.0.1:${PORT}/api/v1/health"; then
  echo ""
  echo "Local API OK"
else
  echo "Local API failed"
fi
kill "$PID" 2>/dev/null || true

echo "[5/5] export credentials..."
python3 scripts/export_member_credentials.py

cat <<EOF

=== Done ===
1. Ask ops: nginx proxy $PUBLIC_URL -> http://127.0.0.1:$PORT
2. Start API: python3 -m uvicorn api.server:app --host 0.0.0.0 --port $PORT
3. Verify: curl $PUBLIC_URL/api/v1/health
4. Send package/colleague zip + config/member_credentials.md to team
EOF
