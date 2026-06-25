# Paper forward analysis pulls

Point-in-time NAS snapshots for forward paper review. **Not git-tracked by default** — refresh on each review cycle.

| File | Source on NAS |
|------|----------------|
| `ledger_nas_*.json` | `.../paper_trading/ledger.json` |
| `paper_forward_scorecard_nas_*.json` | `.../status/paper_forward_scorecard.json` |
| `latest_paper_signal_nas_*.json` | `.../paper_trading/latest_paper_signal.json` |

**Latest report:** [`PAPER_FORWARD_ANALYSIS_20260625.md`](PAPER_FORWARD_ANALYSIS_20260625.md)

Refresh:

```bash
NAS_HOST=MediaServer2 ./ingest/scripts/pull_paper_forward_dossier.sh
NAS_HOST=MediaServer2 ./ingest/scripts/kmia_paper_ops_watch.sh
```

Automated classification: `ingest/scripts/classify_paper_ledger.py`
