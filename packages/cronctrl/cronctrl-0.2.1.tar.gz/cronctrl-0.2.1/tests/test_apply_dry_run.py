from cronctrl import cli
from cronctrl import cron


def test_apply_dry_run_outputs(cronctrl_config_path, capsys):
    args = [
        "--config",
        cronctrl_config_path,
        "apply",
        "--mode",
        "etc-crond",
        "--user",
        "root",
        "--dry-run",
    ]
    assert cli.main(args) == 0
    out = capsys.readouterr().out
    assert "# cron output" in out
    assert "# logrotate output" in out


def test_apply_dry_run_user_crontab_outputs(cronctrl_config_path, capsys, monkeypatch):
    monkeypatch.setattr(cron, "_read_crontab", lambda: "")
    args = [
        "--config",
        cronctrl_config_path,
        "apply",
        "--mode",
        "user-crontab",
        "--dry-run",
        "--remove-missing",
    ]
    assert cli.main(args) == 0
    out = capsys.readouterr().out
    assert "# cron output" in out
    assert "# logrotate output" in out
