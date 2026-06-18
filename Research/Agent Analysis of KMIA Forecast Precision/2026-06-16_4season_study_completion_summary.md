# 4-Season Precision Study — Completion Summary

**Study ID:** `KMIA_NDFD_4Season_MaxT_Precision_2021`  
**Completed:** 2026-06-15 (Legion5)  
**Pipeline:** SMB robocopy (`Z:`) + 4 parallel `wgrib2` workers (Spring/Summer/Fall); Winter used pre-optimization SSH path

## Months processed

| Season | Month | Notes |
|--------|-------|-------|
| Winter | 2021-12 | Dec proxy (Jan–Mar 2021 missing on NAS) |
| Spring | 2021-04 | |
| Summer | 2021-07 | |
| Fall | 2021-10 | |

## Headline metrics

| Metric | Value |
|--------|-------|
| Target dates | 126 |
| Forecast releases (0–36h before 4 PM ET) | 4,530 |
| Overall MAE | **1.20°F** |
| Within 2°F | **77.3%** |

## Season comparison (full months only)

| Season | Month | Within 2°F | Within 1°F | MAE |
|--------|-------|------------|------------|-----|
| Fall | Oct (10) | **85.6%** | 76.7% | 0.99°F |
| Summer | Jul (7) | 82.3% | 70.4% | 1.10°F |
| Winter | Dec (12) | 81.5% | 72.2% | 1.12°F |
| Spring | Apr (4) | **59.5%** | 52.7% | 1.59°F |

Spring was the weakest season in this sample; Fall the strongest.

## Best lead hour by season (% within 2°F)

| Season | Best lead | Accuracy |
|--------|-----------|----------|
| Fall | 24h | 93.5% |
| Summer | 30h | 90.3% |
| Winter | 10h | 87.1% |
| Spring | 27h | 66.7% |

## Condition highlights

- **STABLE** forecast days: 83.3% within 2°F
- **Observed wind SE:** 89.3% within 2°F
- **Narrow forecast range (≤1.5°F):** 81.1% within 2°F

## Processing time (observed)

| Month | Duration | Pull mode |
|-------|----------|-----------|
| Spring, Summer, Fall | ~26 min each | SMB + 4 workers |
| Winter | ~50 min | SSH tar (pre-optimization) |

## Outputs

Full tables: [KMIA_NDFD_4Season_MaxT_Precision_2021/](./KMIA_NDFD_4Season_MaxT_Precision_2021/)

Key files: `accuracy_report.md`, `four_season_precision_summary.csv`, `lead_hour_accuracy_by_season.csv`, `conditions_accuracy.csv`

## Caveats

- Winter uses **December 2021**, not meteorological winter (Jan–Mar missing on NAS).
- `four_season_precision_summary.csv` includes sparse rows for months 5, 8, 11 (1-day edge cases from `sample_season` tagging) — use full-month rows (4, 7, 10, 12) for season comparison.
