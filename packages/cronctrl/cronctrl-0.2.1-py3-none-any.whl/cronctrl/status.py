"""Status inspection helpers (Phase 5)."""

from __future__ import annotations

import json
import os
from typing import Any


class StatusError(Exception):
    pass


def load_status(cfg: dict[str, Any], job_name: str | None = None) -> list[dict[str, Any]]:
    jobs = cfg.get("jobs")
    if not isinstance(jobs, dict):
        raise StatusError("jobs: missing or invalid in config")

    state_dir = cfg.get("state_dir")
    if not isinstance(state_dir, str) or not state_dir.strip():
        raise StatusError("state_dir: required")

    job_names = [job_name] if job_name else sorted(jobs.keys())
    results: list[dict[str, Any]] = []

    for name in job_names:
        if name not in jobs:
            raise StatusError(f"job not found: {name}")
        state_path = os.path.join(state_dir, "state", f"{name}.json")
        state = _read_state(state_path)
        results.append(
            {
                "job": name,
                "last_started_at": state.get("last_started_at"),
                "last_finished_at": state.get("last_finished_at"),
                "last_exit_code": state.get("last_exit_code"),
                "last_duration_seconds": state.get("last_duration_seconds"),
                "last_message": state.get("message"),
            }
        )

    return results


def _read_state(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except (OSError, json.JSONDecodeError):
        return {}
    return {}
