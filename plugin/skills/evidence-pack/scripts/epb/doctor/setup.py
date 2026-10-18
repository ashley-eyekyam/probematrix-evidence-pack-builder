"""``epb doctor --setup``: build the private Python environment (PKG-06, PKG-08, D-03, D-18).

Setup is the only part of the plugin that downloads anything, and it runs only when the user
asks for it. The steps, in order:

1. create a virtual environment at the fixed per-user path for this plugin version (D-03);
2. upgrade pip inside it to 26.1 or later (the bundled pip rejects the cutoff flag);
3. install ``requirements.txt`` with ``--uploaded-prior-to P14D``, the two-week rule (D-18);
4. install each reviewed pin from ``security-exceptions.json`` as a separate second step;
5. verify that the core packages import and meet their minimum versions.

Only then is the marker ``epb-env.json`` written, so the launcher trusts the environment only
after a complete, verified setup. An interrupted or failed setup leaves no current marker and
the next run rebuilds the environment from scratch.

Safety (T-01-24 to T-01-27): every program runs from an argv list with a timeout, never
through a shell. Packages go only into the private environment, through its own interpreter;
nothing is installed into the system Python and nothing runs with elevated rights (commands
such as ``sudo apt install python3-venv`` are only printed for the user). The only folder
setup ever removes is ``<data root>/envs/<this plugin version>``.

Standard library only: setup runs in whatever Python launched ``epb.py``.
"""

import json
import re
import shutil
import subprocess
import sys

from epb import launcher
from epb.cli import Result
from epb.doctor import probes
from epb.doctor.report import command_text, render_setup_human
from epb.errors import EpbError

SETUP_STEPS = (
    "create environment",
    "upgrade pip",
    "install core packages",
    "install reviewed security pins",
    "verify",
)
CREATE, UPGRADE, CORE, PINS, VERIFY = SETUP_STEPS

VENV_TIMEOUT = 300
PIP_TIMEOUT = 900
TAIL_LINES = 20
PIP_MINIMUM = "pip>=26.1"
CUTOFF = probes.CUTOFF
EXCEPTIONS_FILE = "security-exceptions.json"
VERIFY_IMPORTS = "import yaml, jsonschema, openpyxl, defusedxml"
# pip must never stop to ask a question or nag about its own version.
PIP_QUIET = ("--disable-pip-version-check", "--no-input")

# A reviewed pin becomes one "name==version" argument. Both parts are checked so a damaged
# exceptions file can never smuggle an option (such as --index-url) into the pip command.
_PACKAGE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")
_VERSION = re.compile(r"[0-9][A-Za-z0-9.+!_-]*")

BLOCKED_HINT = (
    "If your AI app blocks downloads or writing outside the project, open a terminal and run: "
)


# --- helpers ------------------------------------------------------------------------------


def terminal_command():
    """The setup command a person can paste into a terminal."""
    return command_text([sys.executable, str(launcher.epb_script()), "doctor", "--setup"])


def _python_text():
    return ".".join(str(part) for part in sys.version_info[:3])


def _tail(output):
    return (output or "").splitlines()[-TAIL_LINES:]


def _text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _call(run, argv, timeout):
    """Run one program; return ``(succeeded, combined output)``. Never raises."""
    try:
        completed = run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return False, _text(exc.output) + f"\nThe step did not finish within {timeout} seconds."
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return False, f"The program {argv[0]} could not be run ({type(exc).__name__}: {exc})."
    return completed.returncode == 0, _text(completed.stdout)


def _failed(step, output, env):
    """The SETUP_FAILED error for one step, with the end of its output."""
    return EpbError(
        "SETUP_FAILED",
        f'First-time setup stopped at the step "{step}". The private environment is not '
        "ready yet; run setup again to retry.",
        hint=BLOCKED_HINT + terminal_command(),
        data={
            "setup": {"status": "failed", "step": step, "environment": str(env)},
            "output_tail": _tail(output),
        },
    )


def _step(run, step, argv, timeout, env):
    succeeded, output = _call(run, argv, timeout)
    if not succeeded:
        raise _failed(step, output, env)


# --- plugin files -------------------------------------------------------------------------


def _damaged_exceptions(detail):
    return EpbError(
        "SETUP_FAILED",
        f"The plugin's {EXCEPTIONS_FILE} file is damaged ({detail}).",
        hint="Reinstall the plugin, then run setup again.",
        data={"setup": {"status": "failed", "step": PINS}},
    )


def reviewed_pins():
    """``name==version`` for each reviewed security exception, in file order.

    A missing file means there are no exceptions; a malformed one is an error."""
    path = launcher.locate_plugin_file(EXCEPTIONS_FILE)
    if path is None:
        return []
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise _damaged_exceptions("it is not readable JSON") from None
    entries = document.get("exceptions") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        raise _damaged_exceptions('it has no "exceptions" list')
    pins = []
    for number, entry in enumerate(entries, start=1):
        package = entry.get("package") if isinstance(entry, dict) else None
        version = entry.get("version") if isinstance(entry, dict) else None
        if not (
            isinstance(package, str)
            and isinstance(version, str)
            and _PACKAGE.fullmatch(package)
            and _VERSION.fullmatch(version)
        ):
            raise _damaged_exceptions(f"entry {number} has no valid package and version")
        pins.append(f"{package}=={version}")
    return pins


