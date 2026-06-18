# Automated full-year 2021 analysis (Legion5)

**Study ID:** `KMIA_NDFD_Year_MaxT_Precision_2021`  
**Started:** 2026-06-15 (background, nohup)  
**Completed:** 2026-06-16 03:02 UTC (~2 h runtime)  
**Scope:** 2021 months **04–12** (Jan–Mar not on NAS; 9 months merged)

## Results (headline)

- **275** target days, **10,139** forecast releases
- **MAE 1.16°F**, **77.9%** within 2°F
- Best month: **Aug** (91.8%); weakest: **Apr** (59.5%)
- Synced to Mac: `KMIA_NDFD_Year_MaxT_Precision_2021/`

## What runs

1. **BUILD** — `35_process_month_from_nas.sh` per month (SMB + 8 workers); skips months already VALID_ONLY (04, 07, 10, 12)
2. **New months:** 05, 06, 08, 09, 11 (~26 min each → ~2.2 h total)
3. **MERGE** — yearly maxt/wdir + combined forecast CSV
4. **ANALYZE** — `analyze_kmia_forecast_accuracy.py` (full year, not four-season sample)
5. **CHART** — `chart_kmia_year_stability_wind.py` (if present)

## Monitor (Legion5 Git Bash)

```bash
tail -f /d/KMIA_Process/logs/processing/KMIA_NDFD_Year_MaxT_Precision_2021.nohup.log
```

## Done when

```text
/d/KMIA_Process/analysis/KMIA_NDFD_Year_MaxT_Precision_2021/COMPLETE.txt
/d/KMIA_Process/analysis/KMIA_NDFD_Year_MaxT_Precision_2021/accuracy_report.md
```

## Pull results to Mac

```bash
scp -r Legion5:D:/KMIA_Process/analysis/KMIA_NDFD_Year_MaxT_Precision_2021/ \
  "Research/Agent Analysis of KMIA Forecast Precision/"
```

## Relaunch

```bash
ssh Legion5 'C:/Progra~1/Git/bin/bash.exe -lc "/d/KMIA_Process/run_KMIA_Year_Accuracy_2021.sh"'
```

Scripts: `legion5/45_kmia_year_maxt_precision_analysis.sh`, `run_KMIA_Year_Accuracy_2021.sh`
