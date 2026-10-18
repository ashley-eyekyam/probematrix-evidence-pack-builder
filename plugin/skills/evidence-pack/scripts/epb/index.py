"""``INDEX.md``: the plain-language summary of a case folder (WS-09, design §6.1, PF-04).

``render_index`` builds the whole file from the case settings, the state, the source records
and the run records. It is rewritten inside the same transaction as ``state.json`` by every
command that changes the case folder, so it never disagrees with the state.

The file has a title, a short note and six sections in a fixed order, one provider each.
A section with nothing to show reads ``none yet``. Every path is shown relative to the case
folder; no absolute path, home folder or account name is ever written.

The "What to import where" section ends with one task-list line per workbook,
``- [ ] Imported: <file>`` (``- [x]`` once imported). That form is fixed now so a later
version can read the user's ticks back (research Pattern 7).

Every value written into INDEX.md is first made single-line by ``_inline``, so no input name
or record field can add a heading or an Imported? line.
"""

import re
from dataclasses import dataclass, field

NONE_YET = "none yet"
INDEX_FILE = "INDEX.md"

NOTE = (
    "> This file is rewritten by the evidence pack builder every time it runs. "
    "Do not edit it, except to tick an Imported? box."
)
IMPORT_INSTRUCTION = (
    "Import the master into a new incident; import each delta, in order, into the same "
    "incident. Never re-import a file already imported."
)
PENDING_TEXT = "waiting for conversion (coming in a later version)"
REMOVED = "removed from folder"

# A short label for the file types people meet most; anything else shows its MIME type.
MIME_LABELS = {
    "application/pdf": "PDF",
    "application/msword": "Word document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word document",
    "application/vnd.ms-excel": "Excel workbook",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel workbook",
    "application/vnd.ms-powerpoint": "PowerPoint deck",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": (
        "PowerPoint deck"
    ),
    "application/vnd.oasis.opendocument.text": "OpenDocument text",
    "application/vnd.oasis.opendocument.spreadsheet": "OpenDocument spreadsheet",
    "application/rtf": "Rich text",
    "text/plain": "Text",
    "text/markdown": "Markdown",
    "text/csv": "CSV",
    "text/html": "Web page",
    "application/json": "JSON",
    "application/xml": "XML",
    "text/xml": "XML",
    "message/rfc822": "Email",
    "application/vnd.ms-outlook": "Outlook message",
    "image/jpeg": "JPEG image",
    "image/png": "PNG image",
    "image/gif": "GIF image",
    "image/tiff": "TIFF image",
    "image/heic": "HEIC image",
    "audio/wav": "WAV audio",
    "audio/x-wav": "WAV audio",
    "audio/mpeg": "MP3 audio",
    "audio/mp4": "M4A audio",
    "video/mp4": "MP4 video",
    "video/quicktime": "QuickTime video",
    "video/x-matroska": "MKV video",
    "application/zip": "ZIP archive",
    "application/x-7z-compressed": "7z archive",
    "application/gzip": "gzip archive",
    "application/x-ole-storage": "OLE2 file",
}

# C0 controls (tab and NUL included), DEL, C1 controls (NEL included) and the Unicode line and
# paragraph separators. ``str.splitlines()`` treats several of these as line boundaries.
_SINGLE_LINE = re.compile("[\x00-\x1f\x7f-\x9f\u2028\u2029]")
_RUN_TIME = re.compile(r"^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})")
_IGNORED_REASONS = {
    "link": "a link, which the plugin does not follow",
    "special": "not a regular file (for example a pipe or a device)",
}


@dataclass
class IndexInputs:
    """Everything ``render_index`` reads. ``sources`` and ``runs`` are lists of records."""

    case: dict
    state: dict
    sources: list = field(default_factory=list)
    runs: list = field(default_factory=list)


# --- small helpers ----------------------------------------------------------------------------


def _inline(value) -> str:
    """``value`` as text on one line: each control or separator character becomes one space."""
    return _SINGLE_LINE.sub(" ", str(value))


def _cell(value) -> str:
    """Text safe inside one Markdown table cell."""
    text = _inline(value)
    return text.replace("\\", "\\\\").replace("|", "\\|")


