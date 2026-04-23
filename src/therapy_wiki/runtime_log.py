"""Lightweight CLI progress logging."""

from __future__ import annotations

import sys
from datetime import datetime

_ENABLED = True


def set_cli_logging(enabled: bool) -> None:
    global _ENABLED
    _ENABLED = enabled


def cli_log(message: str) -> None:
    if not _ENABLED:
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[therapy {timestamp}] {message}", file=sys.stderr, flush=True)
