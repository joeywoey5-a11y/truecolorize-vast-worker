#!/usr/bin/env bash
set -euo pipefail
DIR="${PYWORKER_DIR:-/workspace/truecolorize-vast-worker}"
LOG="/var/log/truecolorize"
mkdir -p "$LOG"
if [ ! -d "$DIR/.git" ]; then
  rm -rf "$DIR"; git clone "$PYWORKER_REPO" "$DIR"
fi
cd "$DIR"
git fetch --all --prune || true
git checkout "${PYWORKER_REF:-main}"
git pull --ff-only || true
python -m pip install --no-cache-dir -r requirements.txt
: > "$LOG/model.log"
nohup python -u run_model_server.py > "$LOG/model.log" 2>&1 &
for i in $(seq 1 180); do
  curl -fsS http://127.0.0.1:18000/health >/dev/null 2>&1 && break
  sleep 1
done
exec python -u worker.py
