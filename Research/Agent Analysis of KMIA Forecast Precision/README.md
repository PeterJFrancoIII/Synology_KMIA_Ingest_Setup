# Agent Analysis of KMIA Forecast Precision

Research archive for KMIA NDFD forecast-vs-observed precision studies.  
Use this folder for workflow decisions, benchmark conclusions, and short analysis reports.

## Canonical workflow (use for full 2020–2025 processing)

**[OPTIMAL_ANALYSIS_WORKFLOW.md](./OPTIMAL_ANALYSIS_WORKFLOW.md)** — benchmarked three-machine workflow:

- **Phase 1 BUILD:** Legion5 SMB + `wgrib2` → monthly `VALID_ONLY` CSVs → sync to NAS
- **Phase 2 ANALYZE:** Legion5 merge + `analyze_kmia_forecast_accuracy.py` (~5 min if CSVs exist)
- **Phase 3 CHARTS:** `47_build_kmia_chart_suite.sh` → golden-master PNG + unified `kmia_chart_suite.html` (3 tabs)

Mirror copy also at `docs/OPTIMAL_ANALYSIS_WORKFLOW.md`.

## Completed studies

| Study | Report | Data |
|-------|--------|------|
| **KMIA_NDFD_Year_MaxT_Precision_2021** | [accuracy_report.md](./KMIA_NDFD_Year_MaxT_Precision_2021/accuracy_report.md) | [folder](./KMIA_NDFD_Year_MaxT_Precision_2021/) · [chart suite](./KMIA_NDFD_Year_MaxT_Precision_2021/kmia_chart_suite.html) |
| **KMIA_NDFD_4Season_MaxT_Precision_2021** | [accuracy_report.md](./KMIA_NDFD_4Season_MaxT_Precision_2021/accuracy_report.md) | [folder](./KMIA_NDFD_4Season_MaxT_Precision_2021/) |

Months: 2021-12 (Winter), 2021-04 (Spring), 2021-07 (Summer), 2021-10 (Fall).  
Legion5 source: `D:\KMIA_Process\analysis\KMIA_NDFD_4Season_MaxT_Precision_2021\`

## Short agent analysis reports

| Date | Document | Topic |
|------|----------|-------|
| 2026-06-15 | [2026-06-15_infrastructure_optimization_summary.md](./2026-06-15_infrastructure_optimization_summary.md) | SMB pull, parallel workers, Legion5 defaults |
| 2026-06-16 | [2026-06-16_system_bottleneck_analysis.md](./2026-06-16_system_bottleneck_analysis.md) | Bottleneck ranking and scale recommendations |
| 2026-06-16 | [2026-06-16_4season_study_completion_summary.md](./2026-06-16_4season_study_completion_summary.md) | First completed precision study headline results |

## Related project docs

- `docs/PROJECT_STATE_AND_OBJECTIVES.md` — system handoff
- `.cursor/rules/legion5-processor-defaults.mdc` — Legion5 default env (SMB + workers)
- `legion5/44_benchmark_workflow.sh` — re-run benchmarks before scaling
