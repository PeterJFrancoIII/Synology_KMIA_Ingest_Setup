# Claude Code Instructions

Read [AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md](AI_System_Architect_Bootloader_Zero-Drift_Build_5.18.26.md), then [MISSION.md](MISSION.md) and [AGENTS.md](AGENTS.md) before planning.

Use subagents for noisy exploration, Legion5 log inspection, and large searches. Keep the main conversation focused on mission, plan, scope, verification, and handoff.

Before editing:
- summarize objective
- list allowed files
- list forbidden files
- list verification commands

After editing:
- summarize diff
- run verification where possible
- update docs/handoffs if work continues

Never perform red-zone changes without explicit approval. Never commit secrets or multi-GB data files.
