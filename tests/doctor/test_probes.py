"""epb doctor: the tool registry, the probes, the D-17 checklist and the JSON report (PKG-07,
D-14, D-17)."""

import dataclasses
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from epb import __version__, launcher
from epb.doctor import probes, report, tools
from epbtest.envkit import make_fake_env

TOOL_IDS = ["7z", "ffmpeg", "tesseract", "soffice", "pandoc", "git"]
EXTRA_IDS = ["email", "media", "docs"]
HEADINGS = ["Ready", "Optional, not installed", "What to do next"]
OSES = ("linux", "macos", "windows")

# Version banners as the real tools print them (the 7-Zip banner starts with a blank line).
BANNERS = {
    "7z": "\n7-Zip 26.00 (x64) : Copyright (c) 1999-2026 Igor Pavlov : 2026-02-12\n",
    "ffmpeg": "ffmpeg version 8.0.1 Copyright (c) 2000-2026 the FFmpeg developers\n",
    "tesseract": "tesseract 5.3.4\n leptonica-1.84.1\n",
    "soffice": "LibreOffice 25.8.4.2 580(Build:2)\n",
    "pandoc": "pandoc 3.6.4\nFeatures: +server +lua\n",
    "git": "git version 2.53.0\n",
}
VERSIONS = {
    "7z": "26.00",
    "ffmpeg": "8.0.1",
    "tesseract": "5.3.4",
    "soffice": "25.8.4.2",
    "pandoc": "3.6.4",
    "git": "2.53.0",
}


def spec(tool_id):
    return next(item for item in tools.REGISTRY if item.id == tool_id)


def fake_run(stdout="", stderr="", calls=None, raises=None):
    """A stand-in for subprocess.run that records its calls."""

    def run(argv, **kwargs):
        if calls is not None:
            calls.append((argv, kwargs))
        if raises is not None:
            raise raises
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr=stderr)

    return run


def banner_run(argv, **kwargs):
    """Answer every version probe with the banner of the tool whose name was run."""
    name = Path(argv[0]).name
    for tool_id, names in ((item.id, item.names) for item in tools.REGISTRY):
        if name in names:
            return subprocess.CompletedProcess(argv, 0, stdout=BANNERS[tool_id], stderr="")
    return subprocess.CompletedProcess(argv, 1, stdout="", stderr="")


def which_from(available):
    return lambda name: f"/opt/fake/{name}" if name in available else None


# --- registry -------------------------------------------------------------------------


def test_registry_order():
    assert [item.id for item in tools.REGISTRY] == TOOL_IDS
    assert [item.id for item in tools.EXTRAS] == EXTRA_IDS


@pytest.mark.parametrize("tool_id", TOOL_IDS)
def test_registry_rows_are_complete(tool_id):
    item = spec(tool_id)
    assert item.label and item.enables
    assert item.names and all(item.names)
    assert isinstance(item.version_args, tuple) and item.version_args
    re.compile(item.version_regex)
    assert isinstance(item.in_use, bool)
    assert set(item.install) == set(OSES)
    assert all(item.install[os_id].strip() for os_id in OSES)


@pytest.mark.parametrize("tool_id", TOOL_IDS)
def test_version_regex_reads_real_banner(tool_id):
    match = re.search(spec(tool_id).version_regex, BANNERS[tool_id])
    assert match is not None
    assert match.group(1) == VERSIONS[tool_id]


def test_seven_zip_row():
    item = spec("7z")
    assert item.label == "7-Zip"
    assert item.names == ("7z", "7za", "7zz")
    assert item.version_args == ("i",)
    assert item.enables == ".7z archives"
    assert item.extra_paths["windows"] == (r"C:\Program Files\7-Zip\7z.exe",)
    assert item.install == {
        "linux": "sudo apt install 7zip",
        "macos": "brew install sevenzip",
        "windows": "winget install 7zip.7zip",
    }


def test_only_git_is_in_use():
    assert [item.id for item in tools.REGISTRY if item.in_use] == ["git"]


def test_tesseract_regex_accepts_v_prefix():
    assert re.search(spec("tesseract").version_regex, "tesseract v5.4.0.20240606").group(1) == (
        "5.4.0.20240606"
    )


def test_extras_rows():
    rows = {item.id: item for item in tools.EXTRAS}
    assert rows["email"].file == "requirements-email.txt"
    assert rows["email"].packages == ("extract-msg",)
    assert rows["email"].licence == "GPL-3.0"
    assert rows["media"].packages == ("faster-whisper",)
    assert "GPL" in rows["media"].licence
    assert rows["docs"].packages == ("docling",)
    for item in tools.EXTRAS:
        assert launcher.locate_plugin_file(item.file) is not None
        assert item.enables


