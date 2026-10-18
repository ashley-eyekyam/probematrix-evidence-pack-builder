"""Supply-chain checks (PKG-09, D-12, D-18): decision logic on canned metadata, no network."""

import email.message
import json
from pathlib import Path
from types import SimpleNamespace

import check_licences as lic
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = REPO_ROOT / "tools" / "licence-allowlist.json"

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
