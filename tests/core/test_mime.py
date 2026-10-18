"""File types by name and by content (D-13, research Pattern 4 and Pitfall 5).

Every fixture is a synthetic byte prefix written to ``tmp_path``.
"""

import ast
import builtins
import hashlib
import io
import json
import re
import struct
import zipfile
from pathlib import Path

import pytest
from epb import mime, schema

REPO = Path(__file__).resolve().parents[2]
MIME_PY = REPO / "plugin/skills/evidence-pack/scripts/epb/mime.py"

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
ODT = "application/vnd.oasis.opendocument.text"

# The table is authoritative: these answers must not depend on the Python version (CI runs
# 3.11 and 3.14) or on the machine's MIME database.
EXPECTED_TABLE = {
    "pdf": "application/pdf",
    "docx": DOCX,
    "xlsx": XLSX,
    "pptx": PPTX,
    "odt": ODT,
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "rtf": "application/rtf",
    "doc": "application/msword",
    "xls": "application/vnd.ms-excel",
    "ppt": "application/vnd.ms-powerpoint",
    "msg": "application/vnd.ms-outlook",
    "eml": "message/rfc822",
    "csv": "text/csv",
    "txt": "text/plain",
    "md": "text/markdown",
    "html": "text/html",
    "htm": "text/html",
    "xml": "application/xml",
    "json": "application/json",
    "yaml": "application/yaml",
    "yml": "application/yaml",
    "zip": "application/zip",
    "7z": "application/x-7z-compressed",
    "gz": "application/gzip",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "tif": "image/tiff",
    "tiff": "image/tiff",
    "heic": "image/heic",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "avi": "video/x-msvideo",
    "mkv": "video/x-matroska",
    "webm": "video/webm",
}


# --- synthetic files --------------------------------------------------------------------------


def _zip(members, *, first_stored=None):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        if first_stored is not None:
            name, data = first_stored
            archive.writestr(zipfile.ZipInfo(name), data, compress_type=zipfile.ZIP_STORED)
        for name, data in members:
            archive.writestr(name, data)
    return buffer.getvalue()


def _ftyp(brand):
    return struct.pack(">I", 24) + b"ftyp" + brand + b"\x00\x00\x02\x00" + b"isommp41"


def _riff(kind):
    return b"RIFF" + struct.pack("<I", 1000) + kind + b"synthetic chunk data"


