"""The stdlib-only launcher: version gate, interpreter discovery, env path, marker, re-exec
(PKG-06, D-03, A8)."""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from epb import __version__, launcher
from epbtest.envkit import make_fake_env

SCRIPTS = Path(launcher.__file__).resolve().parent.parent
OLD_SYNTAX_FILES = [
    SCRIPTS / "epb.py",
    SCRIPTS / "epb" / "__init__.py",
    SCRIPTS / "epb" / "launcher.py",
]
posix_only = pytest.mark.skipif(os.name == "nt", reason="fake interpreters are shell scripts")


# --- data_root and env paths (D-03, research Q6) ---------------------------------------


def test_data_root_linux_ignores_xdg(monkeypatch, home_dir):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(home_dir / "xdg-elsewhere"))
    assert launcher.data_root() == home_dir / ".local" / "share" / "probematrix-epb"


def test_data_root_macos(monkeypatch, home_dir):
    monkeypatch.setattr(sys, "platform", "darwin")
    expected = home_dir / "Library" / "Application Support" / "probematrix-epb"
    assert launcher.data_root() == expected


def test_data_root_windows_localappdata(monkeypatch, home_dir):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(home_dir / "LAD"))
    assert launcher.data_root() == home_dir / "LAD" / "probematrix-epb"


def test_data_root_windows_fallback(monkeypatch, home_dir):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    assert launcher.data_root() == home_dir / "AppData" / "Local" / "probematrix-epb"


def test_env_dir_is_versioned_under_fake_home(monkeypatch, home_dir):
    monkeypatch.setattr(sys, "platform", "linux")
    root = home_dir / ".local" / "share" / "probematrix-epb"
    assert launcher.env_dir() == root / "envs" / __version__
    assert launcher.env_dir("9.9.9") == root / "envs" / "9.9.9"


