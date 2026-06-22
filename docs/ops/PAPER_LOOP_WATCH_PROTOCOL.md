# Paper loop watch protocol (9h agent loop)

**Created:** 2026-06-20  
**Mode:** Read-only diagnostics unless explicit failure

## Restore from backup

Backups live under:

`~/Desktop/App Development/KMIA_System_Backups/pre_watch_20260620/`

```bash
# Example restore Console 2 (destructive — extract elsewhere first)
cd "/Users/computer/Desktop/App Development"
tar xzf KMIA_System_Backups/pre_watch_20260620/Synology_KMIA_Ingest_Setup.tar.gz
```

See `MANIFEST.txt` in that folder for checksums.

## Agent rules during watch

**Allowed (green):**
- Read NAS logs via SSH
- Run `ingest/scripts/kmia_paper_ops_watch.sh`
- Restart `kmia-paper-research` container if exited (no rebuild)
- Re-run `run_nas_paper_loop.sh` once if cron silent >30 min

**Forbidden without human approval:**
- Git force push, mass deletes, policy re-approval
- NAS secrets, trading_policy.json edits
- Code changes in Kalshi/Console2 unless single-line cron fix

## Watch log

`docs/ops/watch_logs/latest_watch.log` (in this repo)

## Loop

30-minute ticks for 9 hours via background shell sentinel `AGENT_LOOP_TICK_paper_watch`.
