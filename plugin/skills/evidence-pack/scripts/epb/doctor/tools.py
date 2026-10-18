"""The doctor registry: optional external tools and optional Python extras (PKG-07, D-14).

Everything doctor reports about a tool comes from one row here, so adding a tool or fixing an
install command is a one-line edit. Rows are listed in the order doctor prints them; that
order is part of the output contract (two runs on one machine print identical text).

The macOS and Windows install commands are research assumptions (A6) that have not been run
on those systems; the user manual marks them "not yet tested on this system".

Standard library only: doctor runs before first-time setup.
"""

import sys
from dataclasses import dataclass, field

OS_IDS = ("linux", "macos", "windows")


def os_id(platform=None):
    """Map a ``sys.platform`` value to ``linux``, ``macos`` or ``windows``. Any other POSIX
    platform is treated as ``linux``."""
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        return "windows"
    if platform == "darwin":
        return "macos"
    return "linux"


@dataclass(frozen=True)
class ToolSpec:
    """One optional external program.

    ``names`` are tried in order on PATH; ``extra_paths`` maps an OS id to absolute fallback
    locations for installers that do not add the program to PATH. ``version_regex`` has one
    group, read from the program's combined stdout and stderr after running it with
    ``version_args``. ``in_use`` is False while the plugin does not use the tool yet.
    ``install`` maps each OS id to one install command.
    """

    id: str
    label: str
    names: tuple
    version_args: tuple
    version_regex: str
    enables: str
    in_use: bool
    install: dict
    extra_paths: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExtraSpec:
    """One optional group of Python packages, installed from its own requirements file."""

    id: str
    file: str
    packages: tuple
    licence: str
    enables: str
    in_use: bool = False


REGISTRY = (
    ToolSpec(
        id="7z",
        label="7-Zip",
        names=("7z", "7za", "7zz"),
        version_args=("i",),
        version_regex=r"7-Zip\s+(\d+(?:\.\d+)+)",
        enables=".7z archives",
        in_use=False,
        install={
            "linux": "sudo apt install 7zip",
            "macos": "brew install sevenzip",
            "windows": "winget install 7zip.7zip",
        },
        extra_paths={"windows": (r"C:\Program Files\7-Zip\7z.exe",)},
    ),
    ToolSpec(
        id="ffmpeg",
        label="ffmpeg",
        names=("ffmpeg",),
        version_args=("-version",),
        version_regex=r"ffmpeg version (\S+)",
        enables="audio and video recordings",
        in_use=False,
        install={
            "linux": "sudo apt install ffmpeg",
            "macos": "brew install ffmpeg",
            "windows": "winget install Gyan.FFmpeg",
        },
    ),
    ToolSpec(
        id="tesseract",
        label="Tesseract OCR",
        names=("tesseract",),
        version_args=("--version",),
        version_regex=r"tesseract v?(\S+)",
        enables="scanned pages and images of text",
        in_use=False,
        install={
            "linux": "sudo apt install tesseract-ocr",
            "macos": "brew install tesseract",
            "windows": "winget install UB-Mannheim.TesseractOCR",
        },
    ),
    ToolSpec(
        id="soffice",
        label="LibreOffice",
        names=("soffice", "libreoffice"),
        version_args=("--version",),
        version_regex=r"LibreOffice (\S+)",
        enables="ODT, RTF and older Office files",
        in_use=False,
        install={
            "linux": "sudo apt install libreoffice",
            "macos": "brew install --cask libreoffice",
            "windows": "winget install TheDocumentFoundation.LibreOffice",
        },
    ),
    ToolSpec(
        id="pandoc",
        label="pandoc",
        names=("pandoc",),
        version_args=("--version",),
        version_regex=r"pandoc (\S+)",
        enables="an extra converter for word-processor files",
        in_use=False,
        install={
            "linux": "sudo apt install pandoc",
            "macos": "brew install pandoc",
            "windows": "winget install JohnMacFarlane.Pandoc",
        },
    ),
    ToolSpec(
        id="git",
        label="git",
        names=("git",),
        version_args=("--version",),
        version_regex=r"git version (\S+)",
        enables="a warning when a case folder sits inside a git repository",
        in_use=True,
        install={
            "linux": "sudo apt install git",
            "macos": "brew install git",
            "windows": "winget install Git.Git",
        },
    ),
)

EXTRAS = (
    ExtraSpec(
        id="email",
        file="requirements-email.txt",
        packages=("extract-msg",),
        licence="GPL-3.0",
        enables="Outlook .msg emails",
    ),
    ExtraSpec(
        id="media",
        file="requirements-media.txt",
        packages=("faster-whisper",),
        licence="MIT; pulls GPL-licensed codec binaries",
        enables="local transcription of audio and video",
    ),
    ExtraSpec(
        id="docs",
        file="requirements-docs.txt",
        packages=("docling",),
        licence="MIT; large download",
        enables="layout-aware conversion of complex PDFs",
    ),
)
