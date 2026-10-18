"""Supply-chain checks (PKG-09, D-12, D-18): decision logic on canned metadata, no network."""

import email.message
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import check_dependency_age as age
import check_licences as lic
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = REPO_ROOT / "tools" / "licence-allowlist.json"
EXCEPTIONS = REPO_ROOT / "plugin" / "security-exceptions.json"

ALLOWED = [
    "MIT",
    "MIT-0",
    "MIT-CMU",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "Apache-2.0",
    "PSF-2.0",
    "ISC",
]


def fake_dist(name, version="1.0", *, expression=None, licence=None, classifiers=()):
    """A stand-in for an installed distribution, with an email.message metadata object."""
    meta = email.message.Message()
    meta["Name"] = name
    meta["Version"] = version
    if expression is not None:
        meta["License-Expression"] = expression
    if licence is not None:
        meta["License"] = licence
    for classifier in classifiers:
        meta["Classifier"] = classifier
    return SimpleNamespace(metadata=meta)


@pytest.fixture
def config():
    return lic.load_config(ALLOWLIST)


# --- The shipped allow-list ---------------------------------------------------------------


def test_allowlist_has_exactly_the_agreed_identifiers():
    data = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert sorted(data["allowed"]) == sorted(ALLOWED)
    assert "MPL-2.0" in data["note"]


def test_allowlist_overrides_are_reviewed(config):
    entry = config["overrides"]["pypdfium2"]
    assert entry["licence"] == "BSD-3-Clause AND Apache-2.0"
    assert entry["reviewed_on"] == "2026-10-17"
    assert entry["reason"].strip()


# --- SPDX expression evaluation -----------------------------------------------------------


@pytest.mark.parametrize(
    "expr",
    [
        "MIT",
        "mit",
        "Apache-2.0 OR BSD-2-Clause",
        "Apache-2.0 OR GPL-3.0-only",
        "MIT AND BSD-3-Clause",
        "MIT OR (GPL-3.0-only AND BSD-3-Clause)",
        "(MIT)",
        "Apache-2.0 WITH LLVM-exception",
        "GPL-3.0-only OR Apache-2.0 WITH LLVM-exception",
        "MIT and ISC",
    ],
)
def test_allowed_expressions(expr):
    assert lic.evaluate_expression(expr, ALLOWED) is True


@pytest.mark.parametrize(
    "expr",
    [
        "GPL-3.0-only",
        "MIT AND GPL-3.0-only",
        "(MIT OR GPL-3.0-only) AND LGPL-2.1-only",
        "GPL-2.0-only WITH Classpath-exception-2.0",
        "LicenseRef-Proprietary",
        "MIT AND LicenseRef-Custom",
        "MIT OR",
        "(MIT",
        "MIT)",
        "MIT WITH",
        "MIT, Apache-2.0",
        "",
    ],
)
def test_disallowed_or_malformed_expressions(expr):
    assert lic.evaluate_expression(expr, ALLOWED) is False


def test_and_binds_tighter_than_or():
    # Read as "GPL-3.0-only OR (MIT AND BSD-3-Clause)", which has an allowed alternative.
    assert lic.evaluate_expression("GPL-3.0-only OR MIT AND BSD-3-Clause", ALLOWED) is True
    # Read as "(MIT AND GPL-3.0-only) OR LGPL-2.1-only", where neither side is allowed.
    assert lic.evaluate_expression("MIT AND GPL-3.0-only OR LGPL-2.1-only", ALLOWED) is False


def test_licenseref_is_never_allowed_even_when_listed():
    assert lic.evaluate_expression("LicenseRef-Mine", ["LicenseRef-Mine"]) is False


# --- Where the licence comes from --------------------------------------------------------


def test_license_expression_field_wins_over_license_and_classifiers(config):
    dist = fake_dist(
        "packaging",
        expression="Apache-2.0 OR BSD-2-Clause",
        licence="GPL-3.0-only",
        classifiers=["License :: OSI Approved :: GNU General Public License v3 (GPLv3)"],
    )
    assert lic.licence_of(dist, config) == ("Apache-2.0 OR BSD-2-Clause", "License-Expression")


