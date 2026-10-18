"""``epb doctor --setup`` without the network (PKG-06, PKG-08, D-03, D-18, T-01-24..27).

``run_setup`` is called in-process with a fake runner in place of ``subprocess.run``. The
runner records every argv, creates the environment folder and a placeholder interpreter on the
venv step, and returns scripted results, so no test here downloads or installs anything. The
autouse fake home from ``tests/conftest.py`` holds every environment these tests build.
"""

import ast
import hashlib
import json
import os
import subprocess
import sys
from itertools import pairwise
from pathlib import Path

import pytest
from epb import __version__, launcher
from epb.cli import Context
from epb.doctor import probes, report
from epb.doctor import setup as epb_setup
from epb.errors import EpbError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "plugin" / "skills" / "evidence-pack" / "scripts"
EPB_PACKAGE = SCRIPTS / "epb"
REQUIREMENTS = REPO_ROOT / "plugin" / "requirements.txt"
INSTALL_CODEX = REPO_ROOT / "tools" / "install-codex.py"

STEPS = [
    "create environment",
    "upgrade pip",
    "install core packages",
    "install reviewed security pins",
    "verify",
]
ENSUREPIP_OUTPUT = (
    "Error: Command '['/x/bin/python3', '-m', 'ensurepip', '--upgrade', '--default-pip']' "
    "returned non-zero exit status 1.\n"
    "The virtual environment was not created successfully because ensurepip is not\n"
    "available.  On Debian/Ubuntu systems, you need to install the python3-venv\n"
    "package using the following command.\n"
)


def kind(argv):
    """Which setup step an argv belongs to."""
    if argv[1:3] == ["-m", "venv"]:
        return "create environment"
    if argv[1:4] == ["-m", "pip", "install"]:
        if "--upgrade" in argv:
            return "upgrade pip"
        if "--uploaded-prior-to" in argv:
            return "install core packages"
        return "install reviewed security pins"
    if epb_setup.VERIFY_IMPORTS in argv:
        return "verify imports"
    if "from importlib import metadata" in " ".join(argv):
        return "verify packages"
    return "unknown"


class FakeRunner:
    """Stands in for ``subprocess.run``. ``fail`` maps a step kind to its failing output."""

    def __init__(self, fail=None):
        self.fail = dict(fail or {})
        self.calls = []
        self.kinds = []
        self.kwargs = []
        self.marker_seen = []

    def __call__(self, argv, **kwargs):
        argv = [str(part) for part in argv]
        step = kind(argv)
        env = launcher.env_dir()
        self.calls.append(argv)
        self.kinds.append(step)
        self.kwargs.append(kwargs)
        self.marker_seen.append(launcher.marker_path(env).exists())
        if step in self.fail:
            return subprocess.CompletedProcess(argv, 1, stdout=self.fail[step], stderr=None)
        stdout = ""
        if step == "create environment":
            python = launcher.env_python(Path(argv[3]))
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_text("placeholder interpreter\n", encoding="utf-8")
        elif step == "verify packages":
            names = argv[argv.index("-c") + 2 :]
            stdout = json.dumps({name: "999.0" for name in names})
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr=None)


@pytest.fixture
def ctx(case_dir):
    return Context(case=case_dir, json=True, verbose=False, wait=60.0)


@pytest.fixture
def env():
    return launcher.env_dir()


def tree(root):
    """Relative POSIX path -> sha256 of every file under ``root``."""
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def use_exceptions(monkeypatch, tmp_path, document):
    """Point ``security-exceptions.json`` at a file holding ``document`` (str or JSON)."""
    path = tmp_path / "security-exceptions.json"
    text = document if isinstance(document, str) else json.dumps(document)
    path.write_text(text, encoding="utf-8")
    original = launcher.locate_plugin_file

    def locate(name):
        return path if name == "security-exceptions.json" else original(name)

    monkeypatch.setattr(launcher, "locate_plugin_file", locate)


def build(ctx, runner=None):
    runner = runner or FakeRunner()
    return epb_setup.run_setup(ctx, run=runner), runner


# --- a fresh setup ------------------------------------------------------------------------


