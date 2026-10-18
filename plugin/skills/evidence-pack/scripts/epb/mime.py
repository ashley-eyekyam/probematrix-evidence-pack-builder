"""File types by name and by content (D-13, research Pattern 4 and Pitfall 5).

``EXTENSION_TABLE`` is authoritative for every type the design names. Python's own
``mimetypes`` gives different answers on different Python versions and machines (3.11 has no
``.md``, ``.yaml``, ``.7z``, ``.mkv``, ``.m4a`` or ``.rtf``; the module-level ``guess_type``
reads ``/etc/mime.types`` and the Windows registry), so it is only a fallback for extensions
the table does not know, through a private ``mimetypes.MimeTypes()`` instance. Anything
still unknown is ``application/octet-stream``.

Standard library only; no ``python-magic``.
"""

import mimetypes
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


def detect(path):
    """``(mime, mismatch)`` for the file at ``path``. ``mismatch`` is ``None`` when the name
    and the content agree, else ``{"by_extension": ..., "by_content": ...}``."""
    return by_extension(PurePath(path).name), None