def test_env_python_per_os(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    assert launcher.env_python(tmp_path) == tmp_path / "Scripts" / "python.exe"
    monkeypatch.setattr(sys, "platform", "linux")
    assert launcher.env_python(tmp_path) == tmp_path / "bin" / "python"


# --- marker -----------------------------------------------------------------------------


def _bare_env(path):
    """An env folder with a placeholder interpreter file and a current marker."""
    python = launcher.env_python(path)
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_bytes(b"")
    launcher.write_marker(path, launcher.marker_record((3, 12, 0)))
    return path


def test_marker_round_trip(tmp_path):
    env = _bare_env(tmp_path / "env")
    record = launcher.read_marker(env)
    assert record["schema_version"] == 1
    assert record["plugin_version"] == __version__
    assert record["python"] == "3.12.0"
    assert len(record["requirements_sha256"]) == 64
    assert record["created_at"].endswith("Z")
    assert launcher.marker_path(env) == env / "epb-env.json"
    assert launcher.marker_is_current(env)


def test_marker_unreadable_is_none(tmp_path):
    env = tmp_path / "env"
    env.mkdir()
    launcher.marker_path(env).write_text("{not json", encoding="utf-8")
    assert launcher.read_marker(env) is None
    assert launcher.marker_is_current(env) is False


@pytest.mark.parametrize("key", ["plugin_version", "requirements_sha256"])
def test_stale_marker_is_env_not_set_up(key, capsys):
    env = _bare_env(launcher.env_dir())
    record = launcher.read_marker(env)
    record[key] = "stale"
    launcher.write_marker(env, record)
    assert launcher.marker_is_current(env) is False
    exit_code = launcher.main(["--json", "status"])
    envelope = json.loads(capsys.readouterr().out)
    assert exit_code == 3
    assert envelope["errors"][0]["code"] == "ENV_NOT_SET_UP"
    assert "out of date" in envelope["errors"][0]["message"]
    assert envelope["next"] == ["doctor --setup"]


def test_missing_env_message(capsys):
    exit_code = launcher.main(["--json", "status"])
    envelope = json.loads(capsys.readouterr().out)
    assert exit_code == 3
    assert envelope["errors"][0]["code"] == "ENV_NOT_SET_UP"
    assert "has not been run" in envelope["errors"][0]["message"]
    assert "doctor --setup" in envelope["errors"][0]["hint"]


# --- re-exec ----------------------------------------------------------------------------


def test_reexec_passes_through_exit_code_and_output(run_epb, case_dir):
    make_fake_env()
    proc = run_epb(["--json", "frobnicate"], cwd=case_dir, in_env=False)
    assert proc.returncode == 2, proc.stderr
    envelope = json.loads(proc.stdout)
    assert envelope["errors"][0]["code"] == "USAGE"
    assert envelope["exit_code"] == 2


def test_running_inside_env_prefix_goes_straight_to_cli(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "env_dir", lambda version=None: Path(sys.prefix))
    exit_code = launcher.main(["--json", "frobnicate"])
    envelope = json.loads(capsys.readouterr().out)
    assert exit_code == 2
    assert envelope["errors"][0]["code"] == "USAGE"


# --- version gate -----------------------------------------------------------------------


def test_python_too_old_for_normal_command(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "python_version", lambda: (3, 9, 0))
    exit_code = launcher.main(["--json", "status"])
    envelope = json.loads(capsys.readouterr().out)
    assert exit_code == 3
    assert envelope["errors"][0]["code"] == "PYTHON_TOO_OLD"
    assert "3.9.0" in envelope["errors"][0]["message"]
    assert "Install Python" in envelope["errors"][0]["hint"]


def test_python_too_old_setup_uses_found_interpreter(monkeypatch, capfd):
    monkeypatch.setattr(launcher, "python_version", lambda: (3, 9, 0))
    probe = "import json, sys; print(json.dumps(sys.argv[1:])); sys.exit(7)"
    monkeypatch.setattr(launcher, "find_python", lambda: [sys.executable, "-c", probe])
    exit_code = launcher.main(["doctor", "--setup"])
    assert exit_code == 7
    child_argv = json.loads(capfd.readouterr().out)
    assert child_argv == [str(launcher.epb_script()), "doctor", "--setup"]


def test_python_too_old_setup_without_interpreter(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "python_version", lambda: (3, 9, 0))
    monkeypatch.setattr(launcher, "find_python", lambda: None)
    exit_code = launcher.main(["--json", "doctor", "--setup"])
    envelope = json.loads(capsys.readouterr().out)
    assert exit_code == 3
    assert envelope["errors"][0]["code"] == "PYTHON_TOO_OLD"


# --- interpreter discovery --------------------------------------------------------------


def _fake_interpreter(folder, name, body):
    path = folder / name
    path.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    path.chmod(0o755)
    return str(path)


@posix_only
def test_find_python_posix_order(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    found = {
        "python3.13": _fake_interpreter(tmp_path, "python3.13", "echo 3.10.2"),
        "python3.12": _fake_interpreter(tmp_path, "python3.12", "exit 1"),
        "python3": _fake_interpreter(tmp_path, "python3", "echo 3.12.1"),
        "python": _fake_interpreter(tmp_path, "python", "echo 3.13.0"),
    }
    monkeypatch.setattr(launcher.shutil, "which", lambda name: found.get(name))
    assert launcher.find_python() == [found["python3"]]


@posix_only
def test_find_python_windows_py_launcher(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "win32")
    body = 'case "$1" in -3.12) echo 3.12.4 ;; -3) echo 3.13.1 ;; *) exit 1 ;; esac'
    py = _fake_interpreter(tmp_path, "py", body)
    monkeypatch.setattr(launcher.shutil, "which", lambda name: py if name == "py" else None)
    assert launcher.find_python() == [py, "-3.12"]


@posix_only
def test_find_python_none(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "platform", "linux")
    old = _fake_interpreter(tmp_path, "python3", "echo 3.9.18")
    monkeypatch.setattr(launcher.shutil, "which", lambda name: old if name == "python3" else None)
    assert launcher.find_python() is None


# --- routing and plugin files -----------------------------------------------------------


def test_route():
    assert launcher.route(["--case", "x", "doctor"]) == "bootstrap"
    assert launcher.route(["doctor", "--setup"]) == "bootstrap"
    assert launcher.route(["scan"]) == "env"
    assert launcher.route(["--wait", "5", "scan"]) == "env"


def test_locate_plugin_file(monkeypatch, tmp_path):
    scripts = tmp_path / "plugin" / "skills" / "evidence-pack" / "scripts"
    scripts.mkdir(parents=True)
    monkeypatch.setattr(launcher, "scripts_dir", lambda: scripts)
    assert launcher.locate_plugin_file("requirements.txt") is None
    plugin_copy = tmp_path / "plugin" / "requirements.txt"
    plugin_copy.write_text("x\n", encoding="utf-8")
    assert launcher.locate_plugin_file("requirements.txt") == plugin_copy
    codex_copy = scripts.parent / launcher.PLUGIN_FILES_DIR / "requirements.txt"
    codex_copy.parent.mkdir()
    codex_copy.write_text("y\n", encoding="utf-8")
    assert launcher.locate_plugin_file("requirements.txt") == codex_copy


def test_real_layout_finds_requirements():
    found = launcher.locate_plugin_file("requirements.txt")
    assert found == SCRIPTS.parent.parent.parent / "requirements.txt"
    assert launcher.epb_script() == SCRIPTS / "epb.py"


# --- old-syntax guard (PKG-06, A8) ------------------------------------------------------


@pytest.mark.parametrize("path", OLD_SYNTAX_FILES, ids=lambda p: p.name)
def test_parses_as_python_36(path):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 6))


