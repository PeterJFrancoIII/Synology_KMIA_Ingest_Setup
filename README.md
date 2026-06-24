# Synology KMIA Ingest Setup

Historical NDFD ingest + KMIA forecast-precision (MAE) research for Kalshi max-temperature analysis.

**Console 2 of 3** — separate from the Kalshi Main Console (human live UI) and Auto Trader Console. See `docs/architecture/THREE_CONSOLE_ARCHITECTURE.md`.

**Research / dry-run only** — no live trading in this repo.

## Start here

| Layer | Where | When |
|-------|-------|------|
| **Agent boot** | [0_Developer_Source_Files/](0_Developer_Source_Files/README.md) | Every AI session — mission, objective, agent rules, bootloader |
| **Reference docs** | [docs/README.md](docs/README.md) | Deploy, NAS ops, architecture, handoffs |

**Live project state:** [`0_Developer_Source_Files/current-objective.md`](0_Developer_Source_Files/current-objective.md) (not dated handoffs under `docs/handoffs/`).

## Documentation map

See [docs/README.md](docs/README.md) for the full two-layer layout (boot bundle vs reference docs).

## Machines

- **Mac** — repo source of truth, deploy scripts
- **NAS (MediaServer2)** — raw GRIB lake, Docker ingest (`kmia-arch-ingest`), Kalshi policy/paper loop (`kmia-paper-research`), **WebSocket orderbook archive** (`kmia-orderbook-ws`)
- **Legion5** — SMB pull + parallel wgrib2 extract + analysis + charts

Kalshi WS orderbook design: `docs/architecture/KALSHI_WS_ORDERBOOK_INGEST.md`

## Charts (Legion5)

```
D:\KMIA_Process\analysis\KMIA_Chart_Portal\kmia_chart_portal.html
```

## License

Private research tooling — see repository owner.
