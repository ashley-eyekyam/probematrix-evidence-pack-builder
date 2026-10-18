"""Stdlib-only launcher: decides where a command runs before anything else is imported.

``scripts/epb.py`` calls ``main(argv)``. The launcher:

1. refuses to run on Python older than ``MIN_PYTHON`` (``PYTHON_TOO_OLD``, exit 3), except
   for ``doctor --setup``, which re-runs itself under a newer interpreter it finds;
2. runs ``doctor`` (the bootstrap command) in the current interpreter, so it works before
   setup;
3. runs every other command inside the private environment at the fixed per-OS path (D-03),
   re-running the same arguments under that environment's interpreter, or exits 3
   ``ENV_NOT_SET_UP`` when the environment is missing or out of date.

Keep this module parseable and importable by old Python 3 interpreters (3.6 syntax and APIs:
no annotations, no walrus, no match, no ``text=``/``capture_output=`` in subprocess calls),
so that an outdated interpreter still reaches the friendly version message. It must import
only the standard library and ``epb/__init__.py``.
"""

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from epb import __version__

MIN_PYTHON = (3, 11)
BOOTSTRAP_COMMANDS = ("doctor",)
PLUGIN_FILES_DIR = "plugin-files"
DATA_FOLDER = "probematrix-epb"
MARKER_NAME = "epb-env.json"
MARKER_SCHEMA_VERSION = 1
PROBE_TIMEOUT = 10

# Global options that take a value; their value is never the command token.
_VALUE_OPTIONS = ("--case", "--wait")
_POSIX_CANDIDATES = ("python3.14", "python3.13", "python3.12", "python3.11", "python3", "python")
_WINDOWS_PY_FLAGS = ("-3.14", "-3.13", "-3.12", "-3.11", "-3")
_PROBE_CODE = "import sys; print('%d.%d.%d' % sys.version_info[:3])"


# --- command line -------------------------------------------------------------------------


def command_token(argv):
    """Return the command name in ``argv``: the first argument that is not an option or an
    option's value. Returns None when there is no command."""
    skip_next = False
    for arg in argv:
        if skip_next:
            skip_next = False
            continue
        if arg == "--":
            return None
        if arg in _VALUE_OPTIONS:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        return arg
    return None


def route(argv):
    """``"bootstrap"`` when the command runs in the current interpreter, else ``"env"``."""
    if command_token(argv) in BOOTSTRAP_COMMANDS:
        return "bootstrap"
    return "env"


# --- paths --------------------------------------------------------------------------------


def data_root():
    """The fixed per-user data folder (D-03). ``XDG_DATA_HOME`` is deliberately ignored so
    the manual can quote one path per OS (research Q6)."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / DATA_FOLDER
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / DATA_FOLDER
    return Path.home() / ".local" / "share" / DATA_FOLDER


def env_dir(version=None):
    """The private environment folder for one plugin version."""
    return data_root() / "envs" / (version or __version__)


def env_python(env):
    """The interpreter inside a private environment."""
    env = Path(env)
    if sys.platform == "win32":
        return env / "Scripts" / "python.exe"
    return env / "bin" / "python"


def scripts_dir():
    """The folder holding ``epb.py`` (and the ``epb`` package)."""
    return Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def epb_script():
    """The absolute path of ``epb.py``."""
    return scripts_dir() / "epb.py"


def locate_plugin_file(name):
    """Find a file that ships at the plugin root, such as ``requirements.txt``.

    The Codex copy layout (``<skill>/plugin-files/<name>``) is checked first, so a stray file
    beside a copied skill folder is never used; then the normal plugin layout
    (scripts -> evidence-pack -> skills -> plugin). Returns None when neither exists.
    """
    scripts = scripts_dir()
    for candidate in (
        scripts.parent / PLUGIN_FILES_DIR / name,
        scripts.parent.parent.parent / name,
    ):
        if candidate.is_file():
            return candidate
    return None


# --- marker -------------------------------------------------------------------------------


def marker_path(env):
    return Path(env) / MARKER_NAME


def _requirements_sha256():
    path = locate_plugin_file("requirements.txt")
    if path is None:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def marker_record(python_version):
    """The marker written after a successful setup. ``python_version`` is a version tuple
    or a ``"3.x.y"`` string."""
    if isinstance(python_version, str):
        python = python_version
    else:
        python = ".".join(str(part) for part in tuple(python_version)[:3])
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "schema_version": MARKER_SCHEMA_VERSION,
        "plugin_version": __version__,
        "requirements_sha256": _requirements_sha256(),
        "python": python,
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_marker(env, record):
    """Write the marker atomically: a temp file in the same folder, then ``os.replace``."""
    target = marker_path(env)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=".epb-env-", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, str(target))
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def read_marker(env):
    """The marker as a dict, or None when it is missing or unreadable."""
    try:
        with open(str(marker_path(env)), encoding="utf-8") as stream:
            record = json.load(stream)
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict):
        return None
    return record


def marker_is_current(env):
    """True only when the env interpreter exists and the marker matches this plugin version
    and this requirements file."""
    if not env_python(env).exists():
        return False
    record = read_marker(env)
    if record is None:
        return False
    return (
        record.get("plugin_version") == __version__
        and record.get("requirements_sha256") == _requirements_sha256()
    )


# --- interpreters -------------------------------------------------------------------------


def python_version():
    """The running interpreter's version (a patch point for tests)."""
    return tuple(sys.version_info[:3])


