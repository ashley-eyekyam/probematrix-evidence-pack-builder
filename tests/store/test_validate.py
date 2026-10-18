"""The workspace store: validate-on-write refusal, path rules, manifest ordering, recovery and
guarded state loading (WS-06, WS-08, D-09, D-19).

Everything runs in-process against folders under ``tmp_path``. Journals for the recovery tests
are built by hand so each crash shape is exact.
"""

import json
import os

import pytest
from epb import __version__, fsio, state, txn
from epb.errors import EpbError
from epb.state import STATE_FILE, load_state, new_state


def _tree_hashes(root):
    """Every file under ``root`` with its sha256, as a dict keyed by relative POSIX path."""
    return {
        path.relative_to(root).as_posix(): fsio.sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _chunk_plan():
    return {
        "schema_version": 1,
        "chunks": [
            {
                "chunk_id": "S001.c001",
                "src_id": "S001",
                "version": 1,
                "section_path": ["Synthetic heading"],
                "seg_ids": ["S001-p001"],
                "est_tokens": 100,
                "overlap_from": None,
            }
        ],
    }


@pytest.fixture
def case(tmp_path):
    root = tmp_path / "case"
    (root / ".epb" / "tmp").mkdir(parents=True)
    (root / "inputs").mkdir()
    (root / "inputs" / "report.txt").write_text("synthetic input\n", encoding="utf-8")
    return root


def _journal(case_root, txn_id, blobs, *, committed=True):
    """Build ``.epb/tmp/txn-<id>/`` by hand: one tmp file per blob and, when ``committed``,
    a manifest. Returns the folder and the manifest entries."""
    txn_dir = case_root / txn.TMP_DIR / f"txn-{txn_id}"
    txn_dir.mkdir(parents=True)
    entries = []
    for index, (final, data) in enumerate(blobs):
        name = f"{index:04d}"
        (txn_dir / name).write_bytes(data)
        entries.append({"tmp": name, "final": final, "sha256": fsio.sha256_bytes(data)})
    if committed:
        manifest = {"schema_version": 1, "txn": txn_id, "command": "test", "entries": entries}
        (txn_dir / txn.MANIFEST).write_bytes(fsio.json_bytes(manifest))
    return txn_dir, entries


# --- validate on write (WS-08) -----------------------------------------------------------


def test_set_state_with_two_problems_is_refused(case):
    before = _tree_hashes(case)
    bad = new_state(__version__)
    bad["counters"]["evidence"] = -1
    bad["plugin_version"] = ""
    transaction = txn.Transaction(case, "test")
    with pytest.raises(EpbError) as caught:
        transaction.set_state(bad)
    error = caught.value
    assert error.code == "RECORD_INVALID"
    assert error.exit_code == 4
    pointers = [issue["pointer"] for issue in error.data["issues"]]
    assert pointers == ["/counters/evidence", "/plugin_version"]
    for issue in error.data["issues"]:
        assert issue["pointer"] in error.message
    assert transaction.commit() is None
    assert _tree_hashes(case) == before


def test_invalid_record_never_reaches_disk(case):
    before = _tree_hashes(case)
    plan = _chunk_plan()
    plan["chunks"][0]["seg_ids"] = []
    transaction = txn.Transaction(case, "test")
    with pytest.raises(EpbError) as caught:
        transaction.stage_json(".epb/ledger/chunks.json", plan, "chunks")
    assert caught.value.code == "RECORD_INVALID"
    assert transaction.staged_paths == []
    assert _tree_hashes(case) == before


def test_empty_commit_writes_nothing(tmp_path):
    root = tmp_path / "bare"
    root.mkdir()
    assert txn.Transaction(root, "test").commit() is None
    assert list(root.iterdir()) == []


# --- path rules ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel",
    [
        "inputs/a.txt",
        "../x",
        ".epb/../../x",
        "outputs/../inputs/a.txt",
        ".epb\\a.json",
        "notes.md",
        "",
        STATE_FILE,
    ],
)
def test_forbidden_paths_are_refused_before_staging(case, rel):
    transaction = txn.Transaction(case, "test")
    with pytest.raises(EpbError) as caught:
        transaction.stage_text(rel, "x")
    assert caught.value.code == "INTERNAL_ERROR"
    assert transaction.staged_paths == []


