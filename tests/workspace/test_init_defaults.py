"""``epb init`` writes ``.epb/case.yaml`` with the case settings, in the same transaction as
``state.json``, and it reads back as exact text (WS-01, WS-08, D-15)."""

import argparse
import json
import re
import unicodedata

import pytest
from epb import casefile, schema, yamlio
from epb.errors import EpbError
from epb.state import STATE_FILE

SLUG_RE = r"[a-z0-9]+(-[a-z0-9]+)*"
PREFIX_RE = r"[A-Z][A-Z0-9]{1,5}"
TZ_ENV = {"TZ": "Asia/Kolkata"}

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
    created = envelope["data"]["created"]
    assert casefile.CASE_FILE in created
    assert created[-1] == STATE_FILE
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


# --- D-15 defaults ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("folder", "slug"),
    [
        ("Acme Pump Trip 2026", "acme-pump-trip-2026"),
        ("Ölpumpe – Störfall", "olpumpe-storfall"),
        ("Ölpumpe – Störfall 2026", "olpumpe-storfall-2026"),
        ("CON", "con-case"),
        ("com1", "com1-case"),
        ("LPT9", "lpt9-case"),
        ("", "case"),
        ("###", "case"),
        ("  --Acme__Trip--  ", "acme-trip"),
    ],
)
def test_derive_slug(folder, slug):
    assert casefile.derive_slug(folder) == slug


def test_derive_slug_is_capped_at_forty_characters_without_a_trailing_hyphen():
    # The 40-character cut lands just after a hyphen, which must then be stripped.
    slug = casefile.derive_slug("abcdefghij " * 3 + "abcdef ghijkl")
    assert slug == "abcdefghij-abcdefghij-abcdefghij-abcdef"
    assert len(slug) <= 40
    assert not slug.endswith("-")
    assert re.fullmatch(SLUG_RE, slug)


@pytest.mark.parametrize(
    ("title", "prefix"),
    [
        ("Acme Pump Trip", "APT"),
        ("Explosion", "EXP"),
        ("Ölpumpe Störfall", "OS"),
        ("Ölpumpe – Störfall 2026", "OS"),
        ("One Two Three Four Five Six Seven Eight", "OTTFFS"),
        ("श्री", None),
        ("2026 ###", None),
        ("x", None),
    ],
)
def test_derive_prefix(title, prefix):
    assert casefile.derive_prefix(title) == prefix


@pytest.mark.parametrize("title", ["Acme Pump Trip", "Pump", "a b", "Zeta 9 Alpha", "Q1 review"])
def test_derived_prefixes_match_the_id_rule(title):
    assert re.fullmatch(PREFIX_RE, casefile.derive_prefix(title))


# --- timezone detection (research Pitfall 9) ---------------------------------------------


def _tz(tmp_path, *, environ=None, etc_timezone=None, link_to=None):
    etc = tmp_path / "etc-timezone"
    if etc_timezone is not None:
        etc.write_text(etc_timezone, encoding="utf-8")
    localtime = tmp_path / "localtime"
    if link_to is not None:
        try:
            localtime.symlink_to(link_to)
        except OSError:
            pytest.skip("symbolic links are not available here")
    return casefile.detect_timezone(environ=environ or {}, etc_timezone=etc, localtime=localtime)


@pytest.mark.parametrize(
    ("value", "zone"),
    [
        ("Europe/London", "Europe/London"),
        (":Asia/Kolkata", "Asia/Kolkata"),
        ("/usr/share/zoneinfo/America/New_York", "America/New_York"),
        (":/usr/share/zoneinfo/Europe/Berlin", "Europe/Berlin"),
        ("UTC", "UTC"),
    ],
)
def test_detect_timezone_from_tz(tmp_path, value, zone):
    assert _tz(tmp_path, environ={"TZ": value}, etc_timezone="Asia/Tokyo\n") == zone


def test_detect_timezone_skips_an_invalid_tz_then_reads_etc_timezone(tmp_path):
    zone = _tz(tmp_path, environ={"TZ": "IST"}, etc_timezone="Europe/Berlin\nextra line\n")
    assert zone == "Europe/Berlin"


def test_detect_timezone_falls_back_to_the_localtime_link(tmp_path):
    target = tmp_path / "usr" / "share" / "zoneinfo" / "Asia" / "Kolkata"
    zone = _tz(tmp_path, environ={"TZ": "IST-5:30"}, etc_timezone="IST\n", link_to=target)
    assert zone == "Asia/Kolkata"


