# cronctrl

cronctrl is a lightweight cron orchestration tool that uses a single YAML file as the source of truth for jobs. It provides a simple CLI to validate configs, run jobs, manage cron entries, and view logs/status.

## Highlights
- Single YAML config file describing all jobs
- `cronctrl validate` for schema checks and basic cron validation
- `cronctrl run <job>` to execute a job immediately with logging and state tracking
- `cronctrl apply` to generate cron entries and logrotate config
- `cronctrl logs` and `cronctrl status` for quick visibility

## Requirements
- Python 3.11+ (tested locally on macOS; target environment is Linux)
- cron and logrotate available on the system for apply mode
- PyYAML (install via requirements or editable install)

## Install
From repo root:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Quick start (configure + activate cron)
This is the minimal flow to get all jobs in your YAML file active via cron.

1) Create your config YAML (start from the example):

```bash
sudo mkdir -p /etc/cronctrl
sudo cp examples/jobs.yaml /etc/cronctrl/jobs.yaml
```

Edit `/etc/cronctrl/jobs.yaml` and make sure:
- `log_dir` and `state_dir` are absolute paths
- each job has a valid `schedule` and `exec`

2) Validate your config:

```bash
cronctrl --config /etc/cronctrl/jobs.yaml validate
```

3) Activate all cron jobs from the YAML:

```bash
cronctrl --config /etc/cronctrl/jobs.yaml apply --mode etc-crond --user root
```

That single `apply` step installs cron entries for every enabled job in the config.

Flags:
- `--mode etc-crond` writes to `/etc/cron.d/cronctrl` (system-wide cron)
- `--user root` sets the OS user cron will run the jobs as in `/etc/cron.d` mode

Note: `--config` is a global option, so it must appear before the subcommand.

## Configuration
Schema is defined in `YAML_SCHEMA.md`. Example (`examples/jobs.yaml`):

```yaml
version: 1
timezone: "America/New_York"
user: "securepixel"

log_dir: "/var/log/cronctrl"
state_dir: "/var/lib/cronctrl"

defaults:
  retention_days: 14
  timeout_seconds: 3600
  shell: "/bin/bash"
  concurrency: "forbid"

jobs:
  heartbeat_minutely:
    schedule: "* * * * *"
    exec: "/bin/echo heartbeat"
    retention_days: 1
    description: "Minutely heartbeat for smoke testing"

  export_daily:
    schedule: "0 2 * * *"
    exec: "/opt/securepixel/jobs/export_daily.sh"
    retention_days: 30
    description: "Daily export job"
```

### Notes
- `version` must be `1`
- `log_dir` and `state_dir` must be absolute paths
- `jobs` is required and must be a mapping
- Job names must match `^[a-zA-Z0-9][a-zA-Z0-9_-]{1,63}$`
- `schedule` must be a basic 5-field cron string (MVP)
- `retention_days` is required (or defaulted from `defaults`)
- `exec` should be an absolute path for scripts/binaries (recommended); plain command names must exist on cron's PATH
- Relative `exec` values run relative to `cwd` (if set) or `/` (cron default), so absolute paths are safer

## CLI commands

### `cronctrl validate`
Parses your YAML file, applies defaults, and validates required fields, job names, schedules, and retention settings. It prints any issues it finds and exits non-zero if the config is invalid, which makes it safe to run in CI or before an `apply`.

```bash
cronctrl --config /etc/cronctrl/jobs.yaml validate
```

### `cronctrl list`
Prints a table of jobs from the config, including schedule, exec, retention, and disabled status. Use `--enabled-only` to filter out disabled jobs.

```bash
cronctrl --config /etc/cronctrl/jobs.yaml list
cronctrl --config /etc/cronctrl/jobs.yaml list --enabled-only
```

### Run a single job immediately (`cronctrl run <job>`)
Executes one job right away using the exact command and settings from the YAML, capturing output into per-job and global logs and recording a state JSON summary for status reporting.

