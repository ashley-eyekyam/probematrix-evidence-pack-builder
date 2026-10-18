"""Doctor probes: Python, the private environment, its packages and the optional tools.

``collect()`` assembles the full machine report that ``epb doctor --json`` returns. Every
list in it follows a fixed order (registry order for tools and extras, file order for the core
requirements), so two runs on one machine produce identical output.

Programs are only ever run from an argv list, never through a shell, with a timeout, and a
version is read from their output with a fixed regular expression (T-01-18).

Standard library only: doctor runs before first-time setup, in whatever Python launched
``epb.py``.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from epb import __version__, launcher
from epb.doctor import tools

TOOL_TIMEOUT = 10
PACKAGE_TIMEOUT = 30
CUTOFF = "P14D"

# Prints {name: installed version or null} for each distribution name in argv, as JSON.
_PACKAGE_SCRIPT = """
import json, sys
from importlib import metadata
found = {}
for name in sys.argv[1:]:
    try:
        found[name] = metadata.version(name)
    except metadata.PackageNotFoundError:
        found[name] = None
print(json.dumps(found))
"""

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_WINDOWS_ONLY_MARKER = re.compile(r"""^sys_platform\s*==\s*["']win32["']$""")


# --- tools --------------------------------------------------------------------------------


def _locate(spec, which, platform):
    """The first name found on PATH, else an existing fallback path for this OS."""
    for name in spec.names:
        path = which(name)
        if path:
            return name, str(path)
    for candidate in spec.extra_paths.get(tools.os_id(platform), ()):
        if Path(candidate).is_file():
            return Path(candidate).name, candidate
    return None, None


def _read_version(spec, path, run):
    try:
        completed = run(
            [path, *spec.version_args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TOOL_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    match = re.search(spec.version_regex, output)
    return match.group(1) if match else None


def probe_tool(spec, *, which=shutil.which, run=subprocess.run, platform=sys.platform):
    """Report one tool: whether it was found, where, under which name and at what version.

    A tool whose version probe fails or prints something unexpected is still reported as
    found, with version None."""
    name, path = _locate(spec, which, platform)
    version = _read_version(spec, path, run) if path else None
    return {
        "id": spec.id,
        "label": spec.label,
        "found": path is not None,
        "name": name,
        "path": path,
        "version": version,
        "enables": spec.enables,
        "in_use": spec.in_use,
        "install": dict(spec.install),
    }


# --- core requirements and packages -------------------------------------------------------


def core_requirements(*, platform=sys.platform):
    """``(name, spec)`` pairs from the plugin's ``requirements.txt``, in file order.

    A line whose only environment marker is ``sys_platform == "win32"`` is skipped on other
    platforms; any other marker is kept, because the standard library cannot evaluate it."""
    path = launcher.locate_plugin_file("requirements.txt")
    if path is None:
        return []
    pairs = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        requirement, _, marker = line.partition(";")
        marker = marker.strip()
        if marker and _WINDOWS_ONLY_MARKER.match(marker) and platform != "win32":
            continue
        requirement = requirement.strip()
        match = _NAME.match(requirement)
        if match is None:
            continue
        pairs.append((match.group(0), requirement[match.end() :].strip()))
    return pairs


def env_packages(env_python, names, *, run=subprocess.run):
    """The installed version of each distribution in ``names`` inside the environment whose
    interpreter is ``env_python`` (None when missing). If the interpreter cannot be run,
    every package is reported missing. ``run`` is a patch point for tests."""
    names = list(names)
    missing = {name: None for name in names}
    try:
        completed = run(
            [str(env_python), "-I", "-c", _PACKAGE_SCRIPT, *names],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PACKAGE_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return missing
    if completed.returncode != 0:
        return missing
    try:
        found = json.loads(completed.stdout)
    except ValueError:
        return missing
    if not isinstance(found, dict):
        return missing
    return {name: found.get(name) if isinstance(found.get(name), str) else None for name in names}


def _numeric(version):
    parts = []
    for part in version.split("."):
        match = re.match(r"\d+", part)
        if match is None:
            break
        parts.append(int(match.group(0)))
    return tuple(parts)


def _meets(installed, spec):
    """True when ``installed`` satisfies a plain ``>=X.Y`` minimum. Anything the standard
    library cannot compare is accepted, because pip already resolved it."""
    if installed is None:
        return False
    match = re.fullmatch(r">=\s*([0-9][0-9.]*)", spec or "")
    if match is None:
        return True
    have, need = _numeric(installed), _numeric(match.group(1))
    if not have or not need:
        return True
    return have >= need


# --- environment --------------------------------------------------------------------------


def probe_environment():
    """The private environment for this plugin version: where it is, whether it exists and
    is current, how to launch the CLI from it, and which other versions sit beside it."""
    env = launcher.env_dir()
    env_python = launcher.env_python(env)
    current = launcher.marker_is_current(env)
    envs_root = launcher.data_root() / "envs"
    other_versions = []
    if envs_root.is_dir():
        other_versions = sorted(
            entry.name
            for entry in envs_root.iterdir()
            if entry.is_dir() and entry.name != __version__
        )
    return {
        "path": str(env),
        "exists": env.is_dir(),
        "current": current,
        "python": str(env_python),
        "launch": [str(env_python), str(launcher.epb_script())] if current else None,
        "other_versions": other_versions,
    }


# --- the full report ----------------------------------------------------------------------


def _python_report():
    version = tuple(sys.version_info[:3])
    return {
        "version": ".".join(str(part) for part in version),
        "executable": sys.executable,
        "ok": version >= launcher.MIN_PYTHON,
    }


def collect(case_dir, *, which=shutil.which, run=subprocess.run):
    """Build the full doctor report for ``case_dir``. ``folder`` is filled in by the doctor
    command, which knows whether ``case_dir`` is a case folder."""
    environment = probe_environment()
    requirements = core_requirements()
    extra_names = [name for extra in tools.EXTRAS for name in extra.packages]
    if Path(environment["python"]).exists():
        installed = env_packages(
            environment["python"], [name for name, _ in requirements] + extra_names
        )
    else:
        installed = {}
    core_packages = []
    for name, spec in requirements:
        version = installed.get(name)
        core_packages.append(
            {
                "name": name,
                "requirement": name + spec,
                "installed": version,
                "ok": _meets(version, spec),
            }
        )
    extras = []
    for extra in tools.EXTRAS:
        extra_file = launcher.locate_plugin_file(extra.file)
        extras.append(
            {
                "id": extra.id,
                "file": extra.file,
                "packages": list(extra.packages),
                "licence": extra.licence,
                "enables": extra.enables,
                "in_use": extra.in_use,
                "installed": all(installed.get(name) for name in extra.packages),
                "install": "%s -m pip install --uploaded-prior-to %s -r %s"
                % (environment["python"], CUTOFF, extra_file or extra.file),
            }
        )
    python = _python_report()
    return {
        "os": tools.os_id(),
        "home": str(Path.home()),
        "python": python,
        "setup_command": [python["executable"], str(launcher.epb_script()), "doctor", "--setup"],
        "environment": environment,
        "core_packages": core_packages,
        "tools": [
            probe_tool(spec, which=which, run=run, platform=sys.platform) for spec in tools.REGISTRY
        ],
        "extras": extras,
        "folder": {"checked": False, "warnings": []},
    }
