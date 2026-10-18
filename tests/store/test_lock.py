"""The workspace lock: mutating commands wait for it, read-only commands ignore it (WS-07).

The holder is a separate process that takes ``.epb/lock`` through ``epb.lock.acquire`` and
sleeps, so the lock is a real OS lock held by another process, exactly as when two agents run
commands on one case folder.
"""

import json
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from epb import cli, lock, workspace
from epb.errors import EpbError

SCRIPTS = Path(__file__).resolve().parents[2] / "plugin/skills/evidence-pack/scripts"
LOCK_SOURCE = SCRIPTS / "epb/lock.py"
INIT_ARGS = ["init", "--title", "Acme Pump Trip", "--prefix", "APT", "--timezone", "UTC", "--json"]

HOLDER_SCRIPT = """
import sys, time
sys.path.insert(0, sys.argv[1])
from epb import lock
handle = lock.acquire(sys.argv[2], wait_s=0, command="test-holder")
print("locked", flush=True)
time.sleep(float(sys.argv[3]))
handle.release()
print("released", flush=True)
time.sleep(60)
"""


@contextmanager
def holder(case, hold_s=60.0):
    """Hold ``<case>/.epb/lock`` in another process for ``hold_s`` seconds."""
    (case / ".epb").mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            HOLDER_SCRIPT,
            str(SCRIPTS),
            str(case / lock.LOCK_FILE),
            str(hold_s),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    try:
        line = proc.stdout.readline()
        if line.strip() != "locked":
            proc.kill()
            raise AssertionError(f"the holder did not take the lock: {proc.stderr.read()}")
        yield proc
    finally:
        proc.kill()
        proc.wait()


def snapshot(case):
    """Every path under the case folder, with the bytes of every file."""
    return {
        path.relative_to(case).as_posix(): (path.read_bytes() if path.is_file() else None)
        for path in sorted(case.rglob("*"))
    }


def _timed(run_epb, args, case):
    start = time.monotonic()
    result = run_epb(args, case)
    return result, time.monotonic() - start


def test_second_init_times_out_while_lock_is_held(run_epb, case_dir):
    with holder(case_dir):
        before = snapshot(case_dir)
        result, elapsed = _timed(run_epb, [*INIT_ARGS, "--wait", "1"], case_dir)
        after = snapshot(case_dir)
    assert result.returncode == 4, result.stdout + result.stderr
    envelope = json.loads(result.stdout)
    error = envelope["errors"][0]
    assert error["code"] == "LOCK_TIMEOUT"
    assert "test-holder" in error["message"]
    assert elapsed < 5
    assert after == before


def test_status_does_not_wait_for_the_lock(run_epb, case_dir):
    assert run_epb(INIT_ARGS, case_dir).returncode == 0
    with holder(case_dir):
        result, elapsed = _timed(run_epb, ["status", "--json"], case_dir)
    assert result.returncode == 0, result.stdout + result.stderr
    assert elapsed < 5


def test_init_waits_until_the_lock_is_released(run_epb, case_dir):
    with holder(case_dir, hold_s=2.0):
        result, elapsed = _timed(run_epb, [*INIT_ARGS, "--wait", "20"], case_dir)
    assert result.returncode == 0, result.stdout + result.stderr
    assert elapsed >= 1.5
    assert (case_dir / ".epb/state.json").is_file()


def test_a_killed_holder_releases_the_lock_at_once(run_epb, case_dir):
    with holder(case_dir) as proc:
        proc.kill()  # SIGKILL on POSIX: no cleanup runs in the holder
        proc.wait()
        result = run_epb([*INIT_ARGS, "--wait", "0"], case_dir)
    assert result.returncode == 0, result.stdout + result.stderr


def test_lock_file_holds_pid_command_and_started_only(run_epb, case_dir):
    with holder(case_dir) as proc:
        text = (case_dir / lock.LOCK_FILE).read_text(encoding="utf-8")
    record = json.loads(text)
    assert set(record) == {"pid", "command", "started"}
    assert record["pid"] == proc.pid
    assert record["command"] == "test-holder"
    assert socket.gethostname() not in text
    assert run_epb(INIT_ARGS, case_dir).returncode == 0
    assert json.loads((case_dir / lock.LOCK_FILE).read_bytes())["command"] == "init"


def test_mutation_session_waits_for_the_lock(case_dir, run_epb):
    assert run_epb(INIT_ARGS, case_dir).returncode == 0
    ctx = cli.Context(case=case_dir, json=True, verbose=False, wait=0.5)
    with holder(case_dir), pytest.raises(EpbError) as caught:
        with workspace.open_for_mutation(case_dir, ctx, "scan"):
            pass
    assert caught.value.code == "LOCK_TIMEOUT"


def test_one_process_cannot_take_the_lock_twice(case_dir):
    (case_dir / ".epb").mkdir()
    path = case_dir / lock.LOCK_FILE
    with lock.acquire(path, wait_s=0, command="first"):
        with pytest.raises(EpbError) as caught:
            lock.acquire(path, wait_s=0.3, command="second")
        assert caught.value.code == "LOCK_TIMEOUT"
        assert "first" in caught.value.message
    second = lock.acquire(path, wait_s=0, command="second")
    second.release()


def test_wait_defaults_to_sixty_seconds():
    parser = cli.build_parser()
    assert parser.parse_args(["init"]).wait == 60.0
    assert parser.parse_args(["status"]).wait == 60.0


def test_the_lock_never_probes_or_signals_a_process():
    source = LOCK_SOURCE.read_text(encoding="utf-8")
    assert "os.kill" not in source
