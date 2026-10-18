"""File types by name and by content (D-13, research Pattern 4 and Pitfall 5).

``EXTENSION_TABLE`` is authoritative for every type the design names. Python's own
``mimetypes`` gives different answers on different Python versions and machines (3.11 has no
``.md``, ``.yaml``, ``.7z``, ``.mkv``, ``.m4a`` or ``.rtf``; the module-level ``guess_type``
reads ``/etc/mime.types`` and the Windows registry), so it is only a fallback for extensions
the table does not know, through a private ``mimetypes.MimeTypes()`` instance. Anything
still unknown is ``application/octet-stream``.

``sniff`` reads at most the first 4,096 bytes (plus, for a ZIP, its list of member names; no
member is ever extracted) and checks ``MAGIC_RULES``. A text byte-order mark means text, so
``sniff`` gives no verdict for it and the name decides, exactly as for text without a mark.
``detect`` lets the content win: when
the name suggests a different known type, the disagreement is returned as a mismatch, unless
the content only names a family (``AMBIGUOUS_FAMILIES``: an OLE2 ``.msg`` or ``.doc``, a
Matroska ``.webm``) or a container the name refines.

Standard library only; no ``python-magic``.
"""

import mimetypes
import re
import zipfile
from functools import cache
from pathlib import PurePath

OCTET_STREAM = "application/octet-stream"

EXTENSION_TABLE = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "odt": "application/vnd.oasis.opendocument.text",
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


@cache
def _fallback_db() -> mimetypes.MimeTypes:
    """A private ``MimeTypes`` instance holding only Python's built-in defaults."""
    return mimetypes.MimeTypes()


def by_extension(name) -> str:
    """The type a file name suggests: the table first, then Python's built-in defaults, then
    ``application/octet-stream``."""
    name = PurePath(str(name)).name
    suffix = PurePath(name).suffix.lower().lstrip(".")
    if suffix in EXTENSION_TABLE:
        return EXTENSION_TABLE[suffix]
    if not suffix:
        return OCTET_STREAM
    guessed, encoding = _fallback_db().guess_type("file." + suffix, strict=True)
    if guessed and encoding is None:
        return guessed.lower()
    return OCTET_STREAM


# --- content -----------------------------------------------------------------------------------

HEAD_BYTES = 4096  # sniff never reads more than this, except a ZIP's central directory

ZIP = "application/zip"
OLE2 = "application/x-ole-storage"
_ODF_PREFIX = "application/vnd.oasis.opendocument."
_ODF_TYPE = re.compile(r"^application/vnd\.oasis\.opendocument\.[a-z0-9.+-]{1,60}$")
_OOXML_PARTS = (
    ("word/", EXTENSION_TABLE["docx"]),
    ("xl/", EXTENSION_TABLE["xlsx"]),
    ("ppt/", EXTENSION_TABLE["pptx"]),
)
_HEIC_BRANDS = (b"heic", b"heix", b"mif1")


def _ftyp(head: bytes) -> str | None:
    """ISO base media files (``....ftyp<brand>``): QuickTime, M4A audio, HEIC or MP4."""
    if head[4:8] != b"ftyp":
        return None
    brand = head[8:12]
    if brand == b"qt  ":
        return "video/quicktime"
    if brand in (b"M4A ", b"M4B "):
        return "audio/mp4"
    if brand in _HEIC_BRANDS:
        return "image/heic"
    return "video/mp4"


def _riff(head: bytes) -> str | None:
    if head[:4] != b"RIFF":
        return None
    return {b"WAVE": "audio/wav", b"AVI ": "video/x-msvideo"}.get(head[8:12])


