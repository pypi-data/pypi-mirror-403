from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from cronctrl import __version__
from cronctrl import config
from cronctrl import cron
from cronctrl import logrotate
from cronctrl import logs
from cronctrl import runner
from cronctrl import status


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return _cmd_validate(args)
    if args.command == "list":
        return _cmd_list(args)
    if args.command == "apply":
        return _cmd_apply(args)
    if args.command == "logs":
        return _cmd_logs(args)
    if args.command == "remove":
        return _cmd_remove(args)
    if args.command == "run":
        return _cmd_run(args)
    if args.command == "status":
        return _cmd_status(args)

    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cronctrl", description="Job catalog cron manager")
    parser.add_argument("--config", default=config.DEFAULT_CONFIG_PATH)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--version", action="version", version=f"cronctrl {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="Validate YAML config")

    list_parser = subparsers.add_parser("list", help="List jobs from config")
    list_parser.add_argument("--enabled-only", action="store_true")

    apply_parser = subparsers.add_parser("apply", help="Install cron entries")
    apply_parser.add_argument(
        "--mode",
        choices=("etc-crond", "user-crontab"),
        default="etc-crond",
    )
    apply_parser.add_argument("--user")
    apply_parser.add_argument("--remove-missing", action="store_true")
    apply_parser.add_argument("--dry-run", dest="dry_run", action="store_true")

    run_parser = subparsers.add_parser("run", help="Run a single job immediately")
    run_parser.add_argument("job_name")

    logs_parser = subparsers.add_parser("logs", help="Tail logs")
    logs_parser.add_argument("--job")
    logs_parser.add_argument("--follow", "-f", action="store_true")
    logs_parser.add_argument("--lines", type=int, default=200)

    status_parser = subparsers.add_parser("status", help="Show last run status")
    status_parser.add_argument("--job")

    remove_parser = subparsers.add_parser("remove", help="Remove cronctrl managed artifacts")
    remove_parser.add_argument(
        "--mode",
        choices=("etc-crond", "user-crontab"),
        default="etc-crond",
    )
    remove_parser.add_argument("--purge-logs", action="store_true")
    remove_parser.add_argument("--purge-state", action="store_true")

    return parser