def test_license_field_spdx_id_is_used(config):
    assert lic.licence_of(fake_dist("lxml", licence="BSD-3-Clause"), config) == (
        "BSD-3-Clause",
        "License",
    )


def test_license_field_alias_is_mapped(config):
    assert lic.licence_of(fake_dist("defusedxml", licence="PSFL"), config) == (
        "PSF-2.0",
        "License",
    )
    assert lic.licence_of(fake_dist("bs4", licence="MIT License"), config) == ("MIT", "License")


def test_free_text_license_falls_back_to_classifiers(config):
    dist = fake_dist(
        "freetext",
        licence="Permission is hereby granted, free of charge, to any person",
        classifiers=["License :: OSI Approved :: MIT License"],
    )
    assert lic.licence_of(dist, config) == ("MIT", "classifier")


def test_placeholder_license_falls_back_to_classifiers(config):
    dist = fake_dist(
        "oldtool", licence="UNKNOWN", classifiers=["License :: OSI Approved :: MIT License"]
    )
    assert lic.licence_of(dist, config) == ("MIT", "classifier")


@pytest.mark.parametrize(
    ("classifier", "spdx"),
    [
        ("License :: OSI Approved :: MIT License", "MIT"),
        ("License :: OSI Approved :: BSD License", "BSD-3-Clause"),
        ("License :: OSI Approved :: Apache Software License", "Apache-2.0"),
        ("License :: OSI Approved :: Python Software Foundation License", "PSF-2.0"),
        ("License :: OSI Approved :: ISC License (ISCL)", "ISC"),
        ("License :: OSI Approved :: MIT No Attribution License (MIT-0)", "MIT-0"),
    ],
)
def test_classifier_mapping(config, classifier, spdx):
    assert lic.licence_of(fake_dist("c", classifiers=[classifier]), config) == (spdx, "classifier")


def test_several_classifiers_combine_with_or(config):
    dist = fake_dist(
        "dual",
        classifiers=[
            "License :: OSI Approved :: Apache Software License",
            "License :: OSI Approved :: BSD License",
        ],
    )
    assert lic.licence_of(dist, config) == ("Apache-2.0 OR BSD-3-Clause", "classifier")


def test_override_wins_over_every_metadata_field(config):
    dist = fake_dist(
        "PyPDFium2",
        licence="BSD-3-Clause, Apache-2.0, dependency licenses",
        expression="GPL-3.0-only",
    )
    assert lic.licence_of(dist, config) == ("BSD-3-Clause AND Apache-2.0", "reviewed override")


# --- check_distributions ------------------------------------------------------------------


def test_clean_set_has_no_violations(config):
    dists = [
        fake_dist("attrs", expression="MIT"),
        fake_dist("pypdfium2", licence="BSD-3-Clause, Apache-2.0, dependency licenses"),
        fake_dist("pdfplumber", classifiers=["License :: OSI Approved :: MIT License"]),
    ]
    assert lic.check_distributions(dists, config) == []


def test_unknown_licence_is_reported(config):
    dists = [fake_dist("mystery", "2.0")]
    [violation] = lic.check_distributions(dists, config)
    assert violation.name == "mystery"
    assert violation.licence is None
    assert violation.reason == "licence unknown"
    assert violation.line().startswith("VIOLATION mystery 2.0: licence unknown")


def test_unmapped_classifier_is_reported_as_unknown(config):
    dist = fake_dist(
        "gpltool", classifiers=["License :: OSI Approved :: GNU General Public License v3 (GPLv3)"]
    )
    [violation] = lic.check_distributions([dist], config)
    assert violation.reason == "licence unknown"
    assert "GNU General Public License v3" in violation.source