def test_detect_timezone_returns_none_when_nothing_is_valid(tmp_path):
    target = tmp_path / "somewhere" / "else"
    assert _tz(tmp_path, environ={"TZ": "IST"}, etc_timezone="IST\n", link_to=target) is None


def test_detect_timezone_with_no_sources_is_none(tmp_path):
    assert _tz(tmp_path, environ={}) is None


def test_detect_timezone_ignores_a_localtime_that_is_not_a_link(tmp_path):
    (tmp_path / "localtime").write_bytes(b"TZif")
    assert _tz(tmp_path, environ={}) is None


def test_validate_timezone():
    assert casefile.validate_timezone("Asia/Kolkata") == "Asia/Kolkata"
    bad_names = ["Mars/Base", "IST", "", "../etc/passwd", "/etc/localtime", "Europe/"]
    # Files in the zoneinfo folder that ZoneInfo opens but that are not IANA zone names.
    bad_names += ["localtime", "posixrules", "Factory"]
    for bad in bad_names:
        with pytest.raises(EpbError) as caught:
            casefile.validate_timezone(bad)
        assert caught.value.code == "BAD_ARGUMENT"


# --- usage errors write nothing (WS-01 empty edge) ---------------------------------------


def _assert_nothing_written(case_dir):
    """A refused init on an empty folder leaves it empty: no ``.epb``, no lock, nothing."""
    assert not (case_dir / ".epb").exists(), "a refused init left .epb/ behind"
    leftovers = sorted(path.name for path in case_dir.iterdir())
    assert leftovers == [], f"a refused init left {leftovers} behind"


def _error(proc):
    envelope = _envelope(proc)
    assert envelope["errors"], envelope
    return envelope["errors"][0]


def test_init_without_title_is_bad_argument(run_epb, case_dir):
    proc = run_epb(["init", "--json"], cwd=case_dir, env=TZ_ENV)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    error = _error(proc)
    assert error["code"] == "BAD_ARGUMENT"
    assert "--title" in error["message"]
    _assert_nothing_written(case_dir)


@pytest.mark.parametrize("title", ["", "   ", "\t \n"])
def test_init_with_blank_title_is_bad_argument(run_epb, case_dir, title):
    proc = run_epb(["init", "--title", title, "--json"], cwd=case_dir, env=TZ_ENV)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert _error(proc)["code"] == "BAD_ARGUMENT"
    _assert_nothing_written(case_dir)


@pytest.mark.parametrize("title", ["x" * 201, "Line one\nLine two", "Bell\x07"])
def test_init_with_a_bad_title_is_bad_argument(run_epb, case_dir, title):
    proc = run_epb(["init", "--title", title, "--json"], cwd=case_dir, env=TZ_ENV)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert _error(proc)["code"] == "BAD_ARGUMENT"
    _assert_nothing_written(case_dir)


@pytest.mark.parametrize(
    ("flags", "needle"),
    [
        (["--prefix", "apt"], "2 to 6"),
        (["--prefix", "A"], "2 to 6"),
        (["--prefix", "1AB"], "2 to 6"),
        (["--prefix", "ABCDEFG"], "2 to 6"),
        (["--slug", "Acme Trip"], "--slug"),
        (["--slug", "acme--trip"], "--slug"),
        (["--slug", "a" * 41], "--slug"),
        (["--timezone", "Mars/Base"], "Mars/Base"),
        (["--timezone", "IST"], "IST"),
    ],
)
def test_init_with_a_bad_setting_is_bad_argument(run_epb, case_dir, flags, needle):
    proc = run_epb(["init", "--title", "Acme Pump Trip", *flags, "--json"], cwd=case_dir)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    error = _error(proc)
    assert error["code"] == "BAD_ARGUMENT"
    assert needle in error["message"]
    _assert_nothing_written(case_dir)


def test_init_without_a_detectable_timezone_is_timezone_required(cli, case_dir, monkeypatch):
    monkeypatch.setattr(casefile, "detect_timezone", lambda **kwargs: None)
    result = cli(["init", "--title", "Acme Pump Trip", "--json"], cwd=case_dir)
    assert result.exit_code == 2, result.stdout + result.stderr
    error = result.envelope["errors"][0]
    assert error["code"] == "TIMEZONE_REQUIRED"
    assert "--timezone" in error["hint"]
    _assert_nothing_written(case_dir)


