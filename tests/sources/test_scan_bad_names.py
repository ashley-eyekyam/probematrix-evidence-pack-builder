"""``epb scan`` and names that are not valid text (verification gap 2, review CR-01, WS-02).

A file or folder whose name is not valid UTF-8 (for example from unzipping a ZIP made on an
older Windows computer, or a copy from an old shared drive) must not stop the scan of the whole
case. It is skipped as ``bad-name`` under a readable path, and the rest is inventoried.

Every fixture is synthetic. Every scan here checks that ``inputs/`` is left exactly as it was,
comparing raw name bytes so the check itself never decodes a name.
"""

import hashlib
import json
import os
import stat
import sys

import pytest
from epb import runs, schema
from epb.state import STATE_FILE

pytestmark = [
    pytest.mark.skipif(os.name == "nt", reason="raw byte file names are POSIX-only here"),
    pytest.mark.skipif(
        sys.getfilesystemencoding().lower().replace("-", "") != "utf8",
        reason="the file system encoding is not UTF-8",
    ),
]

INIT = [
    "init",
    "--title",
    "Synthetic Valve Trip",
    "--slug",
    "synthetic-valve-trip",
    "--prefix",
    "SVT",
    "--timezone",
    "UTC",
    "--json",
]
OK_BYTES = b"Synthetic shift notes: valve V-1 closed at 10:05.\n"
BAD_BYTES = b"Synthetic notes copied from an old shared drive.\n"
BAD_FILE = b"bad\xffname.txt"
BAD_FILE_SHOWN = "inputs/bad�name.txt"
BAD_NAME_LINE = (
    f"- {BAD_FILE_SHOWN} was skipped: it is named with characters that are not valid text; "
    "rename it, then scan again."
)
SECTION_TITLES = (
    "1. Case",
    "2. What to import where",
    "3. Inputs",
    "4. Outputs",
    "5. Open issues",
    "6. Run history",
)


# --- helpers ----------------------------------------------------------------------------------


def _init(run_epb, case_dir):
    proc = run_epb(INIT, cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def _put(case_dir, rel, data):
    path = case_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _make_raw(folder, raw, kind="file", *, data=BAD_BYTES, target=None) -> bytes:
    """Create an entry named by the raw bytes ``raw`` in ``folder`` and return its bytes path.

    Skips the test, naming the OS error, when the file system refuses such a name (macOS APFS
    and some ZFS setups do)."""
    path = os.fsencode(folder) + b"/" + raw
    try:
        if kind == "file":
            with open(path, "wb") as handle:
                handle.write(data)
        elif kind == "folder":
            os.mkdir(path)
        elif kind == "link":
            os.symlink(os.fsencode(target), path)
        elif kind == "pipe":
            os.mkfifo(path)
        else:
            raise ValueError(kind)
    except OSError as error:
        pytest.skip(f"the file system refused a name that is not valid UTF-8: {error!r}")
    return path


def _raw_tree(folder) -> list:
    """Every entry under ``folder`` as raw name bytes, with the SHA-256 of each regular file.

    Never decodes a name, never follows a link and never opens a pipe."""
    root = os.fsencode(folder)
    found = []
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        for name in sorted(dirnames + filenames):
            path = os.path.join(current, name)
            info = os.lstat(path)
            digest = None
            if stat.S_ISREG(info.st_mode):
                with open(path, "rb") as handle:
                    digest = hashlib.sha256(handle.read()).hexdigest()
            found.append((os.path.relpath(path, root), stat.S_IFMT(info.st_mode), digest))
    return sorted(found)


def _scan(run_epb, case_dir, *, timeout=120):
    """Run ``scan --json``, check it left inputs/ untouched, and return the envelope."""
    before = _raw_tree(case_dir / "inputs")
    proc = run_epb(["scan", "--json"], cwd=case_dir, timeout=timeout)
    assert _raw_tree(case_dir / "inputs") == before, "scan changed inputs/"
    assert proc.stdout, proc.stderr
    envelope = json.loads(proc.stdout)
    envelope["_exit"] = proc.returncode
    envelope["_stderr"] = proc.stderr
    return envelope


def _assert_clean(envelope):
    assert envelope["_exit"] == 0, envelope
    assert envelope["ok"] is True, envelope
    assert envelope["errors"] == [], envelope
    assert "INTERNAL_ERROR" not in json.dumps(envelope), envelope


def _state(case_dir):
    return json.loads((case_dir / STATE_FILE).read_text(encoding="utf-8"))


def _record(case_dir, src_id):
    path = case_dir / ".epb" / "sources" / f"{src_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _index(case_dir) -> str:
    return (case_dir / "INDEX.md").read_text(encoding="utf-8")


def _sections(text):
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


# --- tracer: a bad-named file is skipped and the rest is scanned ------------------------------


def test_scan_skips_a_file_whose_name_is_not_valid_text(run_epb, case_dir):
    _init(run_epb, case_dir)
    _put(case_dir, "inputs/ok.txt", OK_BYTES)
    _make_raw(case_dir / "inputs", BAD_FILE)

    envelope = _scan(run_epb, case_dir)
    _assert_clean(envelope)
    data = envelope["data"]
    assert data["new"] == ["S001"]
    assert _record(case_dir, "S001")["paths"] == ["inputs/ok.txt"]
    assert data["ignored"] == [{"path": BAD_FILE_SHOWN, "reason": "bad-name"}]
    assert sorted(_state(case_dir)["fingerprints"]) == ["inputs/ok.txt"]

    record = json.loads((case_dir / runs.run_json_path("002")).read_text(encoding="utf-8"))
    assert schema.validate(record, "run") == []
    assert record["scan"]["ignored"] == data["ignored"]

    text = _index(case_dir)
    assert BAD_NAME_LINE in _sections(text)["5. Open issues"].splitlines()
    headings = [line for line in text.split("\n") if line.startswith("## ")]
    assert headings == [f"## {title}" for title in SECTION_TITLES]


def test_run_schema_accepts_the_bad_name_reason():
    from epb import __version__, fsio
    from epb.state import new_state

    def record_with(reason):
        scan = {
            "new": [],
            "new_versions": [],
            "renamed": [],
            "duplicates": [],
            "moved": [],
            "removed": [],
            "restored": [],
            "ignored": [{"path": "inputs/x�.txt", "reason": reason}],
            "mime_mismatches": [],
            "sidecars": [],
            "orphan_sidecars": [],
        }
        _, record = runs.new_run(
            new_state(__version__),
            "scan",
            started_at=fsio.utc_now_iso(),
            summary="Took stock.",
            scan=scan,
        )
        return record

    assert schema.validate(record_with("bad-name"), "run") == []
    assert schema.validate(record_with("bad_name"), "run") != []