# --- probe_tool -----------------------------------------------------------------------


def test_probe_finds_first_name_and_reads_version():
    calls = []
    found = probes.probe_tool(
        spec("ffmpeg"),
        which=which_from({"ffmpeg"}),
        run=fake_run(stdout=BANNERS["ffmpeg"], calls=calls),
        platform="linux",
    )
    assert found["id"] == "ffmpeg"
    assert found["found"] is True
    assert found["path"] == "/opt/fake/ffmpeg"
    assert found["version"] == "8.0.1"
    argv, kwargs = calls[0]
    assert argv == ["/opt/fake/ffmpeg", "-version"]
    assert kwargs["timeout"] == 10
    assert not kwargs.get("shell")


def test_probe_alternative_name():
    found = probes.probe_tool(
        spec("7z"), which=which_from({"7zz"}), run=fake_run(stdout=BANNERS["7z"]), platform="linux"
    )
    assert found["found"] is True
    assert found["name"] == "7zz"
    assert found["path"] == "/opt/fake/7zz"
    assert found["version"] == "26.00"


def test_probe_version_from_stderr():
    found = probes.probe_tool(
        spec("git"),
        which=which_from({"git"}),
        run=fake_run(stderr=BANNERS["git"]),
        platform="linux",
    )
    assert found["version"] == "2.53.0"


def test_probe_windows_extra_path(tmp_path):
    exe = tmp_path / "Program Files" / "7-Zip" / "7z.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    windows_spec = dataclasses.replace(spec("7z"), extra_paths={"windows": (str(exe),)})
    found = probes.probe_tool(
        windows_spec, which=which_from(set()), run=fake_run(stdout=BANNERS["7z"]), platform="win32"
    )
    assert found["found"] is True
    assert found["path"] == str(exe)
    assert found["version"] == "26.00"
    # The Windows fallback folder is never consulted on another OS.
    elsewhere = probes.probe_tool(
        windows_spec, which=which_from(set()), run=fake_run(stdout=BANNERS["7z"]), platform="linux"
    )
    assert elsewhere["found"] is False


@pytest.mark.parametrize(
    "failure",
    [OSError("boom"), subprocess.TimeoutExpired(["x"], 10), ValueError("bad")],
    ids=["oserror", "timeout", "valueerror"],
)
def test_crashed_version_probe_is_found_without_version(failure):
    found = probes.probe_tool(
        spec("pandoc"), which=which_from({"pandoc"}), run=fake_run(raises=failure), platform="linux"
    )
    assert found["found"] is True
    assert found["version"] is None


def test_unreadable_banner_is_found_without_version():
    found = probes.probe_tool(
        spec("pandoc"), which=which_from({"pandoc"}), run=fake_run(stdout="??"), platform="linux"
    )
    assert found["found"] is True
    assert found["version"] is None


def test_missing_tool():
    calls = []
    found = probes.probe_tool(
        spec("tesseract"), which=which_from(set()), run=fake_run(calls=calls), platform="linux"
    )
    assert found["found"] is False
    assert found["path"] is None
    assert found["version"] is None
    assert found["install"]["linux"] == "sudo apt install tesseract-ocr"
    assert calls == []


# --- core requirements and packages -----------------------------------------------------


def _requirement_lines():
    path = launcher.locate_plugin_file("requirements.txt")
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            lines.append(line)
    return lines


def test_core_requirements_skip_windows_only_lines_elsewhere():
    pairs = probes.core_requirements(platform="linux")
    names = [name for name, _ in pairs]
    assert "tzdata" not in names
    assert names[0] == "jsonschema"
    assert dict(pairs)["jsonschema"] == ">=4.25"
    assert len(pairs) == len(_requirement_lines()) - 1


def test_core_requirements_keep_windows_only_lines_on_windows():
    names = [name for name, _ in probes.core_requirements(platform="win32")]
    assert names[-1] == "tzdata"
    assert len(names) == len(_requirement_lines())


def test_env_packages_reads_versions_from_the_interpreter():
    versions = probes.env_packages(sys.executable, ["pytest", "epb-no-such-package"])
    assert list(versions) == ["pytest", "epb-no-such-package"]
    assert re.match(r"\d+\.", versions["pytest"])
    assert versions["epb-no-such-package"] is None


def test_env_packages_with_broken_interpreter(tmp_path):
    versions = probes.env_packages(tmp_path / "no-python", ["pytest"])
    assert versions == {"pytest": None}


