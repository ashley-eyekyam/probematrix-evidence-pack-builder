"""The plain-language doctor checklist (D-17).

``render_human`` turns the report from ``probes.collect`` into exactly three groups, in this
order: ``Ready``, ``Optional, not installed`` and ``What to do next``. It reads the OS and the
home folder from the report, never from the live system, so its output is a pure function of
the report; the user manual quotes it and a golden test compares against it.

``render_setup_human`` renders the same three groups after ``doctor --setup``.

Standard library only.
"""

from epb.doctor import tools

HEADINGS = ("Ready", "Optional, not installed", "What to do next")
LATER = "support arrives in a later version of this plugin"
OS_LABELS = {"linux": "Linux", "macos": "macOS", "windows": "Windows"}
NEXT_CASE_FOLDER = (
    "- Set up a case folder: ask the agent to set up an evidence pack case folder here."
)


def current_os(platform=None):
    """``linux``, ``macos`` or ``windows`` for this computer (or for ``platform``)."""
    return tools.os_id(platform)


def _tilde(path, home):
    """Show a path under the home folder as ``~/...`` (or ``~\\...``)."""
    if not path or not home:
        return path
    home = home.rstrip("/\\")
    if path == home:
        return "~"
    for sep in ("/", "\\"):
        if path.startswith(home + sep):
            return "~" + path[len(home) :]
    return path


def command_text(argv):
    """An argv list as one line a person can copy; parts with spaces are double-quoted."""
    return " ".join(f'"{part}"' if any(c.isspace() for c in part) else part for part in argv)


def _later(in_use):
    return "" if in_use else f" ({LATER})"


def _version_note(version, path, home):
    where = f" at {_tilde(path, home)}" if path else ""
    return f" Version {version or 'unknown'}{where}."


def _install_lines(install, os_id, verbose):
    """The install text that ends an optional line: this OS only, or all three verbosely."""
    if not verbose:
        return [f" Install: {install[os_id]}"], []
    return [""], [f"    {OS_LABELS[key]}: {install[key]}" for key in tools.OS_IDS]


def _python_lines(python, home, verbose):
    if not python["ok"]:
        return []
    major_minor = ".".join(python["version"].split(".")[:2])
    line = f"- Python {major_minor} — ready"
    if verbose:
        line += f" (version {python['version']} at {_tilde(python['executable'], home)})"
    return [line]


def _tool_and_extra_lines(report, environment_current, verbose):
    """The Ready and Optional lines for the optional tools and extras."""
    os_id = report.get("os") or "linux"
    home = report.get("home")
    ready, optional = [], []
    for tool in report["tools"]:
        if tool["found"]:
            line = f"- {tool['label']} — ready: {tool['enables']}{_later(tool['in_use'])}"
            if verbose:
                line += "." + _version_note(tool["version"], tool["path"], home)
            ready.append(line)
        else:
            tail, sub = _install_lines(tool["install"], os_id, verbose)
            optional.append(
                f"- {tool['label']} — would enable {tool['enables']}"
                f"{_later(tool['in_use'])}.{tail[0]}"
            )
            optional.extend(sub)

    for extra in report["extras"]:
        name = f"{extra['id']} extra"
        if extra["installed"]:
            ready.append(f"- {name} — ready: {extra['enables']}{_later(extra.get('in_use'))}")
            continue
        when = "" if environment_current else " after first-time setup"
        line = (
            f"- {name} — would enable {extra['enables']}{_later(extra.get('in_use'))}. "
            f"Licence: {extra['licence']}."
        )
        if verbose:
            line += " Packages: " + ", ".join(extra["packages"]) + "."
            optional.append(f"{line} Install{when}: {extra['install']}")
        else:
            optional.append(f"{line} Install{when}: ask the agent to install the {name}.")
    return ready, optional


def _render(ready, optional, next_steps):
    sections = (
        ready or ["- Nothing yet."],
        optional or ["- Nothing: every optional tool and extra is installed."],
        next_steps,
    )
    blocks = [
        "\n".join([heading, *lines]) for heading, lines in zip(HEADINGS, sections, strict=True)
    ]
    return "\n\n".join(blocks)


def render_human(report, *, verbose=False):
    """The D-17 checklist for ``report``. ``verbose`` adds versions, every OS's install
    command and other environment versions."""
    home = report.get("home")
    python = report["python"]
    ready = _python_lines(python, home, verbose)
    next_steps = []

    environment = report["environment"]
    if environment["current"]:
        ready.append(f"- Private environment — ready ({_tilde(environment['path'], home)})")
    if verbose and environment.get("other_versions"):
        ready.append(
            "    Other private environments found: "
            + ", ".join(environment["other_versions"])
            + ". The user manual explains how to remove them."
        )

    core = report["core_packages"]
    missing_core = [package["name"] for package in core if not package["ok"]]
    if environment["current"] and not missing_core:
        ready.append(f"- Core packages — ready ({len(core)} of {len(core)} installed)")
        if verbose:
            ready.extend(f"    {package['name']} {package['installed']}" for package in core)

    tool_ready, optional = _tool_and_extra_lines(report, environment["current"], verbose)
    ready.extend(tool_ready)

    setup = command_text(report["setup_command"])
    if not python["ok"]:
        next_steps.append(
            '- Install Python 3.11 or newer as described in the chapter "Install Python" of '
            "the user manual, then run first-time setup."
        )
    elif not environment["current"]:
        next_steps.append(f"- Run first-time setup: ask the agent to run setup, or run: {setup}")
    elif missing_core:
        next_steps.append(
            "- Run setup again to install the missing core packages ("
            + ", ".join(missing_core)
            + f"): ask the agent to run setup, or run: {setup}"
        )
    folder = report.get("folder") or {}
    for item in folder.get("warnings", []):
        next_steps.append(f"- {item.get('hint') or item['message']}")
    if python["ok"] and environment["current"] and not missing_core:
        if folder.get("checked"):
            next_steps.append(
                "- Carry on with this case folder: ask the agent what to do next with this "
                "evidence pack."
            )
        else:
            next_steps.append(NEXT_CASE_FOLDER)
    return _render(ready, optional, next_steps)


def render_setup_human(setup, report, *, verbose=False):
    """The D-17 checklist after ``doctor --setup``: what setup did to the private environment
    (created, rebuilt or already ready), the core packages, then the optional tools and
    extras exactly as ``render_human`` shows them."""
    home = report.get("home")
    ready = _python_lines(report["python"], home, verbose)
    ready.append(
        f"- Private environment — {setup['status']} ({_tilde(setup['environment'], home)})"
    )
    core = report["core_packages"]
    installed = sum(1 for package in core if package["ok"])
    ready.append(f"- Core packages — installed ({installed} of {len(core)})")
    if verbose:
        ready.extend(f"    {package['name']} {package['installed']}" for package in core)
    tool_ready, optional = _tool_and_extra_lines(report, True, verbose)
    ready.extend(tool_ready)
    return _render(ready, optional, [NEXT_CASE_FOLDER])
