# Synology KMIA Ingest Setup

Historical NDFD ingest + KMIA forecast-precision research for Kalshi max-temperature analysis (**research / dry-run only**).

## Start here

| Document | Purpose |
|----------|---------|
| [Bootloader (source of truth)](docs/bootloader/AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md) | Zero-Drift Build OS for all AI agents |
| [MISSION.md](MISSION.md) | Project mission and success criteria |
| [AGENTS.md](AGENTS.md) | Agent operating rules and commands |
| [Project state](docs/PROJECT_STATE_AND_OBJECTIVES.md) | Architecture, scripts, objectives |

## Machines

- **Mac** — repo source of truth, deploy scripts
- **NAS (MediaServer2)** — raw GRIB lake + Docker ingest
- **Legion5** — SMB pull + parallel wgrib2 extract + analysis + charts

## Charts (Legion5)

```
D:\KMIA_Process\analysis\KMIA_Chart_Portal\kmia_chart_portal.html
```

## License

Private research tooling — see repository owner.
