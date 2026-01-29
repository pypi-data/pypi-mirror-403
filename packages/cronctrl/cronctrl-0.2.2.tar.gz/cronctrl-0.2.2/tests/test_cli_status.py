from cronctrl import cli


def test_status_unknown_job_exits_nonzero(tmp_path):
    cfg_text = (
        "version: 1\n"
        f"log_dir: \"{tmp_path / 'logs'}\"\n"
        f"state_dir: \"{tmp_path / 'state'}\"\n"
        "jobs:\n"
        "  alpha:\n"
        "    schedule: \"* * * * *\"\n"
        "    exec: \"/bin/echo alpha\"\n"
        "    retention_days: 1\n"
    )
    path = tmp_path / "jobs.yaml"
    path.write_text(cfg_text, encoding="utf-8")

    args = ["--config", str(path), "status", "--job", "missing"]
    assert cli.main(args) == 1
