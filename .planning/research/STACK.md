# Stack Research

**Domain:** Local, open-source evidence-conversion CLI (Python) packaged as an Agent Skills plugin for Claude Code, Cowork and OpenAI Codex
**Researched:** 2026-10-17
**Two-week cutoff applied:** nothing uploaded after **2026-10-03** is recommended
**Overall confidence:** HIGH for Python package facts, MEDIUM for host packaging, LOW for Cowork runtime details

## How this was verified

- **Python packages.** Every version, upload date, `Requires-Python`, licence and wheel tag below comes from the PyPI JSON API, queried on 2026-10-17. These facts were then checked by running the code:
  - `uv pip compile --exclude-newer 2026-10-03` for Python 3.10, 3.11 and 3.14 on Linux and Windows.
  - A clean venv on Python 3.14.4 using `pip install --uploaded-prior-to P14D`.
  - Small probe scripts that exercise python-docx, openpyxl, python-pptx, pypdf, Pillow, rapidfuzz and the reportlab→pdfplumber round trip.
  - All of this is rated **HIGH** because it was executed, not read.
- **Security advisories.** These come from the GitHub Security Advisory API for each repository. **HIGH.**
- **Host packaging.** Claude Code, Cowork, Agent Skills and Codex facts come from the vendors' official documentation pages, fetched on 2026-10-17.
  - The GSD `classify-confidence` seam rates `webfetch` as LOW and verified `websearch` as MEDIUM.
  - Claude Code facts are rated **MEDIUM** where three official pages agree: the plugins reference, the marketplace reference and claude.com platform-support.
  - Codex and Cowork runtime facts are rated **LOW–MEDIUM**.
- Context7 could not be used: its MCP server needs an OAuth login. Primary sources were used instead.

---

## Conflicts with design (need owner decision)

These items contradict, or materially change, design §5, §7.2, §13.4, §15 or §18, or the "no dependency younger than two weeks" rule. None has been resolved here. Each one needs an owner decision.

| # | Design says | Finding | Recommendation | Confidence |
|---|---|---|---|---|
| C1 | Python **3.10+** (§15.3, §18) | Python 3.10 reached **end of life on 2026-10-01**. The ecosystem has already moved past it: Pillow 13.0, rapidfuzz 3.14.6, soupsieve 3.0, rpds-py 2026.x, onnxruntime ≥1.26, PyAV ≥18, ocrmypdf 17, hypothesis and platformdirs all need **≥3.11**. Core still resolves on 3.10 today, but it freezes there. 3.10 users get Pillow 12.3.0 as their last Pillow, so any future Pillow CVE stays unpatched for them. Python 3.15.0 shipped on 2026-10-09, which is under two weeks ago. | Raise the floor to **Python 3.11**. CI runs 3.11–3.14. Add 3.15 as an allowed-failure job after 2026-10-23. If the owner keeps 3.10, CI must still test it, and README must say it is EOL. | HIGH |
| C2 | "No dependency younger than two weeks" (kickoff §7, §18) | pypdf published **six security advisories between 2026-10-12 and 2026-10-17**. They cover infinite loops on malformed xref tables, memory blow-ups on crafted arrays, and unvalidated JPEG data. They are fixed only in **6.20.0, 6.20.1, 6.21.0 and 6.21.1** (6.21.1 is not on PyPI yet), and every one of those releases is under two weeks old. This product parses untrusted PDFs by design. | Add a written **security exception**: a release that fixes a published advisory in a parser of untrusted input may be adopted early, after review. Until then, pin `pypdf>=6.19.0`. Run every PDF parse in a subprocess with a timeout and a memory cap, so a malicious PDF can only kill that one source (`unprocessed: parser timeout`). | HIGH |
| C3 | Scanned PDFs: **`ocrmypdf` + Tesseract** primary, with Tesseract on `pdftoppm` images as the fallback (§7.2) | (a) ocrmypdf writes a text layer or a sidecar `.txt` and **does not expose per-word OCR confidence**, which §7.3/§14 need. (b) ocrmypdf 17 needs **Python ≥3.11**, is MPL-2.0, and needs a manual Ghostscript install on Windows for PDF/A. (c) `pdftoppm` is Poppler, which is **GPL**. **pypdfium2** (BSD-3/Apache-2.0) already ships with pdfplumber and renders pages itself. | Make the primary path **pypdfium2 render → `tesseract … tsv` subprocess**. TSV gives a `conf` value for every word, which supplies segment confidence. Keep ocrmypdf as an optional **external CLI**, used only to produce a searchable or deskewed copy. Drop `pdftoppm`. | HIGH (ocrmypdf facts), MEDIUM (that its sidecar has no confidence) |
| C4 | Images "JPG/PNG/**HEIC**/TIFF" via **Pillow** (§7.2) | Pillow cannot open HEIC. The only pip route is **pillow-heif**. Its source is BSD-3, but its own `LICENSES_bundled.txt` says the **binary wheels are GPLv2**, because they bundle x265 plus LGPLv3 libheif and libde265. | Make HEIC an **optional GPL extra** (`requirements-heic.txt`), handled like extract-msg, or convert it through an external tool (`heif-convert` or macOS `sips`). Without either, HEIC is `unprocessed: HEIC decoder missing`. | HIGH |
| C5 | `requirements-media.txt`: faster-whisper plus **opencv-python-headless** for scene detection (§5) | (a) faster-whisper hard-depends on **PyAV**. The PyAV 19.0.0 manylinux wheel bundles **libx264 and libx265 (GPL)**, so the media extra is effectively GPL at the binary level, just like the email extra. (b) OpenCV is not needed: §7.2 already does scene detection with ffmpeg's `select='gt(scene,0.3)'`. (c) docling pulls in **opencv-python** (the GUI build). Having both opencv wheels in one environment causes a known `cv2` clash. | Document the media extra as **"pulls GPL-licensed binaries"** in INSTALL and README, as is already done for extract-msg. **Drop opencv-python-headless.** Do keyframes with the ffmpeg CLI and do any overlay crop or threshold work with Pillow. | HIGH (wheel inspected) |
| C6 | Codex: `.agents/skills -> ../skills` symlink plus `tools/install-codex.sh` "installs for all projects" (§5, §15.3) | (a) Codex scans `.agents/skills` only from the **cwd up to the repo root**. Users run in a *case folder*, not in this repo, so the symlink only helps contributors. (b) Codex now has **plugins**. `codex plugin marketplace add owner/repo` reads a repo's **`.claude-plugin/marketplace.json` as a "legacy-compatible" marketplace**. The native plugin manifest is a root `plugin.json` (Agent Plugins 1.0) or `.codex-plugin/plugin.json`. (c) The user-scope skills directory is **`$HOME/.agents/skills`**. A `.sh` installer does not run on native Windows. | Make Codex plugin install the primary route (`codex plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder`). Ship a **`.codex-plugin/plugin.json`** next to the Claude one. Keep `install-codex.sh` and add `install-codex.ps1` as the fallback; both copy `skills/*` into `$HOME/.agents/skills`. Keep the `.agents/skills` symlink for contributors only. A fresh-machine test must confirm which manifest Codex actually reads. | MEDIUM (marketplace), LOW (whether Codex reads `.claude-plugin/plugin.json`) |
| C7 | `CLAUDE.md` at the repo root saying "See @AGENTS.md" (§5) | The repo root **is** the plugin root. Claude Code docs: "A `CLAUDE.md` at the plugin root isn't loaded as context, and `claude plugin validate` warns when it finds one." | Move it to **`.claude/CLAUDE.md`**, which `.planning/config.json` already names as `claude_md_path`. Claude Code still loads it for contributors, and validation stays clean (`--strict` in CI). | MEDIUM |
| C8 | `plugin.json` sets `"skills": "./skills"` (§5, §15.3) | The `skills` key **adds to** the default `skills/` scan. Pointing it at the default directory is redundant at best. | Omit `skills` from `.claude-plugin/plugin.json`, since the default scan already finds `skills/<name>/SKILL.md`. Keep it only in the Codex manifest, where the official scaffold writes it. | MEDIUM |
| C9 | The repo root is the plugin, and the marketplace entry source is the repo itself (§5) | Every install copies the **whole repo** into the plugin cache and the user's Cowork account: tests, evals, samples and `docs/reference/hazira-2020/`, the official report that names real people. Cowork's limit is 200 MB and 5,000 files per plugin. It is not breached today (2.3 MB, 26 files), but the repo will grow. | Option A: keep it as designed and accept that reference material ships. Option B: move the shippable plugin into a subdirectory (e.g. `plugin/` holding `.claude-plugin/`, `skills/` and `schemas/`) with marketplace `source: "./plugin"`, so docs, tests and reference never ship. | MEDIUM |
| C10 | MIME detection via "python-magic or extension fallback" (§7.1) | python-magic needs the native libmagic library, which is absent on Windows, and its last release was 2022. | Use **stdlib `mimetypes` plus a small magic-byte table** (`%PDF`, `PK\x03\x04` → OOXML/zip, `D0 CF 11 E0` → OLE/.msg, JPEG/PNG/RIFF/ftyp). No new dependency. | HIGH |
| C11 | Archives: ".7z if available" (§7.1) | py7zr is **LGPL-2.1-or-later**. | Handle `.zip` with stdlib (with zip-slip and zip-bomb guards). Handle `.7z` only through an external `7z`/`7zz` binary if it is on PATH; otherwise `unprocessed: 7z missing`. | HIGH |
| C12 | Core `requirements.txt` list (§5) | Three core additions are justified by security or correctness: **`defusedxml`** (openpyxl uses it automatically when installed, and its XML flag is `False` without it), **`lxml>=6.1.0`** (fixes the XXE CVE-2026-41066 in a transitive dependency of python-docx and python-pptx), and **`charset-normalizer`** (CSV and TXT encoding detection; already a transitive dependency). | Add all three to core. Each is permissive (PSF-2.0, BSD-3, MIT). | HIGH |

