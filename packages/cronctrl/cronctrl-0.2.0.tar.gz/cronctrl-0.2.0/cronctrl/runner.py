"""Job execution runner (Phase 2)."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, TextIO

import fcntl
import subprocess


class RunnerError(Exception):
    pass


def run_job(cfg: dict[str, Any], job_name: str) -> int:
    jobs = cfg.get("jobs")
    if not isinstance(jobs, dict):
        raise RunnerError("jobs: missing or invalid in config")
    if job_name not in jobs:
        raise RunnerError(f"job not found: {job_name}")

    job = jobs[job_name]
    if not isinstance(job, dict):
        raise RunnerError(f"job definition is invalid: {job_name}")

    log_dir = cfg.get("log_dir")
    state_dir = cfg.get("state_dir")
    locks_dir = cfg.get("locks_dir")
    if not isinstance(log_dir, str) or not isinstance(state_dir, str):
        raise RunnerError("log_dir/state_dir must be set")
    if not isinstance(locks_dir, str):
        locks_dir = os.path.join(state_dir, "locks")

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(locks_dir, exist_ok=True)
    state_path = _state_path(state_dir, job_name)
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    per_job_log = os.path.join(log_dir, f"{job_name}.log")
    global_log = os.path.join(log_dir, "all.log")

    lock_handle = None
    concurrency = job.get("concurrency")
    if concurrency != "allow":
        lock_handle = _open_lock(locks_dir, job_name)
        if not _try_lock(lock_handle):
            _log_skip(job_name, per_job_log, global_log)
            return 0

    started_at = _utcnow()
    finished_at = started_at
    exit_code = 1
    timed_out = False
    message = "error"

    try:
        with _open_log(per_job_log) as per_handle, _open_log(global_log) as global_handle:
            _write_banner(per_handle, "START", job_name, started_at)
            _write_global(global_handle, job_name, _banner_line("START", job_name, started_at))

            try:
                exit_code, timed_out, output = _run_process(job)
            except Exception as exc:  # pragma: no cover - defensive logging
                finished_at = _utcnow()
                error_line = f"ERROR: {exc}"
                per_handle.write(error_line + "\n")
                _write_global(global_handle, job_name, error_line)
                exit_code = 1
                timed_out = False
                message = "error"
            else:
                _write_output(per_handle, global_handle, job_name, output)

                finished_at = _utcnow()
                if timed_out:
                    message = "timeout"
                    _write_banner(per_handle, "TIMEOUT", job_name, finished_at)
                    _write_global(
                        global_handle,
                        job_name,
                        _banner_line("TIMEOUT", job_name, finished_at),
                    )
                else:
                    message = "ok" if exit_code == 0 else "error"

            _write_banner(per_handle, "END", job_name, finished_at, exit_code)
            _write_global(
                global_handle,
                job_name,
                _banner_line("END", job_name, finished_at, exit_code),
            )

        _write_state(
            state_path,
            {
                "job": job_name,
                "last_started_at": _format_ts(started_at),
                "last_finished_at": _format_ts(finished_at),
                "last_exit_code": exit_code,
                "last_duration_seconds": _duration_seconds(started_at, finished_at),
                "last_command": str(job.get("exec", "")),
                "last_log_file": per_job_log,
                "message": message,
            },
        )
    finally:
        if lock_handle is not None:
            try:
                fcntl.flock(lock_handle, fcntl.LOCK_UN)
            finally:
                lock_handle.close()

    return exit_code


def _run_process(job: dict[str, Any]) -> tuple[int, bool, str]:
    command = job.get("exec")
    if not isinstance(command, str) or not command.strip():
        raise RunnerError("exec: missing or invalid")

    shell = job.get("shell") if isinstance(job.get("shell"), str) else None
    cwd = job.get("cwd") if isinstance(job.get("cwd"), str) else None

    env = None
    if "env" in job:
        job_env = job.get("env")
        if isinstance(job_env, dict):
            env = os.environ.copy()
            env.update(job_env)

    timeout = job.get("timeout_seconds")
    timeout_seconds = timeout if isinstance(timeout, int) and timeout > 0 else None

    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True,
        executable=shell,
        cwd=cwd,
        env=env,
    )

    try:
        output, _ = proc.communicate(timeout=timeout_seconds)
        return proc.returncode or 0, False, output or ""
    except subprocess.TimeoutExpired:
        proc.kill()
        output, _ = proc.communicate()
        return 124, True, output or ""


def _open_lock(locks_dir: str, job_name: str) -> TextIO:
    path = os.path.join(locks_dir, f"{job_name}.lock")
    return open(path, "a+", encoding="utf-8")


def _try_lock(handle: TextIO) -> bool:
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def _open_log(path: str) -> TextIO:
    return open(path, "a", encoding="utf-8")


def _write_output(
    per_handle: TextIO,
    global_handle: TextIO,
    job_name: str,
    output: str,
) -> None:
    if not output:
        return
    for line in output.splitlines(True):
        per_handle.write(line)
        _write_global(global_handle, job_name, line)


def _write_banner(
    per_handle: TextIO,
    label: str,
    job_name: str,
    timestamp: datetime,
    exit_code: int | None = None,
) -> None:
    per_handle.write(_banner_line(label, job_name, timestamp, exit_code))


def _banner_line(
    label: str,
    job_name: str,
    timestamp: datetime,
    exit_code: int | None = None,
) -> str:
    suffix = f" exit_code={exit_code}" if exit_code is not None else ""
    return f"==== {label} {job_name} {_format_ts(timestamp)}{suffix}\n"


def _write_global(global_handle: TextIO, job_name: str, line: str) -> None:
    text = line.rstrip("\n")
    global_handle.write(f"{_format_ts(_utcnow())} {job_name} | {text}\n")


def _log_skip(job_name: str, per_job_log: str, global_log: str) -> None:
    timestamp = _utcnow()
    line = _banner_line("SKIP", job_name, timestamp)
    with _open_log(per_job_log) as per_handle, _open_log(global_log) as global_handle:
        per_handle.write(line)
        _write_global(global_handle, job_name, line)


def _state_path(state_dir: str, job_name: str) -> str:
    return os.path.join(state_dir, "state", f"{job_name}.json")


def _write_state(path: str, payload: dict[str, Any]) -> None:
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp_path, path)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _format_ts(timestamp: datetime) -> str:
    return timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def _duration_seconds(started_at: datetime, finished_at: datetime) -> int:
    return int((finished_at - started_at).total_seconds())
