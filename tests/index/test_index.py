"""INDEX.md: six sections in order, ``none yet`` when empty, the Imported? tick line, and the
inputs, open issues and run history providers on synthetic records (WS-09, PF-04)."""

import json
import os
import re

import pytest
from epb import index
from epb.index import NONE_YET, SECTION_TITLES, IndexInputs, render_import_line, render_index

INIT = [
    "init",
    "--title",
    "Acme Pump Trip",
    "--slug",
    "acme-pump-trip",
    "--prefix",
    "APT",
    "--timezone",
    "UTC",
    "--json",
]

CASE = {
    "title": "Acme Pump Trip",
    "slug": "acme-pump-trip",
    "id_prefix": "APT",
    "timezone": "UTC",
}
SHA_A = "a" * 64
SHA_B = "0123456789ab" + "c" * 52
MASTER = "evidence-pack-acme-pump-trip-master.xlsx"
DELTA = "evidence-pack-acme-pump-trip-delta-002.xlsx"

POSIX_ONLY = pytest.mark.skipif(os.name == "nt", reason="these file names are POSIX-only here")

# Every character that must never reach INDEX.md: C0 controls, DEL, C1 controls (NEL included)
# and the two Unicode separators. ``str.splitlines()`` breaks on several of them.
FORBIDDEN = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]")
TICK_LINE = re.compile(r"^- \[[ xX]\] Imported:")


def sections(text):
    """The body of each ``## N. Title`` section, keyed by title."""
    found = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:]
            found[current] = []
        elif current is not None:
            found[current].append(line)
    return {title: "\n".join(lines).strip("\n") for title, lines in found.items()}


def state(workbooks=()):
    return {"plugin_version": "0.1.0", "workbooks": list(workbooks)}


def workbook(file, *, number=1, kind="master", status="draft", imported_at=None, items=12):
    return {
        "file": file,
        "kind": kind,
        "number": number,
        "status": status,
        "imported_at": imported_at,
        "writes": [
            {
                "run": "003",
                "sha256": SHA_A,
                "item_count": items,
                "tag_first": "TAG-APT-00000001",
                "tag_last": "TAG-APT-00000012",
                "written_at": "2026-10-17T11:00:00Z",
            }
        ],
    }


def source(
    src_id,
    path,
    *,
    mime="application/pdf",
    size=2048,
    sha=SHA_B,
    presence="present",
    status="pending",
    version=1,
    **extra,
):
    record = {
        "schema_version": 1,
        "src_id": src_id,
        "current_version": version,
        "paths": [path] if presence == "present" else [],
        "presence": presence,
        "status": status,
        "parents": [],
        "source_kind": None,
        "sidecar_of": None,
        "sidecars": [],
        "first_seen_run": "002",
        "last_processed_run": None,
        "mime_mismatch": None,
        "versions": [
            {
                "version": number,
                "sha256": sha,
                "size": size,
                "mime": mime,
                "mtime_ns": 0,
                "seen_run": "002",
                "paths": [path],
            }
            for number in range(1, version + 1)
        ],
    }
    record.update(extra)
    return record


def run(number, command="scan", summary="Took stock.", *, finished="2026-10-17T10:00:00Z", **kw):
    return {
        "schema_version": 1,
        "run": number,
        "command": command,
        "started_at": finished,
        "finished_at": finished,
        "plugin_version": "0.1.0",
        "summary": summary,
        "scan": kw.get("scan"),
        "upgrade": None,
    }


# --- structure --------------------------------------------------------------------------------


def test_section_titles():
    assert SECTION_TITLES == (
        "1. Case",
        "2. What to import where",
        "3. Inputs",
        "4. Outputs",
        "5. Open issues",
        "6. Run history",
    )
    assert [title for title, _ in index.PROVIDERS] == list(SECTION_TITLES)


def test_title_note_and_headings():
    text = render_index(IndexInputs(CASE, state()))
    lines = text.splitlines()
    assert lines[0] == "# Acme Pump Trip"
    assert lines[2].startswith("> This file is rewritten by the evidence pack builder")
    assert "except to tick an Imported? box" in lines[2]
    headings = [line for line in lines if line.startswith("#")]
    assert headings == ["# Acme Pump Trip", *(f"## {title}" for title in SECTION_TITLES)]
    assert text.endswith("\n") and not text.endswith("\n\n")


