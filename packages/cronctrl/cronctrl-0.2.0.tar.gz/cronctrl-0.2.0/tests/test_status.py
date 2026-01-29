import json

from cronctrl import status


def _base_cfg(tmp_path):
    return {
        "log_dir": str(tmp_path / "logs"),
        "state_dir": str(tmp_path / "state"),
        "jobs": {
            "a": {"schedule": "* * * * *", "exec": "/bin/echo a", "retention_days": 1},
            "b": {"schedule": "* * * * *", "exec": "/bin/echo b", "retention_days": 1},
        },
    }


def test_load_status_reads_state(tmp_path):
    cfg = _base_cfg(tmp_path)
    state_dir = tmp_path / "state" / "state"
    state_dir.mkdir(parents=True)
    payload = {
        "job": "a",
        "last_started_at": "2026-01-24T01:00:00Z",
        "last_finished_at": "2026-01-24T01:00:05Z",
        "last_exit_code": 0,
        "last_duration_seconds": 5,
        "message": "ok",
    }
    (state_dir / "a.json").write_text(json.dumps(payload), encoding="utf-8")

    rows = status.load_status(cfg)
    rows_by_job = {row["job"]: row for row in rows}

    assert rows_by_job["a"]["last_exit_code"] == 0
    assert rows_by_job["a"]["last_message"] == "ok"
    assert rows_by_job["b"]["last_exit_code"] is None


def test_load_status_single_job(tmp_path):
    cfg = _base_cfg(tmp_path)
    rows = status.load_status(cfg, job_name="b")
    assert len(rows) == 1
    assert rows[0]["job"] == "b"


def test_load_status_handles_invalid_json(tmp_path):
    cfg = _base_cfg(tmp_path)
    state_dir = tmp_path / "state" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "a.json").write_text("{not json", encoding="utf-8")

    rows = status.load_status(cfg)
    rows_by_job = {row["job"]: row for row in rows}

    assert rows_by_job["a"]["last_exit_code"] is None


def test_load_status_unknown_job_raises(tmp_path):
    cfg = _base_cfg(tmp_path)
    try:
        status.load_status(cfg, job_name="missing")
    except status.StatusError as exc:
        assert "job not found" in str(exc)
    else:
        raise AssertionError("expected StatusError")