def test_fresh_setup_runs_the_steps_in_order(ctx, env, home_dir):
    result, runner = build(ctx)
    assert runner.kinds == [
        "create environment",
        "upgrade pip",
        "install core packages",
        "verify imports",
        "verify packages",
    ]
    assert env == home_dir / ".local" / "share" / "probematrix-epb" / "envs" / __version__
    assert runner.calls[0] == [sys.executable, "-m", "venv", str(env)]
    env_python = str(launcher.env_python(env))
    assert all(call[0] == env_python for call in runner.calls[1:])
    assert "pip>=26.1" in runner.calls[1]
    core = runner.calls[2]
    at = core.index("--uploaded-prior-to")
    assert core[at : at + 4] == ["--uploaded-prior-to", "P14D", "-r", str(REQUIREMENTS)]
    assert result.data["setup"]["status"] == "created"
    assert [step["name"] for step in result.data["setup"]["steps"]] == STEPS


def test_marker_is_written_last_and_is_current(ctx, env):
    _, runner = build(ctx)
    assert runner.marker_seen == [False] * len(runner.calls)
    assert launcher.marker_is_current(env)
    record = launcher.read_marker(env)
    assert record["plugin_version"] == __version__
    assert record["python"] == ".".join(str(part) for part in sys.version_info[:3])


def test_every_step_has_a_timeout_and_no_shell(ctx):
    _, runner = build(ctx)
    for argv, kwargs in zip(runner.calls, runner.kwargs, strict=True):
        assert kwargs.get("timeout"), argv
        assert not kwargs.get("shell"), argv
        assert kwargs.get("stdin") == subprocess.DEVNULL, argv
    assert runner.kwargs[0]["timeout"] == 300
    assert {kwargs["timeout"] for kwargs in runner.kwargs[1:4]} == {900}


def test_result_carries_the_doctor_report_and_launch_command(ctx, env):
    result, _ = build(ctx)
    data = result.data
    for key in ("python", "environment", "core_packages", "tools", "extras", "setup_command"):
        assert key in data
    assert data["environment"]["launch"] == [
        str(launcher.env_python(env)),
        str(launcher.epb_script()),
    ]
    assert data["setup"]["environment"] == str(env)


def test_reviewed_pins_install_after_core_and_before_verify(ctx, monkeypatch, tmp_path):
    use_exceptions(
        monkeypatch,
        tmp_path,
        {
            "schema_version": 1,
            "description": "test",
            "exceptions": [
                {"package": "examplepkg", "version": "1.2.3"},
                {"package": "other-pkg", "version": "4.5.6.post1"},
            ],
        },
    )
    result, runner = build(ctx)
    assert runner.kinds == [
        "create environment",
        "upgrade pip",
        "install core packages",
        "install reviewed security pins",
        "install reviewed security pins",
        "verify imports",
        "verify packages",
    ]
    assert runner.calls[3][-1] == "examplepkg==1.2.3"
    assert runner.calls[4][-1] == "other-pkg==4.5.6.post1"
    for argv in runner.calls[3:5]:
        assert "--uploaded-prior-to" not in argv
        assert "-r" not in argv
    pins = [step for step in result.data["setup"]["steps"] if step["name"] == STEPS[3]]
    assert pins == [{"name": STEPS[3], "status": "done"}]


def test_no_exceptions_skips_the_pin_step(ctx):
    result, runner = build(ctx)
    assert "install reviewed security pins" not in runner.kinds
    pins = [step for step in result.data["setup"]["steps"] if step["name"] == STEPS[3]]
    assert pins == [{"name": STEPS[3], "status": "skipped"}]


# --- failures -----------------------------------------------------------------------------


def test_missing_ensurepip_is_venv_unavailable(ctx, env):
    runner = FakeRunner(fail={"create environment": ENSUREPIP_OUTPUT})
    with pytest.raises(EpbError) as caught:
        build(ctx, runner)
    error = caught.value
    assert error.code == "VENV_UNAVAILABLE"
    assert error.exit_code == 3
    assert "sudo apt install python3-venv" in error.hint
    assert f"python3.{sys.version_info[1]}-venv" in error.hint
    assert runner.kinds == ["create environment"]
    assert not launcher.marker_path(env).exists()


def test_other_venv_failure_is_setup_failed(ctx):
    runner = FakeRunner(fail={"create environment": "Error: [Errno 28] No space left on device"})
    with pytest.raises(EpbError) as caught:
        build(ctx, runner)
    assert caught.value.code == "SETUP_FAILED"
    assert "create environment" in caught.value.message


