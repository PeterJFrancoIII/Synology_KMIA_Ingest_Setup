#!/bin/bash
# Read-only NAS + local paper-loop health check. Logs to WATCH_LOG_DIR.
# Auto-fix: none (diagnostics only). Operator/agent reviews log.
#
# Usage: NAS_HOST=MediaServer2Local ./ingest/scripts/kmia_paper_ops_watch.sh

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2Local}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="${WATCH_LOG_DIR:-$REPO_ROOT/docs/ops/watch_logs}"
LOG="$LOG_DIR/watch_${STAMP}.log"
LATEST_LINK="$LOG_DIR/latest_watch.log"

mkdir -p "$LOG_DIR"
exec > >(tee -a "$LOG") 2>&1
ln -sf "$LOG" "$LATEST_LINK"

echo "=== KMIA paper ops watch $STAMP ==="

# --- NAS containers ---
ssh "$NAS" 'sudo /var/packages/ContainerManager/target/usr/bin/docker ps --format "{{.Names}} {{.Status}}" | grep -E "paper|arch" || echo NO_CONTAINERS' || echo "SSH_FAIL"

# --- Cron / recent paper loop ---
ssh "$NAS" 'sudo tail -5 /volume2/Data/App_Development/logs/paper_trading/cron.log 2>/dev/null || echo NO_CRON_LOG' || true
ssh "$NAS" 'sudo ls -lt /volume2/Data/App_Development/logs/paper_trading/paper_loop_*.log 2>/dev/null | head -2' || true

# --- Policy + signal on NAS (pull JSON, parse locally) ---
POL_JSON="$(ssh "$NAS" 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/research/trading_policy.json 2>/dev/null' || true)"
SIG_JSON="$(ssh "$NAS" 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/paper_trading/latest_paper_signal.json 2>/dev/null' || true)"
export POL_JSON SIG_JSON
python3 - <<'PY'
import json, os
pol = os.environ.get("POL_JSON", "")
sig = os.environ.get("SIG_JSON", "")
if pol:
    p = json.loads(pol)
    print("policy_approved:", p.get("approved_by_human"), "order_mode:", p.get("order_mode"), "min_edge:", p.get("min_forecast_edge"))
else:
    print("policy: MISSING")
if sig:
    s = json.loads(sig)
    bet = s.get("bet_recommendations") or {}
    tp = bet.get("trading_policy") or {}
    print("signal_utc:", s.get("generated_at_utc"))
    print("signal_exec:", tp.get("order_mode"), "min_edge:", tp.get("min_forecast_edge"), "action:", bet.get("global_action"))
    wg = s.get("weather_gate") or {}
    print("weather_gate:", wg.get("status"), "allow:", wg.get("allow_paper_recommendations"))
else:
    print("signal: MISSING")
PY

# --- Local copies (if synced) ---
KALSHI="$HOME/Desktop/App Development/Kalshi"
for f in backend/data/research/trading_policy.json backend/data/processed/paper_trading/latest_paper_signal.json; do
  if [ -f "$KALSHI/$f" ]; then
    echo "local: $f exists ($(stat -f %Sm -t '%Y-%m-%d %H:%M' "$KALSHI/$f" 2>/dev/null || stat -c %y "$KALSHI/$f" 2>/dev/null))"
  fi
done

# --- Bot console ---
curl -s -o /dev/null -w "bot_console_http: %{http_code}\n" http://127.0.0.1:8502/ 2>/dev/null || echo "bot_console: DOWN"

echo "=== watch complete $STAMP ==="
echo "LOG=$LOG"
