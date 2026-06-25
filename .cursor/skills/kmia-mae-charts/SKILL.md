---
name: kmia-mae-charts
description: >-
  Builds KMIA NDFD forecast-vs-observed MAE charts and enriched CSV on Legion5.
  Use for golden master chart suites, all-years merge, or pulling charts to Mac.
---

# KMIA MAE charts (Legion5)

## Before starting

1. Read `docs/OPTIMAL_ANALYSIS_WORKFLOW.md`
2. Read `legion5/ACTIVE_MANIFEST.json` → `extract`, `analyze`
3. Read `ingest/scripts/ACTIVE_MANIFEST.json` → `mae_charts`

## Pipeline (Legion5)

```text
BUILD  → 36_process_all_from_nas.sh (monthly VALID_ONLY CSVs)
ANALYZE → 45_kmia_year_maxt_precision_analysis.sh
MERGE  → 50_rebuild_all_years_study.sh
CHARTS → 49_build_all_charts.sh
```

## Canonical outputs

| Artifact | Path |
|----------|------|
| Enriched MAE CSV | `analysis/KMIA_NDFD_AllYears_MaxT_Precision/accuracy_points_enriched.csv` |
| Chart suite | `analysis/.../kmia_chart_suite.html` |
| Portal | `analysis/KMIA_Chart_Portal/kmia_chart_portal.html` |

## Mac mirror (light pull only)

```bash
legion5/pull_all_charts_to_mac.sh
```

Do **not** use `pull_charts_and_data_to_mac.sh` unless debugging raw point CSVs offline.

## Agents: safe Research files on Mac

- `accuracy_points_enriched.csv`, chart HTML, portal
- Avoid: `*_stability_wind.png`, sweep JSON (see `.cursorignore`)

## Golden master skill

For chart methodology details: `~/.cursor/skills/kmia-golden-master-chart/SKILL.md`
