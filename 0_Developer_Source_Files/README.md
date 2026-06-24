# Mission & governance (read first)

**Directory:** `0_Developer_Source_Files/` (repo root)

All canonical mission, agent, and Zero-Drift governance documents live in **this directory**.

Read in order for a new session:

| # | Document | Purpose |
|---|----------|---------|
| 1 | [AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md](AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md) | Zero-Drift Build OS — mandatory for all AI agents (Sections 0–8) |
| 2 | [MISSION.md](MISSION.md) | Console 2 mission, success criteria, non-goals |
| 3 | [current-objective.md](current-objective.md) | Active slice — Mission Control Packet |
| 4 | [PROJECT_STATE_AND_OBJECTIVES.md](PROJECT_STATE_AND_OBJECTIVES.md) | Topology, scripts, handoff state |
| 5 | [AGENTS.md](AGENTS.md) | Agent operating rules, commands, risk classes |
| 6 | [CLAUDE.md](CLAUDE.md) | Claude Code session instructions |
| 7 | [trade_policies.md](trade_policies.md) | **Kalshi algorithmic trading policy — cite for reviews & prompts; auto-sync on policy export** |

Kalshi market data (Console 2 + NAS):

- [KALSHI_WS_ORDERBOOK_INGEST.md](../docs/architecture/KALSHI_WS_ORDERBOOK_INGEST.md) — WebSocket orderbook daemon design (deployed NAS)
- [KALSHI_DATA_COLLECTION.md](../docs/architecture/KALSHI_DATA_COLLECTION.md) — all Kalshi ingest tiers
- [KALSHI_API_RESPONSE_FIELDS.md](../docs/architecture/KALSHI_API_RESPONSE_FIELDS.md) — REST API field catalog

Related (outside this folder):

- **Documentation map:** `docs/README.md` — reference layer (runbooks, architecture, handoffs)
- Three-console architecture: `docs/architecture/THREE_CONSOLE_ARCHITECTURE.md`
- Console 2 export contract: `docs/architecture/CONSOLE_2_EXPORT_CONTRACT.md`
- Moved paths: `docs/REDIRECTS.md`
- Scoped rules: `.cursor/rules/`

Root-level `MISSION.md`, `AGENTS.md`, and `CLAUDE.md` are thin pointers here for tool discoverability.
