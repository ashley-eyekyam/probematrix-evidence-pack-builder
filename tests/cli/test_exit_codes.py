"""Exit codes, stable error codes and the --json envelope (PKG-05)."""

import json
import types
from pathlib import Path

import pytest
from epb import commands, errors, launcher
from epb.cli import Result
from epb.errors import ERROR_CODES, EpbError
from jsonschema import Draft202012Validator

ENVELOPE_KEYS = {"ok", "command", "exit_code", "epb_version", "data", "warnings", "errors", "next"}
SCHEMA_PATH = Path(errors.__file__).resolve().parent / "schemas" / "envelope.schema.json"


@pytest.fixture(scope="module")
def envelope_validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def assert_valid(validator, envelope):
    problems = [error.message for error in validator.iter_errors(envelope)]
    assert problems == [], problems


@pytest.fixture
def fake_command(monkeypatch):
    """Replace command discovery with one fake command whose ``run`` is supplied."""

    def install(run):
        module = types.ModuleType("epb.commands.fake")
        module.NAME = "fake"
        module.HELP = "A fake command for tests."
        module.MUTATING = False
        module.add_arguments = lambda parser: None
        module.run = run
        monkeypatch.setattr(commands, "discover", lambda: [module])

    return install


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


# --- envelope schema --------------------------------------------------------------------


def test_schema_requires_all_keys():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert set(schema["required"]) == ENVELOPE_KEYS
    assert schema["additionalProperties"] is False


def test_success_envelope_matches_schema(cli, fake_command, envelope_validator, case_dir):
    def run(args, ctx):
        ctx.warn("SYNC_FOLDER", "The case folder is inside a sync folder.")
        return Result(data={"count": 1}, next=["scan"], message="Done.")

    fake_command(run)
    result = cli(["--json", "fake", "--case", str(case_dir)])
    assert result.exit_code == 0
    envelope = result.envelope
    assert_valid(envelope_validator, envelope)
    assert envelope["ok"] is True
    assert envelope["command"] == "fake"
    assert envelope["data"] == {"count": 1}
    assert envelope["next"] == ["scan"]
    assert envelope["warnings"][0]["code"] == "SYNC_FOLDER"


def test_failure_keeps_data_and_warnings(cli, fake_command, envelope_validator):
    def run(args, ctx):
        ctx.warn("MIME_MISMATCH", "One file's content does not match its extension.")
        raise EpbError("VALIDATION_FAILED", "The pack failed validation.", data={"findings": 2})

    fake_command(run)
    result = cli(["fake", "--json"])
    assert result.exit_code == 1
    envelope = result.envelope
    assert_valid(envelope_validator, envelope)
    assert envelope["ok"] is False
    assert envelope["data"] == {"findings": 2}
    assert envelope["warnings"][0]["code"] == "MIME_MISMATCH"
    assert envelope["errors"][0]["code"] == "VALIDATION_FAILED"


def test_usage_envelope_matches_schema(cli, envelope_validator):
    result = cli(["--json", "frobnicate"])
    assert result.exit_code == 2
    assert_valid(envelope_validator, result.envelope)


def test_launcher_envelopes_match_schema(monkeypatch, capsys, envelope_validator):
    assert launcher.main(["--json", "status"]) == 3
    assert_valid(envelope_validator, json.loads(capsys.readouterr().out))
    monkeypatch.setattr(launcher, "python_version", lambda: (3, 9, 0))
    assert launcher.main(["--json", "status"]) == 3
    assert_valid(envelope_validator, json.loads(capsys.readouterr().out))


# --- exception mapping ------------------------------------------------------------------


def test_internal_error_traceback_on_stderr_only(cli, fake_command, envelope_validator):
    def run(args, ctx):
        raise ValueError("secret detail from a source file")

    fake_command(run)
    result = cli(["--json", "fake"])
    assert result.exit_code == 4
    envelope = result.envelope
    assert_valid(envelope_validator, envelope)
    error = envelope["errors"][0]
    assert error["code"] == "INTERNAL_ERROR"
    assert "ValueError" in error["message"]
    assert "maintainer" in error["hint"]
    assert "Traceback" in result.stderr
    assert "Traceback" not in result.stdout
    assert "secret detail" not in result.stdout


@pytest.mark.parametrize("name", ["yaml", "yaml.constructor", "PIL"])
def test_core_package_missing(cli, fake_command, envelope_validator, name):
    def run(args, ctx):
        raise ModuleNotFoundError(f"No module named {name!r}", name=name)

    fake_command(run)
    result = cli(["--json", "fake"])
    assert result.exit_code == 3
    assert_valid(envelope_validator, result.envelope)
    error = result.envelope["errors"][0]
    assert error["code"] == "CORE_PACKAGE_MISSING"
    assert "doctor --setup" in error["hint"]


def test_unknown_missing_module_is_internal(cli, fake_command):
    def run(args, ctx):
        raise ModuleNotFoundError("No module named 'not_a_core_package'", name="not_a_core_package")

    fake_command(run)
    result = cli(["--json", "fake"])
    assert result.exit_code == 4
    assert result.envelope["errors"][0]["code"] == "INTERNAL_ERROR"


def test_keyboard_interrupt(cli, fake_command):
    def run(args, ctx):
        raise KeyboardInterrupt

    fake_command(run)
    try:
        result = cli(["--json", "fake"])
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt escaped epb.cli.main")
    assert result.exit_code == 4
    error = result.envelope["errors"][0]
    assert error["code"] == "INTERNAL_ERROR"
    assert error["message"] == "The command was interrupted."


def test_internal_error_plain_language(cli, fake_command):
    def run(args, ctx):
        raise RuntimeError("boom")

    fake_command(run)
    result = cli(["fake"])
    assert result.exit_code == 4
    assert "Error: An internal error occurred (RuntimeError)." in result.stderr
    assert "What to do:" in result.stderr
    assert result.stdout == ""