def _table(header, rows) -> str:
    lines = [
        "| " + " | ".join(header) + " |",
        "|" + "|".join(" --- " for _ in header) + "|",
    ]
    lines.extend("| " + " | ".join(_cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _when(timestamp) -> str:
    """``2026-10-17T10:00:00Z`` as ``2026-10-17 10:00 UTC``."""
    match = _RUN_TIME.match(timestamp or "")
    return f"{match.group(1)} {match.group(2)} UTC" if match else NONE_YET


def _size(size) -> str:
    if not isinstance(size, int):
        return NONE_YET
    if size < 1024:
        return f"{size} B"
    for unit in ("KB", "MB", "GB"):
        size /= 1024
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
    return f"{size:.1f} GB"  # not reached


def _run_number(run_id) -> int:
    try:
        return int(run_id)
    except (TypeError, ValueError):
        return -1


def _src_number(source) -> int:
    try:
        return int(str(source.get("src_id", ""))[1:])
    except ValueError:
        return -1


def _current_version(source) -> dict:
    """The ``versions`` entry for the source's current version (the last one otherwise)."""
    versions = source.get("versions") or [{}]
    for version in versions:
        if version.get("version") == source.get("current_version"):
            return version
    return versions[-1]


def _paths(source) -> list:
    """The source's paths, or its last known paths when it was removed from the folder."""
    paths = source.get("paths") or (source.get("versions") or [{}])[-1].get("paths") or []
    return sorted(paths)


def _path_text(source) -> str:
    return ", ".join(_paths(source)) or NONE_YET


def _note_target(source) -> str | None:
    from epb.sources.sidecars import orphan_target

    return orphan_target(source)


def display_id(source) -> str:
    """``S001`` for version 1 of a source and ``S004v2`` for version 2."""
    version = source.get("current_version") or 1
    src_id = source.get("src_id", "")
    return src_id if version == 1 else f"{src_id}v{version}"


def _status_text(source) -> str:
    if source.get("presence") == REMOVED:
        return REMOVED
    status = source.get("status") or NONE_YET
    return PENDING_TEXT if status == "pending" else status


def _type_label(mime) -> str:
    if not mime:
        return NONE_YET
    return MIME_LABELS.get(mime, mime)


def _latest_write(workbook) -> dict:
    writes = workbook.get("writes") or [{}]
    return writes[-1]


def _workbook_status(workbook) -> str:
    if workbook.get("status") == "imported":
        imported_at = workbook.get("imported_at") or ""
        return f"imported {imported_at[:10]}".strip()
    return workbook.get("status") or "draft"


def _tag_range(write) -> str:
    first, last = write.get("tag_first"), write.get("tag_last")
    if not first:
        return NONE_YET
    return first if not last or last == first else f"{first} to {last}"


def render_import_line(workbook) -> str:
    """The task-list line the user ticks once a workbook is imported into ProbeMatrix."""
    mark = "x" if workbook.get("status") == "imported" else " "
    return f"- [{mark}] Imported: {workbook['file']}"


# --- the six providers ------------------------------------------------------------------------


def case_header(inputs: IndexInputs) -> str:
    case, state = inputs.case, inputs.state
    prefix = case.get("id_prefix", "")
    runs = sorted(inputs.runs, key=lambda run: _run_number(run.get("run")))
    if runs:
        last = runs[-1]
        last_run = (
            f"Run {last.get('run')} · {_when(last.get('finished_at'))} · {last.get('command')}"
        )
    else:
        last_run = NONE_YET
    workbooks = state.get("workbooks") or []
    if workbooks:
        latest = workbooks[-1]
        pack = f"{latest.get('number')} ({latest.get('file')}, {_workbook_status(latest)})"
    else:
        pack = NONE_YET
    lines = [
        f"- Title: {case.get('title', '')}",
        f"- Slug: {case.get('slug', '')}",
        f"- ID prefix: {prefix} (evidence IDs look like EVD-{prefix}-001)",
        f"- Timezone: {case.get('timezone', '')}",
        f"- Plugin version: {state.get('plugin_version', '')}",
        f"- Last run: {last_run}",
        f"- Current pack version: {pack}",
    ]
    return "\n".join(lines)


def what_to_import(inputs: IndexInputs) -> str:
    workbooks = inputs.state.get("workbooks") or []
    if not workbooks:
        return NONE_YET
    rows = []
    for workbook in workbooks:
        write = _latest_write(workbook)
        rows.append(
            (
                workbook.get("file", ""),
                workbook.get("kind", ""),
                _workbook_status(workbook),
                write.get("item_count", 0),
                _tag_range(write),
            )
        )
    table = _table(("File", "Kind", "Status", "Items", "Evidence Tags"), rows)
    ticks = "\n".join(render_import_line(workbook) for workbook in workbooks)
    return f"{table}\n\n{IMPORT_INSTRUCTION}\n\n{ticks}"


def inputs_snapshot(inputs: IndexInputs) -> str:
    if not inputs.sources:
        return NONE_YET
    rows = []
    for source in sorted(inputs.sources, key=lambda item: (_paths(item), _src_number(item))):
        version = _current_version(source)
        sha = version.get("sha256") or ""
        rows.append(
            (
                display_id(source),
                _path_text(source),
                _type_label(version.get("mime")),
                _size(version.get("size")),
                sha[:12] or NONE_YET,
                f"Run {source['first_seen_run']}" if source.get("first_seen_run") else NONE_YET,
                (
                    f"Run {source['last_processed_run']}"
                    if source.get("last_processed_run")
                    else "not yet"
                ),
                _status_text(source),
                NONE_YET,
                NONE_YET,
                NONE_YET,
            )
        )
    header = (
        "ID",
        "Path",
        "Type",
        "Size",
        "SHA-256",
        "First seen",
        "Last processed",
        "Status",
        "Segments",
        "Claims",
        "Items",
    )
    return _table(header, rows)


def outputs_snapshot(inputs: IndexInputs) -> str:
    workbooks = inputs.state.get("workbooks") or []
    if not workbooks:
        return NONE_YET
    rows = [
        (workbook.get("file", ""), _latest_write(workbook).get("item_count", 0), NONE_YET)
        for workbook in workbooks
    ]
    return _table(("Workbook", "Items", "Inputs that contributed items"), rows)


def _latest_scan(runs) -> dict | None:
    scans = [run for run in runs if run.get("scan")]
    if not scans:
        return None
    return max(scans, key=lambda run: _run_number(run.get("run")))["scan"]


def open_issues(inputs: IndexInputs) -> str:
    issues = []
    for source in sorted(inputs.sources, key=_src_number):
        label = f"{_inline(display_id(source))} ({_inline(_path_text(source))})"
        if source.get("presence") == REMOVED:
            issues.append(f"- {label} was removed from the folder. Its record is kept.")
        mismatch = source.get("mime_mismatch")
        if mismatch:
            issues.append(
                f"- {label}: the content is {_inline(mismatch.get('by_content'))}, but the "
                f"file name suggests {_inline(mismatch.get('by_extension'))}. "
                "The content was used."
            )
        if (
            source.get("source_kind") == "sidecar"
            and not source.get("sidecar_of")
            and source.get("presence") != REMOVED
        ):
            target = _note_target(source)
            if target:
                issues.append(
                    f"- {label} is a note for {_inline(target)}, but that file is not in inputs/."
                )
            else:
                issues.append(f"- {label} is a note file with no matching input file.")
    scan = _latest_scan(inputs.runs)
    if scan:
        for entry in sorted(scan.get("ignored") or [], key=lambda item: item.get("path", "")):
            reason = _IGNORED_REASONS.get(entry.get("reason"))
            if reason:  # junk files such as .DS_Store are not issues
                issues.append(f"- {_inline(entry.get('path'))} was skipped: it is {reason}.")
    return "\n".join(issues) if issues else NONE_YET


def run_history(inputs: IndexInputs) -> str:
    if not inputs.runs:
        return NONE_YET
    lines = []
    for run in sorted(inputs.runs, key=lambda item: _run_number(item.get("run"))):
        lines.append(
            f"- Run {run.get('run')} · {_when(run.get('finished_at'))} · "
            f"{run.get('command')} · {run.get('summary', '')}"
        )
    return "\n".join(lines)


PROVIDERS = (
    ("1. Case", case_header),
    ("2. What to import where", what_to_import),
    ("3. Inputs", inputs_snapshot),
    ("4. Outputs", outputs_snapshot),
    ("5. Open issues", open_issues),
    ("6. Run history", run_history),
)
SECTION_TITLES = tuple(title for title, _ in PROVIDERS)


def render_index(inputs: IndexInputs) -> str:
    """The full text of ``INDEX.md``."""
    lines = [f"# {inputs.case.get('title', '')}", "", NOTE]
    for title, provider in PROVIDERS:
        body = provider(inputs).strip("\n") or NONE_YET
        lines.extend(["", f"## {title}", "", body])
    return "\n".join(lines) + "\n"
