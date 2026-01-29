"""Log viewing helpers (Phase 5)."""

from __future__ import annotations

import os
import sys
import time
from collections import deque
from typing import Any


class LogsError(Exception):
    pass


def tail_logs(cfg: dict[str, Any], job_name: str | None = None, follow: bool = False, lines: int = 200) -> None:
    log_dir = cfg.get("log_dir")
    if not isinstance(log_dir, str) or not log_dir.strip():
        raise LogsError("log_dir: required")

    filename = f"{job_name}.log" if job_name else "all.log"
    path = os.path.join(log_dir, filename)
    if not os.path.exists(path):
        raise LogsError(f"log file not found: {path}")

    _tail_file(path, lines=lines, follow=follow)


def _tail_file(path: str, *, lines: int, follow: bool) -> None:
    if lines < 0:
        lines = 0
    if lines > 0:
        tail_lines = _read_last_lines(path, lines)
        for line in tail_lines:
            sys.stdout.write(line)
        sys.stdout.flush()

    if not follow:
        return

    with open(path, "r", encoding="utf-8") as handle:
        handle.seek(0, os.SEEK_END)
        while True:
            line = handle.readline()
            if line:
                sys.stdout.write(line)
                sys.stdout.flush()
            else:
                time.sleep(0.5)


def _read_last_lines(path: str, lines: int) -> list[str]:
    buffer: deque[str] = deque(maxlen=lines)
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            buffer.append(line)
    return list(buffer)
