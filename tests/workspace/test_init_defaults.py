"""``epb init`` writes ``.epb/case.yaml`` with the case settings, in the same transaction as
``state.json``, and it reads back as exact text (WS-01, WS-08, D-15)."""

import json

from epb import casefile, schema
from epb.state import STATE_FILE

FULL_FLAGS = [
    "--title",
    "Acme Pump Trip",
    "--slug",
    "acme-pump-trip",
    "--prefix",
    "APT",
    "--timezone",
    "UTC",
]


def _envelope(proc):
    return json.loads(proc.stdout)


def test_init_writes_case_yaml_from_flags(run_epb, case_dir):
    proc = run_epb(["init", *FULL_FLAGS, "--json"], cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    envelope = _envelope(proc)
    assert envelope["data"]["created"] == [casefile.CASE_FILE, STATE_FILE]
    assert envelope["data"]["case"] == {
        "title": "Acme Pump Trip",
        "slug": "acme-pump-trip",
        "id_prefix": "APT",
        "timezone": "UTC",
    }

    case = casefile.load_case(case_dir)
    assert case["title"] == "Acme Pump Trip"
    assert case["slug"] == "acme-pump-trip"
    assert case["id_prefix"] == "APT"
    assert case["timezone"] == "UTC"
    assert case["draft_warning_days"] == "7"
    assert case["conflict_tolerance_seconds"] == "60"
    assert case["languages"] == ["en"]
    assert case["tags_extra"] == []
    assert schema.validate(case, "case") == []


def test_case_yaml_starts_with_text_schema_version(run_epb, case_dir):
    proc = run_epb(["init", *FULL_FLAGS, "--json"], cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (case_dir / casefile.CASE_FILE).read_text(encoding="utf-8")
    assert text.startswith("schema_version: '1'\n")


def test_human_message_names_the_title(run_epb, case_dir):
    proc = run_epb(["init", *FULL_FLAGS], cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "Case folder set up: Acme Pump Trip" in proc.stdout