@pytest.mark.parametrize(
    ("failing", "step"),
    [
        ("upgrade pip", "upgrade pip"),
        ("install core packages", "install core packages"),
        ("verify imports", "verify"),
        ("verify packages", "verify"),
    ],
)
def test_failing_step_is_setup_failed_and_names_the_step(ctx, env, failing, step):
    output = "\n".join(f"pip output line {number}" for number in range(1, 31))
    runner = FakeRunner(fail={failing: output})
    with pytest.raises(EpbError) as caught:
        build(ctx, runner)
    error = caught.value
    assert error.code == "SETUP_FAILED"
    assert error.exit_code == 4
    assert f'"{step}"' in error.message
    assert error.data["setup"]["step"] == step
    assert sys.executable in error.hint
    assert str(launcher.epb_script()) in error.hint
    assert "doctor --setup" in error.hint
    assert "open a terminal" in error.hint
    assert not launcher.marker_path(env).exists()
    assert not launcher.marker_is_current(env)
    if failing != "verify packages":
        assert error.data["output_tail"] == [f"pip output line {n}" for n in range(11, 31)]


def test_timeout_is_setup_failed(ctx):
    def runner(argv, **kwargs):
        if kind([str(part) for part in argv]) == "upgrade pip":
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"], output=b"Collecting pip")
        return FakeRunner()(argv, **kwargs)

    with pytest.raises(EpbError) as caught:
        epb_setup.run_setup(ctx, run=runner)
    assert caught.value.code == "SETUP_FAILED"
    assert caught.value.data["output_tail"][0] == "Collecting pip"
    assert "900 seconds" in caught.value.data["output_tail"][-1]


def test_missing_requirements_file_is_setup_failed(ctx, monkeypatch):
    monkeypatch.setattr(launcher, "locate_plugin_file", lambda name: None)
    runner = FakeRunner()
    with pytest.raises(EpbError) as caught:
        build(ctx, runner)
    assert caught.value.code == "SETUP_FAILED"
    assert "reinstall the plugin" in caught.value.message
    assert runner.calls == []


@pytest.mark.parametrize(
    "document",
    [
        "{not json",
        {"schema_version": 1},
        {"exceptions": ["examplepkg==1.0"]},
        {"exceptions": [{"package": "--index-url=http://example.invalid", "version": "1"}]},
        {"exceptions": [{"package": "examplepkg", "version": "1.0 --pre"}]},
        {"exceptions": [{"package": "examplepkg"}]},
    ],
)
def test_malformed_exceptions_file_is_setup_failed(ctx, monkeypatch, tmp_path, document):
    use_exceptions(monkeypatch, tmp_path, document)
    runner = FakeRunner()
    with pytest.raises(EpbError) as caught:
        build(ctx, runner)
    assert caught.value.code == "SETUP_FAILED"
    assert "security-exceptions.json" in caught.value.message
    assert runner.calls == []


def test_env_outside_the_data_root_is_refused(ctx, monkeypatch, tmp_path):
    elsewhere = tmp_path / "elsewhere" / __version__
    elsewhere.mkdir(parents=True)
    (elsewhere / "keep.txt").write_text("keep\n", encoding="utf-8")
    monkeypatch.setattr(launcher, "env_dir", lambda version=None: elsewhere)
    runner = FakeRunner()
    with pytest.raises(EpbError) as caught:
        build(ctx, runner)
    assert caught.value.code == "INTERNAL_ERROR"
    assert (elsewhere / "keep.txt").is_file()
    assert runner.calls == []


# --- idempotency, stale environments and interruption ------------------------------------


def test_current_environment_is_ready_and_unchanged(ctx, env):
    build(ctx)
    before = tree(env)
    result, runner = build(ctx)
    assert runner.kinds == ["verify imports", "verify packages"]
    assert result.data["setup"]["status"] == "ready"
    assert tree(env) == before
    assert [item["code"] for item in ctx.warnings] == ["ALREADY_SET_UP"]
    steps = result.data["setup"]["steps"]
    assert [step["status"] for step in steps] == ["skipped"] * 4 + ["done"]


