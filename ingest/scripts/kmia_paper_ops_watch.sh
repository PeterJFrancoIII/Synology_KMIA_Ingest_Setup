#!/bin/bash
# Read-only NAS + local paper-loop health check. Logs to WATCH_LOG_DIR.
# Exit codes: 0=all green, 1=yellow warnings, 2=red critical failure.
#
# Usage: NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh

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
EXIT_CODE=0

# --- NAS containers (paper + WS + arch) ---
CONTAINERS="$(ssh "$NAS" "sudo $DOCKER ps --format '{{.Names}} {{.Status}}' | grep -E 'kmia-paper|kmia-orderbook|kmia-arch' || echo NO_CONTAINERS" || echo SSH_FAIL)"
echo "$CONTAINERS"
if echo "$CONTAINERS" | grep -q 'NO_CONTAINERS\|SSH_FAIL'; then
  echo "ALERT_RED: containers missing or SSH failed"
  EXIT_CODE=2
fi

# --- WebSocket daemon heartbeat ---
WS_JSON="$(ssh "$NAS" 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/kalshi_market_archive/ws_daemon_status.json 2>/dev/null' || true)"
LEDGER_JSON="$(ssh "$NAS" 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/paper_trading/ledger.json 2>/dev/null' || true)"
CRON_TAIL="$(ssh "$NAS" 'sudo tail -1 /volume2/Data/App_Development/logs/paper_trading/cron.log 2>/dev/null' || true)"
export WS_JSON LEDGER_JSON CRON_TAIL
python3 - <<'PY'
import json, os, re
from datetime import datetime, timezone

def alert(level, msg):
    print(f"ALERT_{level}: {msg}")

ws_raw = os.environ.get("WS_JSON", "")
if not ws_raw.strip():
    alert("RED", "ws_daemon_status.json missing")
