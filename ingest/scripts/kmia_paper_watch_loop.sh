#!/bin/bash
# 9-hour agent wake loop — emits AGENT_LOOP_TICK_paper_watch every 30 minutes.
# Started by agent; kill this PID to stop.

set -euo pipefail
END="${END_EPOCH:-$(( $(date +%s) + 9 * 3600 ))}"
INTERVAL="${WATCH_INTERVAL_S:-1800}"
PROMPT='KMIA 9h watch: run ingest/scripts/kmia_paper_ops_watch.sh, read docs/ops/watch_logs/latest_watch.log. Allowed fixes: restart kmia-paper-research if Exited; docker exec run_nas_paper_loop if cron silent >30m. No code edits without human approval. Brief status only.'

echo "AGENT_LOOP_START_paper_watch end_epoch=$END interval_s=$INTERVAL pid=$$"
while [ "$(date +%s)" -lt "$END" ]; do
  sleep "$INTERVAL"
  if [ "$(date +%s)" -ge "$END" ]; then
    break
  fi
  printf 'AGENT_LOOP_TICK_paper_watch {"prompt":"%s"}\n' "$PROMPT"
  # Force line to log file immediately for monitored-shell wake.
  sync 2>/dev/null || true
done
printf 'AGENT_LOOP_TICK_paper_watch {"prompt":"KMIA 9h watch FINAL: run watch script, summarize session, list unresolved issues."}\n'
echo "AGENT_LOOP_END_paper_watch"