def test_disallowed_licence_is_reported_and_sorted(config):
    dists = [
        fake_dist("Zeta_Pkg", expression="GPL-3.0-only"),
        fake_dist("alpha", expression="MIT AND GPL-3.0-only"),
        fake_dist("fine", expression="MIT"),
    ]
    violations = lic.check_distributions(dists, config)
    assert [v.name for v in violations] == ["alpha", "Zeta_Pkg"]
    assert all(v.reason == "licence not allowed" for v in violations)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (None, "not found"),
        ("{not json", "not valid JSON"),
        ('{"schema_version": 2, "allowed": ["MIT"]}', "schema_version"),
        ('{"schema_version": 1, "allowed": []}', "allowed"),
        (
            '{"schema_version": 1, "allowed": ["MIT"], "overrides": {"x": {"licence": "MIT"}}}',
            "reason",
        ),
    ],
)
def test_unusable_allowlist_is_rejected(tmp_path, content, message):
    path = tmp_path / "allow.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        lic.load_config(path)


def test_main_exits_2_on_unusable_allowlist(tmp_path, capsys):
    assert lic.main(["--config", str(tmp_path / "missing.json")]) == 2
    assert "not found" in capsys.readouterr().err


# --- The runner's preinstalled setuptools (gap 1, GitHub run 39141925712) ----------------

# The GitHub Python 3.11 toolcache preinstalls setuptools 79.0.1 with no License-Expression,
# no License field and no licence classifier: fake_dist with no licence arguments matches it.
RUNNER_SETUPTOOLS = ("setuptools", "79.0.1")
REQUIREMENT_NAME = re.compile(r"[A-Za-z0-9._-]+")


def test_main_passes_runner_setuptools_with_the_shipped_allowlist(capsys, monkeypatch):
    dists = [fake_dist(*RUNNER_SETUPTOOLS)]
    monkeypatch.setattr(lic.importlib.metadata, "distributions", lambda: dists)
    assert lic.main([]) == 0
    assert "Licence check passed: all 1 installed distributions are allowed." in (
        capsys.readouterr().out
    )


def test_main_reports_runner_setuptools_without_the_override(tmp_path, capsys, monkeypatch):
    data = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    data["overrides"].pop("setuptools", None)
    copy = tmp_path / "allow-without-setuptools.json"
    copy.write_text(json.dumps(data, indent=2), encoding="utf-8")
    dists = [fake_dist(*RUNNER_SETUPTOOLS)]
    monkeypatch.setattr(lic.importlib.metadata, "distributions", lambda: dists)
    assert lic.main(["--config", str(copy)]) == 1
    out = capsys.readouterr().out
    assert (
        "VIOLATION setuptools 79.0.1: licence unknown (no usable licence metadata; from none)"
        in out
    )
    assert "1 of 1 distributions failed the licence check." in out


def test_setuptools_override_is_reviewed(config):
    entry = config["overrides"]["setuptools"]
    assert entry["licence"] == "MIT"
    assert entry["reviewed_on"] == "2026-10-18"
    assert "toolcache" in entry["reason"]
    assert "79.0.1" in entry["reason"]
    assert "not a project dependency" in entry["reason"].lower()


def test_runner_setuptools_has_the_reviewed_licence(config):
    dist = fake_dist(*RUNNER_SETUPTOOLS)
    assert lic.licence_of(dist, config) == ("MIT", "reviewed override")
    assert lic.check_distributions([dist], config) == []


def test_overrides_are_exactly_the_reviewed_set(config):
    # Adding or removing an override is a licence review: change this list with it.
    assert sorted(config["overrides"]) == ["pypdfium2", "setuptools"]


def test_setuptools_is_not_a_project_dependency():
    # The override's reason says setuptools is only a runner bootstrap tool. If a
    # requirements file ever names it, that reason is false and needs a fresh review.
    files = sorted(REPO_ROOT.glob("requirements*.txt")) + sorted(
        (REPO_ROOT / "plugin").glob("requirements*.txt")
    )
    assert len(files) >= 4, [path.name for path in files]
    for path in files:
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text or text.startswith(("#", "-")):
                continue
            match = REQUIREMENT_NAME.match(text)
            assert match is not None, f"{path.name}: unreadable requirement {line!r}"
            assert lic.normalise(match.group(0)) != "setuptools", f"{path.name}: {line!r}"