# --- collect --------------------------------------------------------------------------


def test_collect_before_setup(case_dir):
    data = probes.collect(case_dir, which=which_from(set()), run=banner_run)
    assert data["os"] in OSES
    assert data["python"]["ok"] is True
    assert data["environment"]["exists"] is False
    assert data["environment"]["current"] is False
    assert data["environment"]["launch"] is None
    assert [tool["id"] for tool in data["tools"]] == TOOL_IDS
    assert [extra["id"] for extra in data["extras"]] == EXTRA_IDS
    assert all(package["installed"] is None for package in data["core_packages"])
    assert data["folder"] == {"checked": False, "warnings": []}


def test_collect_lists_other_environment_versions(case_dir):
    (launcher.data_root() / "envs" / "0.0.9").mkdir(parents=True)
    (launcher.data_root() / "envs" / "0.0.8").mkdir(parents=True)
    data = probes.collect(case_dir, which=which_from(set()), run=banner_run)
    assert data["environment"]["other_versions"] == ["0.0.8", "0.0.9"]


def test_collect_extra_install_command(case_dir):
    data = probes.collect(case_dir, which=which_from(set()), run=banner_run)
    email = next(extra for extra in data["extras"] if extra["id"] == "email")
    env_python = str(launcher.env_python(launcher.env_dir()))
    email_file = str(launcher.locate_plugin_file("requirements-email.txt"))
    assert email["installed"] is False
    assert email["install"] == (
        f"{env_python} -m pip install --uploaded-prior-to P14D -r {email_file}"
    )


def test_two_collects_render_identically(case_dir):
    first = probes.collect(case_dir, which=which_from({"7z", "git"}), run=banner_run)
    second = probes.collect(case_dir, which=which_from({"7z", "git"}), run=banner_run)
    assert json.dumps(first) == json.dumps(second)
    assert report.render_human(first) == report.render_human(second)
    assert report.render_human(first, verbose=True) == report.render_human(second, verbose=True)


# --- render_human (D-17) ----------------------------------------------------------------


def _report(os_id="linux", *, current=True, found=("7z", "git"), missing_core=()):
    """A synthetic report, so the renderer is tested independently of this machine."""
    home = "/home/tester"
    env_path = f"{home}/.local/share/probematrix-epb/envs/{__version__}"
    env_python = f"{env_path}/bin/python"
    core = [
        {
            "name": name,
            "requirement": f"{name}>=1.0",
            "installed": None if name in missing_core else "1.2.3",
            "ok": name not in missing_core,
        }
        for name in ("jsonschema", "PyYAML", "openpyxl")
    ]
    tool_rows = []
    for item in tools.REGISTRY:
        is_found = item.id in found
        tool_rows.append(
            {
                "id": item.id,
                "label": item.label,
                "found": is_found,
                "name": item.names[0] if is_found else None,
                "path": f"/usr/bin/{item.names[0]}" if is_found else None,
                "version": VERSIONS[item.id] if is_found else None,
                "enables": item.enables,
                "in_use": item.in_use,
                "install": dict(item.install),
            }
        )
    extras = [
        {
            "id": item.id,
            "file": item.file,
            "packages": list(item.packages),
            "licence": item.licence,
            "enables": item.enables,
            "installed": False,
            "install": f"{env_python} -m pip install --uploaded-prior-to P14D -r /p/{item.file}",
        }
        for item in tools.EXTRAS
    ]
    return {
        "os": os_id,
        "home": home,
        "python": {"version": "3.12.4", "executable": "/usr/bin/python3", "ok": True},
        "setup_command": ["/usr/bin/python3", "/p/epb.py", "doctor", "--setup"],
        "environment": {
            "path": env_path,
            "exists": current,
            "current": current,
            "python": env_python,
            "launch": [env_python, "/p/epb.py"] if current else None,
            "other_versions": ["0.0.9"],
        },
        "core_packages": core,
        "tools": tool_rows,
        "extras": extras,
        "folder": {"checked": False, "warnings": []},
    }


def _headings(text):
    return [line for line in text.splitlines() if line and not line.startswith((" ", "-"))]


@pytest.mark.parametrize("verbose", [False, True])
def test_render_has_exactly_three_headings_in_order(verbose):
    assert _headings(report.render_human(_report(), verbose=verbose)) == HEADINGS


def test_render_ready_lines():
    text = report.render_human(_report())
    assert "- Python 3.12 — ready" in text
    assert f"- Private environment — ready (~/.local/share/probematrix-epb/envs/{__version__})" in (
        text
    )
    assert "- Core packages — ready (3 of 3 installed)" in text
    assert (
        "- 7-Zip — ready: .7z archives (support arrives in a later version of this plugin)" in text
    )
    assert "/home/tester" not in text


