"""The WS-03 change corpus: new versions, renames, copies, removals, restores, swaps and the
content-wins move (design §7.1, research Pattern 4 and Q4).

Every fixture is synthetic. Scans run in-process through the ``cli`` fixture; the
classify-level cases call ``classify`` directly with hand-built fingerprints and records.
"""

import copy
import hashlib
import json
import os
import unicodedata

import pytest
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


# --- the WS-03 corpus -------------------------------------------------------------------------


def _source_files(case):
    return sorted(path.name for path in (case / ".epb" / "sources").glob("*.json"))


def _scan_checked(cli, case):
    """``scan --json`` that also checks no source record was deleted and every record is valid."""
    before = _source_files(case) if (case / ".epb" / "sources").is_dir() else []
    envelope = _scan(cli, case)
    after = _source_files(case)
    assert set(before) <= set(after), f"source records deleted: {set(before) - set(after)}"
    for name in after:
        record = json.loads((case / ".epb" / "sources" / name).read_text("utf-8"))
        assert schema.validate(record, "source") == [], name
    run_id = envelope["data"]["run"]
    if run_id is not None:
        assert schema.validate(_run(case, run_id), "run") == []
    return envelope


def _codes(envelope):
    return [item["code"] for item in envelope["warnings"]]


def _owners(case):
    return {rel: entry["src_id"] for rel, entry in _state(case)["fingerprints"].items()}