# --- Dependency age (two-week rule) -------------------------------------------------------

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
FOURTEEN_DAYS = timedelta(days=14)


def exception_entry(package, version, **changes):
    entry = {
        "package": package,
        "version": version,
        "advisory": "GHSA-xxxx-yyyy-zzzz",
        "reason": "Fixes a parser crash on crafted input; the fix is newer than the cutoff.",
        "reviewed_by": "maintainer",
        "reviewed_on": "2026-10-17",
    }
    entry.update(changes)
    return entry


def write_exceptions(tmp_path, entries, **top):
    data = {"schema_version": 1, "description": "test", "exceptions": entries}
    data.update(top)
    path = tmp_path / "security-exceptions.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_upload_just_under_14_days_is_a_violation():
    uploaded = NOW - (FOURTEEN_DAYS - timedelta(hours=1))  # 13 days 23 hours ago
    report = age.evaluate([("newpkg", "2.0")], {("newpkg", "2.0"): uploaded}, [], NOW)
    assert [(f.name, f.version) for f in report.violations] == [("newpkg", "2.0")]
    assert report.violations[0].age_days == 13


def test_upload_exactly_14_days_ago_passes():
    uploaded = NOW - FOURTEEN_DAYS
    report = age.evaluate([("oldpkg", "1.0")], {("oldpkg", "1.0"): uploaded}, [], NOW)
    assert report.violations == []
    assert report.stale == []


def test_min_age_days_is_configurable():
    uploaded = NOW - timedelta(days=3)
    installed = [("pkg", "1.0")]
    times = {("pkg", "1.0"): uploaded}
    assert age.evaluate(installed, times, [], NOW, min_age_days=3).violations == []
    assert len(age.evaluate(installed, times, [], NOW, min_age_days=4).violations) == 1


def test_reviewed_exception_with_exact_version_is_not_a_violation():
    uploaded = NOW - timedelta(days=2)
    installed = [("Py_PDF", "6.21.1")]
    times = {("py-pdf", "6.21.1"): uploaded}
    report = age.evaluate(installed, times, [exception_entry("py.pdf", "6.21.1")], NOW)
    assert report.violations == []
    assert [(f.name, f.version) for f in report.excepted] == [("Py_PDF", "6.21.1")]


def test_exception_for_another_version_does_not_cover_the_installed_one():
    uploaded = NOW - timedelta(days=2)
    installed = [("pypdf", "6.21.1")]
    times = {("pypdf", "6.21.1"): uploaded}
    report = age.evaluate(installed, times, [exception_entry("pypdf", "6.21.0")], NOW)
    assert [(f.name, f.version) for f in report.violations] == [("pypdf", "6.21.1")]


def test_exception_now_old_enough_is_stale_not_a_failure():
    uploaded = NOW - timedelta(days=20)
    installed = [("pypdf", "6.21.1")]
    times = {("pypdf", "6.21.1"): uploaded}
    report = age.evaluate(installed, times, [exception_entry("pypdf", "6.21.1")], NOW)
    assert report.violations == []
    assert [(f.name, f.version) for f in report.stale] == [("pypdf", "6.21.1")]
    assert "can be removed" in report.stale[0].line("STALE")


def test_missing_upload_time_is_a_violation():
    report = age.evaluate([("localonly", "0.1")], {("localonly", "0.1"): None}, [], NOW)
    assert [(f.name, f.version) for f in report.violations] == [("localonly", "0.1")]
    assert report.violations[0].uploaded is None
    assert "no upload time" in report.violations[0].line("VIOLATION")


def test_pip_is_exempt_with_a_documented_reason():
    assert "26.1" in age.EXEMPT["pip"]
    report = age.evaluate([("pip", "26.2.1")], {("pip", "26.2.1"): NOW}, [], NOW)
    assert report.violations == []
    assert [name for name, _reason in report.exempt] == ["pip"]