@pytest.mark.parametrize("full", [False, True], ids=["empty", "full"])
def test_every_heading_has_blank_lines_around_it(full):
    if full:
        inputs = IndexInputs(
            CASE,
            state([workbook(MASTER)]),
            [source("S001", "inputs/a.pdf")],
            [run("001", "init"), run("002")],
        )
    else:
        inputs = IndexInputs(CASE, state())
    lines = render_index(inputs).splitlines()
    for number, line in enumerate(lines):
        if line.startswith("## "):
            assert lines[number - 1] == "", line
            assert lines[number + 1] == "", line
            assert lines[number + 2].strip(), line


def test_fresh_init_reads_none_yet(run_epb, case_dir):
    proc = run_epb(INIT, cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["ok"] is True
    text = (case_dir / "INDEX.md").read_text(encoding="utf-8")
    body = sections(text)
    assert list(body) == list(SECTION_TITLES)
    for title in SECTION_TITLES[1:5]:
        assert body[title] == NONE_YET, title
    assert "- Current pack version: none yet" in body["1. Case"]
    assert "- Title: Acme Pump Trip" in body["1. Case"]
    assert "- ID prefix: APT (evidence IDs look like EVD-APT-001)" in body["1. Case"]
    assert "- Timezone: UTC" in body["1. Case"]


def test_empty_inputs_render_none_yet_everywhere_but_the_header():
    body = sections(render_index(IndexInputs(CASE, state())))
    for title in SECTION_TITLES[1:]:
        assert body[title] == NONE_YET
    assert "- Last run: none yet" in body["1. Case"]


# --- what to import where ---------------------------------------------------------------------


def test_import_line_syntax():
    assert render_import_line(workbook(MASTER)) == f"- [ ] Imported: {MASTER}"
    imported = workbook(MASTER, status="imported", imported_at="2026-10-18T09:00:00Z")
    assert render_import_line(imported) == f"- [x] Imported: {MASTER}"


def test_draft_master_workbook():
    body = sections(render_index(IndexInputs(CASE, state([workbook(MASTER)]))))
    section = body["2. What to import where"]
    assert section.splitlines()[-1] == f"- [ ] Imported: {MASTER}"
    assert index.IMPORT_INSTRUCTION in section
    assert f"| {MASTER} | master | draft | 12 | TAG-APT-00000001 to TAG-APT-00000012 |" in section
    assert "- Current pack version: 1" in body["1. Case"]
    assert MASTER in body["4. Outputs"]


def test_imported_master_and_draft_delta():
    books = [
        workbook(MASTER, status="imported", imported_at="2026-10-18T09:00:00Z"),
        workbook(DELTA, number=2, kind="delta", items=3),
    ]
    section = sections(render_index(IndexInputs(CASE, state(books))))["2. What to import where"]
    ticks = [line for line in section.splitlines() if line.startswith("- [")]
    assert ticks == [f"- [x] Imported: {MASTER}", f"- [ ] Imported: {DELTA}"]
    assert "imported 2026-10-18" in section


# --- inputs and open issues -------------------------------------------------------------------


def synthetic_sources():
    return [
        source("S002", "inputs/b/photo.png", mime="image/png", size=512),
        source(
            "S001",
            "inputs/a/report.pdf",
            size=3 * 1024 * 1024,
            mime_mismatch={"by_extension": "text/plain", "by_content": "application/pdf"},
        ),
        source("S003", "inputs/c/old.docx", presence="removed from folder", mime="x/unknown"),
        source(
            "S004",
            "inputs/d/orphan.note.md",
            mime="text/markdown",
            size=10,
            source_kind="sidecar",
        ),
        source("S005", "inputs/e/v2.txt", mime="text/plain", version=2, size=0),
    ]


def test_inputs_table():
    body = sections(render_index(IndexInputs(CASE, state(), synthetic_sources())))
    rows = [line for line in body["3. Inputs"].splitlines() if line.startswith("| ")]
    assert rows[0] == (
        "| ID | Path | Type | Size | SHA-256 | First seen | Last processed | Status | "
        "Segments | Claims | Items |"
    )
    assert set(rows[1].replace("|", "").split()) == {"---"}
    data = rows[2:]
    paths = [row.split(" | ")[1] for row in data]
    assert paths == sorted(paths)
    by_id = {row.split(" | ")[0][2:]: row for row in data}
    assert set(by_id) == {"S001", "S002", "S003", "S004", "S005v2"}
    pdf = by_id["S001"]
    assert "| PDF | 3.0 MB | 0123456789ab |" in pdf
    assert "| Run 002 | not yet | waiting for conversion (coming in a later version) |" in pdf
    assert pdf.endswith("| none yet | none yet | none yet |")
    assert "| PNG image | 512 B |" in by_id["S002"]
    assert "| inputs/c/old.docx | x/unknown |" in by_id["S003"]
    assert "| removed from folder |" in by_id["S003"]
    assert "| 0 B |" in by_id["S005v2"]


def test_open_issues():
    body = sections(render_index(IndexInputs(CASE, state(), synthetic_sources())))
    issues = body["5. Open issues"].splitlines()
    assert issues == [
        "- S001 (inputs/a/report.pdf): the content is application/pdf, but the file name "
        "suggests text/plain. The content was used.",
        "- S003 (inputs/c/old.docx) was removed from the folder. Its record is kept.",
        "- S004 (inputs/d/orphan.note.md) is a note for inputs/d/orphan, but that file is not "
        "in inputs/.",
    ]


def test_links_and_special_files_from_the_latest_scan_are_issues():
    scan = {
        "ignored": [
            {"path": "inputs/.DS_Store", "reason": "junk"},
            {"path": "inputs/shortcut", "reason": "link"},
            {"path": "inputs/pipe", "reason": "special"},
        ]
    }
    older = {"ignored": [{"path": "inputs/old-link", "reason": "link"}]}
    runs = [run("002", scan=older), run("003", scan=scan)]
    issues = sections(render_index(IndexInputs(CASE, state(), [], runs)))["5. Open issues"]
    assert issues.splitlines() == [
        "- inputs/pipe was skipped: it is not a regular file (for example a pipe or a device).",
        "- inputs/shortcut was skipped: it is a link, which the plugin does not follow.",
    ]


@POSIX_ONLY
def test_scan_of_line_breaking_names_keeps_six_headings(run_epb, case_dir, tmp_path):
    """A real scan of hostile synthetic file names cannot add a heading or forge a tick."""
    proc = run_epb(INIT, cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    inputs_dir = case_dir / "inputs"
    inputs_dir.mkdir(exist_ok=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "target.txt").write_bytes(b"synthetic file outside the case folder")

    statement = inputs_dir / "statement\n## Injected heading.txt"
    statement.write_bytes(b"synthetic witness statement")
    log = inputs_dir / "log\u2028## Second injected heading.txt"
    log.write_bytes(b"%PDF-1.4\n% synthetic pdf bytes under a text name\n")
    os.symlink(
        outside / "target.txt",
        inputs_dir / "link\n- [x] Imported: evidence-pack-inj-master.xlsx",
    )

    first = run_epb(["scan", "--json"], cwd=case_dir)
    assert first.returncode == 0, first.stdout + first.stderr
    statement.unlink()
    second = run_epb(["scan", "--json"], cwd=case_dir)
    assert second.returncode == 0, second.stdout + second.stderr

    text = (case_dir / "INDEX.md").read_text(encoding="utf-8")
    lines = text.split("\n")
    headings = [line for line in lines if line.startswith("## ")]
    assert headings == [f"## {title}" for title in SECTION_TITLES]
    assert not [line for line in lines if TICK_LINE.match(line)]
    assert not FORBIDDEN.findall(text.replace("\n", ""))
    assert text.splitlines() == text[:-1].split("\n")
    issues = sections(text)["5. Open issues"]
    assert "was removed from the folder" in issues
    assert "Injected heading.txt" in issues
    assert "the content is application/pdf" in issues
    assert "was skipped: it is a link" in issues


def test_display_id():
    assert index.display_id(source("S004", "inputs/x.pdf")) == "S004"
    assert index.display_id(source("S004", "inputs/x.pdf", version=2)) == "S004v2"
    assert index.display_id(source("S1000", "inputs/x.pdf", version=3)) == "S1000v3"


def test_table_cells_are_escaped():
    odd = source("S001", "inputs/a|b.pdf")
    rows = sections(render_index(IndexInputs(CASE, state(), [odd])))["3. Inputs"]
    assert "inputs/a\\|b.pdf" in rows


def test_table_cells_are_single_line():
    odd = source("S001", "inputs/a\u2028b|c.pdf")
    section = sections(render_index(IndexInputs(CASE, state(), [odd])))["3. Inputs"]
    rows = [line for line in section.splitlines() if line.startswith("| S001 ")]
    assert len(rows) == 1
    assert "| inputs/a b\\|c.pdf |" in rows[0]


# --- single-line values -----------------------------------------------------------------------

BREAKS = ["\n", "\r", "\r\n", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85"]
BREAKS += ["\u2028", "\u2029", "\x00", "\t"]


def test_inline_maps_each_break_to_one_space():
    assert index._inline("a\n\nb") == "a  b"
    assert index._inline("a\r\nb") == "a  b"
    assert index._inline("\u2028") == " "
    assert index._inline("plain name.pdf") == "plain name.pdf"


@pytest.mark.parametrize("brk", BREAKS, ids=[repr(brk) for brk in BREAKS])
def test_hostile_values_cannot_break_index_structure(brk):
    hostile = "x" + brk + "## Injected" + brk + "- [x] Imported: evidence-pack-inj-master.xlsx"
    case = {"title": hostile, "slug": hostile, "id_prefix": hostile, "timezone": hostile}
    books = state([workbook(hostile)])
    books["plugin_version"] = hostile
    mismatch = {"by_content": hostile, "by_extension": hostile}
    sources = [
        source("S001", hostile, presence="removed from folder"),
        source("S002", "inputs/odd.txt", mime_mismatch=mismatch),
        source("S003", hostile, mime="text/markdown", source_kind="sidecar"),
    ]
    ignored = {"ignored": [{"path": hostile, "reason": "link"}]}
    runs = [run(hostile, command=hostile, summary=hostile, scan=ignored)]

    text = render_index(IndexInputs(case, books, sources, runs))
    lines = text[:-1].split("\n")
    titles = [number for number, line in enumerate(lines) if line.startswith("# ")]
    assert titles == [0]
    headings = [line for line in lines if line.startswith("## ")]
    assert headings == [f"## {title}" for title in SECTION_TITLES]
    ticks = [number for number, line in enumerate(lines) if TICK_LINE.match(line)]
    assert len(ticks) == 1
    tick = lines[ticks[0]]
    assert tick.startswith("- [ ] Imported: ")
    owner = [line for line in lines[: ticks[0]] if line.startswith("## ")][-1]
    assert owner == "## 2. What to import where"
    assert not FORBIDDEN.findall(text.replace("\n", ""))
    assert text.splitlines() == lines


# --- run history ------------------------------------------------------------------------------


def test_run_history_is_sorted_by_number():
    runs = [
        run("010", finished="2026-10-18T12:30:59Z"),
        run("001", "init", "Case folder created."),
        run("002"),
    ]
    body = sections(render_index(IndexInputs(CASE, state(), [], runs)))
    assert body["6. Run history"].splitlines() == [
        "- Run 001 · 2026-10-17 10:00 UTC · init · Case folder created.",
        "- Run 002 · 2026-10-17 10:00 UTC · scan · Took stock.",
        "- Run 010 · 2026-10-18 12:30 UTC · scan · Took stock.",
    ]
    assert "- Last run: Run 010 · 2026-10-18 12:30 UTC · scan" in body["1. Case"]


def test_no_absolute_path_is_rendered():
    text = render_index(
        IndexInputs(CASE, state([workbook(MASTER)]), synthetic_sources(), [run("001")])
    )
    assert not re.search(r"(^|[\s|(])/[A-Za-z]", text)
