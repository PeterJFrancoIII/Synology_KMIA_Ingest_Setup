#!/usr/bin/env bash
# Thin wrapper — daily NBM + ingest + NAS sync (see 55_daily_kalshi_research.sh).
exec bash "$(dirname "$0")/55_daily_kalshi_research.sh" "$@"