def test_title_without_ascii_letters_needs_a_prefix(run_epb, case_dir):
    proc = run_epb(["init", "--title", "श्री", "--json"], cwd=case_dir, env=TZ_ENV)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    error = _error(proc)
    assert error["code"] == "BAD_ARGUMENT"
    assert "--prefix" in error["message"]
    _assert_nothing_written(case_dir)

    proc = run_epb(
        ["init", "--title", "श्री", "--prefix", "SRI", "--json"], cwd=case_dir, env=TZ_ENV
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert casefile.load_case(case_dir)["title"] == "श्री"


# --- defaults and encoding (WS-01 encoding edge) -----------------------------------------


def test_defaults_come_from_folder_title_and_system_zone(run_epb, tmp_path):
    case_dir = tmp_path / "Ölpumpe – Störfall 2026"
    case_dir.mkdir()
    title = "Ölpumpe – Störfall 2026"
    proc = run_epb(["init", "--title", title, "--json"], cwd=case_dir, env=TZ_ENV)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert _envelope(proc)["data"]["case"] == {
        "title": title,
        "slug": "olpumpe-storfall-2026",
        "id_prefix": "OS",
        "timezone": "Asia/Kolkata",
    }
    case = casefile.load_case(case_dir)
    assert case["slug"] == "olpumpe-storfall-2026"
    assert case["id_prefix"] == "OS"
    assert case["timezone"] == "Asia/Kolkata"
    raw = (case_dir / casefile.CASE_FILE).read_bytes()
    assert title.encode("utf-8") in raw
    assert b"\\u" not in raw and b"\\x" not in raw


def test_title_is_stored_in_nfc_form(run_epb, case_dir):
    decomposed = unicodedata.normalize("NFD", "Ölpumpe – Störfall 2026")
    assert decomposed != unicodedata.normalize("NFC", decomposed)
    proc = run_epb(["init", "--title", f"  {decomposed} ", "--json"], cwd=case_dir, env=TZ_ENV)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert casefile.load_case(case_dir)["title"] == "Ölpumpe – Störfall 2026"


def test_case_yaml_holds_only_text(run_epb, case_dir):
    proc = run_epb(["init", *FULL_FLAGS, "--json"], cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    text = (case_dir / casefile.CASE_FILE).read_text(encoding="utf-8")
    yamlio.assert_text_only(yamlio.load_text_yaml(text, source="case.yaml"))
    assert "draft_warning_days: '7'" in text
    assert "conflict_tolerance_seconds: '60'" in text


# --- re-run rules (WS-01 idempotency edge) -----------------------------------------------


def _snapshot(case_dir):
    return {rel: (case_dir / rel).read_bytes() for rel in (casefile.CASE_FILE, STATE_FILE)}


@pytest.mark.parametrize(
    "flags",
    [
        [],
        ["--title", "Acme Pump Trip"],
        FULL_FLAGS,
        ["--prefix", "APT", "--timezone", "UTC"],
    ],
)
def test_rerun_with_no_or_equal_flags_changes_nothing(run_epb, case_dir, flags):
    first = run_epb(["init", *FULL_FLAGS, "--json"], cwd=case_dir)
    assert first.returncode == 0, first.stdout + first.stderr
    before = _snapshot(case_dir)

    again = run_epb(["init", *flags, "--json"], cwd=case_dir)
    assert again.returncode == 0, again.stdout + again.stderr
    envelope = _envelope(again)
    assert [w["code"] for w in envelope["warnings"]] == ["ALREADY_SET_UP"]
    assert envelope["data"]["created"] == []
    assert _snapshot(case_dir) == before


@pytest.mark.parametrize(
    ("flags", "fields"),
    [
        (["--title", "Another Trip"], ["title"]),
        (["--slug", "other-slug"], ["slug"]),
        (["--prefix", "OTH"], ["prefix"]),
        (["--timezone", "Europe/London"], ["timezone"]),
        (["--title", "Another Trip", "--timezone", "Asia/Kolkata"], ["title", "timezone"]),
        (["--title", "Acme Pump Trip", "--slug", "other-slug"], ["slug"]),
    ],
)
def test_rerun_with_different_flags_is_workspace_exists(run_epb, case_dir, flags, fields):
    first = run_epb(["init", *FULL_FLAGS, "--json"], cwd=case_dir)
    assert first.returncode == 0, first.stdout + first.stderr
    before = _snapshot(case_dir)

    again = run_epb(["init", *flags, "--json"], cwd=case_dir)
    assert again.returncode == 2, again.stdout + again.stderr
    envelope = _envelope(again)
    error = envelope["errors"][0]
    assert error["code"] == "WORKSPACE_EXISTS"
    assert envelope["data"]["fields"] == fields
    for field in fields:
        assert f"--{field}" in error["message"]
    assert _snapshot(case_dir) == before


def test_differences_names_only_changed_flags():
    settings = casefile.CaseSettings("Acme Pump Trip", "acme-pump-trip", "APT", "UTC")
    record = casefile.new_case_record(settings, "0.1.0", "2026-10-18T10:00:00Z")
    same = argparse.Namespace(title=" Acme Pump Trip ", slug=None, prefix="APT", timezone=None)
    assert casefile.differences(record, same) == []
    changed = argparse.Namespace(title=None, slug="x", prefix="APT", timezone="Asia/Kolkata")
    assert casefile.differences(record, changed) == ["slug", "timezone"]


# --- damaged case.yaml (D-19, WS-08 empty and encoding edges) ----------------------------


DAMAGED = {
    "empty": b"",
    "comment only": b"# nothing here\n",
    "not utf-8": b"title: \xff\xfe broken\n",
    "a list": b"- a\n- b\n",
    "an explicit int": None,  # filled from a valid record below
    "an empty title": None,
    "a duplicate key": None,
}


def _valid_record_text():
    settings = casefile.CaseSettings("Acme Pump Trip", "acme-pump-trip", "APT", "UTC")
    record = casefile.new_case_record(settings, "0.1.0", "2026-10-18T10:00:00Z")
    return yamlio.dump_yaml(record)


def _damaged_bytes(kind):
    text = _valid_record_text()
    if kind == "an explicit int":
        return text.replace("draft_warning_days: '7'", "draft_warning_days: !!int 7").encode()
    if kind == "an empty title":
        return text.replace("title: Acme Pump Trip", "title: ''").encode()
    if kind == "a duplicate key":
        return (text + "slug: other\n").encode()
    return DAMAGED[kind]


@pytest.mark.parametrize("kind", sorted(DAMAGED))
def test_load_case_refuses_damage(tmp_path, kind):
    path = tmp_path / casefile.CASE_FILE
    path.parent.mkdir(parents=True)
    path.write_bytes(_damaged_bytes(kind))
    with pytest.raises(EpbError) as caught:
        casefile.load_case(tmp_path)
    assert caught.value.code == "STATE_INVALID"
    assert ".epb/case.yaml" in caught.value.message


def test_load_case_refuses_a_missing_file(tmp_path):
    with pytest.raises(EpbError) as caught:
        casefile.load_case(tmp_path)
    assert caught.value.code == "STATE_INVALID"


def test_load_case_accepts_a_valid_record(tmp_path):
    path = tmp_path / casefile.CASE_FILE
    path.parent.mkdir(parents=True)
    path.write_text(_valid_record_text(), encoding="utf-8")
    assert casefile.load_case(tmp_path)["id_prefix"] == "APT"


@pytest.mark.parametrize("kind", ["missing", "not utf-8", "an explicit int", "empty"])
def test_rerun_on_a_damaged_case_yaml_is_state_invalid(run_epb, case_dir, kind):
    first = run_epb(["init", *FULL_FLAGS, "--json"], cwd=case_dir)
    assert first.returncode == 0, first.stdout + first.stderr
    path = case_dir / casefile.CASE_FILE
    if kind == "missing":
        path.unlink()
    else:
        path.write_bytes(_damaged_bytes(kind))
    state_before = (case_dir / STATE_FILE).read_bytes()

    again = run_epb(["init", "--json"], cwd=case_dir)
    assert again.returncode == 4, again.stdout + again.stderr
    error = _error(again)
    assert error["code"] == "STATE_INVALID"
    assert ".epb/case.yaml" in error["message"]
    assert (case_dir / STATE_FILE).read_bytes() == state_before


def test_rerun_on_a_damaged_state_json_is_state_invalid(run_epb, case_dir):
    first = run_epb(["init", *FULL_FLAGS, "--json"], cwd=case_dir)
    assert first.returncode == 0, first.stdout + first.stderr
    (case_dir / STATE_FILE).write_text("{not json", encoding="utf-8")

    again = run_epb(["init", "--json"], cwd=case_dir)
    assert again.returncode == 4, again.stdout + again.stderr
    assert _error(again)["code"] == "STATE_INVALID"