---

## Recommended Stack

### Core Technologies (requirements.txt, all permissive, pure-Python or wheels on Windows, macOS and Linux)

**What the version columns mean:**
- **Current stable**: the newest release on PyPI, with its upload date.
- **≥2-wk-old resolved**: what `--uploaded-prior-to P14D` installs today.
- **Min pin**: the recommended floor in `requirements.txt`.

**How to read the Python column:** "3.10–3.14 ✓" means it installs and works on 3.10–3.14, with cp314 wheels or pure Python.

| Library | Current stable | ≥2-wk-old resolved | Min pin | Licence | Python | Purpose and why | Caveats | Conf. |
|---|---|---|---|---|---|---|---|---|
| **openpyxl** | 3.1.5 (2024-06-28) | 3.1.5 | `>=3.1.5` | MIT | 3.8+; works on 3.14 (probed) | Writes the importer-exact `EVIDENCE_PACK_V2` workbook and reads XLSX inputs. It is the only mainstream library that both reads and writes styled xlsx. Column widths use `ws.column_dimensions[c].width`. | **Probed on 3.14:** (1) A string starting with `=` becomes a **formula** (`data_type 'f'`). Set `cell.data_type = "s"` and `number_format = "@"` on every cell, which also keeps dates and hashes as text. (2) Control characters raise **`IllegalCharacterError`**, so sanitise with `openpyxl.cell.cell.ILLEGAL_CHARACTERS_RE`. (3) Strings are written as `inlineStr`. (4) No release since 2024, but it is stable and Python 3.14 works. Use `read_only=True` for big DCS/CMMS exports. | HIGH |
| **PyYAML** | 6.0.3 (2025-09-25) | 6.0.3 | `>=6.0.3` | MIT | 3.8+, cp314 wheels from 6.0.3 | `case.yaml`, items and rosters. | Always use `yaml.safe_load` and `safe_dump(sort_keys=False, allow_unicode=True)`. 6.0.2 has no cp314 wheels. | HIGH |
| **rapidfuzz** | 3.14.6 (2026-08-30) | 3.14.6 (on 3.10: 3.14.5) | `>=3.14.1` | MIT | 3.14.6 needs **≥3.11**; 3.14.1–3.14.5 support 3.10; cp314 wheels from 3.14.1 | Fuzzy matching for held-back conclusions (§11.3 gate 7), roster alias matching, and near-miss diagnostics in the quote verifier. | Verbatim verification itself must be **exact match after normalisation**, never a fuzzy score. Use rapidfuzz only for "did you mean" and conclusion screening. | HIGH |
| **pdfplumber** | 0.11.10 (2026-06-15) | 0.11.10 | `>=0.11.9` | MIT | 3.8+ (pure) | Per-page text, words with positions (for boilerplate, header and footer detection and printed page labels), and tables. | **Security floor:** pdfplumber pins pdfminer.six exactly, and **CVE-2025-64512** (arbitrary code execution through a pickle in the CMap loader) is fixed only in pdfminer.six ≥20251230. That means pdfplumber ≥0.11.9. pdfplumber 0.11.10 requires Pillow ≥12.2. `extract_text()` collapses double spaces (probed), so the verifier must normalise whitespace. | HIGH |
| ↳ pdfminer.six | 20260107 | 20260107 | transitive | MIT | ≥3.10 | pdfplumber engine | Pulls in `cryptography` (Apache-2.0 OR BSD-3). | HIGH |
| ↳ **pypdfium2** | 5.14.0 (2026-10-04) | 5.13.0 | transitive (use directly) | BSD-3 / Apache-2.0 | abi3 wheels for all three OSes | **Use it directly to render page images for OCR** (C3), replacing `pdftoppm`. | Has no cp-specific wheels, so it is Python-version agnostic. | HIGH |
| **pypdf** | 6.21.0 (2026-10-16) | **6.19.0** | `>=6.19.0` (see C2) | BSD-3 | 3.9+ (pure) | Fallback text extraction. Reads **`/PageLabels`** through `PdfReader.page_labels` (probed), the authoritative source for printed labels when a PDF defines them (§7.3). Also does metadata and attachment listing. | It has a high advisory rate: 8 advisories since 2026-09-16, all DoS-class. Isolate parsing (C2). | HIGH |
| **python-docx** | 1.2.0 (2025-06-16) | 1.2.0 | `>=1.2.0` | MIT | 3.9+ (pure) | Paragraphs, tables, headers and footers, and **comments**. 1.2.0 added `Document.comments` (probed: author and text read back). | **Probed:** `paragraph.text` **silently drops tracked insertions** (`w:ins`) and ignores deletions (`w:delText`). A tracked "not" disappears, which flips the meaning. python-docx has no revisions API, so tracked changes must be read through lxml XPath (`.//w:ins//w:t`, `.//w:del//w:delText`) and rendered explicitly as inserted or deleted. Build a DOCX fixture with tracked changes in Phase 2. | HIGH |
| **python-pptx** | 1.0.2 (2024-08-07) | 1.0.2 | `>=1.0.2` | MIT | 3.8+; works on 3.14 with no deprecation warnings (probed) | Slide text, tables and speaker notes (probed). | Upstream has been dormant (last push Aug 2024). It is stable, but plan to read raw XML with lxml if needed. Pulls in XlsxWriter (BSD-2). | HIGH |
| **beautifulsoup4** | 4.15.0 (2026-06-07) | 4.15.0 | `>=4.13` | MIT | 3.7+ | HTML inputs, email HTML bodies, web snapshots. | soupsieve 3.0 (2026-10-12) needs ≥3.11.5. Pip backtracks to 2.10 on 3.10, and the two-week rule also selects 2.10. Use the `lxml` parser. | HIGH |
| **markdownify** | 1.2.3 (2026-06-30) | 1.2.3 | `>=1.2.0` | MIT | pure | HTML to Markdown, keeping tables and lists. | Adds `six`. For **evidence**, convert the *whole* document after stripping only `script`, `style` and `noscript`. Readability-style trimming is for web snapshots only (see trafilatura). | HIGH |
| **Pillow** | 13.0.0 (2026-10-16, too new) | **12.3.0** | `>=12.3.0` | MIT-CMU | 12.x: 3.10+; 13.x: 3.11+ | EXIF capture time and device. **GPS stripping** (GPS IFD tag 34853). Keyframe crops for overlay OCR. Scanned-PDF fixture generation (`img.save(x.pdf)`). | **Security floor:** 4 CVEs (heap out-of-bounds writes, decompression-bomb bypasses) fixed in 12.3.0. For shareable images, `ImageOps.exif_transpose` then **re-encode the pixels only**. Deleting the GPS IFD is not enough: XMP (`img.info["xmp"]`) and maker notes can also carry location. No HEIC support (C4). | HIGH |
| **jsonschema** | 4.26.0 (2026-01-07) | 4.26.0 | `>=4.25` | MIT | 4.26: 3.10+ | Validates `schemas/*.json` (source, segment, claim, item, conflict, state) on `claims add` and `items add`. | Pulls in rpds-py, a Rust wheel: 2026.x needs ≥3.11, and 3.10 resolves to 0.30.0. Use `Draft202012Validator`. | HIGH |
| **lxml** (add, C12) | 6.1.3 (2026-09-02) | 6.1.3 | `>=6.1.0` | BSD-3 | cp310–cp315 wheels | Already a dependency of docx and pptx. Pin it explicitly for the **XXE fix CVE-2026-41066**, and use it for tracked changes and raw-XML fallbacks. | First cp314 wheels arrived in 6.0.1. | HIGH |
| **defusedxml** (add, C12) | 0.7.1 (2021) | 0.7.1 | `>=0.7.1` | PSF-2.0 | pure | openpyxl switches to defused parsing automatically when this is installed (probe: `openpyxl.xml.DEFUSEDXML == False` without it). Guards against billion-laughs attacks in untrusted XLSX. | Old but complete. Also a docling dependency. | HIGH |
| **charset-normalizer** (add, C12) | 3.5.2 (2026-09-30) | 3.5.2 | `>=3.4.3` | MIT | wheels for all three OSes, cp314 | Encoding detection for CSV, TXT and chat exports. Already transitive via pdfminer.six. | Record the detected encoding in the source record. | HIGH |
| **stdlib** | n/a | n/a | n/a | PSF | n/a | `email` (with `policy.default`) for .eml and attachments, `csv`, `zipfile`, `hashlib` (SHA-256), `pathlib`, `subprocess`, `json`, `mimetypes`, `wave`. | Use `email.policy.default`, not compat32, for correct RFC 2047 decoding of headers. | HIGH |

