# NDFD GRIB Archive Integrity Audit (SMB scan via Legion5)

**Audited:** 2026-06-16  
**Method:** `legion5/52c_audit_archive_smb.ps1` on `Z:\App_Development\KMIA_Ingest\raw\forecast\ndfd_aws`  
**Result:** **55 / 69 months OK** · **14 gaps** on NAS (need ingest backfill before extraction)  
**Legion5 manifest:** `D:\KMIA_Process\manifest\archive_integrity_smb_latest.json`

SSH-based audits return 0 files (NAS ACL); **SMB is authoritative**.

## Pattern: systematic winter gaps

Every year **2021–2025** is missing **January maxt+wdir** and **February maxt** (wdir present). This is a NAS ingest backfill issue, not an extraction bug.

| Year | Jan | Feb | Mar+ |
|------|-----|-----|------|
| 2021–2025 | MISSING_BOTH | MISSING_MAXT (wdir only) | OK (~2400–2550 files/var/month) |

## All 14 NAS gaps

| Month | maxt | wdir | Status |
|-------|------|------|--------|
| 2020-04 | 885 | 0 | MISSING_WDIR (partial Apr; AWS archive starts 2020-04-16) |
| 2020-05 | 0 | 0 | MISSING_BOTH |
| 2020-07 | 0 | 2421 | MISSING_MAXT |
| 2021-01 | 0 | 0 | MISSING_BOTH |
| 2021-02 | 0 | 0 | MISSING_BOTH |
| 2021-03 | 0 | 2397 | MISSING_MAXT |
| 2022-01 | 0 | 0 | MISSING_BOTH |
| 2022-02 | 0 | 2227 | MISSING_MAXT |
| 2023-01 | 0 | 0 | MISSING_BOTH |
| 2023-02 | 0 | 2211 | MISSING_MAXT |
| 2024-01 | 0 | 0 | MISSING_BOTH |
| 2024-02 | 0 | 2295 | MISSING_MAXT |
| 2025-01 | 0 | 0 | MISSING_BOTH |
| 2025-02 | 0 | 2233 | MISSING_MAXT |

## Extraction status (Legion5)

**Pipeline restarted** 2026-06-16 after fixing robocopy infinite-retry (`/R:3 /W:5`) and SMB remount.

- **2021 Apr–Dec:** VALID_ONLY complete (prior run)
- **2020:** partial — 06, 08–12 OK; 04/05/07 gaps; 12 was stuck, now resuming
- **2022–2025:** BUILD in progress via `36_process_all_from_nas.sh`

Months with NAS gaps will log `WARN month failed` until backfilled on NAS.

**Backfill:** `legion5/54_backfill_nas_gaps.sh` — downloads missing maxt/wdir from **AWS S3 → Legion5 `D:\KMIA_Process\raw`**, then extracts to VALID_ONLY (NAS SMB user `kmia_legion5` is **read-only**; cannot write GRIB to NAS lake without elevated NAS credentials).

## Scripts

| Script | Purpose |
|--------|---------|
| `legion5/52c_audit_archive_smb.ps1` | Month-level integrity (recommended) |
| `ingest/scripts/audit_ndfd_archive_integrity.py` | Day-level detail (slow on SMB) |
| `legion5/53_audit_extraction_coverage.sh` | VALID_ONLY coverage on Legion5 |
