# Current objective

**Updated:** 2026-06-18  
**Status:** Resume BUILD complete on Legion5; charts + portal live

## Active slice

Post-BUILD maintenance and research consumption:

1. Use Legion5 chart portal as primary visualization (`D:\KMIA_Process\analysis\KMIA_Chart_Portal\`)
2. Optional: selective Mac pulls via `legion5/pull_all_charts_to_mac.sh` (not full CSV lake)
3. Future: 2026 ingest via Docker `kmia-arch-ingest`; NAS raw gap backfill requires write-capable credentials

## Success for this slice

- [x] 2020–2025 maxt + wdir VALID_ONLY on Legion5
- [x] Per-year + all-years analysis and chart suites
- [x] Chart portal with 8 studies
- [ ] Document any remaining NAS raw gaps (see `docs/ARCHIVE_INTEGRITY_AUDIT_2026-06-16.md`)

## Non-goals (this slice)

- Git-storing multi-GB forecast CSVs
- Live trading integration

## Verification

```bash
ssh Legion5 "C:\Program Files\Git\bin\bash.exe -lc 'tail -3 /d/KMIA_Process/logs/processing/process_all.log'"
ssh Legion5 "C:\Program Files\Git\bin\bash.exe -lc 'ls /d/KMIA_Process/analysis/KMIA_Chart_Portal/'"
```

## Architecture reference

See `docs/PROJECT_STATE_AND_OBJECTIVES.md` for three-machine topology, golden master chart standard, and script inventory.