def _probe(prefix):
    """The version tuple an interpreter reports, or None if it cannot be run."""
    try:
        completed = subprocess.run(
            list(prefix) + ["-c", _PROBE_CODE],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
            timeout=PROBE_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if completed.returncode != 0:
        return None
    try:
        return tuple(int(part) for part in completed.stdout.strip().split("."))
    except ValueError:
        return None


def _candidates():
    if sys.platform == "win32":
        py = shutil.which("py")
        if py is None:
            return []
        return [[py, flag] for flag in _WINDOWS_PY_FLAGS]
    found = []
    for name in _POSIX_CANDIDATES:
        path = shutil.which(name)
        if path is not None:
            found.append([path])
    return found


def find_python():
    """The argv prefix of the first interpreter that reports ``MIN_PYTHON`` or newer, or
    None. Candidates are fixed names only; one that fails its probe (such as a Windows Store
    alias stub) is skipped."""
    for prefix in _candidates():
        version = _probe(prefix)
        if version is not None and version >= MIN_PYTHON:
            return prefix
    return None


# --- output -------------------------------------------------------------------------------


def _emit_error(code, message, hint, command, json_mode, next_steps, exit_code):
    """Print one error the same way ``epb.cli`` does: an envelope under --json, else plain
    language on stderr. Returns the exit code."""
    if json_mode:
        envelope = {
            "ok": False,
            "command": command,
            "exit_code": exit_code,
            "epb_version": __version__,
            "data": {},
            "warnings": [],
            "errors": [{"code": code, "message": message, "hint": hint, "pointer": None}],
            "next": list(next_steps),
        }
        sys.stdout.write(json.dumps(envelope, ensure_ascii=False) + "\n")
        sys.stdout.flush()
    else:
        sys.stderr.write("Error: " + message + "\n")
        if hint:
            sys.stderr.write("What to do: " + hint + "\n")
        sys.stderr.flush()
    return exit_code


def _version_text(version):
    return ".".join(str(part) for part in version)


def _too_old(command, json_mode, found_none):
    needed = _version_text(MIN_PYTHON)
    current = _version_text(python_version())
    if found_none:
        message = (
            "No Python %s or newer was found on this computer. The Python running this "
            "command is version %s." % (needed, current)
        )
    else:
        message = "This Python is version %s, but the plugin needs Python %s or newer." % (
            current,
            needed,
        )
    hint = (
        'Install Python %s or newer as described in the chapter "Install Python" of the '
        "user manual, then run doctor --setup." % needed
    )
    return _emit_error("PYTHON_TOO_OLD", message, hint, command, json_mode, ["doctor --setup"], 3)


def _run_cli(argv):
    from epb import cli

    return cli.main(argv)


def _in_env():
    if os.environ.get("EPB_IN_ENV") == "1":
        return True
    try:
        return Path(sys.prefix).resolve() == env_dir().resolve()
    except OSError:
        return False


# --- entry --------------------------------------------------------------------------------


def main(argv):
    argv = list(argv)
    json_mode = "--json" in argv
    command = command_token(argv)

    # 1. Version gate. Only doctor --setup may continue, by re-running under a newer Python.
    if python_version() < MIN_PYTHON:
        if command == "doctor" and "--setup" in argv:
            prefix = find_python()
            if prefix is None:
                return _too_old(command, json_mode, found_none=True)
            return subprocess.run(list(prefix) + [str(epb_script())] + argv).returncode
        return _too_old(command, json_mode, found_none=False)

    # 2. Bootstrap commands, or already inside the private environment.
    if route(argv) == "bootstrap" or _in_env():
        return _run_cli(argv)

    # 3. The private environment must exist and match this plugin version.
    env = env_dir()
    if not marker_is_current(env):
        if read_marker(env) is not None:
            message = "The private environment is out of date for this plugin version."
        else:
            message = "First-time setup has not been run on this computer yet."
        hint = "Run: %s %s doctor --setup" % (sys.executable, epb_script())
        return _emit_error(
            "ENV_NOT_SET_UP", message, hint, command, json_mode, ["doctor --setup"], 3
        )

    # 4. Re-run the same arguments under the environment's interpreter. subprocess (not
    # os.execv) keeps exit codes and stdio uniform on Windows.
    child_env = dict(os.environ, EPB_IN_ENV="1")
    return subprocess.run(
        [str(env_python(env)), str(epb_script())] + argv, env=child_env
    ).returncode
