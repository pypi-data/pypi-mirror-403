import json
import os

from cronctrl import cli
from cronctrl import cron
from cronctrl import logrotate


def _write_config(tmp_path):
    cfg_text = (
        "version: 1\n"
        f"log_dir: \"{tmp_path / 'logs'}\"\n"
        f"state_dir: \"{tmp_path / 'state'}\"\n"
        "jobs:\n"
        "  alpha:\n"
        "    schedule: \"* * * * *\"\n"
        "    exec: \"/bin/echo alpha\"\n"
        "    retention_days: 1\n"
        "  beta:\n"
        "    schedule: \"* * * * *\"\n"
        "    exec: \"/bin/echo beta\"\n"
        "    retention_days: 1\n"
    )
    path = tmp_path / "jobs.yaml"
    path.write_text(cfg_text, encoding="utf-8")
    return str(path)


def test_remove_purges_logs_and_state(tmp_path, monkeypatch):
    config_path = _write_config(tmp_path)

    log_dir = tmp_path / "logs"
    state_dir = tmp_path / "state"
    locks_dir = state_dir / "locks"
    state_state_dir = state_dir / "state"
    log_dir.mkdir(parents=True)
    locks_dir.mkdir(parents=True)
    state_state_dir.mkdir(parents=True)

    (log_dir / "alpha.log").write_text("alpha", encoding="utf-8")
    (log_dir / "beta.log").write_text("beta", encoding="utf-8")
    (log_dir / "all.log").write_text("all", encoding="utf-8")

    (state_state_dir / "alpha.json").write_text(json.dumps({"job": "alpha"}), encoding="utf-8")
    (state_state_dir / "beta.json").write_text(json.dumps({"job": "beta"}), encoding="utf-8")
    (locks_dir / "alpha.lock").write_text("", encoding="utf-8")

    monkeypatch.setattr(cron, "remove_etc_crond", lambda: None)
    monkeypatch.setattr(logrotate, "remove", lambda: None)

    args = [
        "--config",
        config_path,
        "remove",
        "--mode",
        "etc-crond",
        "--purge-logs",
        "--purge-state",
    ]
    assert cli.main(args) == 0

    assert not (log_dir / "alpha.log").exists()
    assert not (log_dir / "beta.log").exists()
    assert not (log_dir / "all.log").exists()
    assert not (state_state_dir / "alpha.json").exists()
    assert not (state_state_dir / "beta.json").exists()
    assert not (locks_dir / "alpha.lock").exists()


def test_remove_noop_when_files_missing(tmp_path, monkeypatch):
    config_path = _write_config(tmp_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "state").mkdir()

    monkeypatch.setattr(cron, "remove_user_crontab", lambda: None)
    monkeypatch.setattr(logrotate, "remove", lambda: None)

    args = [
        "--config",
        config_path,
        "remove",
        "--mode",
        "user-crontab",
        "--purge-logs",
        "--purge-state",
    ]
    assert cli.main(args) == 0
    assert os.path.isdir(tmp_path / "logs")
    assert os.path.isdir(tmp_path / "state")