def test_violations_and_stale_entries_are_sorted_by_normalised_name():
    new = NOW - timedelta(days=1)
    old = NOW - timedelta(days=30)
    installed = [("Zeta", "1"), ("alpha_pkg", "1"), ("Beta", "1"), ("delta", "1"), ("Gamma", "1")]
    times = {
        ("zeta", "1"): new,
        ("alpha-pkg", "1"): new,
        ("beta", "1"): new,
        ("delta", "1"): old,
        ("gamma", "1"): old,
    }
    exceptions = [exception_entry("Gamma", "1"), exception_entry("delta", "1")]
    report = age.evaluate(installed, times, exceptions, NOW)
    assert [f.name for f in report.violations] == ["alpha_pkg", "Beta", "Zeta"]
    assert [f.name for f in report.stale] == ["delta", "Gamma"]


def test_violation_line_format():
    uploaded = datetime(2026, 10, 15, 9, 30, tzinfo=UTC)
    report = age.evaluate([("newpkg", "2.0")], {("newpkg", "2.0"): uploaded}, [], NOW)
    assert report.violations[0].line("VIOLATION") == (
        "VIOLATION newpkg 2.0: uploaded 2026-10-15, 3 days ago"
    )


def test_normalise_follows_pep_503():
    assert age.normalise("Foo.Bar__baz-QUX") == "foo-bar-baz-qux"


def test_parse_upload_time_takes_the_earliest_file():
    payload = {
        "urls": [
            {"upload_time_iso_8601": "2026-10-09T08:00:00.123456Z"},
            {"upload_time_iso_8601": "2026-10-08T23:59:59.000001Z"},
        ]
    }
    assert age.parse_upload_time(payload) == datetime(2026, 10, 8, 23, 59, 59, 1, tzinfo=UTC)
    assert age.parse_upload_time({"urls": []}) is None


# --- The exceptions file ------------------------------------------------------------------