Behavior:
- Acquires a lock (unless `concurrency: allow`)
- Writes per-job and global logs
- Records state JSON with timestamps, exit code, and duration
- Returns the job exit code
 - Runs in `cwd` if set; otherwise cron typically runs with `/` as the working directory

```bash
cronctrl --config /etc/cronctrl/jobs.yaml run export_daily
```

### `cronctrl apply`
Installs the cron schedule and log retention configuration derived from your YAML. In other words, it generates the cron lines that invoke `cronctrl run <job>` on the schedule you defined and writes them to either `/etc/cron.d/cronctrl` (system-wide mode) or your user crontab (user mode). It also generates `/etc/logrotate.d/cronctrl` so job logs are rotated based on `retention_days`.

Modes:
- `etc-crond` (default): writes `/etc/cron.d/cronctrl`
- `user-crontab`: writes a managed block to the current user crontab

```bash
cronctrl --config /etc/cronctrl/jobs.yaml apply --mode etc-crond --user root
cronctrl --config /etc/cronctrl/jobs.yaml apply --mode user-crontab
```

Options:
- `--dry-run` prints cron + logrotate output without writing
- `--remove-missing` (user-crontab only): remove entries that no longer exist in YAML

```bash
cronctrl --config /etc/cronctrl/jobs.yaml apply --mode user-crontab --dry-run
```

### `cronctrl remove`
Removes cronctrl-managed artifacts to stop scheduled runs. It deletes the cronctrl cron entries (either `/etc/cron.d/cronctrl` or the managed block in your user crontab) and removes `/etc/logrotate.d/cronctrl`. It does not delete logs or state unless you opt in with flags.

```bash
cronctrl --config /etc/cronctrl/jobs.yaml remove --mode etc-crond
cronctrl --config /etc/cronctrl/jobs.yaml remove --mode user-crontab
```

Options:
- `--purge-logs` removes per-job logs and `all.log` from `log_dir`
- `--purge-state` removes per-job state JSON and lock files from `state_dir`

### `cronctrl logs`
Streams log output so you can quickly see what jobs are doing. By default it reads the global log (`all.log`), but you can target a single job with `--job`, control how many lines with `--lines`, and follow with `--follow`.

```bash
cronctrl --config /etc/cronctrl/jobs.yaml logs
cronctrl --config /etc/cronctrl/jobs.yaml logs --job export_daily
cronctrl --config /etc/cronctrl/jobs.yaml logs --follow --lines 200
```

### `cronctrl status`
Summarizes the last run for each job using the state JSON files written by `cronctrl run`. This shows last start/finish timestamps, exit code, duration, and message, and can be filtered to a single job.

```bash
cronctrl --config /etc/cronctrl/jobs.yaml status
cronctrl --config /etc/cronctrl/jobs.yaml status --job export_daily
```

## Logs and state
- Per-job log: `<log_dir>/<job>.log`
- Global log: `<log_dir>/all.log`
- State JSON: `<state_dir>/state/<job>.json`

Example state:

```json
{
  "job": "export_daily",
  "last_started_at": "2026-01-24T10:00:00Z",
  "last_finished_at": "2026-01-24T10:02:33Z",
  "last_exit_code": 0,
  "last_duration_seconds": 153,
  "last_command": "/opt/securepixel/jobs/export_daily.sh",
  "last_log_file": "/var/log/cronctrl/export_daily.log",
  "message": "ok"
}
```

## Testing

```bash
/Users/anthonybaum/venv/crontrl/bin/pytest
```

## Release
cronctrl uses a GitHub Actions release workflow that triggers on version tags (e.g., `v0.2.0`). When you push a tag, the workflow builds the sdist and wheel and attaches them to a GitHub Release.

Typical flow:
```bash
git checkout main
git pull origin main
git tag v0.2.0
git push origin v0.2.0
```

## Roadmap
- Phase 6 polish: additional dry-run behaviors, schedule validation improvements
- Phase 7: packaging for pip install (publishable build, ensure cron PATH compatibility)
- Improve UX and output formatting

## License
TBD