**Verified license sweep:** a full transitive install of the core set on Python 3.14 found these licences only:

MIT, MIT-0, MIT-CMU, BSD-2, BSD-3, Apache-2.0 OR BSD-3, PSF-2.0, and pypdfium2's BSD-3/Apache-2.0.

There is **no GPL, LGPL or AGPL** anywhere in core, and **PyMuPDF (AGPL) is not pulled in by anything** in core or any recommended extra. Keep it out explicitly: no `pymupdf` or `pymupdf4llm`. **HIGH.**

### Optional extras (separate requirements files; a missing extra marks inputs `unprocessed`, never fails a run)

| Extra / tool | Current stable | ≥2-wk-old resolved | Min pin | Licence (effective) | Python / OS | Purpose | Caveats | Conf. |
|---|---|---|---|---|---|---|---|---|
| **extract-msg** (`requirements-email.txt`) | 0.56.1 (2026-08-14) | 0.56.1 | `>=0.55` | **GPL-3.0** (transitive: RTFDE LGPL-3.0, pcodedmp GPL) | pure; 3.10–3.14 | Outlook `.msg` body, headers and attachments | As the design says: optional, GPL, never imported by core code paths. Lazy-import only inside the `.msg` converter. | HIGH |
| python-oxmsg (alternative to evaluate) | 0.0.2 (2025-02-03) | 0.0.2 | n/a | **MIT** (deps: olefile BSD, click BSD) | pure | Possible permissive `.msg` reader. docling's standard extra uses it. | Immature (3 commits, v0.0.x). Body and RTF coverage unverified. Spike it in the email phase. If adequate, `.msg` could become permissive. | LOW |
| **faster-whisper** (`requirements-media.txt`) | 1.2.1 (2025-10-31) | 1.2.1 | `>=1.2.1` | MIT, but **PyAV wheels bundle GPL x264 and x265** (C5) | 3.9+. Resolves on 3.10 (av 17.1, onnxruntime 1.23.2) and 3.14 (av 19.0, ort 1.30). **No macOS x86_64 wheels** for onnxruntime or torch-era stacks | Local transcription with word timestamps and per-segment `avg_logprob` / `no_speech_prob` (confidence) | Models download from Hugging Face on first use, which is the only network step. `doctor` must report whether the model is cached, and runs should set `HF_HUB_OFFLINE=1` after setup. The repo is active (pushed 2026-10-16) even though the last release was a year ago. Default model `small` (§19). CI uses `tiny`. Pass a 16 kHz mono numpy array from the ffmpeg CLI if PyAV decoding misbehaves. | HIGH (deps), MEDIUM (runtime) |
| ↳ ctranslate2 | 4.8.3 (2026-10-13) | 4.8.2 | `>=4.6.1` | MIT | cp314 from 4.6.1; wheels for macOS arm64 and x86_64, Linux and Windows | Inference engine | GPU is optional; CPU int8 is the default. | HIGH |
| **ffmpeg** (system binary) | 9.0.2 (2026-09-18) | 9.0.x / 8.1.x | `>=6.0` | LGPL-2.1+ or GPL-2+, depending on build; called as a **subprocess**, so no licence effect on MIT code | Windows (winget/choco), macOS (brew), Linux (apt) | Audio extraction to 16 kHz wav, scene-change keyframes, timestamp-overlay test fixtures (`drawtext`, which needs libfreetype) | Detect it with `ffmpeg -version`. Some minimal builds lack `drawtext`, so the fixture test must skip cleanly. | HIGH |
| **Tesseract** (system binary) | 5.5.3 (2026-07-24) | 5.5.3 | `>=5.0` | Apache-2.0; tessdata Apache-2.0 | Windows (UB Mannheim build via winget), macOS (brew + `tesseract-lang`), Linux (apt `tesseract-ocr-<lang>`) | OCR for scanned pages and CCTV overlays. **Call `tesseract img - -l <langs> tsv` directly** for per-word `conf` (C3). | `doctor` checks `tesseract --list-langs` against `case.yaml` languages (§13.3a). Prefer `tessdata_best` for Devanagari and Gujarati. Do not add pytesseract: it is a thin wrapper, its last release was 2024, and a 30-line subprocess wrapper is clearer. | HIGH |
| ocrmypdf (external CLI, optional) | 17.13.0 (2026-09-28) | 17.13.0 | `>=17` | MPL-2.0; deps pikepdf MPL-2.0, fpdf2 **LGPL-3.0**; Ghostscript (AGPL) now optional | **Python ≥3.11**; install with `uv tool install ocrmypdf`, `brew install ocrmypdf` or apt | Optional only: deskewed, searchable PDF copies (C3) | Never import it into the epb environment. Run it as a separate tool, which keeps its Python floor and licences isolated. | HIGH |
| **docling** (`requirements-docs.txt`) | 2.140.0 (2026-10-16) | 2.132.0 (2026-10-01) | Floor = the version proven in the Phase 7 spike | MIT; pulls in torch (BSD), transformers (Apache), rapidocr (Apache), **opencv-python**; no PyMuPDF | 3.10–3.14; **no torch wheels for macOS x86_64**; arm64 needs macOS 14+ | Layout- and table-aware PDF and DOCX to Markdown for complex reports | Heavy install (torch plus models from Hugging Face on first use). It releases almost daily, so the two-week rule matters here. Conflicts with opencv-python-headless (C5). Model weights carry their own licences, which need checking before docling becomes the default (§19). | MEDIUM |
| **spaCy + en_core_web_sm** (`requirements-nlp.txt`) | spacy 3.8.16 (2026-08-24); model 3.8.0 | 3.8.16 | `spacy>=3.8.10` (first cp314 wheels) | MIT; the model is MIT | 3.9–3.14 | Third de-identification net (§13.1) | The model is **not on PyPI**: pin the direct wheel URL `en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl`. `--uploaded-prior-to` does not apply to direct URLs. English only. Check the licence of any multilingual model (e.g. `xx_ent_wiki_sm`) before adopting it. | MEDIUM |
| **trafilatura** (`requirements-web.txt`) | 2.3.1 (2026-10-06) | 2.3.0 | `>=2.0` | Apache-2.0. Transitive: courlan and htmldate Apache-2.0, dateparser BSD-3, justext BSD-2, tld tri-licensed (MPL-1.1 OR GPL OR LGPL, so use MPL), certifi MPL-2.0 | 3.10–3.15 | **Web snapshots only** (§7.9): main-content extraction and publish-date metadata for dated snapshots | Never apply it to user-supplied HTML evidence, because it discards content by design. Do not use readability-lxml: 0.9 pins `chardet<6`, which is LGPL. | HIGH |
| pillow-heif (`requirements-heic.txt`, C4) | 1.8.1 (2026-10-11) | 1.8.0 | `>=1.8.0` | **GPLv2 binary wheels** | 3.10–3.15 | HEIC decoding | GPL extra, or use an external `heif-convert` / `sips`. | HIGH |
| pyannote.audio (not shipped) | 4.0.7 | 4.0.7 | n/a | MIT code, gated model licence | torch stack | Diarisation (§7.2: optional) | Document it only. The model requires accepting the Hugging Face terms, as the design already notes. | MEDIUM |
| LibreOffice / pandoc (external) | any recent | n/a | n/a | MPL-2.0 / GPL-2+ binaries, called as a subprocess | all three OSes | ODT and RTF fallback (§7.2) | For RTF only, **striprtf** (BSD-3, pure Python, 0.0.33) is a lighter optional fallback. Do not use odfpy, which has had no release since 2020. | MEDIUM |