OOXML_TYPES = b"<?xml version='1.0'?><Types/>"
SAMPLES = {
    "pdf": (b"%PDF-1.7\n% synthetic\n", "application/pdf"),
    "zip": (_zip([("notes.txt", b"synthetic")]), "application/zip"),
    "docx": (
        _zip([("[Content_Types].xml", OOXML_TYPES), ("word/document.xml", b"<w/>")]),
        DOCX,
    ),
    "xlsx": (_zip([("[Content_Types].xml", OOXML_TYPES), ("xl/workbook.xml", b"<x/>")]), XLSX),
    "pptx": (
        _zip([("[Content_Types].xml", OOXML_TYPES), ("ppt/presentation.xml", b"<p/>")]),
        PPTX,
    ),
    "odt": (
        _zip([("content.xml", b"<office/>")], first_stored=("mimetype", ODT.encode())),
        ODT,
    ),
    "ole2": (bytes.fromhex("d0cf11e0a1b11ae1") + b"\x00" * 504, "application/x-ole-storage"),
    "png": (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", "image/png"),
    "jpeg": (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00", "image/jpeg"),
    "gif87a": (b"GIF87a\x01\x00\x01\x00", "image/gif"),
    "gif89a": (b"GIF89a\x01\x00\x01\x00", "image/gif"),
    "wav": (_riff(b"WAVE"), "audio/wav"),
    "avi": (_riff(b"AVI "), "video/x-msvideo"),
    "ftyp-qt": (_ftyp(b"qt  "), "video/quicktime"),
    "ftyp-m4a": (_ftyp(b"M4A "), "audio/mp4"),
    "ftyp-heic": (_ftyp(b"heic"), "image/heic"),
    "ftyp-heix": (_ftyp(b"heix"), "image/heic"),
    "ftyp-mif1": (_ftyp(b"mif1"), "image/heic"),
    "ftyp-isom": (_ftyp(b"isom"), "video/mp4"),
    "matroska": (b"\x1a\x45\xdf\xa3\x9f\x42\x86\x81\x01", "video/x-matroska"),
    "7z": (b"7z\xbc\xaf\x27\x1c\x00\x04synthetic", "application/x-7z-compressed"),
    "gzip": (b"\x1f\x8b\x08\x00\x00\x00\x00\x00", "application/gzip"),
    "id3": (b"ID3\x04\x00\x00\x00\x00\x00\x00synthetic", "audio/mpeg"),
    "mpeg-frame": (b"\xff\xfb\x90\x64\x00\x00\x00\x00", "audio/mpeg"),
    "ogg": (b"OggS\x00\x02\x00\x00\x00\x00", "audio/ogg"),
    "tiff-le": (b"II*\x00\x08\x00\x00\x00", "image/tiff"),
    "tiff-be": (b"MM\x00*\x00\x00\x00\x08", "image/tiff"),
}


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_bytes(data)
    return path


# --- sniffing ---------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", sorted(SAMPLES))
def test_sniff_identifies_each_magic(tmp_path, kind):
    data, expected = SAMPLES[kind]
    assert mime.sniff(_write(tmp_path, "sample.bin", data)) == expected


@pytest.mark.parametrize(
    "data", [b"", b"plain synthetic text, no magic here\n", b"a,b,c\n1,2,3\n"], ids=repr
)
def test_sniff_returns_none_without_magic(tmp_path, data):
    assert mime.sniff(_write(tmp_path, "sample.bin", data)) is None


def test_docx_named_file_with_pdf_bytes_is_a_pdf_with_mismatch(tmp_path):
    path = _write(tmp_path, "report.docx", SAMPLES["pdf"][0])
    assert mime.detect(path) == (
        "application/pdf",
        {"by_extension": DOCX, "by_content": "application/pdf"},
    )


@pytest.mark.parametrize(
    ("name", "kind", "expected"),
    [
        ("message.msg", "ole2", "application/vnd.ms-outlook"),
        ("letter.doc", "ole2", "application/msword"),
        ("sheet.xls", "ole2", "application/vnd.ms-excel"),
        ("deck.ppt", "ole2", "application/vnd.ms-powerpoint"),
        ("clip.webm", "matroska", "video/webm"),
    ],
)
def test_ambiguous_families_are_not_mismatches(tmp_path, name, kind, expected):
    path = _write(tmp_path, name, SAMPLES[kind][0])
    assert mime.detect(path) == (expected, None)


@pytest.mark.parametrize(
    ("name", "expected"),
    [("notes.txt", "text/plain"), ("table.csv", "text/csv"), ("readme.md", "text/markdown")],
)
def test_text_without_magic_is_not_a_mismatch(tmp_path, name, expected):
    path = _write(tmp_path, name, b"synthetic text with no magic bytes\n")
    assert mime.detect(path) == (expected, None)


def test_matching_name_and_content_is_not_a_mismatch(tmp_path):
    path = _write(tmp_path, "report.docx", SAMPLES["docx"][0])
    assert mime.detect(path) == (DOCX, None)


@pytest.mark.parametrize(
    "data",
    [
        b"PK\x03\x04" + b"\x00" * 40,
        SAMPLES["docx"][0][: len(SAMPLES["docx"][0]) // 2],
        b"PK\x03\x04truncated",
    ],
    ids=["zero-header", "half-docx", "short"],
)
def test_truncated_or_corrupt_zip_is_application_zip(tmp_path, data):
    path = _write(tmp_path, "broken.zip", data)
    assert mime.sniff(path) == "application/zip"
    assert mime.detect(path) == ("application/zip", None)


def test_odf_mimetype_member_must_look_like_a_type(tmp_path):
    data = _zip([], first_stored=("mimetype", b"<script>not a type</script>"))
    assert mime.sniff(_write(tmp_path, "odd.odt", data)) == "application/zip"


# --- reading limits ---------------------------------------------------------------------------


def _counting_open(monkeypatch):
    reads = []
    real_open = builtins.open

    class Counting(io.RawIOBase):
        def __init__(self, handle):
            self._handle = handle

        def read(self, size=-1):
            data = self._handle.read(size)
            reads.append(len(data))
            return data

        def readinto(self, buffer):
            data = self.read(len(buffer))
            buffer[: len(data)] = data
            return len(data)

        def readable(self):
            return True

        def seekable(self):
            return self._handle.seekable()

        def seek(self, *args):
            return self._handle.seek(*args)

        def tell(self):
            return self._handle.tell()

        def close(self):
            self._handle.close()
            super().close()

    def fake_open(file, mode="r", *args, **kwargs):
        handle = real_open(file, mode, *args, **kwargs)
        return Counting(handle) if "b" in mode else handle

    monkeypatch.setattr(mime, "open", fake_open, raising=False)
    return reads


def test_sniff_reads_at_most_4096_bytes(tmp_path, monkeypatch):
    path = _write(tmp_path, "large.bin", b"\x00" * 200_000)
    reads = _counting_open(monkeypatch)
    assert mime.sniff(path) is None
    assert reads and sum(reads) <= 4096


def test_magic_beyond_4096_bytes_is_not_seen(tmp_path):
    path = _write(tmp_path, "late.bin", b"\x00" * 5000 + b"%PDF-1.7\n")
    assert mime.sniff(path) is None


def test_zip_members_are_listed_never_extracted(tmp_path, monkeypatch):
    path = _write(tmp_path, "report.docx", SAMPLES["docx"][0])

    def refuse(*args, **kwargs):
        raise AssertionError("a zip member was opened")

    for name in ("open", "read", "extract", "extractall"):
        monkeypatch.setattr(zipfile.ZipFile, name, refuse)
    before = sorted(p.name for p in tmp_path.iterdir())
    assert mime.sniff(path) == DOCX
    assert sorted(p.name for p in tmp_path.iterdir()) == before


# --- the extension table ----------------------------------------------------------------------


def test_extension_table_is_exactly_the_expected_table():
    assert mime.EXTENSION_TABLE == EXPECTED_TABLE


@pytest.mark.parametrize("ext", sorted(EXPECTED_TABLE))
def test_table_answers_never_consult_mimetypes(monkeypatch, ext):
    def refuse():
        raise AssertionError("mimetypes consulted for a table extension")

    monkeypatch.setattr(mime, "_fallback_db", refuse)
    assert mime.by_extension(f"file.{ext}") == EXPECTED_TABLE[ext]
    assert mime.by_extension(f"FILE.{ext.upper()}") == EXPECTED_TABLE[ext]


def test_unknown_and_missing_extensions_fall_back():
    assert mime.by_extension("README") == "application/octet-stream"
    assert mime.by_extension("file.qqqzz") == "application/octet-stream"


def test_mime_py_never_calls_module_level_guess_type():
    tree = ast.parse(MIME_PY.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "guess_type":
            assert not (isinstance(node.value, ast.Name) and node.value.id == "mimetypes")
        if isinstance(node, ast.ImportFrom) and node.module == "mimetypes":
            pytest.fail("mime.py imports from mimetypes directly")


def test_no_python_magic_dependency():
    files = [REPO / "pyproject.toml", *REPO.glob("requirements*.txt")]
    files += list((REPO / "plugin").glob("requirements*.txt"))
    assert files
    pattern = re.compile(r"^\s*\"?(python-magic|magic)\b", re.IGNORECASE | re.MULTILINE)
    for path in files:
        assert not pattern.search(path.read_text(encoding="utf-8")), path


def test_magic_rules_cover_the_d13_minimum():
    assert len(mime.MAGIC_RULES) >= 14
    assert mime.AMBIGUOUS_FAMILIES["application/x-ole-storage"] >= {
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
        "application/vnd.ms-outlook",
    }
    assert "video/webm" in mime.AMBIGUOUS_FAMILIES["video/x-matroska"]


# --- through scan -----------------------------------------------------------------------------

INIT = ["init", "--title", "Synthetic Mime Case", "--prefix", "SMC", "--timezone", "UTC"]


def test_scan_records_and_reports_a_mismatch(run_epb, case_dir):
    proc = run_epb([*INIT, "--json"], cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    pdf_bytes = SAMPLES["pdf"][0]
    (case_dir / "inputs" / "report.docx").write_bytes(pdf_bytes)

    proc = run_epb(["scan", "--json"], cwd=case_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    envelope = json.loads(proc.stdout)
    assert (case_dir / "inputs" / "report.docx").read_bytes() == pdf_bytes

    record = json.loads((case_dir / ".epb/sources/S001.json").read_text(encoding="utf-8"))
    assert schema.validate(record, "source") == []
    assert record["versions"][0]["mime"] == "application/pdf"
    assert record["versions"][0]["sha256"] == hashlib.sha256(pdf_bytes).hexdigest()
    assert record["mime_mismatch"] == {"by_extension": DOCX, "by_content": "application/pdf"}

    warnings = [item for item in envelope["warnings"] if item["code"] == "MIME_MISMATCH"]
    assert len(warnings) == 1
    assert "inputs/report.docx" in warnings[0]["message"]
    assert "treat it by its content" in warnings[0]["message"]

    run = json.loads((case_dir / ".epb/runs/002/run.json").read_text(encoding="utf-8"))
    assert run["scan"]["mime_mismatches"] == [
        {
            "src_id": "S001",
            "path": "inputs/report.docx",
            "by_extension": DOCX,
            "by_content": "application/pdf",
        }
    ]
    index_text = (case_dir / "INDEX.md").read_text(encoding="utf-8")
    issues = index_text.split("## 5. Open issues", 1)[1].split("## 6.", 1)[0]
    assert "S001 (inputs/report.docx)" in issues
    assert "application/pdf" in issues