def test_current_marker_with_broken_packages_rebuilds(ctx, env):
    build(ctx)
    runner = FakeRunner(fail={"verify imports": "ModuleNotFoundError: No module named 'yaml'"})
    calls = []

    def first_verify_fails(argv, **kwargs):
        calls.append(kind([str(part) for part in argv]))
        if len(calls) == 1:
            return runner(argv, **kwargs)
        return FakeRunner()(argv, **kwargs)

    result = epb_setup.run_setup(ctx, run=first_verify_fails)
    assert result.data["setup"]["status"] == "rebuilt"
    assert calls[1] == "create environment"
    assert launcher.marker_is_current(env)


def test_stale_environment_is_removed_and_rebuilt_siblings_untouched(ctx, env):
    sibling = env.parent / "0.0.9"
    (sibling / "bin").mkdir(parents=True)
    (sibling / "bin" / "python").write_text("old interpreter\n", encoding="utf-8")
    (sibling / "epb-env.json").write_text('{"plugin_version": "0.0.9"}\n', encoding="utf-8")
    (sibling / "lib" / "site.txt").parent.mkdir()
    (sibling / "lib" / "site.txt").write_text("old packages\n", encoding="utf-8")
    sibling_before = tree(sibling)

    launcher.env_python(env).parent.mkdir(parents=True)
    launcher.env_python(env).write_text("stale interpreter\n", encoding="utf-8")
    (env / "leftover.txt").write_text("from the old build\n", encoding="utf-8")
    record = launcher.marker_record(sys.version_info[:3])
    record["requirements_sha256"] = "0" * 64
    launcher.write_marker(env, record)
    assert not launcher.marker_is_current(env)

    result, runner = build(ctx)
    assert result.data["setup"]["status"] == "rebuilt"
    assert runner.kinds[0] == "create environment"
    assert not (env / "leftover.txt").exists()
    assert launcher.marker_is_current(env)
    assert tree(sibling) == sibling_before


def test_interrupted_setup_is_not_trusted_and_the_next_run_rebuilds(ctx, env):
    with pytest.raises(EpbError):
        build(ctx, FakeRunner(fail={"install core packages": "Connection reset by peer"}))
    assert env.is_dir()
    assert not launcher.marker_is_current(env)

    result, runner = build(ctx)
    assert result.data["setup"]["status"] == "rebuilt"
    assert runner.kinds[0] == "create environment"
    assert launcher.marker_is_current(env)


def test_launcher_reports_env_not_set_up_after_a_failed_setup(ctx, env, case_dir, capsys):
    with pytest.raises(EpbError):
        build(ctx, FakeRunner(fail={"verify imports": "ImportError"}))
    exit_code = launcher.main(["init", "--json"])
    envelope = json.loads(capsys.readouterr().out)
    assert exit_code == 3
    assert envelope["errors"][0]["code"] == "ENV_NOT_SET_UP"


# --- the command line and the checklist ---------------------------------------------------


def test_doctor_setup_flag_dispatches_to_run_setup(cli, case_dir, monkeypatch):
    seen = []

    def fake_run_setup(ctx):
        seen.append(ctx.case)
        from epb.cli import Result

        return Result(data={"setup": {"status": "ready"}}, message="done")

    monkeypatch.setattr(epb_setup, "run_setup", fake_run_setup)
    outcome = cli(["doctor", "--setup", "--json"], cwd=case_dir)
    assert outcome.exit_code == 0
    assert outcome.envelope["data"] == {"setup": {"status": "ready"}}
    assert seen == [case_dir]


def test_setup_failure_envelope_through_the_cli(cli, case_dir, monkeypatch):
    real_run_setup = epb_setup.run_setup

    def broken(ctx):
        return real_run_setup(ctx, run=FakeRunner(fail={"upgrade pip": "no network"}))

    monkeypatch.setattr(epb_setup, "run_setup", broken)
    outcome = cli(["doctor", "--setup", "--json"], cwd=case_dir)
    assert outcome.exit_code == 4, outcome.stderr
    assert outcome.envelope["errors"][0]["code"] == "SETUP_FAILED", outcome.stderr
    assert outcome.envelope["data"]["output_tail"] == ["no network"]


