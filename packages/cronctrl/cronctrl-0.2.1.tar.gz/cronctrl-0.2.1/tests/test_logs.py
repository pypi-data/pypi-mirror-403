from cronctrl import logs


def test_tail_logs_last_lines(tmp_path, capsys):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_path = log_dir / "all.log"
    log_path.write_text("one\ntwo\nthree\n", encoding="utf-8")

    cfg = {"log_dir": str(log_dir), "state_dir": str(tmp_path / "state"), "jobs": {}}
    logs.tail_logs(cfg, lines=2)

    captured = capsys.readouterr()
    assert captured.out == "two\nthree\n"


def test_tail_logs_missing_file_raises(tmp_path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    cfg = {"log_dir": str(log_dir), "state_dir": str(tmp_path / "state"), "jobs": {}}

    try:
        logs.tail_logs(cfg, job_name="missing")
    except logs.LogsError as exc:
        assert "log file not found" in str(exc)
    else:
        raise AssertionError("expected LogsError")
