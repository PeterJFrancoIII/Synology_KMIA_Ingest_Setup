"""Resolve Console 2 ↔ Kalshi artifact paths from environment (Mac or NAS).

NAS layout (default when KMIA_KALSHI_ROOT is set):
  /data/Kalshi/...
  /data/Console2/...

NO REAL TRADING — path helpers only.
"""

from __future__ import annotations

import os
from pathlib import Path

_MAC_KALSHI = Path("/Users/computer/Desktop/App Development/Kalshi")
_MAC_CONSOLE2 = Path("/Users/computer/Desktop/App Development/Synology_KMIA_Ingest_Setup")


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


def console2_root() -> Path:
    return _env_path("CONSOLE2_ROOT", _MAC_CONSOLE2)


def kalshi_root() -> Path:
    return _env_path("KMIA_KALSHI_ROOT", _MAC_KALSHI)


def kalshi_price_history_dir() -> Path:
    return _env_path(
        "KALSHI_PRICE_DIR",
        kalshi_root() / "Kalshi - Miami Max Temp. Bet History",
    )


def kalshi_processed_dir() -> Path:
    return _env_path(
        "KALSHI_PROCESSED_DIR",
        kalshi_root() / "backend" / "data" / "processed",
    )


def kalshi_research_dir() -> Path:
    return _env_path(
        "KALSHI_RESEARCH_DIR",
        kalshi_root() / "backend" / "data" / "research",
    )


def kalshi_candle_archive_dir() -> Path:
    return _env_path(
        "KALSHI_CANDLE_ARCHIVE_DIR",
        kalshi_processed_dir() / "kalshi_candle_archive",
    )


def kalshi_market_archive_dir() -> Path:
    return _env_path(
        "KALSHI_MARKET_ARCHIVE_DIR",
        kalshi_processed_dir() / "kalshi_market_archive",
    )


def kalshi_nws_dir() -> Path:
    return kalshi_processed_dir() / "weather_nws"


def kalshi_observed_jsonl() -> Path:
    return _env_path(
        "KALSHI_OBSERVED_JSONL",
        kalshi_processed_dir() / "weather_nws" / "nws_observed_history.jsonl",
    )


def kalshi_forecast_reports_dir() -> Path:
    return _env_path(
        "KALSHI_FORECAST_REPORTS_DIR",
        kalshi_processed_dir() / "reports",
    )


def kmia_daily_history_jsonl() -> Path:
    return _env_path(
        "KMIA_DAILY_HISTORY_JSONL",
        kalshi_processed_dir() / "history" / "kmia_daily_history.jsonl",
    )


def ncei_climatology_txt() -> Path:
    return _env_path(
        "NCEI_CLIMATOLOGY_TXT",
        kalshi_root()
        / "1948-2026_Climatological_Report_USW00012839_MIAMI_INTERNATIONAL_AIRPORT_.txt",
    )


def console2_backtest_dir() -> Path:
    return _env_path(
        "CONSOLE2_BACKTEST_DIR",
        console2_root()
        / "Research"
        / "Agent Analysis of KMIA Forecast Precision"
        / "Kalshi_Price_Backtest",
    )


def console2_enriched_csv() -> Path:
    return _env_path(
        "CONSOLE2_ENRICHED_CSV",
        console2_root()
        / "Research"
        / "Agent Analysis of KMIA Forecast Precision"
        / "KMIA_NDFD_AllYears_MaxT_Precision"
        / "accuracy_points_enriched.csv",
    )


def default_ndfd_kalshi_maxt_csv() -> Path | None:
    """Merged Legion5 maxt VALID_ONLY at MapClick pin for Kalshi anchor backfill."""
    import os

    raw = os.environ.get("NDFD_KALSHI_MAXT_CSV")
    if raw:
        p = Path(raw)
        return p if p.is_file() else None
    candidates = [
        kalshi_processed_dir() / "ndfd_kalshi" / "kalshi_ndfd_maxt_VALID_ONLY.csv",
        console2_root() / "Research" / "NDFD_Kalshi_Anchor" / "kalshi_ndfd_maxt_VALID_ONLY.csv",
        Path("/d/KMIA_Process/processed/points/station=KMIA/kalshi_ndfd_maxt_VALID_ONLY.csv"),
        Path("/e/KMIA_Ingest/processed/points/station=KMIA/kalshi_ndfd_maxt_VALID_ONLY.csv"),
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def mae_priors_output() -> Path:
    return _env_path(
        "MAE_PRIORS_FILE",
        kalshi_processed_dir() / "mae" / "mae_priors.json",
    )


def optional_existing(path: Path) -> Path | None:
    return path if path.exists() else None
