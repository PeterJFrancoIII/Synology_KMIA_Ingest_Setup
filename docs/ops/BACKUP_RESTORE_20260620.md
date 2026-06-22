# Restore from pre-watch backup (2026-06-20)

**Location:** `/Users/computer/Desktop/App Development/KMIA_System_Backups/pre_watch_20260620/`  
**Permissions:** Archives are read-only (`chmod a-w`).

## Checksums

See `MANIFEST.txt` in the backup folder.

## Restore Console 2

```bash
cd "/Users/computer/Desktop/App Development"
# Extract to a NEW directory first — do not overwrite live tree blindly
mkdir -p KMIA_Restore_Test
tar xzf KMIA_System_Backups/pre_watch_20260620/Synology_KMIA_Ingest_Setup.tar.gz -C KMIA_Restore_Test
```

## Restore Kalshi (code + docs only in archive)

```bash
mkdir -p Kalshi_Restore_Test
tar xzf KMIA_System_Backups/pre_watch_20260620/Kalshi.tar.gz -C Kalshi_Restore_Test
```

## Git refs at backup time

- Console 2: `58f751e` (59 uncommitted files)
- Kalshi: `11cffc86` (232 uncommitted files)

Tarballs capture working tree including uncommitted changes; git tags were not required.

## Excluded from backup (re-fetch if needed)

- Multi-GB CSVs (`accuracy_points_enriched.csv`, Kalshi price-history CSVs)
- `1_Downloads/`, venvs, secrets (`.env`, `api_keys.env`)