def test_render_optional_line_uses_this_os_only():
    text = report.render_human(_report("linux"))
    assert (
        "- ffmpeg — would enable audio and video recordings (support arrives in a later "
        "version of this plugin). Install: sudo apt install ffmpeg"
    ) in text
    assert "brew install" not in text
    assert "winget install" not in text
    mac = report.render_human(_report("macos"))
    assert "Install: brew install ffmpeg" in mac
    assert "sudo apt" not in mac


def test_render_verbose_lists_all_three_oses_and_versions():
    text = report.render_human(_report("linux"), verbose=True)
    for command in spec("ffmpeg").install.values():
        assert command in text
    assert "3.12.4" in text
    assert "26.00" in text
    assert "0.0.9" in text


def test_render_reads_os_from_report_not_from_this_machine():
    assert "winget install Gyan.FFmpeg" in report.render_human(_report("windows"))


def test_render_next_step_when_ready():
    text = report.render_human(_report())
    next_part = text.split("What to do next", 1)[1]
    assert "Set up a case folder: ask the agent to set up an evidence pack case folder here." in (
        next_part
    )


def test_render_next_step_before_setup():
    text = report.render_human(_report(current=False))
    next_part = text.split("What to do next", 1)[1]
    first = next_part.strip().splitlines()[0]
    assert first == (
        "- Run first-time setup: ask the agent to run setup, or run: "
        "/usr/bin/python3 /p/epb.py doctor --setup"
    )
    assert "Private environment — ready" not in text


def test_render_names_missing_core_packages():
    text = report.render_human(_report(missing_core=("openpyxl",)))
    assert "Core packages — ready" not in text
    assert "openpyxl" in text.split("What to do next", 1)[1]


def test_current_os():
    assert report.current_os() in OSES


# --- the doctor command end to end --------------------------------------------------------


def test_doctor_json_before_setup(run_epb, case_dir):
    proc = run_epb(["doctor", "--json"], case_dir, in_env=False)
    assert proc.returncode == 3, proc.stderr
    envelope = json.loads(proc.stdout)
    assert envelope["command"] == "doctor"
    assert envelope["errors"][0]["code"] == "ENV_NOT_SET_UP"
    data = envelope["data"]
    assert [tool["id"] for tool in data["tools"]] == TOOL_IDS
    assert [extra["id"] for extra in data["extras"]] == EXTRA_IDS
    assert data["environment"]["current"] is False


def test_doctor_human_before_setup_shows_checklist(run_epb, case_dir):
    proc = run_epb(["doctor"], case_dir, in_env=False)
    assert proc.returncode == 3
    for heading in HEADINGS:
        assert heading in proc.stderr
    assert "doctor --setup" in proc.stderr


def test_doctor_json_after_setup(run_epb, case_dir):
    make_fake_env()
    proc = run_epb(["doctor", "--json"], case_dir, in_env=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)["data"]
    assert data["environment"]["current"] is True
    launch = data["environment"]["launch"]
    assert len(launch) == 2
    assert all(Path(part).is_absolute() for part in launch)
    assert launch[1] == str(launcher.epb_script())
    assert data["core_packages"]
    assert all(package["ok"] for package in data["core_packages"]), data["core_packages"]


def test_doctor_human_after_setup(run_epb, case_dir):
    make_fake_env()
    proc = run_epb(["doctor"], case_dir, in_env=False)
    assert proc.returncode == 0, proc.stderr
    assert _headings(proc.stdout) == HEADINGS


def test_missing_optional_tools_never_change_the_exit_code(run_epb, case_dir, tmp_path):
    make_fake_env()
    empty = tmp_path / "empty-path"
    empty.mkdir()
    with_tools = run_epb(["doctor", "--json"], case_dir, in_env=False)
    without = run_epb(["doctor", "--json"], case_dir, in_env=False, env={"PATH": str(empty)})
    assert without.returncode == with_tools.returncode == 0, without.stdout + without.stderr
    data = json.loads(without.stdout)["data"]
    assert [tool["found"] for tool in data["tools"]] == [False] * len(TOOL_IDS)
    human = run_epb(["doctor"], case_dir, in_env=False, env={"PATH": str(empty)})
    optional = human.stdout.split("Optional, not installed", 1)[1].split("What to do next", 1)[0]
    for item in tools.REGISTRY:
        assert f"- {item.label} — would enable" in optional