### Development Tools (`requirements-dev.txt`)

| Tool | Current stable | ≥2-wk-old resolved | Min pin | Licence | Notes | Conf. |
|---|---|---|---|---|---|---|
| **pytest** | 9.1.1 (2026-06-19) | 9.1.1 | `>=9.0` | MIT | Run with `--no-network`-style discipline: mark network tests and never run them in CI. Optional-tool tests use `pytest.importorskip` / `shutil.which` with a reason string. | HIGH |
| **ruff** | 0.17.1 (2026-10-15, too new) | **0.16.10** | `==0.16.10` exact | MIT | Pin exactly, because rule sets change between minor versions. Use it as both linter and formatter. Wheels for all three OSes. | HIGH |
| **reportlab** | 5.0.1 (2026-08-20) | 5.0.1 | `>=5.0.1` | BSD | Builds text-PDF fixtures at test time. **Probed:** it draws curly quotes in core Helvetica and pdfplumber extracts them; "Page N of M" footers round-trip. Core fonts are WinAnsi only, so Devanagari or Gujarati fixtures need an embedded OFL TTF (Noto Sans Devanagari or Gujarati). Do not use fpdf2, which is LGPL-3.0. | HIGH |
| Pillow (already core) | | | | | Generates image-only "scanned" PDF fixtures (`Image.save("x.pdf")`), with no extra dependency. | HIGH |
| python-docx + lxml (core) | | | | | Generates DOCX fixtures with tracked changes and comments (probed). | HIGH |
| hypothesis (optional) | 6.170.1 (too new) | 6.168.3 | `>=6.130` | **MPL-2.0** (dev-only, so it doesn't affect shipped code) | Needs ≥3.11. Useful for property tests of quote normalisation, ellipsis fragments and cross-page spans. | MEDIUM |
| **pip** | 26.2.1 (2026-08-04) | 26.2.1 | `>=26.1` | MIT | **Enforces the two-week rule:** `pip install --uploaded-prior-to P14D …`. 26.0 added the flag and 26.1 added `P<n>D` durations. **Probed:** the pip bundled by `python -m venv` on 3.14.4 is **25.1.1**, which rejects the flag, so INSTALL must upgrade pip first. Setting the `PIP_UPLOADED_PRIOR_TO` env var also works. | HIGH |
| **uv** (optional fast path) | 0.13.1 (too new) | 0.12.22 | any ≥0.12 | MIT OR Apache-2.0 | `uv pip install --exclude-newer "14 days"`, or `exclude-newer = "14 days"` in config. Friendly and ISO-8601 durations are supported. Also usable for PEP 723 inline metadata in `epb.py` if the owner wants zero-setup runs where uv exists. | MEDIUM |

---

## Host packaging (Claude Code, Cowork, Codex, Agent Skills)

### Agent Skills SKILL.md (agentskills.io specification) — MEDIUM

- **Required frontmatter:**
  - `name`: 1–64 characters, lowercase `a-z0-9-` only, no leading, trailing or double hyphen. It **must match the parent directory name**, which all seven design names satisfy.
  - `description`: 1–**1,024** characters. Say what the skill does and when to use it.
- **Optional frontmatter:** `license`, `compatibility` (≤500 characters, the right place for "Requires Python 3.11+; optional ffmpeg, tesseract"), `metadata` (string to string), and `allowed-tools` (experimental).
- **Use only these six keys.** Claude Code ignores unknown keys, but **packaging for claude.ai or Cowork fails hard on unknown frontmatter keys** (for example `argument-hint`). Claude Code also truncates `description` plus `when_to_use` at 1,536 characters. Keep descriptions under 1,024 characters with the trigger first.
- **Size:** the spec says to keep SKILL.md under 500 lines and under 5k tokens. The design's ~150-line cap is stricter, which is fine.
- **References:** use relative paths from the skill root, one level deep. The design's cross-skill links into `skills/evidence-pack/references/` work inside a whole-plugin install. They **break if a single skill is installed on its own**, for example copied into `$HOME/.agents/skills/`. The installer must therefore copy all seven skills together. Each sub-skill should reference `../evidence-pack/...` and say so.
- **Validator:** `skills-ref validate ./skills/<name>`. Add it to CI.

### Claude Code plugin (`.claude-plugin/plugin.json`) — MEDIUM

- `name` is the **only required field**. It must be kebab-case. Names that begin `claude-` or `anthropic-` are reserved; `probematrix-evidence-pack-builder` is fine.
- Also set: `version`, `description`, `author{name}`, `homepage`, `repository`, `license: "MIT"`, `keywords`.
- **`version` pins users** until you change it, so bump it every release.
- **Default layout:** `skills/<name>/SKILL.md` is scanned automatically, so omit the `skills` key (C8).
- **Do not add a top-level `bin/`**: claude.ai and Cowork refuse any plugin that has one. The design has none, so keep it that way.
- **Substitutions in SKILL.md bodies:** `${CLAUDE_SKILL_DIR}` (this skill's directory), `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` (persistent across updates).
  - These are **not** set in the Bash tool's environment. They are substituted textually into skill content.
  - Write the CLI call as `python "${CLAUDE_PLUGIN_ROOT}/skills/evidence-pack/scripts/epb.py" …` for Claude Code.
  - Give a host-neutral fallback ("the `scripts/epb.py` beside the evidence-pack SKILL.md") for Codex.
- **Validation:** `claude plugin validate . --strict` in CI.
  - It warns on a root `CLAUDE.md` (C7), unknown fields and a missing version.
  - It errors on paths that escape the plugin root, or paths containing `..`.
- **Python dependencies are not installed by Claude Code.** It only auto-installs Node package dependencies. This is a **design gap**: see Gaps.

### Claude Code / Cowork marketplace (`.claude-plugin/marketplace.json`) — MEDIUM

- **Required fields:** `name`, `owner{name}`, `plugins[]`. Each entry needs `name` and `source`.
- **Plugin at the repo root:** use `"source": "./"` (relative paths must start with `./`; `"."` also denotes the root).
- **Marketplace name rules:** letters, digits, `.`, `_`, `-`, no reserved or official-looking names. `probematrix-evidence-pack-builder` is valid (§18).
- **Keep the entry `name` equal to the manifest `name`.** Put `version` in **one** place only (plugin.json wins, and validation warns on a mismatch).
- **Install for users:**
  - `claude plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder`
  - then `claude plugin install probematrix-evidence-pack-builder@probematrix-evidence-pack-builder`
- **Cowork:** **Customize → Plugins → Add marketplace** with `owner/repo`. Cowork accepts GitHub, plus public GitLab and Bitbucket.
  - Limits are 200 MB and 5,000 files per plugin.
  - A plugin installed on the account also syncs to Claude Code and chat.
  - In chat, skills load but **agents and hooks are ignored**, and no local tools are available, so text intake is the only realistic baseline there.
  - Cowork's runtime (whether pip can install packages, whether ffmpeg or tesseract exist) is **not documented**, which keeps §18's "doctor decides" correct. **LOW.**

### Codex — LOW to MEDIUM

- **Skills scopes:**
  - Repo scope: `.agents/skills` in each directory from cwd up to the repo root.
  - User scope: **`$HOME/.agents/skills`**.
  - Admin scope: `/etc/codex/skills`.
- **Symlinks:** symlinked skill folders are followed.
- **Invocation:** explicitly with `$skill-name` or `/skills`, or implicitly by matching the description.
- **Optional `agents/openai.yaml`:** inside a skill, for UI metadata and `policy.allow_implicit_invocation`.
- **Duplicate names:** two skills with the same `name` are not merged, so other `evidence-*` skills in the user scope would duplicate.
- **Plugins (current recommended distribution):**
  - Add a marketplace with `codex plugin marketplace add owner/repo [--ref]`.
  - Marketplace locations: `.agents/plugins/marketplace.json`, `~/.agents/plugins/marketplace.json`, and the legacy-compatible **`.claude-plugin/marketplace.json`**.
  - Native Codex marketplace entries require `policy.installation`, `policy.authentication` and `category`. Whether the legacy Claude file needs them is undocumented.
  - Manifest: root `plugin.json` per **Agent Plugins 1.0** (`$schema: https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`, required `$schema` and `name`, closed schema), or `.codex-plugin/plugin.json` as the compatibility layout.
  - Install cache: `~/.codex/plugins/cache/<marketplace>/<plugin>/<version>/`.
  - Enable with `[plugins."<plugin>@<marketplace>"] enabled = true` in `config.toml`.
- **AGENTS.md:** Codex reads `AGENTS.md` from the user's *working project*, not from installed plugins. This repo's AGENTS.md therefore serves contributors only, and **skills must be self-sufficient**.
- **Sandbox:** Codex's default sandbox usually blocks network. Dependency installation should therefore happen outside the agent session (the README install step), or the user must approve it. **LOW.**

---

## Installation

```bash
# 0. Use Python 3.11+ (see C1). On Windows use `py -3.12` / `python`, not `python3`.
python -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -U "pip>=26.1"                # venv-bundled pip (25.x) lacks --uploaded-prior-to

# 1. Core (all permissive) - two-week rule enforced by pip itself
python -m pip install --uploaded-prior-to P14D -r requirements.txt

# 2. Optional extras (each documented with its effective licence)
python -m pip install --uploaded-prior-to P14D -r requirements-media.txt   # faster-whisper (PyAV wheels: GPL codecs)
python -m pip install --uploaded-prior-to P14D -r requirements-email.txt   # extract-msg (GPL-3.0)
python -m pip install --uploaded-prior-to P14D -r requirements-docs.txt    # docling (heavy, torch)
python -m pip install --uploaded-prior-to P14D -r requirements-nlp.txt     # spaCy + en_core_web_sm (direct URL)
python -m pip install --uploaded-prior-to P14D -r requirements-web.txt     # trafilatura (web-snapshot skill only)
python -m pip install --uploaded-prior-to P14D -r requirements-heic.txt    # pillow-heif (GPLv2 wheels) - if owner accepts C4

# 3. System tools (optional; detected by `epb doctor`)
#    macOS:   brew install ffmpeg tesseract tesseract-lang
#    Ubuntu:  sudo apt install ffmpeg tesseract-ocr tesseract-ocr-hin tesseract-ocr-guj
#    Windows: winget install Gyan.FFmpeg UB-Mannheim.TesseractOCR
#    Optional searchable-PDF copies: uv tool install ocrmypdf   (separate env, Python >=3.11)

# Dev
python -m pip install --uploaded-prior-to P14D -r requirements-dev.txt
```

`requirements.txt` (proposed):
```
openpyxl>=3.1.5
PyYAML>=6.0.3
rapidfuzz>=3.14.1
pdfplumber>=0.11.9        # pdfminer.six CVE-2025-64512 fix
pypdf>=6.19.0             # see C2 for the security-exception question
python-docx>=1.2.0        # comments API
python-pptx>=1.0.2
beautifulsoup4>=4.13
markdownify>=1.2.0
Pillow>=12.3.0            # 4 CVEs fixed in 12.3.0
jsonschema>=4.25
lxml>=6.1.0               # XXE CVE-2026-41066 (C12)
defusedxml>=0.7.1         # openpyxl hardening (C12)
charset-normalizer>=3.4.3 # CSV/TXT encoding (C12)
```

`requirements-dev.txt`: `-r requirements.txt`, `pytest>=9.0`, `ruff==0.16.10`, `reportlab>=5.0.1`, optionally `hypothesis>=6.130`.

It must **not** blanket-include the GPL extras (email, media, heic). The design's "dev = pytest, ruff + all optional" would make every contributor environment GPL-tainted. Use a separate `requirements-dev-full.txt` for the CI media job instead.

---

## Alternatives Considered

| Recommended | Alternative | When to use the alternative |
|---|---|---|
| openpyxl (read and write) | XlsxWriter (BSD-2, already transitive via python-pptx) | If writer-side control matters more than one library. `write_string()` never coerces to a formula, and it writes shared strings exactly as Excel does. It cannot read, so the validator would still need openpyxl. |
| pdfplumber + pypdf | PyMuPDF / pymupdf4llm | **Never.** AGPL-3.0. |
| pypdfium2 render + Tesseract TSV | ocrmypdf | Only to produce a searchable or deskewed PDF copy for the user (external CLI). |
| Tesseract (subprocess) | tesserocr (MIT, C-API binding) | No Windows wheels, so it breaks parity across the three OSes. |
| Tesseract | EasyOCR / RapidOCR (Apache-2.0) | Possibly for scripts where Tesseract is weak. Both pull in torch or onnxruntime and opencv. Keep them out of v0.1.0. |
| faster-whisper | openai-whisper (MIT, torch) or whisper.cpp bindings | openai-whisper is heavier and slower on CPU. whisper.cpp bindings are less standard in Python and confidence data is harder to get. |
| ffmpeg CLI scene filter | opencv-python-headless | Not needed (C5). |
| stdlib mimetypes + magic bytes | python-magic / filetype | python-magic needs libmagic, which is absent on Windows. filetype (MIT) is acceptable but adds little. |
| extract-msg (GPL extra) | python-oxmsg (MIT) | If a spike shows it handles bodies and attachments adequately, `.msg` could become permissive. |
| bs4 + markdownify (whole document) | trafilatura | Web snapshots only. |
| jsonschema | fastjsonschema (BSD-3, pure Python, 2.22.2) | If the rpds-py Rust wheel becomes a portability problem. It generates code; error messages are weaker. |
| pip `--uploaded-prior-to P14D` | uv `--exclude-newer "14 days"` | Contributors who already use uv. CI can use either. |

## What NOT to Use

| Avoid | Why | Use instead |
|---|---|---|
| PyMuPDF, pymupdf4llm, `fitz` | AGPL-3.0, incompatible with a permissive core | pdfplumber + pypdfium2 + pypdf |
| `paragraph.text` from python-docx for evidence | Silently drops tracked insertions (probed) | lxml walk over `w:p` handling `w:ins`, `w:del`, `w:moveFrom` and `w:moveTo` |
| Fuzzy scores as quote verification | One invented quote fails the product | Exact match after documented normalisation. rapidfuzz only for diagnostics and conclusion screening. |
| pdftoppm / Poppler | GPL, and a separate system install | pypdfium2 (already installed) |
| pytesseract | Thin wrapper, last release 2024, hides TSV confidence handling | Own `subprocess.run(["tesseract", img, "-", "-l", langs, "tsv"])` |
| opencv-python-headless | Redundant, and conflicts with docling's opencv-python | ffmpeg + Pillow |
| readability-lxml | Pins LGPL chardet<6 | trafilatura (web only) |
| fpdf2 (for fixtures) | LGPL-3.0 | reportlab (BSD) |
| py7zr | LGPL-2.1+ | External `7z` binary, optional |
| python-magic | libmagic is missing on Windows | stdlib + magic bytes |
| `yaml.load` / pickle anywhere | Arbitrary code execution | `yaml.safe_load`, JSON |
| Unknown SKILL.md frontmatter keys | claude.ai and Cowork packaging hard-fails | The six spec keys only |
| A top-level `bin/` in the plugin | Cowork and claude.ai refuse the plugin | `skills/evidence-pack/scripts/epb.py` |
| `python3` in skill instructions | Missing on Windows or pointing at the Store stub | Detect `python` / `py -3` / `python3`. `doctor` records the working interpreter. |

## Stack Patterns by Variant

**If the host is Claude Code (full local machine):**
- Use every extra the user installed. Fan extraction out to subagents (§15.3).
- Reference the CLI through `${CLAUDE_PLUGIN_ROOT}`.

**If the host is Cowork:**
- Assume text-document intake only, until `doctor` proves which tools exist.
- Never rely on hooks or `bin/`. Keep frontmatter spec-pure.

**If the host is Codex:**
- Run extraction sequentially.
- Resolve the CLI path from the skill's own location.
- Expect a sandbox without network: install dependencies before the session.

**If the platform is Windows:**
- No symlinks at runtime.
- Use `py`/`python` rather than `python3`.
- Ship `install-codex.ps1`.
- Tesseract and ffmpeg come from winget.
- Long paths: use `pathlib` and avoid deep `.epb/` nesting.

**If the platform is an Intel Mac:**
- Media and docling extras may not install, because current onnxruntime and torch ship no x86_64 macOS wheels.
- `doctor` must report this as `unprocessed: <tool> unavailable on this platform`.

## Version Compatibility

| Package | Compatible with | Notes |
|---|---|---|
| pdfplumber 0.11.9–0.11.10 | pdfminer.six ==20251230 / ==20260107 (exact pins) | Never pin pdfminer.six separately. Let pdfplumber choose. |
| pdfplumber 0.11.10 | Pillow ≥12.2 | Fine with the Pillow ≥12.3 floor. |
| docling 2.13x | Pillow <13, opencv-python 5.x | Conflicts with opencv-python-headless and blocks Pillow 13. |
| faster-whisper 1.2.1 | av ≥11, onnxruntime <2, ctranslate2 <5 | On 3.10 the resolver picks av 17.1 and ort 1.23.2. On 3.14 it picks av 19.0 and ort 1.30. |
| ocrmypdf 17 | Python ≥3.11, pdfminer.six ≥20260107 | Keep it out of the epb environment, as an external tool. |
| beautifulsoup4 4.15 | soupsieve 2.10 (3.10) / 3.0.x (≥3.11.5) | Automatic, through Requires-Python. |
| jsonschema 4.26 | rpds-py 0.30 (3.10) / 2026.x (≥3.11) | Automatic. |
| Python 3.15 | Partial wheel coverage | Pillow 13, lxml, rapidfuzz and pyyaml have cp315 or abi3 wheels. Not all do. Add it as allowed-failure after 2026-10-23. |

## Gaps (not conflicts, but unspecified by the design)

1. **How Python dependencies reach the user's machine on each host.** None of the three hosts installs Python packages for a plugin.
   - Proposal: keep `epb.py` **stdlib-only up to a bootstrap point**, so `doctor` always runs and exits with code 3 on missing dependencies.
   - Add `epb doctor --setup`, which creates one venv in a user data directory (`~/.epb/venv`, or `${CLAUDE_PLUGIN_DATA}` when present) with the two-week pip flag.
   - `epb.py` then re-executes itself inside that venv.
   - This needs owner sign-off.
2. **Transcription test fixture.** The design wants fixtures generated at test time, but there is no permissive offline TTS to synthesise speech. A tiny committed synthetic-voice wav (generated once, documented) is probably required.
3. **Two-week rule enforcement in CI.** Run `pip install --uploaded-prior-to P14D` in CI, and add a check script that fails if any locked version was uploaded less than 14 days ago. A security-exception list is needed if C2 is accepted.
4. **Docling and spaCy model licences** must be checked before either becomes a default.

## Sources

- PyPI JSON API, `https://pypi.org/pypi/<pkg>/json` and `/<pkg>/<ver>/json`, for every package above: versions, upload dates, Requires-Python, licence expressions and wheel tags. Queried 2026-10-17. **HIGH (registry, executed).**
- Local verification on Python 3.14.4:
  - `uv pip compile --exclude-newer 2026-10-03T00:00:00Z` on 3.10, 3.11 and 3.14, for Linux and `x86_64-pc-windows-msvc`.
  - A venv install with pip 26.2.1 `--uploaded-prior-to P14D`.
  - Probes of python-docx (tracked changes and comments), openpyxl (formula coercion, IllegalCharacterError, text cells, width), python-pptx (notes), pypdf (`page_labels`), Pillow (GPS IFD), and reportlab→pdfplumber.
  - Transitive licence sweep via `importlib.metadata`.
  - PyAV 19.0.0 wheel inspection (bundled libx264 and libx265).
  - **HIGH.**
- GitHub Security Advisories API for pdfminer.six (CVE-2025-64512), pypdf (2026-09/10 advisories), Pillow (CVE-2026-59205, -59199, -55380, -54060) and lxml (CVE-2026-41066). **HIGH.**
- GitHub releases API for Tesseract 5.5.3, OCRmyPDF 17.13.0, faster-whisper, docling and spacy-models. **HIGH.**
- endoflife.date API for Python: 3.10 EOL 2026-10-01; 3.15.0 released 2026-10-09; ffmpeg 9.0.2. **MEDIUM.**
- pillow-heif `LICENSES_bundled.txt` (raw GitHub), stating "binary wheels: GPLv2". **HIGH.**
- pip NEWS.rst: `--uploaded-prior-to` in 26.0 (2026-01-30), `P<n>D` in 26.1 (2026-04-26). pip install docs. **HIGH.**
- uv settings reference: `exclude-newer` friendly and ISO-8601 durations. **MEDIUM.**
- OCRmyPDF installation docs: Python ≥3.11, Ghostscript optional, pypdfium2 rasterizer, fpdf2 renderer, Windows notes. **MEDIUM.**
- Claude Code docs:
  - https://code.claude.com/docs/en/plugins-reference (manifest fields, skills adds-to-default, root CLAUDE.md warning, `bin/`, env vars)
  - https://code.claude.com/docs/en/plugins/marketplace-reference (marketplace schema, reserved names, `./` sources)
  - https://code.claude.com/docs/en/plugin-marketplaces
  - https://code.claude.com/docs/en/skills (frontmatter extensions, 1,536-character cap, `${CLAUDE_SKILL_DIR}`, unknown keys hard-fail on claude.ai packaging)
  - **MEDIUM.**
- claude.com docs:
  - https://claude.com/docs/cowork/guide/plugins (Cowork install and limits)
  - https://claude.com/docs/plugins/overview
  - https://claude.com/docs/plugins/platform-support (per-surface component table; `bin/` refused)
  - **MEDIUM.**
- Agent Skills specification, https://agentskills.io/specification. **MEDIUM.**
- OpenAI docs:
  - https://learn.chatgpt.com/docs/build-skills (Codex skill scopes, `$HOME/.agents/skills`, symlinks, `agents/openai.yaml`)
  - https://developers.openai.com/plugins/build/plugins (portable `plugin.json`, `.codex-plugin/plugin.json`, marketplace locations including legacy `.claude-plugin/marketplace.json`, `codex plugin marketplace add`, cache path)
  - **LOW–MEDIUM.**
- Agent Plugins 1.0 specification, https://agent-plugins.org/specification (root `plugin.json`, closed schema, `skills/` discovery). **LOW–MEDIUM.**
- Web search, unverified, used only to scope questions: third-party notes on Codex reading Claude manifests ([awslabs cross-tool comparison](https://awslabs.github.io/aidlc-workflows/reference/research/Cross-Tool%20Plugin%20Comparison/), [codex-sdk hexdocs](https://codex-sdk.hexdocs.pm/13-plugin-authoring.html)); PyAV wheel licensing ([pyav-ffmpeg](https://github-redirect.dependabot.com/PyAV-Org/pyav-ffmpeg)); Cowork guides ([support.claude.com](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)). **LOW.**

---
*Stack research for: ProbeMatrix Evidence Pack Builder (local evidence conversion CLI + Agent Skills plugin)*
*Researched: 2026-10-17*