else:
    try:
        ws = json.loads(ws_raw)
    except json.JSONDecodeError:
        alert("RED", "ws_daemon_status invalid JSON")
    else:
        print("ws_connected:", ws.get("connected"), "seq_gaps:", ws.get("seq_gap_count"))
        print("ws_subscribed:", len(ws.get("subscribed_tickers") or []))
        hb = ws.get("updated_at_utc") or ws.get("last_message_utc")
        if hb:
            try:
                ts = datetime.fromisoformat(str(hb).replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
                print("ws_heartbeat_age_min:", round(age, 2))
                if age > 120:
                    alert("RED", f"WS heartbeat stale ({age:.1f} min)")
                elif age > 90:
                    alert("YELLOW", f"WS heartbeat aging ({age:.1f} min)")
            except ValueError:
                print("ws_heartbeat:", hb)
        if not ws.get("connected"):
            alert("RED", "WS daemon not connected")
PY

# --- Smarter paper verify (Kalshi runtime script on NAS) ---
ssh "$NAS" "sudo $DOCKER exec kmia-paper-research python3 /data/Kalshi/scripts/verify_smarter_paper.py 2>/dev/null" || echo "verify_smarter_paper: UNAVAILABLE"

# --- Cron / recent paper loop ---
ssh "$NAS" 'sudo tail -5 /volume2/Data/App_Development/logs/paper_trading/cron.log 2>/dev/null || echo NO_CRON_LOG' || true
ssh "$NAS" 'sudo ls -lt /volume2/Data/App_Development/logs/paper_trading/paper_loop_*.log 2>/dev/null | head -2' || true

# --- Policy + signal + ledger on NAS ---
POL_JSON="$(ssh "$NAS" 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/research/trading_policy.json 2>/dev/null' || true)"
SIG_JSON="$(ssh "$NAS" 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/paper_trading/latest_paper_signal.json 2>/dev/null' || true)"
NWS_JSON="$(ssh "$NAS" 'sudo cat /volume2/Data/App_Development/Kalshi/backend/data/processed/weather_nws/latest_nws_kmia_snapshot.json 2>/dev/null' || true)"
export POL_JSON SIG_JSON NWS_JSON LEDGER_JSON CRON_TAIL
HEALTH_EXIT="$(python3 - <<'PY'
import json, os, re, sys
from datetime import datetime, timezone

red = []
yellow = []

def mark(level, msg):
    (red if level == "RED" else yellow).append(msg)
    print(f"ALERT_{level}: {msg}")

pol = os.environ.get("POL_JSON", "")
sig = os.environ.get("SIG_JSON", "")
nws = os.environ.get("NWS_JSON", "")
ledger_raw = os.environ.get("LEDGER_JSON", "")
cron_tail = os.environ.get("CRON_TAIL", "")

if pol:
    p = json.loads(pol)
    print("policy_approved:", p.get("approved_by_human"), "order_mode:", p.get("order_mode"), "min_edge:", p.get("min_forecast_edge"))
else:
    mark("RED", "trading_policy.json missing on NAS")

if sig:
    s = json.loads(sig)
    bet = s.get("bet_recommendations") or {}
    tp = bet.get("trading_policy") or {}
    print("signal_utc:", s.get("generated_at_utc"))
    print("signal_exec:", tp.get("order_mode"), "min_edge:", tp.get("min_forecast_edge"), "action:", bet.get("global_action"))
    wg = s.get("weather_gate") or {}
    print("weather_gate:", wg.get("status"), "allow:", wg.get("allow_paper_recommendations"))
    print("current_temp_f:", nws and json.loads(nws).get("current_temp_f") if nws else None)
    if wg.get("status") == "ERROR":
        mark("RED", f"weather_gate ERROR: {wg.get('no_trade_reason')}")
    elif wg.get("status") == "STALE":
        mark("YELLOW", f"weather_gate STALE: {wg.get('no_trade_reason')}")
    if not wg.get("allow_paper_recommendations", False):
        reason = wg.get("no_trade_reason") or bet.get("global_block_reason")
        if wg.get("status") == "ERROR":
            pass
        elif reason and "open" in str(reason).lower():
            mark("YELLOW", f"entries blocked: {reason}")
        elif reason:
            mark("YELLOW", f"paper recommendations blocked: {reason}")
    fac = s.get("forecast_accuracy_context") or {}
    ptw = wg.get("paper_trading_window") or {}
    if ptw:
        print("trading_window:", ptw.get("mode"), "end_et:", ptw.get("end_time_et"), "within:", ptw.get("within_window"))
    if fac:
        print(
            "mae_slice:", fac.get("slice"),
            "stability:", fac.get("forecast_stability"),
            "std_f:", fac.get("distribution_std_f"),
            "forecast_mode_bin:", fac.get("forecast_mode_bin") or s.get("forecast_mode_bin"),
            "prob_model:", fac.get("prob_model_source"),
        )
    if pol:
        approved_mode = json.loads(pol).get("order_mode")
        live_mode = tp.get("live_order_mode") or tp.get("order_mode")
        if approved_mode and live_mode and approved_mode != live_mode:
            mark("RED", f"order_mode mismatch policy={approved_mode!r} signal={live_mode!r}")
else:
    mark("RED", "latest_paper_signal.json missing on NAS")

if nws:
    snap = json.loads(nws)
    if snap.get("endpoint_status") == "ERROR":
        mark("RED", "NWS snapshot endpoint_status ERROR")
    if snap.get("current_temp_f") is None:
        mark("RED", "NWS current_temp_f missing")
    elif snap.get("stale_data"):
        mark("YELLOW", "NWS stale_data flag set")
else:
    mark("RED", "latest_nws_kmia_snapshot.json missing")

if ledger_raw:
    ledger = json.loads(ledger_raw)
    trades = ledger.get("trades") or []
    real = [t for t in trades if str(t.get("market_ticker", "")).startswith("KXHIGHMIA-")]
    mock = [t for t in trades if str(t.get("market_ticker", "")).startswith("MOCK")]
    settled = [t for t in real if str(t.get("status", "")).lower() in ("settled", "closed", "won", "lost")]
    wins = sum(1 for t in settled if float(t.get("pnl") or 0) > 0)
    mock_wins = sum(1 for t in mock if float(t.get("pnl") or 0) > 0 and str(t.get("status", "")).lower() in ("settled", "closed", "won", "lost"))
    print(f"ledger_real_settled: {len(settled)} wins: {wins} mock_wins: {mock_wins}")
    if mock_wins > 0 and wins == 0:
        mark("YELLOW", "MOCK trades are the only wins in ledger — use real_kxhighmia scorecard stats")
    maker_settled = sum(1 for t in settled if str(t.get("order_mode") or "").lower() == "maker_limit")
    print(f"ledger_maker_limit_settled: {maker_settled} (gate 10)")
    print(f"ledger_real_settled_gate: {len(settled)}/20")

if cron_tail:
    m = re.search(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})", cron_tail)
    if m:
        try:
            ts = datetime.fromisoformat(m.group(1).replace(" ", "T")).replace(tzinfo=timezone.utc)
            age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60.0
            print("cron_last_age_min:", round(age_min, 1))
            if age_min > 30:
                mark("RED", f"paper cron silent {age_min:.0f} min")
        except ValueError:
            pass

if red:
    sys.exit(2)
if yellow:
    sys.exit(1)
sys.exit(0)
PY
)"
HEALTH_EXIT="${HEALTH_EXIT:-0}"
if [ "$HEALTH_EXIT" -gt "$EXIT_CODE" ]; then
  EXIT_CODE="$HEALTH_EXIT"
fi

# --- Local copies (if synced) ---
KALSHI="$HOME/Desktop/App Development/Kalshi"
for f in backend/data/research/trading_policy.json backend/data/processed/paper_trading/latest_paper_signal.json; do
  if [ -f "$KALSHI/$f" ]; then
    echo "local: $f exists ($(stat -f %Sm -t '%Y-%m-%d %H:%M' "$KALSHI/$f" 2>/dev/null || stat -c %y "$KALSHI/$f" 2>/dev/null))"
  fi
done

# --- Bot console (optional; yellow only) ---
BOT_HTTP="$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8502/ 2>/dev/null || echo "000")"
echo "bot_console_http: $BOT_HTTP"
if [ "$BOT_HTTP" != "200" ]; then
  echo "ALERT_YELLOW: bot_console not reachable on :8502"
  if [ "$EXIT_CODE" -lt 1 ]; then EXIT_CODE=1; fi
fi

echo "=== watch complete $STAMP exit=$EXIT_CODE ==="
echo "LOG=$LOG"
exit "$EXIT_CODE"
