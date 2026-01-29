import textwrap

from cronctrl import config


def test_load_and_validate(tmp_path):
    yaml_text = textwrap.dedent(
        """
        version: 1
        log_dir: "/var/log/cronctrl"
        state_dir: "/var/lib/cronctrl"
        defaults:
          retention_days: 7
        jobs:
          export_daily:
            schedule: "0 2 * * *"
            exec: "/opt/jobs/export_daily.sh"
        """
    ).strip()
    path = tmp_path / "jobs.yaml"
    path.write_text(yaml_text, encoding="utf-8")

    cfg = config.load(str(path))
    errors = config.validate(cfg)
    assert errors == []
    assert cfg["jobs"]["export_daily"]["retention_days"] == 7


def test_invalid_job_name(tmp_path):
    yaml_text = textwrap.dedent(
        """
        version: 1
        log_dir: "/var/log/cronctrl"
        state_dir: "/var/lib/cronctrl"
        defaults:
          retention_days: 7
        jobs:
          "bad name":
            schedule: "0 2 * * *"
            exec: "/opt/jobs/export_daily.sh"
        """
    ).strip()
    path = tmp_path / "jobs.yaml"
    path.write_text(yaml_text, encoding="utf-8")

    cfg = config.load(str(path))
    errors = config.validate(cfg)
    assert any("invalid job name" in error for error in errors)
