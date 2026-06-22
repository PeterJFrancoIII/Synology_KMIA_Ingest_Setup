# Smoke Test Checklist — KMIA Ingest

## Pre-Flight

- [ ] NAS root exists: `/volume2/Data/App_Development`
- [ ] Directory tree created via `00_create_tree.sh`
- [ ] Host audit passes: `01_host_audit.sh`
- [ ] No accidental project data outside root: `02_find_project_data.sh`
- [ ] Writable paths confirmed: `03_permissions_check.sh`
- [ ] Local repo tests pass: `tests/test_*.sh`

## Container

- [ ] `docker compose build` succeeds
- [ ] `docker compose up -d` starts `kmia-arch-ingest`
- [ ] `/volume2/Data/App_Development` mounted at `/data`
- [ ] `smoke_container.sh` reports Python, AWS CLI, CDO/NCO/eccodes
- [ ] `wgrib2 -version` works OR clear fallback message logged

## NDFD AWS Smoke (`10_ndfd_aws_smoke_maxt.sh`)

- [ ] Lists `s3://noaa-ndfd-pds/wmo/maxt/2020/06/01/`
- [ ] Downloads files to `/data/KMIA_Ingest/raw/forecast/ndfd_aws/maxt/2020/06/01/`
- [ ] SHA256 recorded in log
- [ ] Manifest record appended via `40_manifest_append.py`
- [ ] If `wgrib2` present: `wgrib2 <file> -s -vt -lon -80.3164 25.7906` succeeds
- [ ] If `wgrib2` missing: script exits 2 with clear message (download still OK)

## ISD Smoke (`11_isd_smoke_kmia.sh`)

- [ ] Downloads `72202012839.csv` for configured year
- [ ] File stored at `/data/KMIA_Ingest/raw/observed/isd/<year>/72202012839.csv`
- [ ] SHA256 recorded in log
- [ ] Manifest record appended
- [ ] First 5 lines show hourly station data

## Post-Smoke Verification

```bash
find /volume2/Data/App_Development/KMIA_Ingest/raw -type f | head
find /volume2/Data/App_Development/KMIA_Ingest/logs/smoke_tests -type f
tail -5 /volume2/Data/App_Development/KMIA_Ingest/manifest/run_log.jsonl
```

## Gate Before Backfill

Do **not** start historical backfill until all smoke tests pass and manifest logging works.

Backfill discipline:

```text
one source
one variable
one month
one worker
verify manifest
then continue
```

## No-Go

Stop deployment if any no-go condition in `docs/NAS_Runbook.md` triggers.
