#!/bin/bash
# Read-only NAS + local paper-loop health check. Logs to WATCH_LOG_DIR.
# Auto-fix: none (diagnostics only). Operator/agent reviews log.
#
# Usage: NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh
# (env var must prefix the script invocation — not a separate cd command)

set -euo pipefail

NAS="${NAS_HOST:-MediaServer2}"
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

DOCKER="/var/packages/ContainerManager/target/usr/bin/docker"

# --- NAS containers (paper + WS + arch) ---
ssh "$NAS" "sudo $DOCKER ps --format '{{.Names}} {{.Status}}' | grep -E 'kmia-paper|kmia-orderbook|kmia-arch' || echo NO_CONTAINERS" || echo "SSH_FAIL"

# --- WebSocket daemon heartbeat ---
WS_JSON="$(ssh "$NAS" 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/kalshi_market_archive/ws_daemon_status.json 2>/dev/null' || true)"
export WS_JSON
python3 - <<'PY'
import json, os
from datetime import datetime, timezone
raw = os.environ.get("WS_JSON", "")
if not raw.strip():
    print("ws_daemon: MISSING")
else:
    try:
        ws = json.loads(raw)
    except json.JSONDecodeError:
        print("ws_daemon: INVALID_JSON")
    else:
        print("ws_connected:", ws.get("connected"), "seq_gaps:", ws.get("seq_gap_count"))
        print("ws_subscribed:", len(ws.get("subscribed_tickers") or []))
        hb = ws.get("updated_at_utc") or ws.get("last_message_utc")
        if hb:
            try:
                ts = datetime.fromisoformat(str(hb).replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
                print("ws_heartbeat_age_min:", round(age, 2))
            except ValueError:
                print("ws_heartbeat:", hb)
PY

# --- Smarter paper verify (Kalshi runtime script on NAS) ---
ssh "$NAS" "sudo $DOCKER exec kmia-paper-research python3 /data/Kalshi/scripts/verify_smarter_paper.py 2>/dev/null" || echo "verify_smarter_paper: UNAVAILABLE"

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
    fac = s.get("forecast_accuracy_context") or {}
    ptw = wg.get("paper_trading_window") or {}
    if ptw:
        print(
            "trading_window:", ptw.get("mode"),
            "end_et:", ptw.get("end_time_et"),
            "within:", ptw.get("within_window"),
        )
    if fac:
        print(
            "mae_slice:", fac.get("slice"),
            "stability:", fac.get("forecast_stability"),
            "std_f:", fac.get("distribution_std_f"),
            "forecast_mode_bin:", fac.get("forecast_mode_bin") or s.get("forecast_mode_bin"),
            "prob_model:", fac.get("prob_model_source"),
            "nbm_p10/p90:", fac.get("nbm_p10_f"), fac.get("nbm_p90_f"),
        )
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
