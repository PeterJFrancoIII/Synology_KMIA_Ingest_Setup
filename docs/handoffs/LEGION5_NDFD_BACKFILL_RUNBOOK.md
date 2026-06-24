# Legion5 NDFD backfill + full policy sweep — operator runbook

**Created:** 2026-06-23  
**When:** NAS daily pipeline shows forecast validation gaps (`64 without forecast validation`) or scorecard &lt; 90% join.

NAS cannot run NDFD extract without Legion5-produced `kalshi_ndfd_maxt_VALID_ONLY.csv`. This runbook is the **primary** path to full backtest coverage.

---

## Prerequisites

1. Mac deploy (once per session):

```bash
cd "/Users/computer/Desktop/App Development/Synology_KMIA_Ingest_Setup"
scp legion5/{52,54,55}* legion5/kmia_kalshi_legion5_env.sh legion5/kmia_legion5_env.sh \
  Viper117@Legion5:/d/KMIA_Process/scripts/
```

2. Legion5: `Z:` NAS SMB mounted (`43_setup_nas_smb.ps1` if needed).
3. Kalshi API env on Legion5 (read-only keys).

---

## Step 1 — NDFD anchor backfill (`52_*`)

On Legion5 **Git Bash**:

```bash
export KMIA_FORCE_REEXTRACT=1
export KMIA_EXTRACT_WORKERS=10
bash D:/KMIA_Process/scripts/52_kalshi_ndfd_anchor_backfill.sh 2026 04 2026 06
```

**Output:** `D:/KMIA_Process/processed/points/station=KMIA/kalshi_ndfd_maxt_VALID_ONLY.csv`

---

## Step 2 — Full research pipeline (`54_*`)

```bash
export KALSHI_BACKTEST_PROB_MODEL=integer_dist_v1
export KALSHI_BACKTEST_ORDER_MODE=taker
export FORCE_NDFD_RESEARCH=1
bash D:/KMIA_Process/scripts/54_kalshi_ndfd_research_pipeline.sh
```

**Produces:** NWS snapshots, backtest, `policy_sweep_*.json`, `trading_policy_draft.json` under Legion5 mirror.

> **Note:** `54_*` still runs `maker_limit` at step 2 by default. For taker parity with live paper, run NAS `run_nas_policy_pipeline.sh` after sync, or extend `54_*` to pass `--order-mode taker`.

---

## Step 3 — Sync to NAS

```powershell
# PowerShell on Legion5 (requires write access to NAS share — not read-only kmia_legion5)
powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\55_sync_kalshi_mirror_to_nas.ps1
```

**If robocopy fails (65+ file errors):** use admin DSM credentials or copy via Mac:

```bash
# Mac — Legion5 scp works; Synology scp subsystem may be disabled — use tar over ssh
scp "Legion5:D:/KMIA_Process/analysis/Kalshi_Price_Backtest/recommended_policy.json" /tmp/
tar cf - -C /tmp recommended_policy.json | ssh MediaServer2 "sudo tar xf - -C /tmp && sudo cp /tmp/recommended_policy.json '/volume2/Data/App_Development/KMIA_Ingest/setup_repo/Research/Agent Analysis of KMIA Forecast Precision/Kalshi_Price_Backtest/'"
```

**2026-06-23 run result:** Legion5 `54_*` completed — 65 NDFD NWS snapshots, 0 forecast-validation gaps, recommended **9% edge / $0.35 cap / 24 trades / 58.3% win** (moderate confidence). Robocopy sync failed (read-only SMB); manual artifact copy required.

---

## Step 4 — Verify on NAS (Mac, LAN)

```bash
ssh MediaServer2 'sudo /var/packages/ContainerManager/target/usr/bin/docker exec kmia-paper-research \
  python3 /data/KMIA_Ingest/setup_repo/ingest/scripts/kalshi_weather_coverage_scorecard.py' | tail -15
```

Expect **≥90%** forecast + full join on scored days.

---

## NAS-only fallback (after Legion5 sync)

If merged CSV is on NAS at `Kalshi/backend/data/processed/ndfd_kalshi/kalshi_ndfd_maxt_VALID_ONLY.csv`:

```bash
ssh MediaServer2 'sudo /var/packages/ContainerManager/target/usr/bin/docker exec kmia-paper-research bash -c "
  export PATH=/opt/kmia-venv/bin:\$PATH
  export NDFD_KALSHI_MAXT_CSV=/data/Kalshi/backend/data/processed/ndfd_kalshi/kalshi_ndfd_maxt_VALID_ONLY.csv
  python3 /data/KMIA_Ingest/setup_repo/ingest/scripts/backfill_nws_snapshots_from_ndfd.py \
    --ndfd-csv \$NDFD_KALSHI_MAXT_CSV --replace-iem \
    --price-history-dir \"/data/Kalshi/Kalshi - Miami Max Temp. Bet History\"
"'
```

Then: `run_nas_policy_pipeline.sh`

---

## Related

- [`PAPER_TRADING_READINESS.md`](../ops/PAPER_TRADING_READINESS.md)
- [`KALSHI_TRADING_BRIDGE_STATE.md`](../architecture/KALSHI_TRADING_BRIDGE_STATE.md)
