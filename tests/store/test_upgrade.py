"""The D-09 workspace upgrade and the newer or damaged workspace paths (D-09, D-19).

v0.1.0 registers no upgrade step, so these tests pretend the plugin is one workspace version
ahead: they patch ``epb.state.SCHEMA_VERSION`` to 2 and register a synthetic 1 → 2 step.
"""

import json

import pytest
from epb import casefile, schema, state, upgrade
from epb.state import STATE_FILE, load_state
from epbtest.crash import assert_workspace_consistent

INIT_ARGS = ["init", "--title", "Acme Pump Trip", "--prefix", "APT", "--timezone", "UTC"]
BACKUP = ".epb/runs/002/pre-upgrade"


def snapshot(case, *, skip=()):
    """Every path under the case folder with the bytes of every file, minus ``skip``."""
    return {
        path.relative_to(case).as_posix(): (path.read_bytes() if path.is_file() else None)
        for path in sorted(case.rglob("*"))
        if path.relative_to(case).as_posix() not in skip
    }


def codes(items):
    return [item["code"] for item in items]


@pytest.fixture
def initialised(cli, case_dir):
    result = cli([*INIT_ARGS, "--json", "--case", str(case_dir)])
    assert result.exit_code == 0, result.stdout
    return case_dir


def _synthetic_step(snapshot):
    """A made-up 1 → 2 step: it changes one case setting, so its effect is visible."""
    snapshot["case"]["draft_warning_days"] = "14"


@pytest.fixture
def version_two(monkeypatch):
    """Pretend the plugin is at workspace version 2 with a registered 1 → 2 step."""
    monkeypatch.setattr(state, "SCHEMA_VERSION", 2)
    monkeypatch.setitem(upgrade.UPGRADE_STEPS, 1, _synthetic_step)


def test_status_only_warns_upgrade_pending(cli, initialised, version_two):
    before = snapshot(initialised)
    result = cli(["status", "--json", "--case", str(initialised)])
    assert result.exit_code == 0, result.stdout
    assert "UPGRADE_PENDING" in codes(result.envelope["warnings"])
    assert snapshot(initialised) == before


def test_mutating_command_upgrades_with_a_backup(cli, initialised, version_two):
    old_state = (initialised / STATE_FILE).read_bytes()
    old_case = (initialised / casefile.CASE_FILE).read_bytes()
    old_index = (initialised / "INDEX.md").read_text(encoding="utf-8")

    result = cli(["init", "--json", "--case", str(initialised)])

    assert result.exit_code == 0, result.stdout
    warned = codes(result.envelope["warnings"])
    assert "WORKSPACE_UPGRADED" in warned
    message = next(w for w in result.envelope["warnings"] if w["code"] == "WORKSPACE_UPGRADED")
    assert f"{BACKUP}/" in message["message"]
    assert (initialised / BACKUP / ".epb/state.json").read_bytes() == old_state
    assert (initialised / BACKUP / ".epb/case.yaml").read_bytes() == old_case

    new_state = json.loads((initialised / STATE_FILE).read_bytes())
    assert new_state["schema_version"] == 2
    assert schema.validate(new_state, "state") == []
    assert new_state["counters"]["run"] == 2
    new_case = casefile.load_case(initialised)
    assert new_case["schema_version"] == "2"
    assert new_case["draft_warning_days"] == "14"

    run = json.loads((initialised / ".epb/runs/002/run.json").read_bytes())
    assert schema.validate(run, "run") == []
    assert run["command"] == "upgrade"
    assert run["upgrade"] == {"from": 1, "to": 2, "steps": ["1 → 2"], "backup_dir": f"{BACKUP}/"}
    index = (initialised / "INDEX.md").read_text(encoding="utf-8")
    assert index != old_index and "upgrade" in index
    assert_workspace_consistent(initialised)


def test_upgrade_happens_once(cli, initialised, version_two):
    assert cli(["init", "--json", "--case", str(initialised)]).exit_code == 0
    again = cli(["init", "--json", "--case", str(initialised)])
    assert again.exit_code == 0
    assert "WORKSPACE_UPGRADED" not in codes(again.envelope["warnings"])
    assert json.loads((initialised / STATE_FILE).read_bytes())["counters"]["run"] == 2


def test_missing_upgrade_step_changes_nothing(cli, initialised, monkeypatch):
    monkeypatch.setattr(state, "SCHEMA_VERSION", 2)
    before = snapshot(initialised, skip={".epb/lock"})
    result = cli(["init", "--json", "--case", str(initialised)])
    assert result.exit_code == 4
    assert codes(result.envelope["errors"]) == ["INTERNAL_ERROR"]
    assert "No upgrade step from workspace version 1" in result.envelope["errors"][0]["message"]
    assert snapshot(initialised, skip={".epb/lock"}) == before


def test_shipped_plugin_registers_no_step(initialised):
    assert upgrade.UPGRADE_STEPS == {}
    assert upgrade.needs_upgrade(load_state(initialised)) is False


def _exit_and_code(run_epb, args, case):
    result = run_epb([*args, "--json"], case)
    envelope = json.loads(result.stdout)
    return result.returncode, codes(envelope["errors"]), envelope


@pytest.mark.parametrize("command", [["status"], ["init"]])
def test_newer_workspace_exits_4(run_epb, initialised, command):
    path = initialised / STATE_FILE
    data = json.loads(path.read_bytes())
    data["schema_version"] = 99
    path.write_text(json.dumps(data), encoding="utf-8")
    exit_code, errors, _ = _exit_and_code(run_epb, command, initialised)
    assert (exit_code, errors) == (4, ["WORKSPACE_TOO_NEW"])


def _bad_json(case):
    (case / STATE_FILE).write_text("{not json", encoding="utf-8")


def _unknown_key(case):
    path = case / STATE_FILE
    data = json.loads(path.read_bytes())
    data["surprise"] = True
    path.write_text(json.dumps(data), encoding="utf-8")


def _damaged_case(case):
    (case / casefile.CASE_FILE).write_text("title: [unclosed\n", encoding="utf-8")


@pytest.mark.parametrize("command", [["status"], ["init"]])
@pytest.mark.parametrize("damage", [_bad_json, _unknown_key, _damaged_case])
def test_damaged_workspace_exits_4(run_epb, initialised, command, damage):
    damage(initialised)
    exit_code, errors, envelope = _exit_and_code(run_epb, command, initialised)
    assert (exit_code, errors) == (4, ["STATE_INVALID"])
    if damage is _damaged_case:
        assert ".epb/case.yaml" in envelope["errors"][0]["message"]
