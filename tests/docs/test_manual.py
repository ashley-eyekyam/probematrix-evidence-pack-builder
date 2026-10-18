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


def _headed_lines(text):
    """Each line of ``text`` with its heading level (0 for a non-heading line). A line inside
    a fenced block, indented or not, is never a heading, so quoted output cannot start a
    section."""
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        match = None if fenced else re.match(r"(#+) (.+)$", line)
        yield (len(match.group(1)), match.group(2)) if match else (0, line)


def _headings(text):
    return [title for level, title in _headed_lines(text) if level]


def _sections(text, level):
    """``(title, body)`` for each heading of ``level`` (2 for ``##``) in ``text``. A body
    keeps its fenced blocks and runs to the next heading of the same or a higher level."""
    sections = []
    for line_level, line in _headed_lines(text):
        if line_level and line_level <= level:
            if line_level == level:
                sections.append((line, []))
            else:
                sections.append((None, []))
        elif sections:
            sections[-1][1].append(line if not line_level else "#" * line_level + " " + line)
    return [(title, "\n".join(body)) for title, body in sections if title is not None]


def chapters():
    return dict(_sections(manual_text(), 2))


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
    for heading in _headings(manual_text()):
        for word in ("todo", "tbd", "coming soon"):
            assert word not in heading.lower(), heading


# --- what this version does with file names (DOC-04, gap 5, review C-CR-01) ---------------

_ITEM_START = re.compile(r"(- |\d+\. )")


def _items(text):
    """Each paragraph or list item of ``text`` as one line of single-spaced text.

    A blank line ends a paragraph, a heading stands alone, and a line starting with ``- `` or
    with digits followed by ``. `` (indented or not) starts a new item. Fenced blocks are
    skipped, so quoted plugin output is never an item.
    """
    items, current, fenced = [], [], False

    def flush():
        if current:
            items.append(" ".join(current))
            current.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush()
            fenced = not fenced
            continue
        if fenced:
            continue
        if not stripped:
            flush()
        elif stripped.startswith("#"):
            flush()
            items.append(stripped)
        else:
            if _ITEM_START.match(stripped):
                flush()
            current.append(stripped)
    flush()
    return items


def test_items_splits_paragraphs_list_items_and_skips_fences():
    text = "One\ntwo.\n\n- a\n  b\n1. c\n```text\n- quoted\n```\n### Head\nend"
    assert _items(text) == ["One two.", "- a b", "1. c", "### Head", "end"]


def test_no_paragraph_promises_a_name_free_index():
    for item in _items(manual_text()):
        lowered = item.lower()
        if "index.md" in lowered and "role label" in lowered:
            assert "later version" in lowered, (
                f"this paragraph says INDEX.md uses role labels without saying that arrives "
                f"in a later version: {item}"
            )


def test_privacy_chapter_says_file_names_are_shown_as_given():
    items = [item.lower() for item in _items(chapter("2. What stays on your computer"))]
    assert any("index.md" in item and "file name" in item and "rename" in item for item in items), (
        "chapter 2 needs one paragraph or step about INDEX.md, file names and renaming"
    )


def test_privacy_chapter_has_a_file_names_section():
    titles = [title.lower() for title, _ in _sections(chapter("2. What stays on your computer"), 3)]
    assert any("file names" in title for title in titles), titles


def test_first_case_folder_chapter_warns_about_names_in_file_names():
    body = chapter("6. Your first case folder")
    assert "rename" in body.lower()
    assert "file name" in body.lower()
    sections = dict(_sections(body, 3))
    put_files = next(text for title, text in sections.items() if title.startswith("Put your files"))
    assert any(
        "rename" in item.lower() and "index.md" in item.lower() for item in _items(put_files)
    ), "the inputs step must say to rename files because INDEX.md shows file names"
    read_index = next(text for title, text in sections.items() if title.startswith("Read "))
    inputs_bullet = next(item for item in _items(read_index) if item.startswith("- **3. Inputs**"))
    assert "file name" in inputs_bullet.lower(), inputs_bullet
    assert any(
        "before you share" in item.lower() and "person's name" in item.lower()
        for item in _items(read_index)
    ), "Read INDEX.md must say to check file names for a person's name before sharing"