def test_absolute_path_is_refused(case):
    transaction = txn.Transaction(case, "test")
    absolute = (case / ".epb" / "a.json").as_posix()
    with pytest.raises(EpbError) as caught:
        transaction.stage_json(absolute, _chunk_plan(), "chunks")
    assert caught.value.code == "INTERNAL_ERROR"
    assert transaction.staged_paths == []


def test_same_path_twice_is_refused(case):
    transaction = txn.Transaction(case, "test").stage_text("INDEX.md", "a")
    with pytest.raises(EpbError) as caught:
        transaction.stage_text("INDEX.md", "b")
    assert caught.value.code == "INTERNAL_ERROR"
    assert transaction.staged_paths == ["INDEX.md"]


@pytest.mark.parametrize("rel", ["INDEX.md", ".epb/ledger/chunks.json", "outputs/pack.xlsx"])
def test_allowed_paths(case, rel):
    transaction = txn.Transaction(case, "test")
    transaction.stage_text(rel, "x")
    assert transaction.staged_paths == [rel]


# --- ordering (WS-06) ---------------------------------------------------------------------


def test_manifest_and_apply_order_put_state_last(case, monkeypatch):
    applied = []
    manifests = []
    original = fsio.replace_with_retry

    def recording(src, dst, **kwargs):
        if not manifests:
            manifests.append(fsio.read_json(os.path.join(os.path.dirname(src), txn.MANIFEST)))
        applied.append(os.path.relpath(dst, case).replace(os.sep, "/"))
        return original(src, dst, **kwargs)

    monkeypatch.setattr(fsio, "replace_with_retry", recording)
    transaction = (
        txn.Transaction(case, "test")
        .stage_json(".epb/a.json", _chunk_plan(), "chunks")
        .stage_text("INDEX.md", "# Index\n")
        .set_state(new_state(__version__))
    )
    expected = [".epb/a.json", "INDEX.md", STATE_FILE]
    assert transaction.staged_paths == expected
    txn_id = transaction.commit()

    assert txn_id is not None
    manifest = manifests[0]
    assert manifest["schema_version"] == 1
    assert manifest["txn"] == txn_id
    assert [entry["final"] for entry in manifest["entries"]] == expected
    assert [entry["tmp"] for entry in manifest["entries"]] == ["0000", "0001", "0002"]
    assert applied == expected
    assert list((case / txn.TMP_DIR).iterdir()) == []
    written = json.loads((case / STATE_FILE).read_text(encoding="utf-8"))
    assert written["last_txn"]["id"] == txn_id


def test_json_bytes_is_deterministic():
    first = {"b": 1, "a": {"y": "Zürich", "x": [3, 1]}}
    second = {"a": {"x": [3, 1], "y": "Zürich"}, "b": 1}
    assert fsio.json_bytes(first) == fsio.json_bytes(second)
    data = fsio.json_bytes(first)
    assert data.endswith(b"\n")
    assert "Zürich".encode() in data
    assert data.startswith(b'{\n  "a"')


# --- recovery (WS-06) ---------------------------------------------------------------------


def test_recover_rolls_forward_idempotently(case):
    applied_data = b"already applied\n"
    pending_data = b"still pending\n"
    txn_dir, _ = _journal(
        case,
        "20261018T093000Z-1-abcdef",
        [(".epb/applied.json", applied_data), (".epb/pending.json", pending_data)],
    )
    # Entry 0 was applied before the crash: its tmp is gone and the final matches.
    os.replace(txn_dir / "0000", case / ".epb" / "applied.json")

    assert txn.pending_journals(case) == ["20261018T093000Z-1-abcdef"]
    assert txn.recover(case) == ["20261018T093000Z-1-abcdef"]
    assert (case / ".epb" / "applied.json").read_bytes() == applied_data
    assert (case / ".epb" / "pending.json").read_bytes() == pending_data
    assert not txn_dir.exists()
    assert txn.pending_journals(case) == []

    after = _tree_hashes(case)
    assert txn.recover(case) == []
    assert _tree_hashes(case) == after