# --- the environment ----------------------------------------------------------------------


def _verify(run, env_python, requirements):
    """None when the core packages import and meet their minimums, else what is wrong."""
    succeeded, output = _call(run, [str(env_python), "-I", "-c", VERIFY_IMPORTS], PIP_TIMEOUT)
    if not succeeded:
        return output or "The core packages could not be imported."
    installed = probes.env_packages(env_python, [name for name, _ in requirements], run=run)
    missing = [
        name + spec for name, spec in requirements if not probes._meets(installed.get(name), spec)
    ]
    if missing:
        return "Missing or too old in the private environment: " + ", ".join(missing)
    return None


def _remove(env):
    """Remove exactly ``env``: the marker first, so a half-removed folder is never trusted."""
    if env.is_symlink() or env.is_file():
        env.unlink()
        return
    try:
        launcher.marker_path(env).unlink()
    except FileNotFoundError:
        pass
    shutil.rmtree(env)


def _create(run, env):
    succeeded, output = _call(run, [sys.executable, "-m", "venv", str(env)], VENV_TIMEOUT)
    if succeeded:
        return
    if "ensurepip" in output:
        minor = sys.version_info[1]
        raise EpbError(
            "VENV_UNAVAILABLE",
            "Python's venv module is missing on this computer.",
            hint=(
                "On Ubuntu or Debian run: sudo apt install python3-venv "
                f"(or python3.{minor}-venv), then run setup again."
            ),
            data={
                "setup": {"status": "failed", "step": CREATE, "environment": str(env)},
                "output_tail": _tail(output),
            },
        )
    raise _failed(CREATE, output, env)


def run_setup(ctx, *, run=subprocess.run):
    """Build (or confirm) the private environment for this plugin version and return the
    doctor report with a ``setup`` section. ``run`` is a patch point for tests."""
    requirements_file = launcher.locate_plugin_file("requirements.txt")
    if requirements_file is None:
        raise EpbError(
            "SETUP_FAILED",
            "The plugin's files are incomplete; reinstall the plugin.",
            hint="Reinstall the plugin, then run setup again.",
            data={"setup": {"status": "failed", "step": None}},
        )
    pins = reviewed_pins()
    env = launcher.env_dir()
    if env.parent != launcher.data_root() / "envs":
        raise EpbError(
            "INTERNAL_ERROR",
            "The private environment path is not inside the plugin's data folder.",
            hint="Report this error code to the plugin maintainer.",
        )
    env_python = launcher.env_python(env)
    requirements = probes.core_requirements()

    if launcher.marker_is_current(env) and _verify(run, env_python, requirements) is None:
        steps = [{"name": name, "status": "skipped"} for name in SETUP_STEPS[:-1]]
        steps.append({"name": VERIFY, "status": "done"})
        ctx.warn(
            "ALREADY_SET_UP",
            "The private environment was already set up and working; nothing was changed.",
        )
        python = (launcher.read_marker(env) or {}).get("python") or _python_text()
        return _finish(ctx, "ready", env, python, steps)

    status = "created"
    if env.is_symlink() or env.exists():
        try:
            _remove(env)
        except OSError as exc:
            raise _failed(
                CREATE,
                f"The old private environment could not be removed ({type(exc).__name__}).",
                env,
            ) from None
        status = "rebuilt"
    env.parent.mkdir(parents=True, exist_ok=True)

    steps = []
    _create(run, env)
    steps.append({"name": CREATE, "status": "done"})

    pip = [str(env_python), "-m", "pip", "install", *PIP_QUIET]
    _step(run, UPGRADE, [*pip, "--upgrade", PIP_MINIMUM], PIP_TIMEOUT, env)
    steps.append({"name": UPGRADE, "status": "done"})

    core = [*pip, "--uploaded-prior-to", CUTOFF, "-r", str(requirements_file)]
    _step(run, CORE, core, PIP_TIMEOUT, env)
    steps.append({"name": CORE, "status": "done"})

    for pin in pins:  # D-18: reviewed exceptions newer than the cutoff, one at a time
        _step(run, PINS, [*pip, pin], PIP_TIMEOUT, env)
    steps.append({"name": PINS, "status": "done" if pins else "skipped"})

    problem = _verify(run, env_python, requirements)
    if problem is not None:
        raise _failed(VERIFY, problem, env)
    steps.append({"name": VERIFY, "status": "done"})

    python = _python_text()
    launcher.write_marker(env, launcher.marker_record(python))
    return _finish(ctx, status, env, python, steps)


def _finish(ctx, status, env, python, steps):
    report = probes.collect(ctx.case)
    setup = {"status": status, "environment": str(env), "python": python, "steps": steps}
    return Result(
        data={"setup": setup, **report},
        next=[],
        message=render_setup_human(setup, report, verbose=ctx.verbose),
    )
