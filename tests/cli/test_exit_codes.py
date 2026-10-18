"""Exit codes, stable error codes and the --json envelope (PKG-05)."""

import json

import pytest
from epb import errors
from epb.errors import ERROR_CODES, EpbError

ENVELOPE_KEYS = {"ok", "command", "exit_code", "epb_version", "data", "warnings", "errors", "next"}


def test_usage_error_envelope_subprocess(run_epb, case_dir):
    proc = run_epb(["--json", "frobnicate"], cwd=case_dir)
    assert proc.returncode == 2, proc.stderr
    envelope = json.loads(proc.stdout)
    assert set(envelope) == ENVELOPE_KEYS
    assert envelope["ok"] is False
    assert envelope["exit_code"] == 2
    assert envelope["errors"][0]["code"] == "USAGE"


def test_missing_command_is_usage(run_epb, case_dir):
    proc = run_epb(["--json"], cwd=case_dir)
    assert proc.returncode == 2, proc.stderr
    envelope = json.loads(proc.stdout)
    assert envelope["errors"][0]["code"] == "USAGE"
    assert envelope["exit_code"] == 2


def test_catalogue_exit_classes():
    assert all(1 <= code <= 4 for code in ERROR_CODES.values())
    assert ERROR_CODES["STATE_INVALID"] == errors.EXIT_ENVIRONMENT == 4
    assert ERROR_CODES["USAGE"] == errors.EXIT_USAGE == 2
    assert ERROR_CODES["ENV_NOT_SET_UP"] == errors.EXIT_MISSING_DEPENDENCY == 3


def test_unknown_code_rejected():
    with pytest.raises(ValueError):
        EpbError("NOPE", "x")


def test_not_in_env_without_setup(run_epb, case_dir):
    proc = run_epb(["--json", "status"], cwd=case_dir, in_env=False)
    assert proc.returncode == 3, proc.stderr
    envelope = json.loads(proc.stdout)
    assert envelope["errors"][0]["code"] == "ENV_NOT_SET_UP"
    assert envelope["exit_code"] == 3
    assert envelope["next"] == ["doctor --setup"]