def test_shipped_exceptions_file_is_empty_and_valid():
    data = json.loads(EXCEPTIONS.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert data["exceptions"] == []
    assert "reviewed_by" in data["description"]
    assert age.load_exceptions(EXCEPTIONS) == []


def test_load_exceptions_returns_valid_entries(tmp_path):
    entry = exception_entry("pypdf", "6.21.1")
    assert age.load_exceptions(write_exceptions(tmp_path, [entry])) == [entry]


@pytest.mark.parametrize("missing", ["package", "version", "advisory", "reason", "reviewed_by"])
def test_load_exceptions_rejects_a_missing_field(tmp_path, missing):
    entry = exception_entry("pypdf", "6.21.1")
    del entry[missing]
    with pytest.raises(ValueError, match=missing):
        age.load_exceptions(write_exceptions(tmp_path, [entry]))


@pytest.mark.parametrize("field", ["advisory", "reviewed_on"])
def test_load_exceptions_rejects_an_empty_field(tmp_path, field):
    entry = exception_entry("pypdf", "6.21.1", **{field: "  "})
    with pytest.raises(ValueError, match=field):
        age.load_exceptions(write_exceptions(tmp_path, [entry]))


def test_load_exceptions_rejects_a_bad_review_date(tmp_path):
    entry = exception_entry("pypdf", "6.21.1", reviewed_on="17/10/2026")
    with pytest.raises(ValueError, match="reviewed_on"):
        age.load_exceptions(write_exceptions(tmp_path, [entry]))


def test_load_exceptions_rejects_a_missing_file(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        age.load_exceptions(tmp_path / "absent.json")


def test_load_exceptions_rejects_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{oops", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        age.load_exceptions(path)


def test_load_exceptions_rejects_a_wrong_schema_version(tmp_path):
    with pytest.raises(ValueError, match="schema_version"):
        age.load_exceptions(write_exceptions(tmp_path, [], schema_version=2))


# --- The command line ---------------------------------------------------------------------


@pytest.fixture
def offline_pypi(monkeypatch):
    """Canned upload times instead of PyPI; any lookup outside the table fails loudly."""
    table = {}

    def fetch(name, version, timeout=20.0):
        return table[(age.normalise(name), version)]

    monkeypatch.setattr(age, "fetch_upload_time", fetch)
    return table


def test_pins_prints_one_line_per_exception_without_network(tmp_path, capsys, monkeypatch):
    def no_fetch(*args, **kwargs):
        raise AssertionError("--pins must not contact PyPI")

    monkeypatch.setattr(age, "fetch_upload_time", no_fetch)
    path = write_exceptions(
        tmp_path, [exception_entry("Zeta", "2.0"), exception_entry("alpha", "1.5")]
    )
    assert age.main(["--pins", "--exceptions", str(path)]) == 0
    assert capsys.readouterr().out == "alpha==1.5\nZeta==2.0\n"


def test_pins_with_the_shipped_empty_file_prints_nothing(capsys):
    assert age.main(["--pins"]) == 0
    assert capsys.readouterr().out == ""


def test_main_clean_run_with_empty_exceptions_exits_0(tmp_path, capsys, monkeypatch, offline_pypi):
    monkeypatch.setattr(age, "installed_distributions", lambda: [("oldpkg", "1.0")])
    offline_pypi[("oldpkg", "1.0")] = datetime.now(UTC) - timedelta(days=100)
    assert age.main(["--exceptions", str(write_exceptions(tmp_path, []))]) == 0
    assert "VIOLATION" not in capsys.readouterr().out


def test_main_reports_violations_and_stale_entries(tmp_path, capsys, monkeypatch, offline_pypi):
    monkeypatch.setattr(
        age, "installed_distributions", lambda: [("newpkg", "2.0"), ("fixed", "1.1")]
    )
    offline_pypi[("newpkg", "2.0")] = datetime.now(UTC) - timedelta(days=1)
    offline_pypi[("fixed", "1.1")] = datetime.now(UTC) - timedelta(days=40)
    path = write_exceptions(tmp_path, [exception_entry("fixed", "1.1")])
    assert age.main(["--exceptions", str(path)]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert any(line.startswith("VIOLATION newpkg 2.0: uploaded ") for line in lines)
    assert any(line.startswith("STALE fixed 1.1: ") for line in lines)


def test_main_stale_only_does_not_fail(tmp_path, capsys, monkeypatch, offline_pypi):
    monkeypatch.setattr(age, "installed_distributions", lambda: [("fixed", "1.1")])
    offline_pypi[("fixed", "1.1")] = datetime.now(UTC) - timedelta(days=40)
    path = write_exceptions(tmp_path, [exception_entry("fixed", "1.1")])
    assert age.main(["--exceptions", str(path)]) == 0
    assert "STALE fixed 1.1" in capsys.readouterr().out


@pytest.mark.parametrize("content", [None, "{oops"])
def test_main_exits_2_on_unusable_exceptions_file(tmp_path, capsys, content):
    path = tmp_path / "exceptions.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    assert age.main(["--exceptions", str(path)]) == 2
    assert age.main(["--pins", "--exceptions", str(path)]) == 2
    assert "security exceptions" in capsys.readouterr().err


def test_main_exits_2_when_pypi_cannot_be_reached(tmp_path, capsys, monkeypatch):
    def unreachable(name, version, timeout=20.0):
        raise age.PyPIUnavailable("connection refused")

    monkeypatch.setattr(age, "fetch_upload_time", unreachable)
    monkeypatch.setattr(age, "installed_distributions", lambda: [("pkg", "1.0")])
    assert age.main(["--exceptions", str(write_exceptions(tmp_path, []))]) == 2
    assert "PyPI" in capsys.readouterr().err


def test_fetch_upload_time_goes_through_the_refused_socket_layer():
    # The autouse guard in tests/conftest.py refuses the connection, so pytest never
    # reaches PyPI even if a test forgets to stub the lookup.
    with pytest.raises(RuntimeError, match="network access is not allowed in tests"):
        age.fetch_upload_time("pypdf", "6.19.0")
