"""The user manual (DOC-04, DOC-05, D-17).

The manual quotes the plain-language output of ``doctor`` and ``doctor --setup`` word for
word. The golden tests below render both checklists from one fixed, fake machine report and
compare them with the fenced blocks between the manual's ``<!-- golden:NAME -->`` markers, so
the manual and the code cannot drift apart. When the wording in ``epb/doctor/report.py`` or a
row in the doctor registry changes, regenerate the blocks and re-read the chapter around them.
"""

import re
from pathlib import Path

import pytest
from epb.doctor import probes, report, tools

REPO_ROOT = Path(__file__).resolve().parents[2]
MANUAL = REPO_ROOT / "docs" / "USER-MANUAL.md"

# A made-up Linux computer: a home folder that names no real person, Python 3.12.3, a current
# private environment, every core package installed, 7-Zip and git found, nothing else.
FAKE_HOME = "/home/investigator"
FAKE_ENV = FAKE_HOME + "/.local/share/probematrix-epb/envs/0.1.0"
FAKE_EPB = FAKE_HOME + "/.claude/plugins/evidence-pack/scripts/epb.py"
FOUND_TOOLS = {"7z": ("26.00", "/usr/bin/7z"), "git": ("2.53.0", "/usr/bin/git")}


def _fake_tool(spec):
    version, path = FOUND_TOOLS.get(spec.id, (None, None))
    return {
        "id": spec.id,
        "label": spec.label,
        "found": path is not None,
        "name": spec.names[0] if path else None,
        "path": path,
        "version": version,
        "enables": spec.enables,
        "in_use": spec.in_use,
        "install": dict(spec.install),
    }


def _fake_extra(spec):
    return {
        "id": spec.id,
        "file": spec.file,
        "packages": list(spec.packages),
        "licence": spec.licence,
        "enables": spec.enables,
        "in_use": spec.in_use,
        "installed": False,
        "install": f"{FAKE_ENV}/bin/python -m pip install --uploaded-prior-to P14D -r {spec.file}",
    }


def _fake_core():
    return [
        {"name": name, "requirement": name + spec, "installed": "1.0", "ok": True}
        for name, spec in probes.core_requirements(platform="linux")
    ]


FAKE_REPORT = {
    "os": "linux",
    "home": FAKE_HOME,
    "python": {"version": "3.12.3", "executable": "/usr/bin/python3", "ok": True},
    "setup_command": ["/usr/bin/python3", FAKE_EPB, "doctor", "--setup"],
    "environment": {
        "path": FAKE_ENV,
        "exists": True,
        "current": True,
        "python": FAKE_ENV + "/bin/python",
        "launch": [FAKE_ENV + "/bin/python", FAKE_EPB],
        "other_versions": [],
    },
    "core_packages": _fake_core(),
    "tools": [_fake_tool(spec) for spec in tools.REGISTRY],
    "extras": [_fake_extra(spec) for spec in tools.EXTRAS],
    "folder": {"checked": False, "warnings": []},
}

FAKE_SETUP = {"status": "created", "environment": FAKE_ENV, "python": "3.12.3", "steps": []}


def manual_text():
    return MANUAL.read_text(encoding="utf-8")


def golden_block(name, text=None):
    """The text inside the fenced ``text`` block between the manual's markers for ``name``."""
    text = manual_text() if text is None else text
    pattern = re.compile(
        rf"^<!-- golden:{name} -->\n```text\n(.*?)\n```\n<!-- /golden:{name} -->$",
        re.DOTALL | re.MULTILINE,
    )
    matches = pattern.findall(text)
    assert len(matches) == 1, f"expected exactly one golden:{name} block in {MANUAL.name}"
    return matches[0]


def test_fake_report_is_the_planned_machine():
    assert len(FAKE_REPORT["core_packages"]) == 14
    found = [tool["label"] for tool in FAKE_REPORT["tools"] if tool["found"]]
    assert found == ["7-Zip", "git"]


@pytest.mark.parametrize(
    ("name", "render"),
    [
        ("setup", lambda: report.render_setup_human(FAKE_SETUP, FAKE_REPORT)),
        ("doctor", lambda: report.render_human(FAKE_REPORT)),
    ],
)
def test_manual_quotes_the_renderer_exactly(name, render):
    assert golden_block(name) == render(), (
        f"docs/USER-MANUAL.md golden:{name} block differs from the renderer; "
        "regenerate it and re-read the surrounding chapter"
    )


@pytest.mark.parametrize("name", ["setup", "doctor"])
def test_golden_blocks_show_the_three_headings(name):
    block = golden_block(name)
    for heading in report.HEADINGS:
        assert re.search(rf"^{re.escape(heading)}$", block, re.MULTILINE), heading


def test_golden_block_reader_rejects_a_changed_block():
    text = manual_text().replace("Private environment — ready", "Private environment — fine")
    with pytest.raises(AssertionError):
        assert golden_block("doctor", text) == report.render_human(FAKE_REPORT)