@pytest.mark.parametrize("status", ["created", "rebuilt", "ready"])
def test_setup_checklist(case_dir, home_dir, env, status):
    data = probes.collect(case_dir)
    for package in data["core_packages"]:
        package["ok"] = True
    setup = {"status": status, "environment": str(env), "python": "3.12.3", "steps": []}
    text = report.render_setup_human(setup, data)
    headings = [line for line in text.splitlines() if line and not line.startswith(" ")]
    headings = [line for line in headings if not line.startswith("-")]
    assert headings == list(report.HEADINGS)
    count = len(data["core_packages"])
    assert f"- Private environment — {status} (~/.local/share/probematrix-epb/envs/" in text
    assert f"- Core packages — installed ({count} of {count})" in text
    assert text.endswith(
        "What to do next\n- Set up a case folder: ask the agent to set up an evidence pack "
        "case folder here."
    )


# --- the Codex copy layout ----------------------------------------------------------------

_CODEX_SCRIPT = """
import json, subprocess, sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
from epb import launcher
from epb.cli import Context
from epb.doctor import setup

calls = []

def run(argv, **kwargs):
    argv = [str(part) for part in argv]
    calls.append(argv)
    stdout = ""
    if argv[1:3] == ["-m", "venv"]:
        python = launcher.env_python(Path(argv[3]))
        python.parent.mkdir(parents=True, exist_ok=True)
        python.write_text("placeholder", encoding="utf-8")
    elif "from importlib import metadata" in " ".join(argv):
        names = argv[argv.index("-c") + 2:]
        stdout = json.dumps({name: "999.0" for name in names})
    return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr=None)

ctx = Context(case=Path(sys.argv[2]), json=True, verbose=False, wait=60.0)
result = setup.run_setup(ctx, run=run)
core = [argv for argv in calls if "--uploaded-prior-to" in argv][0]
print(json.dumps({
    "located": str(launcher.locate_plugin_file("requirements.txt")),
    "core_requirements": core[core.index("-r") + 1],
    "status": result.data["setup"]["status"],
    "current": launcher.marker_is_current(launcher.env_dir()),
}))
"""


def test_setup_from_the_codex_copy_uses_plugin_files(tmp_path, case_dir):
    dest = tmp_path / "skills"
    installed = subprocess.run(
        [sys.executable, str(INSTALL_CODEX), "--dest", str(dest)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    assert installed.returncode == 0, installed.stderr
    copied_scripts = dest / "evidence-pack" / "scripts"
    completed = subprocess.run(
        [sys.executable, "-I", "-c", _CODEX_SCRIPT, str(copied_scripts), str(case_dir)],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=dict(os.environ),
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    found = json.loads(completed.stdout)
    expected = str(dest / "evidence-pack" / "plugin-files" / "requirements.txt")
    assert found["located"] == expected
    assert found["core_requirements"] == expected
    assert found["status"] == "created"
    assert found["current"] is True


# --- static guards (T-01-25) --------------------------------------------------------------


def _python_files():
    return sorted(EPB_PACKAGE.rglob("*.py"))


def _string_sequences(tree_):
    for node in ast.walk(tree_):
        if isinstance(node, (ast.List, ast.Tuple)):
            yield [
                element.value
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
                else None
                for element in node.elts
            ]


def test_only_setup_builds_a_pip_command_line():
    builders = set()
    for path in _python_files():
        parsed = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for values in _string_sequences(parsed):
            if any(a == "pip" and b == "install" for a, b in pairwise(values)):
                builders.add(path.relative_to(EPB_PACKAGE).as_posix())
    assert builders == {"doctor/setup.py"}


def test_no_module_runs_sudo_or_a_shell():
    offenders = []
    for path in _python_files():
        name = path.relative_to(EPB_PACKAGE).as_posix()
        parsed = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for values in _string_sequences(parsed):
            if any(value is not None and value.split()[:1] == ["sudo"] for value in values):
                offenders.append(f"{name}: sudo in an argument list")
        for node in ast.walk(parsed):
            if isinstance(node, ast.keyword) and node.arg == "shell":
                offenders.append(f"{name}:{node.value.lineno} shell=")
    assert offenders == []


def test_setup_mentions_sudo_only_in_the_printed_hint():
    parsed = ast.parse((EPB_PACKAGE / "doctor" / "setup.py").read_text(encoding="utf-8"))
    docstring = parsed.body[0].value
    mentions = [
        node.value
        for node in ast.walk(parsed)
        if node is not docstring
        and isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and "sudo" in node.value
    ]
    assert len(mentions) == 1
    assert mentions[0].startswith("On Ubuntu or Debian run: sudo apt install python3-venv ")
