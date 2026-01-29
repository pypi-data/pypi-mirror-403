import json
import os
import fcntl

from cronctrl import runner


def _make_script(tmp_path, body: str) -> str:
    path = tmp_path / "job.sh"
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(0o755)
    return str(path)


def _make_cfg(tmp_path, exec_cmd: str, **job_overrides):
    log_dir = tmp_path / "logs"
    state_dir = tmp_path / "state"
    locks_dir = tmp_path / "locks"
    job = {
        "schedule": "0 2 * * *",
        "exec": exec_cmd,
        "retention_days": 1,
    }
    job.update(job_overrides)
    return {
        "log_dir": str(log_dir),
        "state_dir": str(state_dir),
        "locks_dir": str(locks_dir),
        "jobs": {"test_job": job},
    }


def test_run_job_creates_logs_and_state(tmp_path):
    script = _make_script(tmp_path, "echo hello")
    cfg = _make_cfg(tmp_path, script)

    exit_code = runner.run_job(cfg, "test_job")
    assert exit_code == 0

    per_job_log = tmp_path / "logs" / "test_job.log"
    global_log = tmp_path / "logs" / "all.log"
    state_path = tmp_path / "state" / "state" / "test_job.json"

    assert per_job_log.exists()
    assert global_log.exists()
    assert state_path.exists()

    per_text = per_job_log.read_text(encoding="utf-8")
    global_text = global_log.read_text(encoding="utf-8")

    assert "==== START test_job" in per_text
    assert "hello" in per_text
    assert "==== END test_job" in per_text
    assert "test_job | hello" in global_text

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["job"] == "test_job"
    assert payload["last_exit_code"] == 0
    assert payload["last_log_file"] == str(per_job_log)


def test_run_job_skips_when_locked(tmp_path):
    script = _make_script(tmp_path, "echo locked")
    cfg = _make_cfg(tmp_path, script)

    locks_dir = tmp_path / "locks"
    locks_dir.mkdir(parents=True, exist_ok=True)
    lock_path = locks_dir / "test_job.lock"
    lock_handle = open(lock_path, "a+", encoding="utf-8")
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    try:
        exit_code = runner.run_job(cfg, "test_job")
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()

    assert exit_code == 0

    per_job_log = tmp_path / "logs" / "test_job.log"
    state_path = tmp_path / "state" / "state" / "test_job.json"

    assert per_job_log.exists()
    assert "==== SKIP test_job" in per_job_log.read_text(encoding="utf-8")
    assert not state_path.exists()


def test_run_job_timeout_sets_state(tmp_path):
    script = _make_script(tmp_path, "echo start\nsleep 2\necho end")
    cfg = _make_cfg(tmp_path, script, timeout_seconds=1)

    exit_code = runner.run_job(cfg, "test_job")
    assert exit_code == 124

    per_job_log = tmp_path / "logs" / "test_job.log"
    state_path = tmp_path / "state" / "state" / "test_job.json"

    per_text = per_job_log.read_text(encoding="utf-8")
    assert "==== TIMEOUT test_job" in per_text

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["message"] == "timeout"
    assert payload["last_exit_code"] == 124


def test_run_job_env_and_cwd(tmp_path):
    cfg = _make_cfg(
        tmp_path,
        "echo $FOO > output.txt",
        env={"FOO": "bar"},
        cwd=str(tmp_path),
    )

    exit_code = runner.run_job(cfg, "test_job")
    assert exit_code == 0

    output_path = tmp_path / "output.txt"
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip() == "bar"


def test_run_job_concurrency_allow_ignores_lock(tmp_path):
    script = _make_script(tmp_path, "echo ok")
    cfg = _make_cfg(tmp_path, script, concurrency="allow")

    locks_dir = tmp_path / "locks"
    locks_dir.mkdir(parents=True, exist_ok=True)
    lock_path = locks_dir / "test_job.lock"
    lock_handle = open(lock_path, "a+", encoding="utf-8")
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    try:
        exit_code = runner.run_job(cfg, "test_job")
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()

    assert exit_code == 0

    per_job_log = tmp_path / "logs" / "test_job.log"
    assert "==== START test_job" in per_job_log.read_text(encoding="utf-8")


def test_run_job_missing_exec_path(tmp_path):
    cfg = _make_cfg(tmp_path, "/no/such/path/cronctrl_missing.sh")

    exit_code = runner.run_job(cfg, "test_job")
    assert exit_code == 127

    state_path = tmp_path / "state" / "state" / "test_job.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["last_exit_code"] == 127
    assert payload["message"] == "error"