# --- bootstrap guard: stdlib only before setup (PKG-06, research anti-patterns) ----------

REQUIREMENTS = SCRIPTS.parent.parent.parent / "requirements.txt"

# Every distribution in plugin/requirements.txt, mapped to the top-level import names it and
# its dependencies install. A new requirement must be added here, or the test below fails.
DIST_IMPORT_NAMES = {
    "jsonschema": ["jsonschema", "jsonschema_specifications", "referencing", "rpds", "attrs"],
    "PyYAML": ["yaml", "_yaml"],
    "openpyxl": ["openpyxl", "et_xmlfile"],
    "defusedxml": ["defusedxml"],
    "lxml": ["lxml"],
    "charset-normalizer": ["charset_normalizer"],
    "pdfplumber": ["pdfplumber", "pdfminer", "pypdfium2", "pypdfium2_raw"],
    "pypdf": ["pypdf"],
    "Pillow": ["PIL"],
    "rapidfuzz": ["rapidfuzz"],
    "python-docx": ["docx"],
    "python-pptx": ["pptx", "xlsxwriter"],
    "beautifulsoup4": ["bs4", "soupsieve"],
    "markdownify": ["markdownify", "six"],
    "tzdata": ["tzdata"],
}

_BLOCKING_SCRIPT = """
import sys

BLOCKED = set(sys.argv[2].split(","))


class Blocker:
    def find_spec(self, name, path=None, target=None):
        if name.partition(".")[0] in BLOCKED:
            raise ModuleNotFoundError("blocked for this test: " + name, name=name)
        return None


sys.meta_path.insert(0, Blocker())
sys.path.insert(0, sys.argv[1])
import epb.launcher
import epb.errors
import epb.cli

epb.cli.build_parser()
leaked = sorted(n for n in sys.modules if n.partition(".")[0] in BLOCKED)
if leaked:
    print("third-party modules imported: " + ", ".join(leaked))
    sys.exit(1)
"""


def _requirement_names():
    names = []
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.append(re.split(r"[\s;<>=!~\[]", line, maxsplit=1)[0])
    return names


def test_import_map_covers_requirements():
    assert sorted(_requirement_names()) == sorted(DIST_IMPORT_NAMES)


def test_bootstrap_imports_stdlib_only():
    blocked = sorted({name for names in DIST_IMPORT_NAMES.values() for name in names})
    proc = subprocess.run(
        [sys.executable, "-I", "-c", _BLOCKING_SCRIPT, str(SCRIPTS), ",".join(blocked)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def _epb_python_files():
    return sorted((SCRIPTS / "epb").rglob("*.py"))


def test_never_prompts():
    offenders = []
    for path in _epb_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "input":
                    offenders.append(f"{path.name}:{node.lineno} input()")
            if isinstance(node, ast.Attribute) and node.attr == "stdin":
                if isinstance(node.value, ast.Name) and node.value.id == "sys":
                    offenders.append(f"{path.name}:{node.lineno} sys.stdin")
    assert offenders == []