def test_rename_keeps_the_source(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    _scan_checked(cli, case_dir)
    (case_dir / "inputs/sub").mkdir()
    (case_dir / "inputs/a.txt").rename(case_dir / "inputs/sub/a.txt")
    envelope = _scan_checked(cli, case_dir)
    data = envelope["data"]
    assert data["renamed"] == [{"src_id": "S001", "from": "inputs/a.txt", "to": "inputs/sub/a.txt"}]
    assert data["new"] == [] and data["removed"] == [] and data["new_versions"] == []
    assert _record(case_dir, "S001")["paths"] == ["inputs/sub/a.txt"]
    assert _state(case_dir)["counters"]["source"] == 1
    assert _owners(case_dir) == {"inputs/sub/a.txt": "S001"}


def test_copy_of_an_existing_source_adds_a_path(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    _scan_checked(cli, case_dir)
    _put(case_dir, "inputs/copy.txt", b"synthetic alpha")
    data = _scan_checked(cli, case_dir)["data"]
    assert data["duplicates"] == [{"src_id": "S001", "path": "inputs/copy.txt"}]
    assert data["new"] == []
    assert _record(case_dir, "S001")["paths"] == ["inputs/a.txt", "inputs/copy.txt"]
    assert _state(case_dir)["counters"]["source"] == 1


def test_deleted_input_is_marked_removed_and_kept(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    _put(case_dir, "inputs/b.txt", b"synthetic bravo")
    _scan_checked(cli, case_dir)
    (case_dir / "inputs/b.txt").unlink()
    envelope = _scan_checked(cli, case_dir)
    assert envelope["data"]["removed"] == ["S002"]
    record = _record(case_dir, "S002")
    assert record["presence"] == "removed from folder"
    assert record["paths"] == []
    assert record["versions"][-1]["paths"] == ["inputs/b.txt"]
    removed = [item for item in envelope["warnings"] if item["code"] == "INPUT_REMOVED"]
    assert len(removed) == 1
    assert removed[0]["message"] == (
        "inputs/b.txt is no longer in inputs/. Its record is kept, and anything already "
        "built from it stays."
    )
    issues = _section(_index(case_dir), 5)
    assert "S002 (inputs/b.txt) was removed from the folder" in issues
    assert "inputs/b.txt" not in _owners(case_dir)


def test_all_removed_then_one_restored(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    _put(case_dir, "inputs/b.txt", b"synthetic bravo")
    _scan_checked(cli, case_dir)
    for name in ("a.txt", "b.txt"):
        (case_dir / "inputs" / name).unlink()
    gone = _scan_checked(cli, case_dir)
    assert gone["data"]["changed"] is True
    assert gone["data"]["removed"] == ["S001", "S002"]
    assert _codes(gone).count("INPUT_REMOVED") == 2
    assert _state(case_dir)["fingerprints"] == {}
    for src_id in ("S001", "S002"):
        assert _record(case_dir, src_id)["presence"] == "removed from folder"

    _put(case_dir, "inputs/back/b.txt", b"synthetic bravo")
    back = _scan_checked(cli, case_dir)
    assert back["data"]["restored"] == ["S002"]
    assert back["data"]["new"] == []
    assert _record(case_dir, "S002")["presence"] == "present"
    assert _record(case_dir, "S002")["paths"] == ["inputs/back/b.txt"]
    assert _record(case_dir, "S001")["presence"] == "removed from folder"
    assert _state(case_dir)["counters"]["source"] == 2


def test_swapped_contents_swap_paths(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    _put(case_dir, "inputs/b.txt", b"synthetic bravo")
    _scan_checked(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic bravo")
    _put(case_dir, "inputs/b.txt", b"synthetic alpha")
    data = _scan_checked(cli, case_dir)["data"]
    assert data["new"] == [] and data["removed"] == [] and data["new_versions"] == []
    assert data["renamed"] == [
        {"src_id": "S001", "from": "inputs/a.txt", "to": "inputs/b.txt"},
        {"src_id": "S002", "from": "inputs/b.txt", "to": "inputs/a.txt"},
    ]
    assert _record(case_dir, "S001")["paths"] == ["inputs/b.txt"]
    assert _record(case_dir, "S002")["paths"] == ["inputs/a.txt"]
    assert _owners(case_dir) == {"inputs/a.txt": "S002", "inputs/b.txt": "S001"}
    assert _state(case_dir)["counters"]["source"] == 2


def test_content_wins_moves_the_path(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    _put(case_dir, "inputs/b.txt", b"synthetic bravo")
    _scan_checked(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic bravo")
    envelope = _scan_checked(cli, case_dir)
    data = envelope["data"]
    assert data["moved"] == [{"path": "inputs/a.txt", "from_src": "S001", "to_src": "S002"}]
    assert data["duplicates"] == [{"src_id": "S002", "path": "inputs/a.txt"}]
    assert data["removed"] == ["S001"]
    assert data["new"] == [] and data["new_versions"] == []
    assert _record(case_dir, "S002")["paths"] == ["inputs/a.txt", "inputs/b.txt"]
    assert _record(case_dir, "S001")["presence"] == "removed from folder"
    assert "INPUT_REMOVED" in _codes(envelope)

    _put(case_dir, "inputs/c.txt", b"synthetic charlie")  # any change, to see the human report
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    human = _scan_human(cli, case_dir)
    assert "S001 inputs/a.txt: back in the folder" in human.stdout


def test_content_wins_is_reported_in_plain_words(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    _put(case_dir, "inputs/b.txt", b"synthetic bravo")
    _scan_checked(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic bravo")
    human = _scan_human(cli, case_dir)
    assert (
        "S002 inputs/a.txt: now holds the same content as inputs/b.txt, so it moved from "
        "S001 to S002"
    ) in human.stdout
    assert "S001 inputs/a.txt: its content is no longer in the folder" in human.stdout


def test_duplicate_split_gives_the_edited_copy_a_new_source(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/x.txt", b"synthetic shared log")
    _put(case_dir, "inputs/y.txt", b"synthetic shared log")
    assert _scan_checked(cli, case_dir)["data"]["new"] == ["S001"]
    _put(case_dir, "inputs/y.txt", b"synthetic shared log, annotated")
    human = _scan_human(cli, case_dir)
    assert "S002 inputs/y.txt: new input; it was a copy of S001, and the copies now differ" in (
        human.stdout
    )
    run = _run(case_dir, "003")
    assert run["scan"]["new"] == ["S002"]
    assert run["scan"]["moved"] == [{"path": "inputs/y.txt", "from_src": "S001", "to_src": "S002"}]
    assert run["scan"]["removed"] == [] and run["scan"]["new_versions"] == []
    assert _record(case_dir, "S001")["paths"] == ["inputs/x.txt"]
    assert _record(case_dir, "S001")["current_version"] == 1
    assert _record(case_dir, "S002")["paths"] == ["inputs/y.txt"]


def test_case_only_rename_is_a_rename(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/Report.pdf", PDF_V1)
    _scan_checked(cli, case_dir)
    (case_dir / "inputs/Report.pdf").rename(case_dir / "inputs/report.pdf")
    data = _scan_checked(cli, case_dir)["data"]
    assert data["renamed"] == [
        {"src_id": "S001", "from": "inputs/Report.pdf", "to": "inputs/report.pdf"}
    ]
    assert data["new"] == [] and data["removed"] == []
    assert _record(case_dir, "S001")["paths"] == ["inputs/report.pdf"]


NFC_NAME = unicodedata.normalize("NFC", "inputs/café-log.txt")
NFD_NAME = unicodedata.normalize("NFD", "inputs/café-log.txt")


def test_nfd_and_nfc_spellings_are_one_path_key(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, NFD_NAME, b"synthetic cafe log")
    first = _scan_checked(cli, case_dir)
    assert first["data"]["new"] == ["S001"]
    assert _record(case_dir, "S001")["paths"] == [NFC_NAME]
    assert list(_state(case_dir)["fingerprints"]) == [NFC_NAME]
    os.rename(case_dir / NFD_NAME, case_dir / NFC_NAME)
    again = _scan_checked(cli, case_dir)
    assert again["data"]["changed"] is False
    assert again["data"]["renamed"] == []


def test_two_spellings_of_one_name_are_refused(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, NFD_NAME, b"synthetic cafe log, first file")
    _put(case_dir, NFC_NAME, b"synthetic cafe log, second file")
    if len(list((case_dir / "inputs").iterdir())) != 2:
        pytest.skip("this file system stores both spellings as one name")
    before = sorted(path.name for path in (case_dir / ".epb").rglob("*"))
    result = cli(["scan", "--json", "--case", str(case_dir)])
    assert result.exit_code == 2, result.stdout
    error = result.envelope["errors"][0]
    assert error["code"] == "BAD_ARGUMENT"
    assert NFC_NAME in error["message"]
    assert "two different ways" in error["message"]
    assert sorted(path.name for path in (case_dir / ".epb").rglob("*")) == before
    assert not (case_dir / ".epb" / "sources").exists() or _source_files(case_dir) == []


def test_reverted_content_is_new_content_not_the_old_version(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/report.pdf", PDF_V1)
    _scan_checked(cli, case_dir)
    _put(case_dir, "inputs/report.pdf", PDF_V2)
    _scan_checked(cli, case_dir)
    _put(case_dir, "inputs/report.pdf", PDF_V1)  # back to the bytes of version 1
    data = _scan_checked(cli, case_dir)["data"]
    assert data["new_versions"] == [{"src_id": "S001", "version": 3}]
    assert data["restored"] == [] and data["new"] == []
    record = _record(case_dir, "S001")
    assert record["current_version"] == 3
    assert record["versions"][2]["sha256"] == record["versions"][0]["sha256"]
    assert "S001v3" in _index(case_dir)


# --- several changes at once: fixed order, no ID reuse ----------------------------------------


def _mixed_case(cli, case):
    _init(cli, case)
    for name in ("a", "b", "c", "d"):
        _put(case, f"inputs/{name}.txt", f"synthetic {name} original".encode())
    _scan_checked(cli, case)
    _put(case, "inputs/a.txt", b"synthetic a edited")  # new version of S001
    (case / "inputs/sub").mkdir()
    (case / "inputs/b.txt").rename(case / "inputs/sub/b.txt")  # rename of S002
    (case / "inputs/d.txt").unlink()  # S004 removed
    _put(case, "inputs/e.txt", b"synthetic e new")  # new source
    return _scan_checked(cli, case)


def _comparable(case, envelope):
    data = {key: value for key, value in envelope["data"].items()}
    records = {}
    for name in _source_files(case):
        record = json.loads((case / ".epb" / "sources" / name).read_text("utf-8"))
        records[record["src_id"]] = (
            record["current_version"],
            record["paths"],
            record["presence"],
            [(v["version"], v["sha256"], v["paths"]) for v in record["versions"]],
        )
    return data, records, _owners(case), envelope["warnings"]


def test_several_changes_resolve_in_a_fixed_order(cli, tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    one = _mixed_case(cli, first)
    two = _mixed_case(cli, second)
    data = one["data"]
    assert data["new_versions"] == [{"src_id": "S001", "version": 2}]
    assert data["renamed"] == [{"src_id": "S002", "from": "inputs/b.txt", "to": "inputs/sub/b.txt"}]
    assert data["removed"] == ["S004"]
    assert data["new"] == ["S005"]
    assert _comparable(first, one) == _comparable(second, two)


def test_a_removed_id_is_never_reused(cli, case_dir):
    _init(cli, case_dir)
    _put(case_dir, "inputs/a.txt", b"synthetic alpha")
    _put(case_dir, "inputs/b.txt", b"synthetic bravo")
    _scan_checked(cli, case_dir)
    (case_dir / "inputs/b.txt").unlink()
    _scan_checked(cli, case_dir)
    _put(case_dir, "inputs/c.txt", b"synthetic charlie")
    data = _scan_checked(cli, case_dir)["data"]
    assert data["new"] == ["S003"]
    assert _source_files(case_dir) == ["S001.json", "S002.json", "S003.json"]
    assert _state(case_dir)["counters"]["source"] == 3


# --- classify directly ------------------------------------------------------------------------


def _fact(rel, data):
    from epb.sources.scan import FileFact

    return FileFact(
        rel=rel,
        size=len(data),
        mtime_ns=1_700_000_000_000_000_000,
        sha256=hashlib.sha256(data).hexdigest(),
        mime="text/plain",
        mime_mismatch=None,
    )


def _first_scan(files):
    from epb.sources.classify import classify

    return classify({}, [], files, run_id="002", source_counter=0)


def test_classify_orders_new_content_by_first_path():
    plan = _first_scan(
        [
            _fact("inputs/z.txt", b"zulu"),
            _fact("inputs/m.txt", b"mike"),
            _fact("inputs/a.txt", b"z"),
        ]
    )
    assert plan.new == ["S001", "S002", "S003"]
    assert [record["paths"] for record in plan.sources] == [
        ["inputs/a.txt"],
        ["inputs/m.txt"],
        ["inputs/z.txt"],
    ]


def test_classify_leaves_its_arguments_unchanged():
    from epb.sources.classify import classify

    base = _first_scan([_fact("inputs/a.txt", b"alpha"), _fact("inputs/b.txt", b"bravo")])
    previous = copy.deepcopy(base.fingerprints)
    sources = copy.deepcopy(base.sources)
    files = [_fact("inputs/a.txt", b"alpha 2"), _fact("inputs/c.txt", b"bravo")]
    plan = classify(previous, sources, files, run_id="003", source_counter=2)
    assert previous == base.fingerprints
    assert sources == base.sources
    assert plan.new_versions == [{"src_id": "S001", "version": 2}]
    assert plan.renamed == [{"src_id": "S002", "from": "inputs/b.txt", "to": "inputs/c.txt"}]


def test_classify_never_gives_one_path_to_two_sources():
    """Two records that claim the same current content (a damaged or hand-edited folder) must
    not both take its paths: the lower ID keeps them and the other is not given them."""
    from epb.sources.classify import classify

    base = _first_scan([_fact("inputs/a.txt", b"alpha"), _fact("inputs/b.txt", b"bravo")])
    sources = copy.deepcopy(base.sources)
    sources[1]["versions"][0]["sha256"] = sources[0]["versions"][0]["sha256"]
    plan = classify(
        base.fingerprints,
        sources,
        [_fact("inputs/a.txt", b"alpha")],
        run_id="003",
        source_counter=2,
    )
    owners = {}
    for record in plan.sources:
        for rel in record["paths"]:
            assert rel not in owners, f"{rel} given to {owners.get(rel)} and {record['src_id']}"
            owners[rel] = record["src_id"]
    assert owners == {"inputs/a.txt": "S001"}
    assert plan.fingerprints["inputs/a.txt"]["src_id"] == "S001"
