"""Kalshi RSA-PSS request signing for read-only API ingest (Console 2).

Uses openssl subprocess (same approach as Kalshi repo kalshi_auth.py).
NO REAL TRADING — signing for market data GET only.
"""

from __future__ import annotations

import base64
import os
import subprocess
from typing import Dict


def _key_path() -> str:
    path = os.environ.get("KALSHI_PRIVATE_KEY_PATH") or os.environ.get(
        "KALSHI_READ_ONLY_RSA_KEY_PATH"
    )
    if not path:
        raise ValueError("KALSHI_PRIVATE_KEY_PATH or KALSHI_READ_ONLY_RSA_KEY_PATH required")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"RSA key file not found: {path}")
    return path


def _key_id() -> str:
    key_id = os.environ.get("KALSHI_API_KEY_ID") or os.environ.get("KALSHI_API_KEY")
    if not key_id:
        raise ValueError("KALSHI_API_KEY_ID (or KALSHI_API_KEY) required")
    return key_id


def sign_kalshi_request(
    private_key_path: str,
    timestamp_ms: str,
    method: str,
    path_without_query: str,
) -> str:
    payload = f"{timestamp_ms}{method}{path_without_query}"
    proc = subprocess.run(
        [
            "openssl",
            "dgst",
            "-sha256",
            "-sigopt",
            "rsa_padding_mode:pss",
            "-sign",
            private_key_path,
        ],
        input=payload.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"OpenSSL signing failed: {proc.stderr.decode()}")
    return base64.b64encode(proc.stdout).decode("utf-8")


def create_kalshi_auth_headers(method: str, path_without_query: str) -> Dict[str, str]:
    import time

    timestamp_ms = str(int(time.time() * 1000))
    signature = sign_kalshi_request(_key_path(), timestamp_ms, method, path_without_query)
    return {
        "KALSHI-ACCESS-KEY": _key_id(),
        "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
        "KALSHI-ACCESS-SIGNATURE": signature,
    }


def auth_configured() -> bool:
    try:
        _key_path()
        _key_id()
        return True
    except (ValueError, FileNotFoundError):
        return False
