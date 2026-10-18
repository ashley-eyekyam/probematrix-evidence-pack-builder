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
from epb.doctor import probes, report, syncfolders, tools

REPO_ROOT = Path(__file__).resolve().parents[2]
MANUAL = REPO_ROOT / "docs" / "USER-MANUAL.md"

CHAPTERS = [
    "1. What this plugin does",
    "2. What stays on your computer",
    "3. Install Python",
    "4. Add the plugin to Claude Code",
    "5. First-time setup",
    "6. Your first case folder",
    "7. Where the private environment lives",
]
UNTESTED = "not yet tested on this system"

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


# --- structure and content of the first edition (DOC-04, DOC-05, D-03) --------------------


def _without_fences(text):
    """The manual with every fenced block blanked, so quoted output is never read as a
    heading."""
    return re.sub(r"^```.*?^```$", "", text, flags=re.DOTALL | re.MULTILINE)


def _sections(text, level):
    """``(title, body)`` for each heading of ``level`` (2 for ``##``) in ``text``."""
    marker = "#" * level
    parts = re.split(rf"^{marker} (.+)$", text, flags=re.MULTILINE)
    return list(zip(parts[1::2], parts[2::2], strict=True))


def chapters():
    return dict(_sections(_without_fences(manual_text()), 2))


def chapter(title):
    return chapters()[title]


def test_chapters_appear_in_the_doc05_order():
    assert list(chapters()) == CHAPTERS


@pytest.mark.parametrize(
    "term",
    [
        "AI host",
        "model provider",
        "OneDrive",
        "Dropbox",
        "iCloud Drive",
        "Google Drive",
        ".epb/private",
        "de-identification",
    ],
)
def test_privacy_chapter_names_what_leaves_and_why(term):
    assert term in chapter("2. What stays on your computer")


def test_manual_never_claims_that_nothing_leaves_the_computer():
    text = manual_text().lower()
    for claim in ("nothing leaves", "nothing is sent", "never leaves", "fully offline"):
        assert claim not in text, claim


def test_privacy_chapter_quotes_the_real_sync_folder_warning():
    warning = syncfolders.warning_for(syncfolders.SyncHit("OneDrive", None, "settings"))
    body = chapter("2. What stays on your computer")
    assert warning["message"] in body
    assert warning["hint"] in body


def _first_line(body):
    return next(line for line in body.splitlines() if line.strip())


@pytest.mark.parametrize("title", ["3. Install Python", "7. Where the private environment lives"])
def test_windows_and_macos_sections_each_carry_their_own_untested_line(title):
    sections = dict(_sections(chapter(title), 3))
    assert {"Linux", "Windows", "macOS"} <= set(sections)
    assert UNTESTED in _first_line(sections["Windows"])
    assert UNTESTED in _first_line(sections["macOS"])
    assert UNTESTED not in sections["Linux"]


def test_install_python_gives_the_check_and_install_commands():
    body = chapter("3. Install Python")
    for text in (
        "python3 --version",
        "sudo apt install python3 python3-venv",
        "py -3 --version",
        "Add python.exe to PATH",
        "python.org",
        "3.11",
    ):
        assert text in body, text


def test_add_plugin_chapter_gives_both_commands():
    body = chapter("4. Add the plugin to Claude Code")
    assert "/plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder" in body
    assert (
        "/plugin install probematrix-evidence-pack-builder@probematrix-evidence-pack-builder"
        in body
    )


def test_codex_note_is_marked_untested():
    sections = dict(_sections(chapter("4. Add the plugin to Claude Code"), 3))
    codex = next(body for title, body in sections.items() if "Codex" in title)
    assert UNTESTED in _first_line(codex)
    assert "codex plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder" in codex
    assert "python3 tools/install-codex.py" in codex


def test_first_case_folder_chapter_walks_through_init_scan_and_index():
    body = chapter("6. Your first case folder")
    for text in ("inputs/", ".note.md", "INDEX.md", "none yet", "waiting for conversion"):
        assert text in body, text


def test_first_case_folder_chapter_names_the_six_index_sections():
    from epb.index import SECTION_TITLES

    body = chapter("6. Your first case folder")
    for title in SECTION_TITLES:
        assert title in body, title


def test_environment_chapter_names_the_three_folders():
    body = chapter("7. Where the private environment lives")
    for path in (
        "~/.local/share/probematrix-epb/",
        "%LOCALAPPDATA%\\probematrix-epb\\",
        "~/Library/Application Support/probematrix-epb/",
        "envs",
    ):
        assert path in body, path


def test_chapter_one_says_once_which_stages_later_editions_add():
    body = chapter("1. What this plugin does")
    assert "later editions" in body
    assert manual_text().count("later editions") == 1


def test_no_heading_is_a_placeholder():
    headings = re.findall(r"^#+ (.+)$", _without_fences(manual_text()), flags=re.MULTILINE)
    for heading in headings:
        for word in ("todo", "tbd", "coming soon"):
            assert word not in heading.lower(), heading
