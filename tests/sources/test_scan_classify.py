"""The WS-03 change corpus: new versions, renames, copies, removals, restores, swaps and the
content-wins move (design §7.1, research Pattern 4 and Q4).

Every fixture is synthetic. Scans run in-process through the ``cli`` fixture; the
classify-level cases call ``classify`` directly with hand-built fingerprints and records.
"""

import json

from epb import schema
from epb.state import STATE_FILE

INIT = [
    "init",
    "--title",
    "Synthetic Conveyor Stop",
    "--slug",
    "synthetic-conveyor-stop",
    "--prefix",
    "SCS",
    "--timezone",
    "UTC",
    "--json",
]
PDF_V1 = b"%PDF-1.4\n% synthetic inspection report, first draft\n%%EOF\n"
PDF_V2 = b"%PDF-1.4\n% synthetic inspection report, signed copy\n%%EOF\n"


# --- helpers ----------------------------------------------------------------------------------


def _init(cli, case):
    result = cli([*INIT, "--case", str(case)])
    assert result.exit_code == 0, result.stdout + result.stderr


def _put(case, rel, data):
    path = case / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _scan(cli, case):
    result = cli(["scan", "--json", "--case", str(case)])
    assert result.exit_code == 0, result.stdout + result.stderr
    return result.envelope


def _scan_human(cli, case):
    result = cli(["scan", "--case", str(case)])
    assert result.exit_code == 0, result.stdout + result.stderr
    return result


def _record(case, src_id):
    return json.loads((case / ".epb" / "sources" / f"{src_id}.json").read_text("utf-8"))


def _state(case):
    return json.loads((case / STATE_FILE).read_text(encoding="utf-8"))


def _run(case, run_id):
    return json.loads((case / ".epb" / "runs" / run_id / "run.json").read_text("utf-8"))


def _index(case):
    return (case / "INDEX.md").read_text(encoding="utf-8")


def _section(text, number):
    return text.split(f"## {number}.", 1)[1].split("\n## ", 1)[0]


# --- tracer: an edited input becomes S001v2 everywhere ----------------------------------------


def test_edited_input_becomes_a_new_version_everywhere(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/report.pdf", PDF_V1)
    first = _scan(cli, case_dir)
    assert first["data"]["new"] == ["S001"]

    _put(case_dir, "inputs/report.pdf", PDF_V2)
    human = _scan_human(cli, case_dir)
    assert "S001v2" in human.stdout
    assert "S001v2 inputs/report.pdf: new version (the file changed since run 002)" in (
        human.stdout
    )

    run = _run(case_dir, "003")
    assert schema.validate(run, "run") == []
    assert run["scan"]["new_versions"] == [{"src_id": "S001", "version": 2}]
    assert run["scan"]["new"] == []

    record = _record(case_dir, "S001")
    assert schema.validate(record, "source") == []
    assert record["current_version"] == 2
    assert [version["version"] for version in record["versions"]] == [1, 2]
    assert record["status"] == "pending"
    assert record["paths"] == ["inputs/report.pdf"]
    assert _state(case_dir)["counters"]["source"] == 1
    assert _state(case_dir)["fingerprints"]["inputs/report.pdf"]["version"] == 2

    text = _index(case_dir)
    assert "S001v2" in text
    assert "| S001v2 | inputs/report.pdf |" in _section(text, 3)


def test_new_version_envelope(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/report.pdf", PDF_V1)
    _scan(cli, case_dir)
    _put(case_dir, "inputs/report.pdf", PDF_V2)
    envelope = _scan(cli, case_dir)
    assert envelope["data"]["changed"] is True
    assert envelope["data"]["run"] == "003"
    assert envelope["data"]["new_versions"] == [{"src_id": "S001", "version": 2}]
    assert envelope["data"]["new"] == []
    assert envelope["data"]["sources_total"] == 1