# MPEG audio frame headers (ISO/IEC 11172-3 and 13818-3). Bitrates in kbit/s for bitrate
# index 1 to 14, keyed by (MPEG-1 or not, layer number 1 to 3).
_MPEG_BITRATES_KBPS = {
    (True, 1): (32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448),
    (True, 2): (32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384),
    (True, 3): (32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
    (False, 1): (32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256),
    (False, 2): (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160),
    (False, 3): (8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160),
}
# Sample rates in Hz for sample-rate index 0 to 2, keyed by the version bits
# (3 is MPEG-1, 2 is MPEG-2, 0 is MPEG-2.5; 1 is reserved).
_MPEG_SAMPLE_RATES = {
    3: (44100, 48000, 32000),
    2: (22050, 24000, 16000),
    0: (11025, 12000, 8000),
}
_MPEG_VERSION_AND_LAYER = 0x1E  # byte 1: version bits 4-3, layer bits 2-1
_MPEG_SAMPLE_RATE = 0x0C  # byte 2: sample-rate index bits 3-2


def _mpeg_frame_length(header: bytes) -> int | None:
    """The length in bytes of the MPEG audio frame that starts with the four bytes ``header``,
    or ``None`` unless they are a frame header with every field valid. The largest legal frame
    is 2,881 bytes (MPEG-2.5 Layer II, 160 kbit/s, 8 kHz, padded)."""
    if len(header) < 4 or header[0] != 0xFF or header[1] & 0xE0 != 0xE0:
        return None
    version, layer_bits = (header[1] >> 3) & 3, (header[1] >> 1) & 3
    bitrate_index, rate_index = header[2] >> 4, (header[2] >> 2) & 3
    padding, emphasis = (header[2] >> 1) & 1, header[3] & 3
    if version == 1 or layer_bits == 0 or rate_index == 3 or emphasis == 2:
        return None
    if bitrate_index in (0, 0xF):  # free format has no computable length; 15 is reserved
        return None
    layer = 4 - layer_bits  # layer bits 11, 10, 01 are Layers I, II, III
    mpeg1 = version == 3
    bitrate = _MPEG_BITRATES_KBPS[(mpeg1, layer)][bitrate_index - 1] * 1000
    rate = _MPEG_SAMPLE_RATES[version][rate_index]
    if layer == 1:
        return (12 * bitrate // rate + padding) * 4
    if layer == 3 and not mpeg1:
        return 72 * bitrate // rate + padding
    return 144 * bitrate // rate + padding


def _mpeg_frame(head: bytes) -> str | None:
    """MPEG audio without an ID3 tag. A frame header counts only when the next frame's header
    follows at exactly the computed frame length, with the same version, layer and sample rate:
    one plausible header alone is too easy to meet by chance (the UTF-16LE mark ``FF FE`` is
    one)."""
    length = _mpeg_frame_length(head[:4])
    if length is None or len(head) < length + 4:
        return None
    second = head[length : length + 4]
    if _mpeg_frame_length(second) is None:
        return None
    if (head[1] ^ second[1]) & _MPEG_VERSION_AND_LAYER or (head[2] ^ second[2]) & _MPEG_SAMPLE_RATE:
        return None
    return "audio/mpeg"


# Text byte-order marks, longest first so a UTF-32LE mark is not read as UTF-16LE. They are
# checked before every rule in MAGIC_RULES: the UTF-16LE mark FF FE also looks like the start of
# an MPEG audio frame header.
_TEXT_BOMS = (
    b"\xff\xfe\x00\x00",  # UTF-32LE
    b"\x00\x00\xfe\xff",  # UTF-32BE
    b"\xef\xbb\xbf",  # UTF-8
    b"\xff\xfe",  # UTF-16LE
    b"\xfe\xff",  # UTF-16BE
)

# Checked in this order; the first match wins. A rule is a byte prefix or a function of the
# first HEAD_BYTES bytes. ZIP is told apart from OOXML and ODF by ``_zip_kind``.
MAGIC_RULES = (
    (b"%PDF-", "application/pdf"),
    (b"PK\x03\x04", ZIP),
    (bytes.fromhex("d0cf11e0a1b11ae1"), OLE2),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (_riff, None),
    (_ftyp, None),
    (b"\x1a\x45\xdf\xa3", "video/x-matroska"),
    (b"7z\xbc\xaf\x27\x1c", "application/x-7z-compressed"),
    (b"\x1f\x8b", "application/gzip"),
    (b"ID3", "audio/mpeg"),
    (_mpeg_frame, None),
    (b"OggS", "audio/ogg"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
)

# Content types that name a family rather than a format. When the file name names a member of
# the family, the name is the more precise answer and there is no mismatch.
AMBIGUOUS_FAMILIES = {
    OLE2: frozenset(
        {
            EXTENSION_TABLE["msg"],
            EXTENSION_TABLE["doc"],
            EXTENSION_TABLE["xls"],
            EXTENSION_TABLE["ppt"],
        }
    ),
    "video/x-matroska": frozenset({EXTENSION_TABLE["webm"]}),
    "video/mp4": frozenset({EXTENSION_TABLE["mov"], EXTENSION_TABLE["m4a"]}),
}
# Container formats that many other formats are built on (an .epub is a ZIP, a .3gp is MP4,
# an .opus is Ogg). A name outside the extension table that the fallback still recognises is
# more precise than the container, so it is kept and is not a mismatch.
_CONTAINERS = frozenset({ZIP, OLE2, "video/mp4", "video/x-matroska", "audio/ogg"})
_TABLE_TYPES = frozenset(EXTENSION_TABLE.values())


def _zip_kind(head: bytes, path) -> str:
    """OOXML, ODF or plain ZIP, from the first member's header and the member names only.
    Nothing is extracted; a damaged archive is simply ``application/zip``."""
    # ODF stores an uncompressed "mimetype" member first, so its value sits in the header.
    if head[26:30] == b"\x08\x00\x00\x00" and head[30:38] == b"mimetype":
        extra = int.from_bytes(head[28:30], "little")
        value = head[38 + extra : 38 + extra + 80].split(b"PK", 1)[0]
        try:
            text = value.decode("ascii").strip()
        except UnicodeDecodeError:
            text = ""
        if _ODF_TYPE.match(text):
            return text
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
    except Exception:  # BadZipFile, OSError, EOFError...: a damaged archive never stops a scan
        return ZIP
    if "[Content_Types].xml" in names:
        for prefix, kind in _OOXML_PARTS:
            if any(name.startswith(prefix) for name in names):
                return kind
    return ZIP


def sniff(path) -> str | None:
    """The type the first bytes of the file at ``path`` show, or ``None`` when they show none
    of the types in ``MAGIC_RULES`` (plain text, for example). A text byte-order mark means
    text, so it also gives ``None`` and the name decides, exactly as for text without a mark."""
    with open(path, "rb") as handle:
        head = handle.read(HEAD_BYTES)
    if head.startswith(_TEXT_BOMS):
        return None
    for rule, kind in MAGIC_RULES:
        if callable(rule):
            found = rule(head)
            if found:
                return found
        elif head.startswith(rule):
            return _zip_kind(head, path) if kind == ZIP else kind
    return None


def _agree(by_name: str, by_content: str) -> bool:
    if by_name == by_content or by_name in AMBIGUOUS_FAMILIES.get(by_content, ()):
        return True
    return by_content in _CONTAINERS and by_name not in _TABLE_TYPES


def detect(path):
    """``(mime, mismatch)`` for the file at ``path``.

    The content wins when ``sniff`` recognises it. ``mismatch`` is
    ``{"by_extension": ..., "by_content": ...}`` when the name suggests a different known type,
    and ``None`` otherwise, including for a name inside the content's family (an OLE2 ``.msg``
    keeps the Outlook type) and for content ``sniff`` does not recognise.
    """
    by_name = by_extension(PurePath(path).name)
    try:
        by_content = sniff(path)
    except OSError:
        by_content = None
    if by_content is None:
        return by_name, None
    if by_name == OCTET_STREAM:
        return by_content, None
    if _agree(by_name, by_content):
        return by_name, None  # the same type, or the name is the more precise member
    return by_content, {"by_extension": by_name, "by_content": by_content}
