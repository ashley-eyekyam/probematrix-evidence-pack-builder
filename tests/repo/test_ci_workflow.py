"""Shape of the Linux core CI workflow (TST-01, PKG-09, D-02, D-12, D-18)."""

import tomllib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


@pytest.fixture(scope="module")
def workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def core(workflow):
    return workflow["jobs"]["core"]


@pytest.fixture(scope="module")
def runs(core):
    """Every step's ``run`` script, in order."""
    return [step.get("run", "") for step in core["steps"]]


def _index(runs, needle):
    matches = [i for i, script in enumerate(runs) if needle in script]
    assert matches, f"no CI step runs {needle!r}"
    return matches[0]


def test_triggers_on_push_and_pull_request(workflow):
    # YAML 1.1 reads a bare `on` key as the boolean True.
    triggers = workflow.get("on", workflow.get(True))
    assert triggers is not None
    assert "push" in triggers
    assert "pull_request" in triggers


def test_core_job_runs_python_3_11_and_3_14_on_ubuntu(core):
    assert core["runs-on"].startswith("ubuntu")
    assert core["strategy"]["matrix"]["python-version"] == ["3.11", "3.14"]
    assert core["strategy"]["fail-fast"] is False
    assert core["env"]["PYTHONWARNDEFAULTENCODING"] == "1"


def test_uses_the_agreed_actions(core):
    uses = [step["uses"] for step in core["steps"] if "uses" in step]
    assert uses == ["actions/checkout@v7", "actions/setup-python@v7"]


@pytest.mark.parametrize(
    "needle",
    [
        '"pip>=26.1"',
        "--uploaded-prior-to P14D -r requirements-dev.txt",
        "check_dependency_age.py --pins",
        "ruff check .",
        "ruff format --check .",
        "pytest",
        "tools/check_dependency_age.py",
        "tools/check_licences.py",
        "claude plugin validate . --strict",
        "claude plugin validate ./plugin --strict",
    ],
)
def test_has_step(runs, needle):
    _index(runs, needle)


AGE_CHECK = "python tools/check_dependency_age.py"


def test_age_check_has_its_own_step(runs):
    # The --pins step also mentions the script; the check itself is a separate step.
    assert AGE_CHECK in runs


def test_steps_run_in_the_agreed_order(runs):
    order = [
        _index(runs, '"pip>=26.1"'),
        _index(runs, "--uploaded-prior-to P14D"),
        _index(runs, "check_dependency_age.py --pins"),
        _index(runs, "ruff check ."),
        _index(runs, "ruff format --check ."),
        _index(runs, "pytest"),
        runs.index(AGE_CHECK),
        _index(runs, "tools/check_licences.py"),
        _index(runs, "claude plugin validate"),
    ]
    assert order == sorted(order)


def test_plugin_validate_is_guarded_by_the_claude_cli(runs):
    script = runs[_index(runs, "claude plugin validate")]
    assert "command -v claude" in script
    assert "skipping plugin validate (D-02)" in script


# --- EncodingWarning filters (verification gap 1, review D-CR-01) ----------------------------

PYPROJECT = REPO_ROOT / "pyproject.toml"
ENCODING_ERROR = "error::EncodingWarning"


def _filterwarnings():
    with PYPROJECT.open("rb") as handle:
        config = tomllib.load(handle)
    return config["tool"]["pytest"]["ini_options"]["filterwarnings"]


def _fields(entry):
    """``action:message:category:module:lineno``, padded with empty strings."""
    parts = entry.split(":", 4)
    return parts + [""] * (5 - len(parts))


def _relaxed_encoding_entries(entries):
    """Every entry that would stop an EncodingWarning from being an error."""
    return [
        entry
        for entry in entries
        if _fields(entry)[0] != "error" and _fields(entry)[2].endswith("EncodingWarning")
    ]


def test_encoding_warnings_stay_errors_for_project_code():
    entries = _filterwarnings()
    assert ENCODING_ERROR in entries
    relaxed = _relaxed_encoding_entries(entries)
    assert relaxed, "expected the openpyxl temp-file ignore entry"
    for entry in relaxed:
        action, _message, _category, module, _lineno = _fields(entry)
        assert action == "ignore", entry
        assert module.startswith("openpyxl"), (
            f"EncodingWarning may be relaxed only for openpyxl, not: {entry!r}"
        )


def test_openpyxl_ignore_comes_after_the_error_entry():
    # pytest gives later filterwarnings entries precedence over earlier ones.
    entries = _filterwarnings()
    openpyxl_entries = [
        entry
        for entry in _relaxed_encoding_entries(entries)
        if _fields(entry)[3].startswith("openpyxl")
    ]
    assert openpyxl_entries, "no EncodingWarning ignore entry for openpyxl"
    error_index = entries.index(ENCODING_ERROR)
    for entry in openpyxl_entries:
        assert entries.index(entry) > error_index, entry


# --- local / CI parity (PKG-11) ---------------------------------------------------------------

AGENTS = REPO_ROOT / "AGENTS.md"
DOCUMENTED_PYTEST = "PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q"
DOCUMENTED_LICENCES = ".venv/bin/python tools/check_licences.py"

# Each command in AGENTS.md's full check and the ci.yml step it stands for, in CI's order.
# The dependency-age check is CI-only on purpose: it queries PyPI, and the full check runs
# offline like the test suite.
FULL_CHECK_STEPS = [
    ("ruff check .", "ruff check ."),
    ("ruff format --check .", "ruff format --check ."),
    (DOCUMENTED_PYTEST, "python -m pytest -q"),
    (DOCUMENTED_LICENCES, "python tools/check_licences.py"),
]


def _full_check_line():
    """AGENTS.md's single line containing "Full check"."""
    lines = [
        line for line in AGENTS.read_text(encoding="utf-8").splitlines() if "Full check" in line
    ]
    assert len(lines) == 1, f"expected one 'Full check' line in AGENTS.md, found {len(lines)}"
    return lines[0]


def test_documented_full_check_matches_ci(core):
    lines = [
        line for line in AGENTS.read_text(encoding="utf-8").splitlines() if "Full check" in line
    ]
    assert len(lines) == 1, f"expected one 'Full check' line in AGENTS.md, found {len(lines)}"
    assert DOCUMENTED_PYTEST in lines[0], (
        "AGENTS.md's full check must run pytest the way CI does: " + DOCUMENTED_PYTEST
    )
    assert core["env"]["PYTHONWARNDEFAULTENCODING"] == "1"


@pytest.mark.parametrize(
    ("documented", "ci_step"), FULL_CHECK_STEPS, ids=["lint", "format", "tests", "licences"]
)
def test_documented_full_check_runs_every_local_ci_step(runs, documented, ci_step):
    assert documented in _full_check_line(), f"AGENTS.md's full check must run {documented!r}"
    _index(runs, ci_step)


def test_documented_full_check_keeps_ci_order(runs):
    line = _full_check_line()
    documented = [line.find(command) for command, _ci_step in FULL_CHECK_STEPS]
    assert -1 not in documented, f"the full check is missing a step: {line!r}"
    assert documented == sorted(documented), "the full check runs its steps out of CI's order"
    in_ci = [_index(runs, ci_step) for _command, ci_step in FULL_CHECK_STEPS]
    assert in_ci == sorted(in_ci), "ci.yml runs these steps in a different order"