def test_recover_discards_uncommitted_journal(case):
    txn_dir, _ = _journal(
        case,
        "20261018T093000Z-1-123456",
        [(".epb/never.json", b"never\n")],
        committed=False,
    )
    assert txn.pending_journals(case) == []
    assert txn.recover(case) == []
    assert not txn_dir.exists()
    assert not (case / ".epb" / "never.json").exists()


def test_recover_removes_stray_manifest_tmp(case):
    txn_dir, _ = _journal(
        case,
        "20261018T093000Z-1-654321",
        [(".epb/never.json", b"never\n")],
        committed=False,
    )
    (txn_dir / txn.MANIFEST_TMP).write_bytes(b'{"half": ')
    assert txn.recover(case) == []
    assert not txn_dir.exists()
    assert not (case / ".epb" / "never.json").exists()


def test_recover_refuses_a_missing_blob_with_a_different_final(case):
    txn_dir, _ = _journal(
        case,
        "20261018T093000Z-1-0a0b0c",
        [(".epb/lost.json", b"journalled\n")],
    )
    (txn_dir / "0000").unlink()
    (case / ".epb" / "lost.json").write_bytes(b"something else\n")
    with pytest.raises(EpbError) as caught:
        txn.recover(case)
    assert caught.value.code == "STATE_INVALID"
    assert caught.value.exit_code == 4


def test_recover_refuses_an_unreadable_manifest(case):
    txn_dir, _ = _journal(case, "20261018T093000Z-1-0d0e0f", [(".epb/x.json", b"x\n")])
    (txn_dir / txn.MANIFEST).write_bytes(b"not json")
    with pytest.raises(EpbError) as caught:
        txn.recover(case)
    assert caught.value.code == "STATE_INVALID"
    assert txn_dir.name in caught.value.message
    assert txn_dir.exists()


# --- guarded state loading (D-09, D-19) ---------------------------------------------------


def _write_state(case_root, payload):
    path = case_root / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_bytes(fsio.json_bytes(payload))


def test_load_state_returns_valid_state(case):
    _write_state(case, new_state(__version__))
    assert load_state(case) == new_state(__version__)


def test_load_state_missing_is_not_a_workspace(tmp_path):
    with pytest.raises(EpbError) as caught:
        load_state(tmp_path)
    assert caught.value.code == "NOT_A_WORKSPACE"
    assert caught.value.exit_code == 2
    assert "epb init" in caught.value.hint


@pytest.mark.parametrize(
    "payload",
    [b"{not json", b"\xff\xfe\x00", b"[1, 2]", b'{"schema_version": "1"}'],
    ids=["bad-json", "bad-utf8", "not-object", "string-version"],
)
def test_load_state_unreadable_is_state_invalid(case, payload):
    _write_state(case, payload)
    with pytest.raises(EpbError) as caught:
        load_state(case)
    error = caught.value
    assert error.code == "STATE_INVALID"
    assert error.exit_code == 4
    assert "damaged" in error.message
    assert "Restore .epb/state.json" in error.hint
    assert "Do not edit it by hand" in error.hint


def test_load_state_schema_violation_is_state_invalid(case):
    bad = new_state(__version__)
    bad["counters"]["tag"] = -5
    _write_state(case, bad)
    with pytest.raises(EpbError) as caught:
        load_state(case)
    assert caught.value.code == "STATE_INVALID"
    assert [issue["pointer"] for issue in caught.value.data["issues"]] == ["/counters/tag"]


def test_load_state_too_new(case):
    newer = new_state(__version__)
    newer["schema_version"] = 99
    _write_state(case, newer)
    with pytest.raises(EpbError) as caught:
        load_state(case)
    assert caught.value.code == "WORKSPACE_TOO_NEW"
    assert caught.value.exit_code == 4
    assert "newer version of the plugin" in caught.value.message


def test_load_state_returns_older_state_unvalidated(case, monkeypatch):
    monkeypatch.setattr(state, "SCHEMA_VERSION", 2)
    older = {"schema_version": 1, "an_old_field": True}
    _write_state(case, older)
    assert load_state(case) == older
