from __future__ import annotations

import os
import re
from typing import Any

import yaml


class ConfigError(Exception):
    pass


JOB_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{1,63}$")
CRON_FIELD_RE = re.compile(r"^[0-9*/,-]+$")


DEFAULT_CONFIG_PATH = "/etc/cronctrl/jobs.yaml"


def load(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    except OSError as exc:
        raise ConfigError(f"unable to read config file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML: {exc}") from exc

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError("top-level config must be a mapping")

    cfg: dict[str, Any] = dict(raw)

    if isinstance(cfg.get("log_dir"), str):
        cfg["log_dir"] = _normalize_path(cfg["log_dir"])
    if isinstance(cfg.get("state_dir"), str):
        cfg["state_dir"] = _normalize_path(cfg["state_dir"])

    if "locks_dir" not in cfg and isinstance(cfg.get("state_dir"), str):
        cfg["locks_dir"] = os.path.join(cfg["state_dir"], "locks")
    if isinstance(cfg.get("locks_dir"), str):
        cfg["locks_dir"] = _normalize_path(cfg["locks_dir"])

    defaults = cfg.get("defaults")
    if defaults is None:
        defaults = {}
    cfg["defaults"] = defaults

    jobs = cfg.get("jobs")
    if isinstance(jobs, dict):
        for name, job in jobs.items():
            if job is None:
                job = {}
            if isinstance(job, dict):
                _apply_defaults(job, defaults)
                if "disabled" not in job:
                    job["disabled"] = False
                if isinstance(job.get("cwd"), str):
                    job["cwd"] = _normalize_path(job["cwd"])
            jobs[name] = job

    return cfg


def validate(cfg: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not isinstance(cfg, dict):
        return ["config: expected mapping at top level"]

    version = cfg.get("version")
    if version is None:
        errors.append("version: required")
    elif not isinstance(version, int):
        errors.append("version: must be an integer")
    elif version != 1:
        errors.append("version: must be 1")

    _require_abs_path(cfg, "log_dir", errors)
    _require_abs_path(cfg, "state_dir", errors)

    locks_dir = cfg.get("locks_dir")
    if locks_dir is not None:
        if not isinstance(locks_dir, str):
            errors.append("locks_dir: must be a string path")
        elif not os.path.isabs(locks_dir):
            errors.append("locks_dir: must be an absolute path")

    defaults = cfg.get("defaults")
    if defaults is not None and not isinstance(defaults, dict):
        errors.append("defaults: must be a mapping")
        defaults = {}

    if isinstance(defaults, dict):
        _validate_positive_int(defaults, "retention_days", errors, optional=True, scope="defaults")
        _validate_positive_int(defaults, "timeout_seconds", errors, optional=True, scope="defaults")
        if "shell" in defaults and not isinstance(defaults["shell"], str):
            errors.append("defaults.shell: must be a string")
        if "concurrency" in defaults and defaults["concurrency"] not in ("forbid", "allow"):
            errors.append("defaults.concurrency: must be 'forbid' or 'allow'")

    jobs = cfg.get("jobs")
    if jobs is None:
        errors.append("jobs: required")
        return errors
    if not isinstance(jobs, dict):
        errors.append("jobs: must be a mapping")
        return errors

    for name, job in jobs.items():
        if not isinstance(name, str):
            errors.append(f"jobs: job name must be a string (got {type(name).__name__})")
            continue
        if not JOB_NAME_RE.match(name):
            errors.append(f"jobs.{name}: invalid job name")
        if not isinstance(job, dict):
            errors.append(f"jobs.{name}: must be a mapping")
            continue

        schedule = job.get("schedule")
        if schedule is None:
            errors.append(f"jobs.{name}.schedule: required")
        elif not isinstance(schedule, str):
            errors.append(f"jobs.{name}.schedule: must be a string")
        elif not _valid_cron(schedule):
            errors.append(f"jobs.{name}.schedule: must be a basic 5-field cron string")

        exec_value = job.get("exec")
        if exec_value is None:
            errors.append(f"jobs.{name}.exec: required")
        elif not isinstance(exec_value, str) or not exec_value.strip():
            errors.append(f"jobs.{name}.exec: must be a non-empty string")

        _validate_positive_int(job, "retention_days", errors, optional=False, scope=f"jobs.{name}")
        _validate_positive_int(job, "timeout_seconds", errors, optional=True, scope=f"jobs.{name}")

        if "cwd" in job:
            cwd = job.get("cwd")
            if not isinstance(cwd, str):
                errors.append(f"jobs.{name}.cwd: must be a string")
            elif not os.path.isabs(cwd):
                errors.append(f"jobs.{name}.cwd: must be an absolute path")

        if "env" in job:
            env = job.get("env")
            if not isinstance(env, dict):
                errors.append(f"jobs.{name}.env: must be a mapping")
            else:
                for key, value in env.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        errors.append(f"jobs.{name}.env: keys and values must be strings")
                        break

        if "disabled" in job and not isinstance(job.get("disabled"), bool):
            errors.append(f"jobs.{name}.disabled: must be a boolean")

        if "description" in job and not isinstance(job.get("description"), str):
            errors.append(f"jobs.{name}.description: must be a string")

    return errors


def _normalize_path(path: str) -> str:
    return os.path.normpath(os.path.expanduser(path))


def _apply_defaults(job: dict[str, Any], defaults: dict[str, Any]) -> None:
    if not isinstance(defaults, dict):
        return
    for key in ("retention_days", "timeout_seconds", "shell", "concurrency"):
        if key not in job and key in defaults:
            job[key] = defaults[key]


def _require_abs_path(cfg: dict[str, Any], key: str, errors: list[str]) -> None:
    value = cfg.get(key)
    if value is None:
        errors.append(f"{key}: required")
        return
    if not isinstance(value, str):
        errors.append(f"{key}: must be a string path")
        return
    if not os.path.isabs(value):
        errors.append(f"{key}: must be an absolute path")


def _validate_positive_int(
    obj: dict[str, Any],
    key: str,
    errors: list[str],
    *,
    optional: bool,
    scope: str,
) -> None:
    value = obj.get(key)
    if value is None:
        if optional:
            return
        errors.append(f"{scope}.{key}: required")
        return
    if not isinstance(value, int):
        errors.append(f"{scope}.{key}: must be an integer")
        return
    if value <= 0:
        errors.append(f"{scope}.{key}: must be positive")


def _valid_cron(schedule: str) -> bool:
    parts = schedule.split()
    if len(parts) != 5:
        return False
    for part in parts:
        if part == "*":
            continue
        if not CRON_FIELD_RE.match(part):
            return False
    return True
