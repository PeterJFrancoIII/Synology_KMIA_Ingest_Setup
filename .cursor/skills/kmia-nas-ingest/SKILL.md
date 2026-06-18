---
name: kmia-nas-ingest
description: >-
  Operates the Synology DS225+ KMIA historical weather ingest on MediaServer2.
  Use when deploying kmia-arch-ingest, backfilling NDFD/ISD data, auditing NAS
  storage, running smoke tests, or bridging NAS raw ingest to golden master
  forecast-precision charts.
---

# KMIA NAS Ingest (MediaServer2)

## Mission

Durable data lake + ingestion worker for KMIA historical NDFD forecasts and NCEI observations. Research/dry-run only — no live Kalshi trading.

## Canonical paths

```text
/volume2/Data/App_Development/                 # project root
/volume2/Data/App_Development/KMIA_Ingest/     # data lake
/volume2/Data/App_Development/Docker/kmia-arch-ingest/  # active compose (capital D)
```

Mount: `/volume2/Data/App_Development` → container `/data`

## Container

```bash
ssh MediaServer2
sudo -n docker ps --filter name=kmia-arch-ingest
sudo -n docker exec -it kmia-arch-ingest bash
```

Image: `kmia-arch-ingest:latest` (Arch + wgrib2 3.8.0 + aws-cli + Python venv)

**Use only** `Docker/kmia-arch-ingest/` compose. Avoid lowercase `docker/kmia-arch-ingest/` (512 MB / `restart: "no"`).

## Ingest architecture

```text
official sources → raw immutable archive → manifest → KMIA point extracts → processed CSV → gap reports
```

## Key scripts (inside container)

| Script | Purpose |
|---|---|
| `10_ndfd_aws_smoke_maxt.sh` | One-day NDFD download + wgrib2 smoke |
| `11_isd_smoke_kmia.sh` | KMIA ISD year pull |
| `20_extract_kmia_point.sh` | wgrib2 point extract (logs today) |
| `21_backfill_ndfd_maxt_month.sh` | One month controlled backfill |
| `30_gap_audit.sh` | Manifest health check |
| `40_manifest_append.py` | Immutable file ledger |

## Current gaps to close

1. `processed/` empty — must emit CSV point extracts matching Mac `VALID_ONLY` format
2. ISD history beyond 2025 not yet on NAS
3. Manifest sparse (one record/day) — expand before large backfill
4. Golden master chart not yet generated from NAS data

## Bridge to charting

Downstream goal: NAS processed CSVs must feed the golden master chart (`kmia-golden-master-chart` skill). Required columns: release time, target date, forecast temp, lead hours, observed max, stability, outcome, wind.

## Safety rules

- No project data outside `/volume2/Data/App_Development`
- Use GRIB ref time (`grib_ref_time_utc` / wgrib2 `d=`) for release time — not filename post times; do not bucket to fixed 00/06/12/18 UTC cycles
- Do not hard-code KMIA grid cell; use nearest point per GRIB
- No secrets in repo; no order execution code
- One source / one variable / one month / verify manifest / then continue

## Operator references

- `docs/NAS_Runbook.md`
- `docs/Smoke_Test_Checklist.md`
- `Research/SYNOLOGY_DS225P_ROADMAP_UPDATED_20260608.md`