def _cmd_validate(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    errors = config.validate(cfg)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("config ok")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    errors = config.validate(cfg)
    if errors:
        for error in errors:
            print(error)
        return 1

    jobs = cfg.get("jobs", {})
    if not jobs:
        print("no jobs defined")
        return 0

    rows: list[tuple[str, str, str, str, str]] = []
    for name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        disabled = bool(job.get("disabled", False))
        if args.enabled_only and disabled:
            continue
        rows.append(
            (
                name,
                str(job.get("schedule", "")),
                str(job.get("exec", "")),
                str(job.get("retention_days", "")),
                "true" if disabled else "false",
            )
        )

    if not rows:
        print("no jobs defined")
        return 0

    rows.sort(key=lambda row: row[0])
    headers = ("name", "schedule", "exec", "retention_days", "disabled")
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    format_line = "  ".join([f"{{:<{width}}}" for width in widths])
    print(format_line.format(*headers))
    print(format_line.format(*["-" * width for width in widths]))
    for row in rows:
        print(format_line.format(*row))

    return 0


def _cmd_apply(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    errors = config.validate(cfg)
    if errors:
        for error in errors:
            print(error)
        return 1

    try:
        if args.dry_run:
            if args.mode == "etc-crond":
                cron_output = cron.render_etc_crond(cfg, config_path=args.config, user=args.user)
            else:
                cron_output = cron.render_user_crontab(
                    cfg,
                    config_path=args.config,
                    remove_missing=args.remove_missing,
                )
            logrotate_output = logrotate.render(cfg)
            print("# cron output")
            print(cron_output.rstrip())
            print("\n# logrotate output")
            print(logrotate_output.rstrip())
            return 0

        if args.mode == "etc-crond":
            cron.apply_etc_crond(cfg, config_path=args.config, user=args.user)
        else:
            cron.apply_user_crontab(cfg, config_path=args.config, remove_missing=args.remove_missing)
        logrotate.apply(cfg)
    except cron.CronError as exc:
        print(str(exc))
        return 1
    except logrotate.LogrotateError as exc:
        print(str(exc))
        return 1

    print("cron applied")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    errors = config.validate(cfg)
    if errors:
        for error in errors:
            print(error)
        return 1

    try:
        return runner.run_job(cfg, args.job_name)
    except runner.RunnerError as exc:
        print(str(exc))
        return 1


def _cmd_logs(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    errors = config.validate(cfg)
    if errors:
        for error in errors:
            print(error)
        return 1

    try:
        logs.tail_logs(cfg, job_name=args.job, follow=args.follow, lines=args.lines)
    except logs.LogsError as exc:
        print(str(exc))
        return 1
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    errors = config.validate(cfg)
    if errors:
        for error in errors:
            print(error)
        return 1

    try:
        rows = status.load_status(cfg, job_name=args.job)
    except status.StatusError as exc:
        print(str(exc))
        return 1

    if not rows:
        print("no jobs found")
        return 0

    headers = ("job", "last_started", "last_finished", "last_exit", "last_duration", "last_message")
    display_rows: list[tuple[str, str, str, str, str, str]] = []
    for row in rows:
        display_rows.append(
            (
                str(row.get("job", "")),
                str(row.get("last_started_at") or "never"),
                str(row.get("last_finished_at") or "never"),
                str(row.get("last_exit_code") if row.get("last_exit_code") is not None else "never"),
                str(
                    row.get("last_duration_seconds")
                    if row.get("last_duration_seconds") is not None
                    else "never"
                ),
                str(row.get("last_message") or "never"),
            )
        )

    widths = [len(header) for header in headers]
    for row in display_rows:
        widths = [max(width, len(value)) for width, value in zip(widths, row)]

    format_line = "  ".join([f"{{:<{width}}}" for width in widths])
    print(format_line.format(*headers))
    print(format_line.format(*["-" * width for width in widths]))
    for row in display_rows:
        print(format_line.format(*row))

    return 0


def _cmd_remove(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config)
    errors = config.validate(cfg)
    if errors:
        for error in errors:
            print(error)
        return 1

    try:
        if args.mode == "etc-crond":
            cron.remove_etc_crond()
        else:
            cron.remove_user_crontab()
        logrotate.remove()
    except cron.CronError as exc:
        print(str(exc))
        return 1

    if args.purge_logs:
        try:
            _purge_logs(cfg)
        except RuntimeError as exc:
            print(str(exc))
            return 1
    if args.purge_state:
        try:
            _purge_state(cfg)
        except RuntimeError as exc:
            print(str(exc))
            return 1

    print("cron removed")
    return 0


def _purge_logs(cfg: dict[str, Any]) -> None:
    log_dir = cfg.get("log_dir")
    if not isinstance(log_dir, str) or not log_dir.strip():
        raise RuntimeError("log_dir: required to purge logs")
    jobs = cfg.get("jobs")
    if not isinstance(jobs, dict):
        raise RuntimeError("jobs: required to purge logs")

    for job_name in jobs.keys():
        _remove_file(os.path.join(log_dir, f"{job_name}.log"))
    _remove_file(os.path.join(log_dir, "all.log"))


def _purge_state(cfg: dict[str, Any]) -> None:
    state_dir = cfg.get("state_dir")
    if not isinstance(state_dir, str) or not state_dir.strip():
        raise RuntimeError("state_dir: required to purge state")
    jobs = cfg.get("jobs")
    if not isinstance(jobs, dict):
        raise RuntimeError("jobs: required to purge state")

    for job_name in jobs.keys():
        _remove_file(os.path.join(state_dir, "state", f"{job_name}.json"))

    locks_dir = cfg.get("locks_dir")
    if not isinstance(locks_dir, str):
        locks_dir = os.path.join(state_dir, "locks")
    if os.path.isdir(locks_dir):
        for entry in os.listdir(locks_dir):
            _remove_file(os.path.join(locks_dir, entry))


def _remove_file(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        return


def _load_config(path: str) -> dict[str, Any]:
    try:
        return config.load(path)
    except config.ConfigError as exc:
        print(str(exc))
        raise SystemExit(1) from exc
