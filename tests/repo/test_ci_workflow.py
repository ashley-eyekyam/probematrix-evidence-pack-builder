"""Shape of the Linux core CI workflow (TST-01, PKG-09, D-02, D-12, D-18)."""

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
