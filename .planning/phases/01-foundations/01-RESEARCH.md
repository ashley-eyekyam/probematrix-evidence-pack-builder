# Phase 1: Foundations - Research

**Researched:** 2026-10-17
**Domain:** Python stdlib-first CLI + transactional file store, importer-exact XLSX writer/validator, Agent Skills plugin packaging (Claude Code, Codex), Linux CI supply-chain checks
**Confidence:** HIGH for format, writer, YAML, packaging layout and the Codex manifest question (all executed locally this session). MEDIUM for CI tooling choices. LOW for Cowork, Windows and macOS runtime behaviour (not testable here).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Packaging and hosts
- **D-01 (OD-13):** Ship `plugin/.codex-plugin/plugin.json` next to `plugin/.claude-plugin/plugin.json` from Phase 1, so the layout is final from day one. The primary Codex route is `codex plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder`. The fallback is a cross-platform Python installer, `tools/install-codex.py`, which copies the plugin's skills into `$HOME/.agents/skills`. It replaces design §5's `install-codex.sh`. Thin `.sh`/`.ps1` wrappers are optional. There is **no** committed `.agents/skills` symlink. A CI test checks that both manifests are valid JSON with the required fields. Which manifest Codex actually reads is proved only in Phase 10 (PKG-10).
- **D-02 (OD-22):** Omit the `skills` key from the Claude manifest, because the default `skills/` scan finds them. Keep `skills` only in the Codex manifest. CI runs `claude plugin validate --strict` when the `claude` CLI is available and skips cleanly otherwise. The root-`CLAUDE.md` half of OD-22 is already settled by A4 and A15: the root is no longer the plugin root.
- **D-03:** The private Python environment lives in **one fixed per-user folder shared by every host**: `~/.local/share/probematrix-epb/` on Linux, `%LOCALAPPDATA%\probematrix-epb\` on Windows and `~/Library/Application Support/probematrix-epb/` on macOS. It does not use `${CLAUDE_PLUGIN_DATA}`. The environment is keyed by plugin version, so an upgrade rebuilds cleanly. The manual names the exact path and explains manual removal. — **Reversibility:** costly — the manual, troubleshooting text and existing user installs all point at this path.
- **D-04:** Phase 1 ships the router skill `plugin/skills/evidence-pack/SKILL.md` in its final location. Its scope is what exists: first-time setup (`doctor --setup`), `init`, `scan` and reading `INDEX.md`, plus a line saying later stages are coming. It carries `scripts/epb.py`, the `scripts/epb/` package and `references/`, with `workspace-contract.md` and `evidence-pack-v2.md` written in Phase 1. Later phases extend this file rather than replace it. The Phase 1 UAT is run the way a user would run it: asking the agent to set up a case folder.

#### Schemas and persisted state
- **D-05 (OD-20):** There is a single canonical schema copy, at `plugin/skills/evidence-pack/scripts/epb/schemas/`, loaded through `importlib.resources`. There is **no** root `schemas/` folder or mirror, which amends the design §5 layout. Every install route carries the schemas because they sit inside `skills/`. — **Reversibility:** costly — validate-on-write and every install route depend on the path.
- **D-06 (OD-21):** Add `.epb/inbox/`, `.epb/tmp/`, `.epb/ledger/chunks.json` and `.epb/.gitattributes` (`* -text`) to the workspace contract now. `init` creates `inbox/`, `tmp/` and `.gitattributes`. `chunks.json` is declared now and created on first extraction. `references/workspace-contract.md` documents every path and marks it raw-text/confidential or shareable.
- **D-07 (resolves a WS-13 vs OD-21 conflict):** Chunk data is **split**. `state.json` holds the authoritative per-chunk *status* (chunk id, segment-ID range, `pending|in_progress|done`, claim count) and no raw text, so WS-13 holds and `state.json` stays trackable. `ledger/chunks.json` holds the chunk *plan*, including section headings. Those headings are raw text, and `ledger/` is git-ignored under A2. Both are declared in the Phase 1 schemas.
- **D-08 (OD-29):** Source records carry `parents: [...]`, a list that is empty for top-level inputs, instead of a single `parent`. An identical attachment delivered by two emails is one source with two parents, and Chain of Custody gets one entry per carrier. — **Reversibility:** one-way — it fixes the persisted source schema and the custody output contract.
- **D-09:** Every persisted file carries `schema_version`. A workspace **newer** than the plugin exits 4 (A11). A workspace **older** than the plugin is upgraded automatically on the next *mutating* command: a backup of the `.epb/` state files goes to `.epb/runs/<NNN>/pre-upgrade/`, the registered upgrade steps run in one journalled transaction, and a plain-language report follows. Read-only commands never upgrade. v0.1.0 has no upgrade steps, but the mechanism and its test exist from Phase 1.
- **D-10:** Record D-01, D-02, D-05, D-06, D-07, D-08 and D-12…D-14 as new design §20 amendments (A16 onwards) in Phase 1. Also update §5 (layout and requirements files), §6 (workspace contract) and §8.1 (`parents`) to match, so the design stays the source of truth.

#### Dependencies and file-type detection
- **D-11:** Dependencies use plain **minimum pins** (`>=`, per PKG-08), resolved at install. There is no lock file and no hash pinning. The owner's own words: "Just chill on such strict requirements." Calibrate the rest of the phase the same way: meet the requirements, and don't add extra hardening machinery beyond them.
- **D-12 (OD-17, dev part):** The plugin requirements are split this way:
  - `plugin/requirements.txt` holds the permissive core.
  - Each optional extra has its own file, with its licence stated in a header comment.
  - The root `requirements-dev.txt` holds core + pytest + ruff + only the permissively licensed extras, and the licence allow-list check covers it.
  - `requirements-dev-full.txt` adds the GPL/LGPL extras, for the Phase 10 media CI job only.

  This replaces design §5's rule that dev requirements include all optional extras.
- **D-13 (OD-23, MIME):** File types are detected with stdlib `mimetypes` (by extension) plus an in-house magic-byte table covering PDF, ZIP/OOXML, OLE2, PNG, JPEG, GIF, WAV, MP4/MOV, MKV, 7z and gzip, at minimum. When extension and content disagree, **content wins**, and the mismatch is recorded on the source and shown in the scan report. No `python-magic`.
- **D-14 (OD-23, .7z):** `.7z` files are handled only through an external `7z`/`7za`/`7zz` binary. Without one, the input is `unprocessed: 7z tool not installed`. `doctor` lists the tool with per-OS install commands. No py7zr (LGPL). Expansion itself is Phase 2 (WS-05).

#### Setup, doctor and smoke workbook
- **D-15:** The `epb` CLI never prompts. `epb init --title "…" [--slug …] [--prefix …] [--timezone …]`. The skill has the agent ask the user only for the case title. It then proposes the slug, the ID prefix (for example `ACM` → `EVD-ACM-001`) and the system timezone, and confirms them in one line. Missing values get defaults: slug from the folder name, prefix from the title's initials, the system timezone.
- **D-16:** The smoke workbook is built by a **repo-only** script, `tools/make-smoke-pack.py`, which is not shipped in `plugin/`. It uses the real format module and validator and writes to a git-ignored scratch path (for example `scratch/smoke/evidence-pack-smoke.xlsx`; add `scratch/` to `.gitignore`). It also prints a checklist of every edge-case value as written. A pytest test builds and validates the same workbook. Nothing generated is committed (A3). The UAT gives the exact command, the file path and the comparison checklist. The owner reports the import result, and the agent never claims it.
- **D-17:** `epb doctor` output for humans is a short, grouped plain-text checklist:
  - **Ready**, for example "Python 3.12 — ready".
  - **Optional, not installed**: what each tool would enable and the single install command for *this* OS.
  - **What to do next.**

  Versions and the install commands for all three OSes appear under `--verbose`. `--json` gives the full machine report, which satisfies PKG-07. The manual quotes this output exactly.

Also locked (CONTEXT `<domain>`): design §20 A1–A15 are not reopened; lock behaviour (OD-19) is settled by WS-07: wait 60 s, and read-only commands take no lock.

### Claude's Discretion
- How a new version of a source (`S004v2`) is stored: versions inside `S004.json` or separate records. The `S004v2` ID form is fixed by WS-03.
- Source ID padding beyond 999 inputs (for example letting it grow to `S1000` with 3-digit minimum padding).
- On-disk JSON formatting (key order, indentation), provided it is deterministic.
- Which later-phase schemas get drafted in Phase 1, as governed by the roadmap's phase-order fixes (PF-01, PF-04…07, PF-11, PF-16, PF-18, PF-20).
- Exact wording of manual sections and doctor lines, within D-17's structure.

### Deferred Ideas (OUT OF SCOPE)
None. The discussion stayed within the phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (short) | Research Support |
|----|---------------------|------------------|
| WS-01 | `epb init` creates `inputs/`, `outputs/`, `INDEX.md`, `.epb/` + `case.yaml` | Pattern 6 (init), case.yaml schema sketch, D-15 defaults, timezone detection (Pitfall 9) |
| WS-02 | `scan` fingerprints (SHA-256, size, MIME, mtime), stable `S001…`, ignores OS junk | Pattern 4 (scan), `hashlib.file_digest`, `os.walk(followlinks=False)`, MIME table (Pitfall 5) |
| WS-03 | new version / rename / duplicate / removed | Pattern 4 classification table, Open Question Q4 |
| WS-04 | `.note.md` / `.note.yaml` sidecar pairing, hashed as inputs | Pattern 4 sidecar rules |
| WS-06 | atomic writes, journalled transactions, `state.json` last, crash resume | Pattern 2 + Code Example 4; crash-injection seam (Code Example 7) |
| WS-07 | lock, 60 s wait, read-only commands take no lock | Pattern 3 + Code Example 3 |
| WS-08 | schema validation on write; strict YAML keeps `12:30`, `0123`, `no` as text | Code Example 2 (verified), jsonschema format pitfall (Pitfall 6) |
| WS-09 | `INDEX.md` six sections in order, "none yet" | Pattern 7 (INDEX providers), tick syntax recommendation |
| WS-11 | `.epb/.gitignore` list; warn when git repo would track `.epb/private/` | Pattern 8 (git check) |
| WS-12 | warn when inside OneDrive, Dropbox, iCloud Drive, Google Drive | Pattern 8 (sync heuristics table) |
| WS-13 | `state.json` schema has workbook registry, ID/Tag counters, chunk status from Phase 1 | state.json schema sketch (Pattern 2) |
| BLD-01 | `formats/probematrix_v2.py` owns marker, sheets, headers, widths, enums, separator, 10-row metadata | "Importer contract" section (verbatim, read this session) |
| BLD-02 | every cell text, control chars removed, no formulas, no numeric coercion | Code Example 1 (verified with openpyxl 3.1.5 + SheetJS 0.18.5 round trip) |
| BLD-03 | validator stricter than importer | Validator rule list (Pattern 5), Code Example 6 |
| BLD-08 | exact 10-row metadata; Total Evidence Items = rows; Attachments Manifest headers only | Importer contract, verbatim metadata rows |
| PKG-01 | `plugin/` with `.claude-plugin/plugin.json`; root marketplace `source: "./plugin"` | Pattern 1 (verified install into isolated Claude config) |
| PKG-03 | `plugin/AGENTS.md` host-neutral agent rules | Pattern 1 note on how AGENTS.md reaches agents (Open Question Q5) |
| PKG-05 | exit codes 0–4 + stable error codes in JSON | Exit-code / error-code catalogue (Pattern 9) |
| PKG-06 | stdlib-only `epb.py` launcher; `doctor --setup` builds private env | Pattern 10 + Code Example 5 |
| PKG-07 | `doctor` reports each tool: found, version, enables, per-OS install | Pattern 11 (probe registry) |
| PKG-08 | permissive core with minimum pins; GPL extras separate, licences documented | Standard Stack, licence sweep (verified) |
| PKG-09 | CI dependency-age (two-week rule + exceptions) and licence allow-list | Pattern 12 (verified pip flag; pip-licenses limitation found) |
| PKG-11 | root AGENTS.md == CLAUDE.md, ≤150 lines, CI test | Validation map |
| TST-01 | pytest + ruff, no network in tests, optional tools skip | conftest socket guard (Code Example 8), ruff config notes |
| TST-07 | crash injected at each transaction step resumes cleanly | Code Example 7 |
| DOC-04 | manual: local vs AI-host, sync folders, de-identification | Manual outline (Pattern 13) |
| DOC-05 | manual started in Phase 1; Windows/macOS "not yet tested on this system" | Manual outline (Pattern 13) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Root `CLAUDE.md` (read this session) directives the planner must honour:
- The design wins over every other doc, and §20 overrides earlier sections. Contradictions go to the owner, not resolved silently.
- **Standalone repo.** The parent checkout `../` is read-only reference: never modify it, depend on it or copy its code. (This research *read* the parent importer to transcribe the file format. No test or tool may import from or execute anything in `../`, and that includes the parent's `node_modules/xlsx`, which was used here once for a manual round-trip check.)
- **Clean-room.** No prose from the Hazira reference files or the prototype goes into code, skills, docs or tests. All fixtures are synthetic.
- **No real names in committed files.** The only exception is the unmodified official report in `docs/reference/`.
- Defects are written `DEF-01`…`DEF-18`, never `D1`–`D18`.
- No published samples or real-incident output in git. Benchmarks run in git-ignored scratch folders.
- Quality outranks token and API cost.
- Work goes through GSD. Branch `phase-01-foundations`, merged `--no-ff` after verification. Ask before pushing a new branch.
- Every UAT is a numbered procedure with prerequisites, exact commands, fixture paths and exact pass/fail strings.
- The owner does every ProbeMatrix import. Never claim an import worked.
- Python 3.11+, `pathlib` everywhere, cross-platform code. CI on Linux only until after v0.1.0.
- `pytest` with no network; tests for optional tools skip when the tool is absent. Lint with `ruff`.
- The plugin ships from `plugin/`; the marketplace file sits at the repo root.
- Root `AGENTS.md` and `CLAUDE.md` are byte-identical, aim for ≤60 lines, never exceed 150, and are edited and committed together. Never run `gsd-tools generate-claude-md` on them.
- From the user's global CLAUDE.md: Docker is not needed in this phase, so the Docker rules don't apply. Ask the owner one question at a time, recommended option first.

## Summary

Phase 1 is a greenfield skeleton. Almost every risky assumption in it could be tested on this machine today, and this session did so:

- **Packaging is proven.** A scratch repo with `.claude-plugin/marketplace.json` (`"source": "./plugin"`) at its root passed `claude plugin validate --strict`, both for the marketplace and for `./plugin`. It then installed into an isolated Claude config dir, and the cache held only the `plugin/` subtree.
- **The Codex manifest question is answered.** The same repo installed through `codex plugin marketplace add <path>` + `codex plugin add` (codex-cli 0.154.0). With both manifests present, **Codex read `.codex-plugin/plugin.json`**, and it fell back to `.claude-plugin/plugin.json` when the Codex file was absent. Codex also **rejects the install when the marketplace entry name differs from `plugin.json` `name`**. This settles most of what D-01 left to Phase 10, at least for local-path installs on Linux.
- **The workbook format is proven against the importer's own reader.** The importer contract was read line by line from the parent repo and is transcribed verbatim below. An openpyxl 3.1.5 workbook was round-tripped through SheetJS 0.18.5, the importer's library, using the importer's read idiom. A Description starting with `=`, the value `0`, a 20-digit ID, `2020-09`, multi-entry Tags and Linked Equipment, and Chain of Custody JSON all came back as exact strings.

The probes also turned up a few planning-relevant surprises:

1. openpyxl **silently truncates strings over 32,767 characters on write**. The length check therefore has to happen before writing, not only on disk.
2. ProbeMatrix's own exports use cell type `t="str"` (no formula), not `inlineStr`. An on-disk validator that rejects `str` outright would reject ProbeMatrix-style files.
3. The importer's metadata layout has a **blank row 7, with the notes in rows 8–10**. Design §8.4 says rows 7–9, which needs a correction amendment under D-10.
4. **pip-licenses 5.5.5 cannot evaluate SPDX `OR` expressions.** It flags `packaging` (`Apache-2.0 OR BSD-2-Clause`) and pypdfium2's free-text licence, so a small in-house licence check is cleaner.
5. stdlib `mimetypes` gives **different answers on Python 3.11 vs 3.14, and module-level vs instance**. 3.11 has no `.md`, `.yaml`, `.7z`, `.mkv`, `.m4a` or `.rtf`, so the in-house extension table must be authoritative.
6. jsonschema **ignores `format: date-time`** without optional packages. Use `pattern` regexes.
7. `claude plugin validate --strict` **does not catch** Cowork-breaking frontmatter keys or a non-spec `name`, so an in-house SKILL.md lint is required.
8. The bundled venv pip (25.1.1) **rejects `--uploaded-prior-to`**. Pip must first be upgraded to ≥26.1, after which `--uploaded-prior-to P14D` resolves the PKG-08 floors (pypdf 6.19.0, Pillow 12.3.0). Both were verified.

**Primary recommendation:**
- Build the layers in this order: (1) `core/` (atomic writes, OS lock, strict YAML, hashing, paths, faults), (2) `store/` (transaction with a redo journal, `state.json` last, recovery, schema validation, upgrade registry), (3) `formats/probematrix_v2` (writer + independent on-disk validator), (4) `sources/scan`, (5) `index/`, (6) `doctor/` + the stdlib launcher.
- Packaging, CI and the manual run as a parallel track.
- Use only stdlib plus openpyxl, PyYAML, jsonschema and defusedxml at runtime in Phase 1. Install the rest of the core list but don't import it yet.

## Architectural Responsibility Map

This is a local CLI plus plugin, so the web tiers are replaced by the plugin's own layers.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ask the user for the case title, propose slug, prefix and timezone | Agent / skill (`SKILL.md`) | CLI flags | D-15: the CLI never prompts |
| Interpreter discovery, private env creation, re-exec | Launcher (`scripts/epb.py`, stdlib only) | `epb/doctor/setup` (stdlib only) | Must run before any third-party package exists (A8) |
| Argument parsing, JSON envelope, exit codes | CLI shell (`epb/cli/`) | `epb/errors.py` | A single place maps exceptions to 0–4 |
| Workspace create, scan and classification | Services (`epb/store/workspace`, `epb/sources/`) | core | Business rules for WS-01…04 |
| Atomic writes, journal, recovery, lock | Store / core (`epb/store/txn`, `epb/core/atomic`, `epb/core/lock`) | OS filesystem | The only writer of `.epb/`; everything else stages through it |
| Schema validation | Store (`epb/store/validate`) | `epb/schemas/*.json` (data, D-05) | Validate on every write (WS-08) |
| Workbook writing and validation | Pure format module (`epb/formats/probematrix_v2`) | openpyxl, zipfile + defusedxml | The §8.5 seam; no pipeline knowledge |
| `INDEX.md` rendering | Services (`epb/index/`) | store (state) | Derived view, written inside the same transaction |
| Tool probing | `epb/doctor/` (stdlib only) | `shutil.which` + subprocess | Must work before setup |
| Sync-folder and git warnings | `epb/doctor/` / `epb/store/workspace` | git CLI (optional) | Shared by `init` and `doctor` (WS-11, WS-12) |
| Plugin distribution | Packaging (`plugin/.claude-plugin`, `plugin/.codex-plugin`, root `.claude-plugin/marketplace.json`) | `tools/install-codex.py` | Host-specific manifests, one tree |
| Supply-chain checks | CI (`.github/workflows/ci.yml`, `tools/check_*.py`) | PyPI JSON API (CI only) | PKG-09; never inside pytest (no network) |

## Standard Stack

### Core runtime (used by Phase 1 code)

| Library | Version (min pin → resolved under the 14-day cutoff) | Purpose | Why standard |
|---------|------------------------------------------------------|---------|--------------|
| Python | ≥3.11 (CI 3.11 + 3.14) | Runtime | A5. 3.11 lacks `Path.walk` (verified: `Path.walk False` on 3.11.17), so use `os.walk` |
| openpyxl | `>=3.1.5` → 3.1.5 | Write and read `EVIDENCE_PACK_V2` | Only mainstream read+write xlsx library. Text-cell behaviour verified this session [VERIFIED: local probe] |
| PyYAML | `>=6.0.3` → 6.0.3 | `case.yaml` and later items and rosters | cp314 wheels from 6.0.3. Strict loader verified [VERIFIED: local probe] |
| jsonschema | `>=4.25` → 4.26.0 | Validate on write (Draft 2020-12) | Reports all errors with paths. Pure + rpds-py wheel [VERIFIED: local install] |
| defusedxml | `>=0.7.1` → 0.7.1 | Hardened XML for openpyxl and the on-disk validator | openpyxl switches to defused parsing when present (verified `DEFUSEDXML True`) |

### Core requirements installed now, imported in later phases (PKG-08 list)

`rapidfuzz>=3.14.1`, `pdfplumber>=0.11.9`, `pypdf>=6.19.0`, `python-docx>=1.2.0`, `python-pptx>=1.0.2`, `beautifulsoup4>=4.13`, `markdownify>=1.2.0`, `Pillow>=12.3.0`, `lxml>=6.1.0`, `charset-normalizer>=3.4.3`. All of them resolved together with the core above under `--exclude-newer 2026-10-03` on Python 3.14 [VERIFIED: uv install this session]. Resolved versions: RapidFuzz 3.14.6, pdfplumber 0.11.10, pdfminer.six 20260107, pypdf 6.19.0, python-docx 1.2.0, python-pptx 1.0.2, beautifulsoup4 4.15.0, markdownify 1.2.3, pillow 12.3.0, lxml 6.1.3 and charset-normalizer 3.5.2.

### Stdlib modules to use (no dependency)

| Module | Use |
|--------|-----|
| `argparse` | CLI. `allow_abbrev=False`; a parent parser carrying `--case/--json/--verbose/--wait` on every subparser; `color=False` (3.14 argparse defaults to colour, per prior research) |
| `hashlib.file_digest` | Streaming SHA-256 (present on 3.11, verified) |
| `os.walk(followlinks=False)` / `os.scandir` | Inputs walk. `Path.walk` is 3.12+ |
| `fcntl.flock` / `msvcrt.locking` | OS advisory lock. Released by the OS when the process dies |
| `os.replace` + `os.fsync` | Atomic file replacement |
| `importlib.resources.files` | Load `epb/schemas/*.json` (D-05) |
| `venv`, `subprocess`, `shutil.which` | Launcher setup and tool probes |
| `zipfile` | Independent on-disk validator, and magic-byte sniffing of OOXML |
| `mimetypes` | Extension fallback only, behind an in-house table (Pitfall 5) |
| `unicodedata` | NFC path keys |
| `zoneinfo` | Validate the `--timezone` IANA name (Linux and macOS have system tzdata) |
| `importlib.metadata` | Licence check, and doctor's report of package versions |
| `json` | `ensure_ascii=False, indent=2, sort_keys=True` + trailing newline (deterministic, Claude's discretion) |

### Development tools

| Tool | Pin | Notes |
|------|-----|-------|
| pytest | `>=9.0` → 9.1.1 (2026-06-19) | `pythonpath` ini option puts `plugin/skills/evidence-pack/scripts` on the path |
| ruff | `==0.16.10` (2026-10-01, 16 days old today) | Pin exactly: rule sets change between minors, and a moving floor plus the 14-day cutoff makes lint drift. This is a dev-tool pin, not dependency hardening, so it is consistent with D-11. 0.17.x is too new |
| pip | `>=26.1` inside venvs | 26.0 added `--uploaded-prior-to`, and 26.1 added `P<n>D`. The bundled 25.1.1 rejects the flag (verified: `no such option: --uploaded-prior-to`) |
| uv (optional, contributors) | any | Already on this machine (0.13.1). `uv run -p 3.11` fetched CPython 3.11.17 for local 3.11 checks (verified) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| openpyxl writer | XlsxWriter (`write_string` never makes formulas) | Write-only, so the validator would still need a reader. One library is simpler |
| In-house licence check | pip-licenses 5.5.5 | **Fails on SPDX `OR` expressions** (verified: flags `packaging` `Apache-2.0 OR BSD-2-Clause`) and has no per-package reviewed override except `--ignore-packages` |
| In-house OS lock | `filelock` (MIT) | Adds a dependency for about 40 lines. The OS lock releases on process death either way |
| In-house SKILL.md lint | `claude plugin validate --strict` alone | Verified it **passes** an `argument-hint:` key (which hard-fails claude.ai/Cowork packaging) and `name: Evidence_Pack` |
| In-house no-network guard | `pytest-socket` | An extra dependency for a five-line autouse fixture |

**Installation (contributor dev env):**
```bash
python3 -m venv .venv                       # system python3 here has no pip module; the venv brings pip 25.1.1
.venv/bin/python -m pip install -U "pip>=26.1"
.venv/bin/python -m pip install --uploaded-prior-to P14D -r requirements-dev.txt
```

## Package Legitimacy Audit

`gsd-tools query package-legitimacy check --ecosystem pypi` was run on all 16 packages. **Every package came back `SUS`**, mostly for `unknown-downloads`, because the PyPI JSON API publishes no download counts, so the seam cannot score PyPI popularity. Some were also flagged `too-new`, meaning their *latest* release is under two weeks old, and charset-normalizer was flagged `no-repository`. Registry facts were gathered from the PyPI JSON API this session.

| Package | Registry | First release (age) | Latest (upload) | Source repo | Seam verdict | Disposition |
|---------|----------|---------------------|-----------------|-------------|--------------|-------------|
| openpyxl | PyPI | 2010-08-11 (16 yr) | 3.1.5 (2024-06-28) | openpyxl.readthedocs.io (Heptapod) | SUS (unknown-downloads) | Flagged: planner adds checkpoint |
| PyYAML | PyPI | 2011-07-01 | 6.0.3 (2025-09-25) | pyyaml.org / github.com/yaml/pyyaml | SUS (unknown-downloads) | Flagged |
| jsonschema | PyPI | 2012-01-02 | 4.26.0 (2026-01-07) | github.com/python-jsonschema/jsonschema | SUS (unknown-downloads) | Flagged |
| defusedxml | PyPI | 2013-02-19 | 0.7.1 (2021-03-08) | github.com/tiran/defusedxml | SUS (unknown-downloads) | Flagged |
| rapidfuzz | PyPI | 2020-03-18 | 3.14.6 (2026-08-30) | github.com/rapidfuzz/RapidFuzz | SUS (unknown-downloads) | Flagged |
| pdfplumber | PyPI | 2015-08-24 | 0.11.10 (2026-06-15) | github.com/jsvine/pdfplumber | SUS (unknown-downloads) | Flagged |
| pypdf | PyPI | 2014-05-17 | 6.21.1 (2026-10-17) | github.com/py-pdf/pypdf | SUS (too-new, unknown-downloads) | Flagged. Floor 6.19.0 (2026-09-16) is ≥14 days |
| python-docx | PyPI | 2014-01-05 | 1.2.0 (2025-06-16) | github.com/python-openxml/python-docx | SUS (unknown-downloads) | Flagged |
| python-pptx | PyPI | 2013-01-26 | 1.0.2 (2024-08-07) | github.com/scanny/python-pptx | SUS (unknown-downloads) | Flagged |
| beautifulsoup4 | PyPI | 2013-10-02 | 4.15.0 (2026-06-07) | crummy.com/software/BeautifulSoup | SUS (unknown-downloads) | Flagged |
| markdownify | PyPI | 2013-07-31 | 1.2.3 (2026-06-30) | github.com/matthewwithanm/python-markdownify | SUS (unknown-downloads) | Flagged |
| Pillow | PyPI | 2010-07-31 | 13.0.0 (2026-10-16) | python-pillow.org | SUS (too-new, unknown-downloads) | Flagged. Floor 12.3.0 resolves under the cutoff (verified) |
| lxml | PyPI | 2007-07-03 | 6.1.3 (2026-09-02) | lxml.de | SUS (unknown-downloads) | Flagged |
| charset-normalizer | PyPI | 2019-08-02 | 3.5.2 (2026-09-30) | github.com/jawah/charset_normalizer | SUS (too-new, unknown-downloads, no-repository) | Flagged. The repo URL *is* in PyPI `project_urls` |
| pytest | PyPI | 2010-11-25 | 9.1.1 (2026-06-19) | docs.pytest.org / github.com/pytest-dev/pytest | SUS (unknown-downloads) | Flagged |
| ruff | PyPI | 2022-08-27 | 0.17.1 (2026-10-15) | docs.astral.sh/ruff / github.com/astral-sh/ruff | SUS (too-new, unknown-downloads) | Flagged. Pin 0.16.10 (2026-10-01) |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** all 16 above. `openpyxl` [WARNING: flagged as suspicious — verify before using.] and every other package in the table carries the same warning, because the PyPI download signal is unavailable. Each package also has 7 to 19 years of release history and a known upstream repository, and the core list was already chosen and owner-reviewed in project research (STACK.md, PKG-08).

**Planner action:** add **one** `checkpoint:human-verify` task, before the first `pip install` of `plugin/requirements.txt` and `requirements-dev.txt`, in which the owner confirms the package list and floor pins. That satisfies the gate without one checkpoint per package (D-11 calibration). No package in this phase was discovered by WebSearch. All of them come from PKG-08 and owner-approved STACK research.

PyPI wheels have no `postinstall` hook, so the npm step does not apply. Source distributions can run build code. Every Phase 1 package installed from wheels in the probe.

## Importer contract (verbatim, read this session from the parent repo; read-only)

These are file-format strings, not code, and design §8.4 explicitly allows transcribing them. Source files: `../server/services/evidenceExportService.ts` (parent `main` at `8e91dfb`, 2026-10-15) and `../shared/schema.ts`.

- Marker and sheet names [VERIFIED: evidenceExportService.ts:4-7]: `EVIDENCE_PACK_MARKER = 'EVIDENCE_PACK_V2'`, `'Evidence Pack'`, `'Pack Metadata'`, `'Attachments Manifest'`.
- Metadata rows, written as array-of-arrays (10 rows) [VERIFIED: evidenceExportService.ts:80-91]:
  `['Evidence Pack Format', EVIDENCE_PACK_MARKER]`, `['Incident Number', incidentNumber]`, `['Incident Title', incidentTitle]`, `['Export Date', new Date().toISOString()]`, `['Total Evidence Items', evidence.length.toString()]`, `['Total Attachments', attachmentCount.toString()]`, `['']`, `['IMPORTANT: Do not modify the structure of this file.']`, `['Modifying column headers or the metadata sheet may cause import errors.']`, `['Note: Attachments are listed in the Attachments Manifest sheet for reference only.']`.
  **Row 7 is blank, and the notes are rows 8–10.** Design §8.4 says "Rows 7–9 carry the importer's standard notes", which is off by one. The prototype pack confirms the exporter layout: its column A reads `[..., 'Total Attachments', None, 'IMPORTANT: …', …]` [VERIFIED: local probe of docs/reference prototype pack]. Record this as a correction amendment under D-10.
- Evidence Pack headers, in order (30) [VERIFIED: evidenceExportService.ts:129-160]: `'Evidence ID', 'Type', 'Description', 'Priority', 'Analysis Status', 'Tags', 'Linked Individuals', 'Linked Equipment', 'Source', 'Collection Date', 'Collection Method', 'Collector', 'Storage Location', 'Evidence Tag', 'Hash/Checksum', 'Related Evidence', 'Chain of Custody (JSON)', 'Integrity Verified', 'Collection Conditions', 'Preservation Method', 'Access Restrictions', 'Regulatory Requirements', 'Retention Category', 'Retention Until', 'QA Status', 'QA Reviewed By', 'QA Reviewed At', 'Verification Notes', 'Created At', 'Updated At'`.
- Evidence Pack widths in `wch` [VERIFIED: evidenceExportService.ts:197-204]: `12, 18, 60, 10, 15, 25, 25, 25, 20, 15, 20, 15, 20, 15, 20, 25, 40, 15, 25, 20, 25, 25, 15, 15, 15, 20, 22, 30, 22, 22`. A ProbeMatrix export stores these on disk as `width = wch + 0.83203125` (e.g. `<col min="1" max="1" width="12.83203125" customWidth="1"/>`, `width="60.83203125"` for column 3) [VERIFIED: local probe of prototype pack XML]. openpyxl writes `width="12.83203125"` exactly when given that float (verified), so the format module can store the `wch` list and write `wch + 0.83203125`.
- Attachments Manifest headers (11) [VERIFIED: evidenceExportService.ts:210-222]: `'Evidence ID', 'Attachment ID', 'File Name', 'File Type', 'File Size (bytes)', 'MIME Type', 'File Hash (SHA-256)', 'Uploaded By', 'Uploaded At', 'Integrity Status', 'Last Verified At'`. Widths [VERIFIED: :239-243]: `12, 12, 40, 12, 15, 25, 70, 15, 22, 15, 22`. The exporter writes this sheet only when attachments exist (:209). BLD-08 writes it with headers only.
- Import checks [VERIFIED: evidenceExportService.ts:259-316, 320-385]:
  - The metadata sheet must be present.
  - `metadataData[0][1]` must equal `EVIDENCE_PACK_V2` or `EVIDENCE_PACK_V1`.
  - The Evidence Pack sheet must be present.
  - Fewer than 2 rows means valid with 0 items.
  - The required headers are `'Evidence ID', 'Type', 'Description', 'Priority', 'Analysis Status'`.
  - Headers are matched by name.
  - Rows with a falsy `Type` cell are skipped (`continue`).
  - A blank Description pushes an error, which invalidates the whole file.
  - Type is lowercased with spaces turned to `_`. Priority is lowercased. Analysis Status is lowercased with spaces turned to `_`. Unknown values become a warning plus a default.
  - Tags, Linked Individuals, Linked Equipment, Related Evidence and Regulatory Requirements are split with `.split(',').map(t => t.trim()).filter(t => t)`.
  - Chain of Custody goes through `JSON.parse(String(chainJson))` in a try block, and a failure is only a warning.
  - `Integrity Verified` is compared with `=== 'Yes'`.
  - Retention Category, Retention Until and QA Status are copied as raw strings.
- Enums [VERIFIED: evidenceExportService.ts:314-316]: `validTypes = ['witness_statement', 'photograph', 'document', 'log_record', 'recording', 'physical_item', 'lab_report', 'other']`, `validPriorities = ['critical', 'high', 'medium', 'low']`, `validStatuses = ['analyzed', 'pending', 'requires_followup']`.
- Lifecycle and retention [VERIFIED: shared/schema.ts:687, 690]: `EvidenceLifecycleStatus = "collected" | "preserved" | "under_review" | "verified" | "disputed" | "released" | "destroyed" | "sealed"`; `RetentionCategory = "regulatory" | "legal" | "internal" | "permanent"`.
- Chain of custody [VERIFIED: shared/schema.ts:615, 618, 621-634]: `ChainOfCustodyEntry { timestamp: string; transferred_from: string; transferred_to: string; received_by: string; reason?: string; condition_on_receipt?: ConditionOnReceipt; verification_confirmed?: boolean; action_type?: CustodyActionType; location?: string; notes?: string; }`, with `ConditionOnReceipt = "intact" | "sealed" | "damaged" | "opened" | "unknown"` and `CustodyActionType = "transfer" | "inspection" | "duplication" | "return" | "sealed" | "unsealed"`.
- The import route [VERIFIED: ../server/routes.ts:645-720] assigns a fresh evidence ID per row, suffixes colliding tags `-IMP<n>`, and has no content dedup. This matches design §8.4 items 1–2. Line numbers have drifted by about 15 lines since the design's check.

**Implication for the smoke pack:** the validator must accept **all 8** QA Status values, because A10 requires every value in the smoke pack, even though the Phase 5 renderer will only ever emit `verified`, `disputed` or blank. Keep "which values the importer accepts" (validator) separate from "which values the builder emits" (renderer policy, Phase 5).

## Architecture Patterns

### System Architecture Diagram

```
 user ──asks──▶ AGENT (router SKILL.md: evidence-pack)
                 │  asks only for case title; proposes slug/prefix/timezone (D-15)
                 ▼
 bootstrap python (python3 | py -3) ──▶ scripts/epb.py  [stdlib-only launcher]
                 │                         │
                 │   cmd == doctor[--setup]│ else
                 │         ▼               ▼
                 │   epb.doctor (stdlib) ─▶ private env exists for this plugin version?
                 │     │ probes tools          │ no ──▶ exit 3 ENV_NOT_SET_UP (+ "run doctor --setup")
                 │     │ --setup: venv ─▶ pip ≥26.1 ─▶ install plugin/requirements.txt ─▶ verify imports
                 │     ▼                       │ yes
                 │   human checklist / --json  ▼
                 │                      re-exec: <env>/bin/python epb.py <args>   (EPB_IN_ENV=1)
                 ▼                             ▼
             JSON envelope ◀──────── epb.cli.main ─▶ handler (init | scan | status)
                                               │
                         ┌─────────────────────┼─────────────────────────────┐
                         ▼                     ▼                             ▼
                 store.workspace        sources.scan                  index.render
                 (init, warnings:       walk inputs/ (no symlinks) ─▶   six providers,
                  sync folder, git)     hash ─▶ classify (new/version/   "none yet"
                         │              rename/dup/removed/junk/sidecar)      │
                         └──────────────┬──────┴──────────────────────────────┘
                                        ▼
                     store.txn  (OS lock, wait 60 s) ─▶ recover() pending journals
                        stage + schema-validate every file ─▶ .epb/tmp/txn-<id>/
                        write manifest.json (commit point) ─▶ os.replace each file
                        ─▶ state.json LAST ─▶ delete txn dir ─▶ release lock
                                        ▼
            <case>/inputs (read-only) · .epb/ (state) · INDEX.md · outputs/ (xlsx only)

 repo-only: tools/make-smoke-pack.py ─▶ formats.probematrix_v2.write ─▶ validate(path) ─▶ scratch/smoke/*.xlsx ─▶ owner imports
 CI (Linux, 3.11 + 3.14): ruff ─▶ pytest ─▶ check_dependency_age (PyPI JSON) ─▶ check_licences ─▶ [claude plugin validate if present]
```

### Recommended Project Structure

```
.claude-plugin/marketplace.json        # repo root; "source": "./plugin"   (verified location: validate requires .claude-plugin/)
plugin/
├── .claude-plugin/plugin.json         # no "skills" key (D-02)
├── .codex-plugin/plugin.json          # "skills": "./skills/" (D-01); same name/version as the Claude manifest
├── AGENTS.md                          # host-neutral agent rules (PKG-03)
├── requirements.txt                   # permissive core, >= pins (PKG-08, D-11)
├── requirements-email.txt …           # optional extras, licence in header comment (D-12)
└── skills/evidence-pack/
    ├── SKILL.md                       # router, Phase 1 scope (D-04)
    ├── references/{workspace-contract.md, evidence-pack-v2.md}
    └── scripts/
        ├── epb.py                     # stdlib-only launcher (A8)
        └── epb/
            ├── __init__.py  version.py  errors.py  launcher.py
            ├── cli/ (main.py, envelope.py, commands/{workspace,intake,doctor}.py)
            ├── core/ (atomic.py lock.py hashing.py yamlio.py paths.py ids.py clock.py faults.py mime.py)
            ├── store/ (workspace.py state.py txn.py validate.py upgrade.py runs.py)
            ├── schemas/ (__init__.py, case, state, source, chunks, run, envelope *.schema.json)   # D-05
            ├── sources/ (scan.py classify.py sidecars.py junk.py expanders/__init__.py)        # PF-11 seam
            ├── formats/ (base.py probematrix_v2.py validate.py)
            ├── index/ (render.py providers.py)
            └── doctor/ (probes.py tools.py setup.py report.py syncfolders.py gitcheck.py)        # stdlib only
tools/ (install-codex.py, make-smoke-pack.py, check_dependency_age.py, check_licences.py,
        dependency-age-exceptions.json, licence-allowlist.json)
tests/ (conftest.py, unit + integration per area)
docs/manual/ (or docs/USER-MANUAL.md)  # DOC-04/05
requirements-dev.txt  requirements-dev-full.txt  pyproject.toml (ruff + pytest config only)
.github/workflows/ci.yml
```

### Pattern 1: Plugin and marketplace manifests (PKG-01, D-01, D-02)

**What:** One plugin tree under `plugin/` with two manifests, and one marketplace file at `<repo>/.claude-plugin/marketplace.json` that both hosts read.

**Verified facts:**
- `claude plugin validate` looks for `.claude-plugin/marketplace.json` or `.claude-plugin/plugin.json`. A bare `marketplace.json` at the root fails: `No manifest found in directory. Expected .claude-plugin/marketplace.json or .claude-plugin/plugin.json` [VERIFIED: claude 2.1.302]. PKG-01's "the repo root holds `marketplace.json`" therefore means `<root>/.claude-plugin/marketplace.json`.
- The marketplace and plugin below pass `--strict`. A `CLAUDE.md` inside `plugin/` produces the warning `CLAUDE.md at the plugin root is not loaded as project context`, which `--strict` turns into a failure. `plugin/AGENTS.md` raises no warning. A root `CLAUDE.md` beside the marketplace raises no warning [VERIFIED: local validate runs].
- With `CLAUDE_CONFIG_DIR=<tmp>`, `claude plugin marketplace add <repo-path>` + `claude plugin install probematrix-evidence-pack-builder@probematrix-evidence-pack-builder` installed into `<tmp>/plugins/cache/<marketplace>/<plugin>/<version>/`. The cache held only `.claude-plugin/ .codex-plugin/ skills/ AGENTS.md requirements.txt`, with **no `docs/` or `tests/`** [VERIFIED: isolated install].
- Codex: with `CODEX_HOME=<tmp>`, `codex plugin marketplace add <repo-path>` read the legacy `.claude-plugin/marketplace.json`, and `codex plugin add <name>@<marketplace>` installed to `<CODEX_HOME>/plugins/cache/<mkt>/<plugin>/<version>/` and wrote `[plugins."<plugin>@<mkt>"] enabled = true` to `config.toml`.
  - With both manifests present, the installed version dir was the Codex manifest's version (`9.9.9-codex`). Without `.codex-plugin/`, it was the Claude manifest's (`7.7.7-claude`).
  - A marketplace entry name that differs from `plugin.json` `name` errors with `plugin.json name ... does not match marketplace plugin name ...` [VERIFIED: codex-cli 0.154.0].
- `claude plugin validate --strict` passed a SKILL.md with `argument-hint:` and `name: Evidence_Pack` [VERIFIED]. An in-house lint is therefore mandatory.

**Example (passes `--strict`; values from this repo's decisions):**
```json
// .claude-plugin/marketplace.json  (repo root)
{ "name": "probematrix-evidence-pack-builder",
  "owner": { "name": "…" },
  "metadata": { "description": "…" },
  "plugins": [ { "name": "probematrix-evidence-pack-builder", "source": "./plugin", "description": "…" } ] }

// plugin/.claude-plugin/plugin.json   (no "skills" key, D-02)
{ "name": "probematrix-evidence-pack-builder", "version": "0.1.0", "description": "…",
  "author": { "name": "…" }, "homepage": "…", "repository": "…", "license": "MIT", "keywords": ["…"] }

// plugin/.codex-plugin/plugin.json   ("skills" kept, D-01)
{ "name": "probematrix-evidence-pack-builder", "version": "0.1.0", "description": "…",
  "license": "MIT", "skills": "./skills/" }
```
**CI test (D-01):** both manifests parse as JSON. `name` is identical in both and equals the marketplace entry `name`. `version` is identical in both, because Codex reads the Codex one and Claude reads the Claude one, so drift means two hosts install different "versions". The Codex manifest has `skills`; the Claude manifest does not.

**How `plugin/AGENTS.md` reaches agents:** neither host loads AGENTS.md from an installed plugin. Claude Code docs say a plugin-root CLAUDE.md "isn't loaded" (verified warning). Prior research says Codex reads AGENTS.md only from the working project [CITED: developers.openai.com/codex skills docs via STACK.md, LOW–MEDIUM]. The router SKILL.md must therefore say "read the plugin rules in `AGENTS.md`, two folders above this skill" (`${CLAUDE_SKILL_DIR}/../../AGENTS.md` on Claude Code). `tools/install-codex.py`, which copies only skills, must also copy `plugin/AGENTS.md` into the copied `evidence-pack/` folder (e.g. as `references/plugin-rules.md`). See Open Question Q5.

### Pattern 2: Transaction with a redo journal, `state.json` last (WS-06, WS-13, D-09)

**What:** Every mutating command runs one or more transactions:
1. Acquire the OS lock (wait up to `--wait`, default 60 s).
2. Run `recover()`.
3. Load and validate `state.json`. Exit 4 `WORKSPACE_TOO_NEW` if `schema_version` > supported. Upgrade via the registry if it is older (D-09).
4. **Stage:** validate each file against its schema, then write it to `.epb/tmp/txn-<id>/<n>` (`open(..., "xb")`, write, flush, `os.fsync`).
5. **Journal:** write `manifest.json.tmp` listing `[{tmp, final, sha256}]` with `.epb/state.json` **last** (including `INDEX.md`, which is case-root but on the same filesystem). fsync it, then `os.replace` it to `manifest.json`. **This rename is the commit point.**
6. **Apply:** `os.replace(tmp, final)` in manifest order, creating parent dirs, with a bounded retry on `PermissionError` (Windows).
7. `state.json` carries `last_txn = <id>`.
8. Delete the txn dir, then release the lock.

**Recovery:** for each `.epb/tmp/txn-*/`, if `manifest.json` exists, roll forward. For each entry, if the tmp file still exists, replace it. If it is missing, check that the final's sha256 equals the manifest's (already applied). Then delete the dir. With no manifest, delete the dir, because nothing was applied. This is idempotent, so a crash *during* recovery is also safe.

**Read-only commands** (no lock): if a committed-but-unapplied journal exists, add warning `RECOVERY_PENDING` ("the last command was interrupted; the next change command will finish it"). Never repair without the lock.

**Why not "temp + rename per file":** a crash between two renames leaves `.epb/` files that disagree with each other and nothing to say which is right. A redo journal with a single commit point fixes that. Because ID counters live in `state.json` inside the same transaction as the records that use them, an ID can never be reused (Pitfall 11 of prior research).

**`state.json` schema sketch (WS-13 fields from Phase 1; names are recommendations [ASSUMED]):**
```json
{
  "schema_version": 1,
  "plugin_version": "0.1.0",
  "last_txn": {"id": "…", "command": "scan", "committed_at": "2026-10-17T10:00:00Z"},
  "counters": {"run": 2, "source": 3, "evidence": 0, "tag": 0, "claim": 0, "conflict": 0},
  "fingerprints": {"inputs/a/report.pdf": {"src_id": "S001", "version": 1, "sha256": "…", "size": 123, "mtime_ns": 0}},
  "workbooks": [],            // [{file, kind: master|delta|consolidated, number, status: draft|imported, imported_at, writes: [{run, sha256, item_count, tag_digest, written_at}]}]
  "items": {},                // item id -> {version_added, workbook}
  "chunks": {},               // chunk id -> {src_id, version, seg_from, seg_to, status: pending|in_progress|done, claim_count}  (D-07, no raw text)
  "imports": [],              // tick/mark-imported records (Phase 6 fills)
  "stage_keys": {}
}
```
Declare `workbooks`, `items`, `chunks` and `counters.evidence/tag` with full item schemas now, even though they stay empty until Phases 3–6 (PF-07). Use `additionalProperties: false` on every object, so a misspelt key fails validation.

**D-09 upgrade:** `store/upgrade.py` holds `UPGRADE_STEPS: dict[int, Callable]` (empty for v0.1.0) and `CURRENT = 1`. The test monkeypatches `CURRENT = 2` and adds a synthetic step `1 → 2`. It then asserts that:
- the pre-upgrade copies landed in `.epb/runs/<NNN>/pre-upgrade/`
- the upgraded files validate
- the report lists the step
- a read-only command did not upgrade

### Pattern 3: OS lock with wait (WS-07)

Use `fcntl.flock(fd, LOCK_EX | LOCK_NB)` on POSIX and `msvcrt.locking(fd, LK_NBLCK, 1)` on Windows, after `seek(0)`, in a poll loop (about 100–250 ms sleep) until the deadline. The lock file is `.epb/lock`. After acquiring it, write `{pid, host, command, started}` into the file for diagnostics only. On timeout, exit 4 with `LOCK_TIMEOUT`, and say in the message which command holds the lock. **Never** use PID liveness checks: `os.kill(pid, 0)` terminates the process on Windows [CITED: docs.python.org/3/library/os.html#os.kill, via prior research]. The OS releases the lock when the holder dies, so no stale-lock handling is needed.

### Pattern 4: Scan classification (WS-02, WS-03, WS-04)

**Walk** `inputs/` with `os.walk(..., followlinks=False)`.
- List symlinks and junctions as `ignored: link`.
- Path keys are `PurePosixPath(rel).as_posix()`, NFC-normalised. Compare keys case-insensitively on Windows and macOS.
- Junk is ignored and listed. Design names `.DS_Store`, `Thumbs.db` and `~$*`. Recommended additions [ASSUMED]: `desktop.ini`, `._*` (AppleDouble), `.~lock.*#` (LibreOffice; already in the repo `.gitignore`) and `*.tmp`.

**Hash:** `hashlib.file_digest(f, "sha256")`. A stat cache keyed on `(size, mtime_ns)` may skip re-hashing unchanged files. That is the planner's call, but if it is used, add `scan --rehash`. Quality says hash when unsure.

**Classify** each present file against the known `fingerprints` and the source records:

| Situation | Classification | Effect |
|---|---|---|
| path known, same sha256 | unchanged | none |
| sha256 known (source S), path unknown, S's old path(s) now missing | **renamed** | S.paths updated, no new ID |
| sha256 known (S), path unknown, S's old path still present | **duplicate** | path added to S.paths (one source, two paths) |
| path known (source S), new sha256 not seen anywhere | **new version** | `S004v2` (version appended inside `S004.json`, recommended) |
| path known (S), new sha256 equal to another source T | **Q4**, recommend: content wins | path moves to T (duplicate); S loses the path and is `removed from folder` if it has no paths left; reported explicitly |
| neither known | **new** | next `S{n:03d}` (grows to `S1000` naturally; sort numerically) |
| known path not present, source has no remaining paths | **removed from folder** | status only; never deletes records |
| `<file>.note.md` / `<file>.note.yaml` | **sidecar** | own source record (`source_kind: sidecar`), hashed; linked to its target via `sidecar_of`/`sidecars`; an orphan sidecar becomes an open issue |

Tests must cover two files swapping contents, a case-only rename, an NFD name, an empty file, and two identical new files in one scan (one source, two paths).

**MIME (D-13):**
- An in-house table `core/mime.py` maps extensions to the canonical MIME, for every type the design lists. stdlib `mimetypes` is a fallback for anything else, through a **fresh `mimetypes.MimeTypes()` instance**, never the module-level `guess_type`, which reads `/etc/mime.types` and the Windows registry.
- The magic-byte table covers at least: `%PDF-`, `PK\x03\x04` (then the `[Content_Types].xml` member to tell docx/xlsx/pptx/zip apart), `D0 CF 11 E0 A1 B1 1A E1` (OLE2: .msg/.doc/.xls), `\x89PNG`, `FF D8 FF`, `GIF87a`/`GIF89a`, `RIFF....WAVE`, `....ftyp` (MP4/MOV), `1A 45 DF A3` (MKV/WebM), `7z\xBC\xAF\x27\x1C` and `1F 8B` (gzip).
- When extension and content disagree, content wins. Record `mime_mismatch: {by_extension, by_content}` on the source and show it in the scan report and INDEX Open issues.

**Expander seam (PF-11):** `sources/expanders/__init__.py` defines an `Expander` protocol and an empty registry. Phase 2 registers the zip and email expanders. A `.7z` is just a source in Phase 1, and the D-14 `unprocessed: 7z tool not installed` status comes with Phase 2 expansion. Record `parents: []` on every Phase 1 source (D-08).

### Pattern 5: Format module, writer and an independent validator (BLD-01, -02, -03, -08)

`formats/probematrix_v2.py` holds data only: the marker, the three sheet names, the 30 headers, the `wch` widths, the 11 attachment headers and widths, the 10 metadata rows (labels and notes), the enums (type 8, priority 4, analysis status 3, QA status 8, retention 4, custody condition 5, custody action 6), and `LIST_SEPARATOR = ", "`.

**Writer:**
- Assign the value, then force `cell.data_type = "s"` and `cell.number_format = "@"`. This yields `t="inlineStr"` with no `<f>` (verified, Code Example 1).
- Sanitise first: replace C0 controls matching openpyxl's `ILLEGAL_CHARACTERS_RE` (pattern `[\000-\010]|[\013-\014]|[\016-\037]`, verified) and reject U+FFFE, U+FFFF and lone surrogates.
- **Run `validate_rows()` before writing**, because openpyxl truncates >32,767 characters silently (verified: a 40,000-character value was written as 32,767).
- Set fixed `wb.properties.created/modified` from the injectable clock, for reproducibility.

**Validator: two independent passes, returning findings with stable codes [code names ASSUMED]:**
1. **Structure and values** via `openpyxl.load_workbook(path, read_only=True)` (defused):
   - Sheet names and order are exactly `Pack Metadata`, `Evidence Pack`, `Attachments Manifest`.
   - Metadata is exactly 10 rows. A1–A6 labels are exact, B1 is exactly `EVIDENCE_PACK_V2` (V1 rejected), B5 equals the data row count, B6 is `0`, row 7 is empty, and rows 8–10 are the exact notes.
   - The Evidence Pack header row is exactly the 30 headers in order. The Attachments header row is exactly the 11, with no data rows.
   - Per row:
     - Type and Description are non-blank (after `strip()`).
     - Type, Priority and Analysis Status are exact enum values.
     - QA Status and Retention Category are blank or an exact enum value.
     - Integrity Verified is exactly `Yes` or `No`.
     - Collection Date is blank or `^\d{4}(-\d{2}(-\d{2})?)?$`.
     - Chain of Custody is a JSON array of objects. Each object has the 4 required string keys, optional keys only from the `ChainOfCustodyEntry` list with the right types and enums, and no unknown keys (stricter than the importer).
     - Every cell value is `str` or `None`.
2. **Raw XML scan** via `zipfile` + `defusedxml.ElementTree` over every `xl/worksheets/*.xml`:
   - Reject any `<f>` element.
   - Reject any `<c>` whose `t` is not in `{inlineStr, s, str}`, or a typeless `<c>` that has a `<v>` (numeric).
   - Reject `t="str"` that has an `<f>`.
   - Reject text over 32,767 characters, and flag exactly 32,767 as probable truncation (Q3).

   **Accept `t="str"` without `<f>`.** ProbeMatrix's own exports use it: the prototype pack's sheets have `types ['str'] has_f False` (verified).
3. **Structural list-fragment check (DEF-14, PF-05)** on Tags, Linked Individuals, Linked Equipment, Related Evidence and Regulatory Requirements. Apply the importer's split exactly, then require:
   - every fragment non-empty
   - every separator exactly `", "` (no other whitespace around commas)
   - no leading or trailing whitespace on the cell
   - no `;`
   - balanced `()[]{}` in every fragment
   - no duplicate fragments

   On the prototype pack, this check finds **24 Linked Equipment cells with unbalanced-bracket fragments, 24 with `;`, and 1 Linked Individuals cell with `;`, across 38 of 60 rows** [VERIFIED: local probe]. SC3's "fails the prototype reference pack on its comma-bearing list fragments" is therefore met by asserting that the `LIST_FRAGMENT_UNBALANCED` code is among the findings. Don't assert just "invalid": the prototype pack *also* lacks the `Attachments Manifest` sheet, so it fails structurally too.

Expose `validate_workbook(path) -> list[Finding]` and `validate_rows(meta, rows) -> list[Finding]`. The writer calls the second before saving and the first after saving. No CLI verb is needed in Phase 1, because `tools/make-smoke-pack.py` and pytest call the module (§15.2 has no validate verb).

### Pattern 6: `init` (WS-01, WS-11, WS-12, D-06, D-15)

`epb init --title T [--slug] [--prefix] [--timezone] [--case DIR]` performs these steps in one transaction:
1. Create `inputs/`, `outputs/`, `INDEX.md`, and `.epb/` holding `case.yaml`, `state.json`, `.gitignore`, `.gitattributes`, `inbox/`, `tmp/`, `runs/` and `private/` (with its own `.gitignore` of `*`, per §6).
2. Write `.epb/.gitignore` with exactly `segments/ ledger/ inbox/ tmp/ media/ runs/ private/` (A2, WS-11).
3. Write `.epb/.gitattributes` with `* -text` (D-06).
4. Run the sync-folder and git checks as warnings (exit 0 with warnings).

Defaults:
- slug: from the folder name, lowercase ASCII, hyphens, a reserved-name guard and a length cap.
- prefix: the title's initials, uppercase, validated `^[A-Z][A-Z0-9]{1,5}$` [ASSUMED range].
- timezone: `TZ` env var, then `/etc/timezone`, then the target of `/etc/localtime` after `zoneinfo/`. On this machine, `/etc/localtime → /usr/share/zoneinfo/Asia/Kolkata` (verified). Note that `datetime.now().astimezone().tzinfo` returns `IST`, not an IANA name (verified), so it must not be used.
- If none is found, require `--timezone` (exit 2 with a hint). Validate with `zoneinfo.ZoneInfo`.

`case.yaml` should declare the later optional fields now, with defaults and `additionalProperties: false`, so later phases need no migration [ASSUMED field names]: `case_number` (default `INC-<PFX>-<year>` at build), `languages` (default `[en]`), `draft_warning_days` (7), `conflict_tolerance_seconds` (60) and `tags_extra` ([]).

Re-running `init` on an initialised folder exits 0 with "already set up" when there is no conflicting flag, and exits 2 `WORKSPACE_EXISTS` on conflicting flags. Never overwrite [ASSUMED behaviour].

### Pattern 7: INDEX.md providers (WS-09, PF-04)

`index/providers.py` is an ordered list of six provider functions, `(state, case) -> markdown`:
1. case header
2. what to import where
3. inputs snapshot
4. outputs snapshot
5. open issues
6. run history

Any provider without data returns `none yet`. The Phase 1 producers are:
- the header
- the inputs snapshot from scan: path, type, size, short sha256, first-seen run, last-processed run and status
- open issues: removed inputs, MIME mismatches, orphan sidecars, ignored links
- run history from `runs/`

Columns for segments, claims and items show `none yet`.

**Tick syntax (fix it now, parse it in Phase 6):** use one GitHub task-list line per workbook, outside the table, keyed by file name: `- [ ] Imported: evidence-pack-<case>-master.xlsx`. It renders as a checkbox in GitHub, VS Code and Obsidian, and it survives table reflow (prior research, Pitfall 10) [ASSUMED rendering]. INDEX is regenerated inside the same transaction, before `state.json`.

### Pattern 8: Sync-folder and git warnings (WS-11, WS-12)

Resolve the case path (`Path.resolve()`), then check it against the roots below, in this order. Any hit gives a plain-language warning with the provider name.

| Source of evidence | Linux | macOS | Windows |
|---|---|---|---|
| Dropbox `info.json` (`path` field) | `~/.dropbox/info.json` | `~/.dropbox/info.json` | `%APPDATA%\Dropbox\info.json`, `%LOCALAPPDATA%\Dropbox\info.json` [CITED: help.dropbox.com/installs/locate-dropbox-folder] |
| OneDrive | `~/.config/onedrive/config` `sync_dir` (abraunegg client) [ASSUMED] | `~/Library/CloudStorage/OneDrive-*` [ASSUMED] | env `OneDrive`, `OneDriveConsumer`, `OneDriveCommercial` [CITED: community docs, LOW] |
| Google Drive | GVFS `/run/user/<uid>/gvfs/google-drive:*` [ASSUMED] | `~/Library/CloudStorage/GoogleDrive-*` [ASSUMED] | `My Drive` under a virtual drive letter or `~\My Drive` [ASSUMED] |
| iCloud Drive | n/a | `~/Library/Mobile Documents/com~apple~CloudDocs` [ASSUMED] | `~\iCloudDrive` [ASSUMED] |
| Name heuristic (all OSes, case-insensitive path components) | `OneDrive`, `OneDrive - *`, `Dropbox`, `Dropbox (*)`, `Google Drive`, `GoogleDrive-*`, `My Drive`, `iCloud Drive`, `iCloudDrive`, `Mobile Documents`, `CloudStorage` [ASSUMED] |

Word the warning as "appears to be inside…", because the heuristics can false-positive. Keep the provider table data-driven, so later fixes are one-line edits.

**Git:**
- Find a work tree with `git -C <case> rev-parse --show-toplevel`. If there is no `git` binary, walk up looking for `.git`.
- Warn if `git ls-files .epb/private` lists anything (already tracked).
- Warn if `git check-ignore -q .epb/private/probe` exits 1 (not ignored).
- Without a git binary but with a `.git` found, warn "inside a git repository; could not check ignore rules because git is not installed".

### Pattern 9: Exit codes and stable error codes (PKG-05)

| Exit | Meaning | Phase 1 codes (stable strings, proposed [ASSUMED]) |
|---|---|---|
| 0 | OK (including "nothing to do", and warnings) | n/a |
| 1 | Gate failure (content rejected) | `VALIDATION_FAILED` (format module findings), later phase gates |
| 2 | Usage | `USAGE`, `NOT_A_WORKSPACE`, `WORKSPACE_EXISTS`, `TIMEZONE_REQUIRED`, `BAD_ARGUMENT` |
| 3 | Missing dependency | `ENV_NOT_SET_UP`, `CORE_PACKAGE_MISSING`, `PYTHON_TOO_OLD` |
| 4 | Internal or environment | `LOCK_TIMEOUT`, `WORKSPACE_TOO_NEW`, `STATE_INVALID` (recommend 4, not 1, see Q8), `TARGET_LOCKED`, `INTERNAL_ERROR` |

The envelope is `{ok, command, exit_code, epb_version, data, warnings[], errors[{code, message, hint, pointer}], next[]}`.
- Subclass `ArgumentParser.error()` so that usage errors under `--json` emit the envelope and exit 2.
- A top-level handler converts any uncaught exception to exit 4 `INTERNAL_ERROR`, with the traceback on stderr only. An uncaught Python exception exits 1, which an agent reads as "fix your content" (prior research, Anti-Pattern 6).
- `sys.stdout.reconfigure(encoding="utf-8")` at start-up.

### Pattern 10: Launcher and private environment (PKG-06, D-03, A8)

**`scripts/epb.py`:**
- **Syntax that parses on old Pythons:** no `match`, no walrus, no `X | Y` annotations, nothing newer than 3.6 at module level. That way a 3.9 `/usr/bin/python3` on macOS reaches the friendly check.
- It inserts its own directory into `sys.path`, imports `epb.launcher` (stdlib only) and calls `main(argv)`.

**`epb.launcher.main`:**
1. If `sys.version_info < (3, 11)` and the command is not `doctor --setup`, exit 3 `PYTHON_TOO_OLD` with the plain-language Python install step. `doctor --setup` instead searches for a better interpreter.
2. `env_dir = data_root / "envs" / PLUGIN_VERSION`, where `data_root` is the D-03 path for the OS. `env_python` is `bin/python` on POSIX and `Scripts\python.exe` on Windows.
3. If the command is `doctor` (with or without `--setup`), run `epb.doctor` in the *current* interpreter, stdlib only. Setup never runs inside the env it is building.
4. Otherwise, if the current interpreter is not `env_python` (compare resolved `sys.prefix` to `env_dir`):
   - if the env is missing or its marker is stale, exit 3 `ENV_NOT_SET_UP` with "run doctor --setup"
   - else run `subprocess.run([env_python, __file__, *argv], env={…, "EPB_IN_ENV": "1"})` and exit with its return code

   Use subprocess rather than `os.execv` on every OS, because `os.execv` on Windows spawns a new process and returns early, which breaks exit codes and stdio in agent shells [ASSUMED Windows behaviour; keep it uniform].
5. Inside the env, import `epb.cli.main` and run it.

**`doctor --setup`:**
1. **Interpreter discovery:** prefer the current interpreter if it is ≥3.11. Else try `python3.14 … python3.11, python3, python` (POSIX) or `py -3.14 … py -3` (Windows), each probed with `-c "import sys; print(sys.version_info[:3])"`. Never assume `python3`: it is missing on Windows, and **`python` is missing on this Ubuntu machine** (verified).
2. **Create the venv** at `env_dir` via `subprocess [py, "-m", "venv", env_dir]`. On failure, detect Debian's missing-ensurepip case [ASSUMED message text: "ensurepip is not available"] and print `sudo apt install python3-venv` (or `python3.X-venv`).
3. `env_python -m pip install -U "pip>=26.1"`.
4. `env_python -m pip install [--uploaded-prior-to P14D] -r <plugin>/requirements.txt` (the cutoff policy is Q1).
5. Verify by importing each core module in the env.
6. Write the marker `<env_dir>/epb-env.json` (atomic) with `{plugin_version, requirements_sha256, python, created_at}`. A dev build with the same version but changed requirements is detected via the hash.
7. Report Ready / Optional / What to do next (D-17). `--json` includes `data.launch = [env_python, abs path of epb.py]`, which the skill uses as the absolute command (A8: "Skills launch the CLI from that environment by absolute path").

Old version envs are left in place and listed under `--verbose`. The manual explains manual removal (D-03).

**Skill invocation contract:**
- On Claude Code, the SKILL.md body uses `${CLAUDE_SKILL_DIR}/scripts/epb.py`. This is substituted textually, not as an env var [CITED: code.claude.com/docs/en/skills].
- SKILL.md also says, host-neutrally: "the `scripts/epb.py` beside this SKILL.md". Codex has no documented substitution [ASSUMED], and if the literal `${CLAUDE_SKILL_DIR}` is read as an unset env var it expands to `/scripts/epb.py`.
- First call uses `python3` (Linux/macOS) or `py -3` (Windows). After setup, use `data.launch`.

### Pattern 11: Doctor probe registry (PKG-07, D-14, D-17)

A data table of `ToolSpec{id, kind: python|binary, names[], version_args, version_regex, enables[], install{linux, macos, windows}, optional: bool}`, probed with `shutil.which` + `subprocess.run(..., timeout=10)`.

Phase 1 rows:
- Python (≥3.11)
- private env status and each core package version (via `importlib.metadata` *of the env*, so doctor runs `env_python -c` to read them)
- `7z`/`7za`/`7zz`: version from the banner of `7z i`. On this machine the first line is blank and line 2 reads `7-Zip 26.00 (x64) …` (verified)
- `ffmpeg -version`
- `tesseract --version`
- `soffice`, `pandoc`, `git`
- the optional Python extras (installed or not)

Example install commands (from STACK.md, [ASSUMED] for macOS and Windows): Ubuntu `sudo apt install 7zip` (Ubuntu 26.04 package `7zip` provides `/usr/bin/7z`, verified), `ffmpeg`, `tesseract-ocr`; macOS `brew install sevenzip ffmpeg tesseract`; Windows `winget install 7zip.7zip Gyan.FFmpeg UB-Mannheim.TesseractOCR`. winget's 7-Zip is not on PATH, so also probe `C:\Program Files\7-Zip\7z.exe` [ASSUMED].

`doctor` also runs the sync-folder check when invoked inside a case folder (WS-12). A missing optional tool never changes the exit code (PKG-07). Doctor exit codes: 0 when core is ready; 3 when the env is not set up, so agents can branch.

### Pattern 12: CI supply-chain checks (PKG-09, D-12)

**Workflow (Linux, matrix Python 3.11 + 3.14):**
1. `actions/checkout@v7` and `actions/setup-python@v7`. Both are latest, published 2026-07-20, so more than 14 days old (verified via `gh api`).
2. `python -m pip install -U "pip>=26.1"`
3. `pip install --uploaded-prior-to P14D -r requirements-dev.txt`
4. `pip install` each reviewed exception pin, if any, without the cutoff
5. `ruff check .` and `ruff format --check .`
6. `pytest -q`
7. `python tools/check_dependency_age.py`
8. `python tools/check_licences.py`
9. `claude plugin validate . --strict && claude plugin validate ./plugin --strict`, only if `claude` is on PATH, else print a skip (D-02)

**Dependency age** (`tools/check_dependency_age.py`, stdlib + network, CI only):
- Enumerate installed dists via `importlib.metadata.distributions()`.
- For each, GET `https://pypi.org/pypi/<name>/<version>/json` and take the earliest `urls[].upload_time_iso_8601`.
- Fail if it is less than 14 days before now, unless `tools/dependency-age-exceptions.json` has `{package, version, advisory, reason, reviewed_by, reviewed_on}`.
- Also warn about exception entries whose version is now older than 14 days (stale), so they can be removed.
- The cutoff at install time keeps CI deterministic. Without it, every upstream release would turn CI red for two weeks.
- Upload times were verified via the API: pypdf `6.19.0 2026-09-16`, `6.20.0 2026-10-09`, `6.21.0 2026-10-16`, `6.21.1 2026-10-17`.
- Unit-test the decision logic with canned JSON (no network in pytest).

**Licences** (`tools/check_licences.py`, stdlib):
- For each installed dist, read `License-Expression` (PEP 639), else `License`, else the `License ::` classifiers.
- Evaluate SPDX `OR` (any allowed alternative passes) and `AND` (all must be allowed).
- Map classifier names to SPDX (`MIT License` → MIT, `BSD License` → BSD-*, `Python Software Foundation License`/`PSFL` → PSF-2.0, `Apache Software License` → Apache-2.0).
- Allow-list: `MIT, MIT-0, MIT-CMU, BSD-2-Clause, BSD-3-Clause, Apache-2.0, PSF-2.0, ISC`, plus `MPL-2.0` (dev-only, hypothesis if ever added).
- Per-package reviewed overrides in `tools/licence-allowlist.json`. pypdfium2's `License` is free text, `BSD-3-Clause, Apache-2.0, dependency licenses` (verified).
- The raw metadata of the full core + pytest set was dumped this session (`License-Expression` / `License` / classifier per package), and every value maps to the allow-list above.

**D-12 file contents:**
- `requirements-dev.txt` is `-r plugin/requirements.txt` + `pytest>=9.0` + `ruff==0.16.10`. pip resolves nested `-r` paths relative to the including file [ASSUMED from pip docs].
- **Recommend adding no permissive extras until their phase lands.** docling would pull torch into every Phase 1 CI run (Q9). `requirements-dev-full.txt` can be created now as a stub that is unused until Phase 10.
- Create the optional extras files now, with licence header comments, to satisfy PKG-08's "GPL extras are kept in separate optional requirements files and their licences are documented". The pins come from STACK.md.

### Pattern 13: User manual first edition (DOC-04, DOC-05)

Recommended location: `docs/manual/` (one file per chapter) or a single `docs/USER-MANUAL.md`. Design §5 had `INSTALL.md` + `USER-GUIDE.md`, and A14 asks for "a detailed manual".

Phase 1 chapters:
1. What this plugin does
2. What stays on your computer and what the AI host sees (DOC-04: conversion is local, excerpts go to the host's model provider, `.epb/private/` must not be synced, de-identification is always on)
3. Install Python (Linux tested; Windows and macOS marked **"not yet tested on this system"**, DOC-05)
4. Add the plugin to Claude Code (`/plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder`, then `/plugin install probematrix-evidence-pack-builder@probematrix-evidence-pack-builder`; CLI equivalents verified locally with a path source)
5. First-time setup (`doctor --setup`), quoting the real output (D-17)
6. Your first case folder (init, scan, reading INDEX.md)
7. Where the private environment lives and how to remove it (D-03)

Add a golden test that renders doctor's human output from a fixed fake probe set and compares it with a marked fenced block in the manual. This keeps "the manual quotes this output exactly" true as wording changes [recommendation].

### Anti-Patterns to Avoid
- **Module-level third-party imports** in the launcher, doctor or envelope path. They turn a missing package into a traceback and exit 1 instead of a JSON exit 3. Add an `ast` test that these modules import only stdlib.
- **`ws.append([...])` with mixed Python types** or relying on openpyxl inference. Always force text cells.
- **Validating rows in memory only.** Re-open the saved file; truncation and formulas happen at write time.
- **Module-level `mimetypes.guess_type`.** It is machine-dependent (verified: module `.wav` → `audio/x-wav` vs instance `audio/vnd.wave` on the same machine).
- **`yaml.safe_load` for any workspace file.** YAML 1.1 coercion (verified: `12:30`→750, `0123`→83, `no`→False, `2017`→int, a date→`datetime.date`).
- **Absolute paths in `.epb/` state.** Cowork and other hosts may map the folder differently. Store case-relative POSIX keys only.
- **Writing anything into `inputs/`** (§6 rule), or following symlinks out of it.
- **A committed `.agents/skills` symlink** (D-01 forbids it).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XLSX read/write | A zip+XML writer | openpyxl (writer + reader); zipfile + defusedxml only for the *validation* scan | Styles, widths, shared strings and content types are fiddly |
| JSON Schema validation | Ad-hoc dict checks | jsonschema `Draft202012Validator` with `iter_errors` | All errors with paths; schemas are the contract |
| SHA-256 streaming | Chunk loops | `hashlib.file_digest` | stdlib, correct, fast |
| Virtual environments | Copying site-packages | stdlib `venv` + pip | PEP 668 safe; standard |
| Hardened XML | Custom entity stripping | defusedxml (and openpyxl's automatic use of it) | Billion-laughs / XXE |
| Dependency resolution cutoff | Your own resolver | `pip --uploaded-prior-to P14D` (pip ≥26.1) | Verified to resolve the PKG-08 floors |
| Timezone database | Offset tables | stdlib `zoneinfo` | IANA names; validation |

**Key insight:** the hand-written pieces in Phase 1 are deliberately small and stdlib-only: the OS lock, the atomic and journal store, the strict YAML loader, the MIME table, the licence and age scripts, and the SKILL.md lint. In each case the off-the-shelf option either adds a dependency for under 100 lines of code or was shown this session to be wrong for this use (pip-licenses on `OR`, `claude plugin validate` on frontmatter, `mimetypes` on cross-version determinism).

## Common Pitfalls

### Pitfall 1: openpyxl turns `=…` into a formula and truncates long strings silently
**What goes wrong:** Assigning `"=SUM(1,2)"` sets `data_type 'f'`. A >32,767-character string is written as exactly 32,767 characters, with no error [VERIFIED: local probe].
**How to avoid:** Force `data_type = "s"` after assignment, sanitise control characters, and length-check before writing (Code Example 1).
**Warning signs:** `has <f>: True` in the raw scan, or a cell of length exactly 32,767.

### Pitfall 2: An on-disk validator that rejects valid ProbeMatrix-style string cells
**What goes wrong:** SheetJS exports use `t="str"` cells without formulas (verified in the prototype pack), and an over-strict validator rejects them.
**How to avoid:** Allow `inlineStr`, `s` and `str`-without-`<f>`. Reject `n`, `b`, `d`, `e`, typeless cells with `<v>`, and any `<f>`.

### Pitfall 3: The metadata layout is off by one
**What goes wrong:** Following design §8.4's "rows 7–9" puts the notes one row early.
**How to avoid:** Use the verbatim exporter rows: a blank row 7, notes in rows 8–10. Record the correction in a §20 amendment (D-10).

### Pitfall 4: Asserting "the prototype pack fails" instead of "fails for list fragments"
**What goes wrong:** The prototype pack also lacks the Attachments Manifest sheet, so a test that checks only `valid is False` passes for the wrong reason.
**How to avoid:** Assert that the specific `LIST_FRAGMENT_*` finding codes appear, and pin the expected count range (24 Linked Equipment bracket fragments, verified).

### Pitfall 5: MIME results differ by Python version and machine
**What goes wrong:** On 3.11 a fresh `MimeTypes()` returns `None` for `.md`, `.yaml`, `.7z`, `.mkv`, `.m4a` and `.rtf`, while 3.14 knows them. The module-level function reads `/etc/mime.types` [VERIFIED: both interpreters probed].
**How to avoid:** Make the in-house table authoritative and test that the same files give the same MIME on 3.11 and 3.14 in CI.

### Pitfall 6: jsonschema `format` does nothing by default
**What goes wrong:** `format: date-time` is not checked even with `FormatChecker()` (it needs extra packages). Without a checker, nothing is checked at all [VERIFIED: local probe: bad `date-time` → no error; bad `date` → error only with `FormatChecker`].
**How to avoid:** Use `pattern` for timestamps (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$`), dates-with-precision, IDs and hashes.

### Pitfall 7: The venv's pip is too old for the two-week flag
**What goes wrong:** `python -m venv` bundles pip 25.1.1, which fails `--uploaded-prior-to` with `no such option` [VERIFIED].
**How to avoid:** Upgrade pip to ≥26.1 inside the env first (verified to work: pip 26.2.1). Or set `PIP_UPLOADED_PRIOR_TO` only after upgrading.

### Pitfall 8: Manifest drift between hosts
**What goes wrong:** Codex installs the Codex manifest's version and Claude installs the Claude manifest's [VERIFIED], and Codex rejects an entry name that does not match `plugin.json` `name` [VERIFIED].
**How to avoid:** A CI test asserting equal `name` and `version` across both manifests and the marketplace entry.

### Pitfall 9: Timezone default returns an abbreviation
**What goes wrong:** `datetime.now().astimezone().tzinfo` gives `IST` [VERIFIED], which is not an IANA name.
**How to avoid:** Read `TZ`, then `/etc/timezone`, then the `/etc/localtime` symlink. Otherwise require `--timezone`. On Windows, `zoneinfo` needs the `tzdata` package (Q10).

### Pitfall 10: Strict YAML still honours explicit tags
**What goes wrong:** With the implicit resolvers cleared, `!!int 5` still loads as `5` [VERIFIED].
**How to avoid:** After loading, walk the result and reject anything that is not `str`, `list` or `dict` (`YAML_NON_TEXT`). Schema validation also catches it, but the walk gives a clearer error.

### Pitfall 11: Crash tests that use exceptions instead of real crashes
**What goes wrong:** Raising inside the transaction runs `finally`/`__exit__` cleanup, so the test passes while a real power cut would not.
**How to avoid:** The fault seam calls `os._exit(97)` in a subprocess at a named checkpoint (Code Example 7). Enumerate the checkpoints from the transaction itself, so a new step is automatically covered.

### Pitfall 12: Host sandboxes block setup
**What goes wrong:**
- Codex's default sandbox blocks network, so pip cannot download [CITED: STACK.md, LOW].
- Claude Code's optional sandbox may block writes outside the project, i.e. to `~/.local/share/probematrix-epb/` [ASSUMED].
**How to avoid:** Have doctor print a plain-language fallback ("run this command in a terminal: …"). The manual covers it. The env path is fixed and shared (D-03), so one terminal run serves every host.

### Pitfall 13: The Claude plugin cache is versioned
**What goes wrong:** The install path includes the version (`…/cache/<mkt>/<plugin>/0.1.0-dev/`, verified). Re-installing an unchanged version during UAT iterations may not refresh the files [ASSUMED].
**How to avoid:** Bump a dev suffix per UAT build, or uninstall and reinstall. The UAT should use a local-path marketplace from the phase branch checkout.

## Code Examples

These were written for this research (clean-room). Examples 1 and 2 were executed this session.

### Code Example 1: text-only cell writing (verified with openpyxl 3.1.5; SheetJS 0.18.5 read back exact strings)
```python
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE   # pattern verified: [\000-\010]|[\013-\014]|[\016-\037]

MAX_CELL = 32_767

def put_text(ws, row: int, col: int, value: str) -> None:
    if not isinstance(value, str):
        raise TypeError("every pack cell is text")           # never int/date/bool (BLD-02)
    clean = ILLEGAL_CHARACTERS_RE.sub(" ", value)
    if len(clean) > MAX_CELL:
        raise ValueError("cell too long")                     # openpyxl would truncate silently
    cell = ws.cell(row=row, column=col)
    cell.value = clean                                        # '=...' sets data_type 'f' here...
    cell.data_type = "s"                                      # ...so force text: written as t="inlineStr", no <f>
    cell.number_format = "@"
```

### Code Example 2: strict YAML loader (verified: `12:30`, `0123`, `no`, `2017`, `2020-09-17`, `~` all stay strings; duplicate keys rejected; `safe_dump` quotes them and round-trips)
```python
import yaml

class TextLoader(yaml.SafeLoader):
    pass

TextLoader.yaml_implicit_resolvers = {}            # class-level copy; SafeLoader itself is untouched (verified)

def _mapping_no_dupes(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate key {key!r}", key_node.start_mark)
        seen.add(key)
    return loader.construct_mapping(node, deep)

TextLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping_no_dupes)

def load_text_yaml(text: str):
    data = yaml.load(text, Loader=TextLoader)       # noqa: S506 - custom safe loader
    _assert_text_only(data)                         # rejects explicit tags like !!int (Pitfall 10)
    return data

def dump_yaml(data) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)   # quotes '12:30', '0123', 'no' (verified)
```

### Code Example 3: OS lock with wait (stdlib; Windows branch untested here [ASSUMED])
```python
import os, sys, time

def acquire(path, wait_s: float = 60.0, poll_s: float = 0.2):
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + wait_s
    while True:
        try:
            if sys.platform == "win32":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd                                   # caller writes {pid, host, command, started} for diagnostics
        except OSError:
            if time.monotonic() >= deadline:
                os.close(fd)
                raise LockTimeout()                     # -> exit 4 LOCK_TIMEOUT
            time.sleep(poll_s)
```

### Code Example 4: commit and recover (shape)
```python
def commit(self):
    txn_dir = self.tmp_root / f"txn-{self.id}"
    entries = []
    for i, (final, data) in enumerate(self.staged + [(STATE_PATH, self.state_bytes)]):   # state.json LAST
        tmp = txn_dir / f"{i:04d}"
        write_durable(tmp, data)                         # open 'xb', write, flush, fsync
        entries.append({"tmp": tmp.name, "final": final, "sha256": sha256(data)})
        faults.checkpoint(f"stage:{i}")
    write_durable(txn_dir / "manifest.json.tmp", json_bytes({"txn": self.id, "entries": entries}))
    os.replace(txn_dir / "manifest.json.tmp", txn_dir / "manifest.json")    # COMMIT POINT
    fsync_dir(txn_dir); faults.checkpoint("manifest")
    apply(txn_dir, entries)                              # os.replace each, retry on Windows PermissionError
    remove_tree(txn_dir); faults.checkpoint("cleanup")

def recover(tmp_root):
    for txn_dir in sorted(tmp_root.glob("txn-*")):
        manifest = txn_dir / "manifest.json"
        if manifest.exists():
            apply(txn_dir, read_json(manifest)["entries"])   # idempotent: skip entries whose tmp is gone and final hash matches
        remove_tree(txn_dir)                                 # no manifest -> nothing was applied
```

### Code Example 5: launcher entry (stdlib; old-syntax-safe)
```python
# scripts/epb.py - keep this file parseable by old Python 3 (no match, no walrus, no PEP 604)
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epb import launcher  # noqa: E402  (stdlib-only module)

if __name__ == "__main__":
    sys.exit(launcher.main(sys.argv[1:]))
```

### Code Example 6: structural list-fragment check (DEF-14 structural; verified against the prototype pack)
```python
LIST_COLUMNS = ("Tags", "Linked Individuals", "Linked Equipment", "Related Evidence", "Regulatory Requirements")
PAIRS = {")": "(", "]": "[", "}": "{"}

def list_findings(column: str, cell: str) -> list[str]:
    if not cell:
        return []
    out = []
    if cell != cell.strip():
        out.append("LIST_CELL_WHITESPACE")
    if ";" in cell:
        out.append("LIST_SEMICOLON")                       # importer keeps "a; b" as ONE entry
    raw = cell.split(",")
    if any(not f.startswith(" ") for f in raw[1:]) or any(f.startswith("  ") for f in raw[1:]):
        out.append("LIST_SEPARATOR")                       # must be exactly ", "
    frags = [f.strip() for f in raw]                       # same as the importer's split/trim
    if any(not f for f in frags):
        out.append("LIST_EMPTY_FRAGMENT")
    if any(not _balanced(f) for f in frags):
        out.append("LIST_FRAGMENT_UNBALANCED")             # "Lamp Posts (125 W" + "9 in radius)"
    if len(set(frags)) != len(frags):
        out.append("LIST_DUPLICATE")
    return out

def _balanced(s: str) -> bool:
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in PAIRS and (not stack or stack.pop() != PAIRS[ch]):
            return False
    return not stack
```

### Code Example 7: crash-injection seam and test
```python
# epb/core/faults.py
import os
_TARGET = os.environ.get("EPB_TEST_CRASH_AT")          # test-only; never documented to users
SEEN: list[str] = []                                   # names recorded for enumeration

def checkpoint(name: str) -> None:
    SEEN.append(name)
    if _TARGET == name:
        os._exit(97)                                   # real crash: no finally, no __exit__

# tests/store/test_crash_resume.py
@pytest.mark.parametrize("point", enumerate_checkpoints("scan"))     # dry run collects faults.SEEN
def test_scan_resumes_after_crash(case_with_inputs, point):
    r = run_epb(["scan", "--json"], case_with_inputs, env={"EPB_TEST_CRASH_AT": point})
    assert r.returncode == 97
    r2 = run_epb(["scan", "--json"], case_with_inputs)               # recovery + rerun
    assert r2.returncode == 0
    assert_state_consistent(case_with_inputs)                        # schemas valid, no tmp/txn-*, counters == max ids, no dup ids
```

### Code Example 8: no-network guard (TST-01)
```python
# tests/conftest.py
import socket
import pytest

@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def refuse(*a, **k):
        raise RuntimeError("network access is not allowed in tests")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
```
Subprocess tests don't inherit the monkeypatch. Only spawn `epb` (which makes no network calls) and never pip.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Plugin = repo root, `.agents/skills` symlink for Codex | `plugin/` subtree + `source: "./plugin"`; Codex reads `.claude-plugin/marketplace.json` and prefers `.codex-plugin/plugin.json` | Verified 2026-10-17 (claude 2.1.302, codex-cli 0.154.0) | Docs, tests and reference never ship; one marketplace for both hosts |
| `python-magic` | stdlib + magic bytes | D-13 | No libmagic on Windows |
| `pip install` newest | `pip --uploaded-prior-to P14D` (pip ≥26.1) | pip 26.0 / 26.1 | Deterministic two-week rule |
| PID-file locks | OS advisory locks | n/a | No stale locks; no `os.kill` on Windows |
| `Path.walk` | `os.walk` (3.11 floor) | `Path.walk` is 3.12+ | Use `os.walk(followlinks=False)` |

**Deprecated/outdated:**
- Design §5 `install-codex.sh`, root `schemas/` and `"skills": "./skills"` in the Claude manifest are replaced by D-01, D-05 and D-02.
- Design §8.4 metadata "rows 7–9" is incorrect: the notes are in rows 8–10.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Debian/Ubuntu without `python3-venv` fails with "ensurepip is not available"; fix is `apt install python3-venv` | Pattern 10 | Setup error message less helpful; low |
| A2 | Windows interpreter discovery via `py -3.X`; Store alias stub; `os.execv` misbehaves on Windows | Pattern 10 | Windows setup untested (A9 marks it untested anyway) |
| A3 | Codex does not substitute `${CLAUDE_SKILL_DIR}` | Pattern 10 | Skill path instructions slightly redundant; low |
| A4 | Codex sandbox blocks network for pip; Claude Code sandbox may block writes to the env folder | Pitfall 12 | Users hit a setup failure; manual fallback mitigates |
| A5 | Sync-folder path heuristics for OneDrive, Google Drive and iCloud (all but Dropbox `info.json`) | Pattern 8 | Missed or false warnings; warnings only |
| A6 | macOS/Windows install commands (brew/winget IDs, 7-Zip install dir) | Pattern 11 | Wrong install hint on untested OSes |
| A7 | Cowork runtime (pip, binaries) | Summary | Out of Phase 1 test scope (PKG-10 Phase 10) |
| A8 | `claude plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder` works once the marketplace is on `main` (only local-path install was executed) | Pattern 1 | UAT must use a local-path install from the phase branch |
| A9 | Re-installing an unchanged plugin version may not refresh the Claude cache | Pitfall 13 | UAT confusion; bump the dev version |
| A10 | `msvcrt.locking` lock and `os.replace` retry behave as described on Windows | Code Example 3 | Windows untested until post-v0.1.0 (A9) |
| A11 | Junk-file additions (`desktop.ini`, `._*`, `*.tmp`), prefix regex, case.yaml optional field names, error-code strings, state.json field names | Patterns 2, 4, 6, 9 | Naming only; the planner may rename |
| A12 | GitHub task-list ticks render as checkboxes in common editors | Pattern 7 | Cosmetic; parser tolerant anyway |
| A13 | pip resolves nested `-r plugin/requirements.txt` relative to the including file | Pattern 12 | Trivially testable in Wave 0 |

## Open Questions (RESOLVED)

1. **Q1. Does the two-week rule apply to end-user installs (`doctor --setup`)?** **RESOLVED:** Owner decision D-18 (setup uses the same cutoff plus a reviewed exceptions file); plans 01-05, 01-10. 
   - What we know: A6 and PKG-09 describe a CI check. D-11 says "minimum pins, resolved at install". pip ≥26.1 supports the cutoff (verified).
   - What's unclear: whether users should get "newest" or "≥14 days old". With the cutoff, security exceptions (e.g. pypdf 6.21.1, uploaded 2026-10-17) need a second install step.
   - Recommendation: apply `--uploaded-prior-to P14D` in `doctor --setup` for parity with CI, then install reviewed exception pins from a small shipped file. Ask the owner (one question).
2. **Q2. What status does a scanned but not-yet-converted source show?** **RESOLVED:** Adopted: `pending` status rendered as waiting for conversion; plans 01-11, 01-13.  The §6.1 vocabulary has no "pending". Recommend adding `pending` to the source status enum in the Phase 1 schema, rendered in INDEX as "waiting for conversion (coming in a later version)".
3. **Q3. How does the validator treat a cell of exactly 32,767 characters?** **RESOLVED:** Adopted: exactly 32,767 characters is rejected (`CELL_PROBABLY_TRUNCATED`); plan 01-04.  Recommend an error (`CELL_PROBABLY_TRUNCATED`) on disk, because nothing the builder emits comes close (Descriptions are ≤1,800).
4. **Q4. A known path whose content changes to equal another source's content.** **RESOLVED:** Adopted: content wins, with a scan-report line; plan 01-14.  Recommend "content wins" (the path joins the other source; the old source is marked removed if it has no paths left) and an explicit line in the scan report. This needs a sentence in the workspace contract.
5. **Q5. How `plugin/AGENTS.md` reaches agents.** **RESOLVED:** Adopted: router skill points to `../../AGENTS.md`, Codex installer copies it; plans 01-06, 01-15.  Recommend that the router SKILL.md points at `../../AGENTS.md`, and that `tools/install-codex.py` copies AGENTS.md into the copied skill folder. No committed mirror.
6. **Q6. XDG.** **RESOLVED:** Adopted: no XDG lookup; plans 01-01, 01-03, 01-10.  D-03 fixes `~/.local/share/probematrix-epb/`. Should `$XDG_DATA_HOME` be honoured when set? Recommend no, to keep D-03 literal and the manual exact. Mention it in the manual.
7. **Q7. Design correction.** **RESOLVED:** Adopted: amendment A29; plan 01-02.  Metadata notes are in rows 8–10, not 7–9. Add it to the D-10 amendments (A16+).
8. **Q8. Exit code for a hand-edited, invalid `state.json`.** **RESOLVED:** Owner decision D-19 (exit 4, `STATE_INVALID`); plans 01-03, 01-07.  Prior architecture research said 1. Recommend 4 (`STATE_INVALID`), because exit 1 tells the agent to "fix content", and A11 frames workspace integrity as an environment problem.
9. **Q9. Permissive extras in `requirements-dev.txt` now?** **RESOLVED:** Adopted: no extras in `requirements-dev.txt`; plan 01-01.  docling would bring torch into every CI run. Recommend: none until their phases. D-12's "only the permissive extras" is a restriction, not a mandate.
10. **Q10. `tzdata` on Windows.** **RESOLVED:** Owner decision D-20 (add `tzdata; sys_platform == "win32"`); plans 01-01, 01-02.  `zoneinfo` needs the `tzdata` package (Apache-2.0, 2026.5, uploaded 2026-10-03) on Windows, which has no system database. Recommend adding `tzdata; sys_platform == "win32"` to core (it is not in the PKG-08 list, so it needs owner confirmation), or skipping timezone validation on Windows.
11. **Q11. Run numbering granularity.** **RESOLVED:** Adopted: only `init` and `scan` create runs in Phase 1; plan 01-11.  Recommend that only pipeline-level commands (`init`, `scan`, later `run`/`build`) allocate a `runs/<NNN>/`, so INDEX run history stays readable.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | everything | ✓ | 3.14.4 | — |
| Python 3.11 | CI parity, local 3.11 tests | ✗ system / ✓ via uv | 3.11.17 (`uv run -p 3.11`, verified) | CI matrix |
| `python` command | none (never assumed) | ✗ | — | `python3` |
| pip in system python | — | ✗ (`No module named pip`) | — | venv brings pip 25.1.1, upgrade to 26.2.1 (verified) |
| python3-venv / ensurepip | `doctor --setup`, dev env | ✓ | python3.14-venv 3.14.4 | — |
| uv | optional contributor path | ✓ | 0.13.1 | pip |
| pytest | tests | ✓ (system 9.0.2; dev env resolves 9.1.1) | — | dev venv |
| ruff | lint | ✗ system | install 0.16.10 in dev venv (verified installs) | — |
| claude CLI | `plugin validate`, install checks | ✓ | 2.1.302 | skip in CI if absent (D-02) |
| codex CLI | manifest check | ✓ | 0.154.0 | optional |
| 7z | doctor probe (D-14) | ✓ | 7-Zip 26.00 (`7zip` package) | `unprocessed: 7z tool not installed` |
| ffmpeg | doctor probe only | ✓ | 8.0.1 | optional |
| tesseract | doctor probe only | ✗ | — | optional (Phase 7) |
| git | git-tracking warning | ✓ | 2.53.0 | walk-up `.git` detection |
| gh + GitHub remote | push and CI | ✓ (public repo `ashley-eyekyam/probematrix-evidence-pack-builder`) | gh 2.46.0 | — |
| Node + parent's SheetJS 0.18.5 | research-only round-trip check | ✓ | — | **must not be used by any committed test or tool** (standalone rule) |

**Missing dependencies with no fallback:** none for Phase 1.
**Missing dependencies with fallback:** tesseract (probe reports "optional, not installed"); a system `ruff` (use the dev venv).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ≥9.0 (resolves 9.1.1 under the cutoff); ruff 0.16.10 |
| Config file | `pyproject.toml` (none yet, Wave 0): `[tool.pytest.ini_options] testpaths=["tests"]`, `pythonpath=["plugin/skills/evidence-pack/scripts", "tools"]`, `filterwarnings=["error::EncodingWarning"]`, with `PYTHONWARNDEFAULTENCODING=1` set in the CI env (interpreter `-X` flags cannot go in pytest `addopts`); `[tool.ruff] target-version="py311"`, `extend-select=["S506", …]`, optionally `preview=true, explicit-preview-rules=true, extend-select=["PLW1514"]` (PLW1514 is preview-only in 0.16.10, verified) |
| Quick run command | `.venv/bin/python -m pytest -x -q tests/<area>` |
| Full suite command | `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WS-01 | init creates the tree, case.yaml, state.json with registry, counters and chunks, .gitignore, .gitattributes, inbox/, tmp/ | integration (in-process CLI) | `pytest tests/workspace/test_init.py -x` | ❌ Wave 0 |
| WS-02 | sha256, size, MIME, mtime; `S001…`; junk listed as ignored; symlinks ignored | integration | `pytest tests/sources/test_scan_fingerprint.py -x` | ❌ |
| WS-03 | new version `S004v2`, rename, duplicate, removed, content swap, case-only rename, NFD | integration (parametrised generated folders) | `pytest tests/sources/test_scan_classify.py -x` | ❌ |
| WS-04 | `.note.md`/`.note.yaml` paired and hashed; orphan sidecar reported | integration | `pytest tests/sources/test_sidecars.py -x` | ❌ |
| WS-06 / TST-07 | crash at every checkpoint (`os._exit`) then resume; no tmp left; no ID reuse | subprocess | `pytest tests/store/test_crash_resume.py -x` | ❌ |
| WS-07 | second mutating run waits; times out with exit 4 `LOCK_TIMEOUT` (`--wait 1`); read-only command runs while locked | subprocess | `pytest tests/store/test_lock.py -x` | ❌ |
| WS-08 | invalid record refused at stage; strict YAML keeps `12:30`, `0123`, `no`; dup keys and `!!int` rejected | unit | `pytest tests/core/test_yamlio.py tests/store/test_validate.py -x` | ❌ |
| WS-09 | INDEX six sections in order; "none yet" | unit + integration | `pytest tests/index/test_index.py -x` | ❌ |
| WS-11 | `.epb/.gitignore` exact list; warning in a temp git repo when private would be tracked (skip if no git) | integration | `pytest tests/workspace/test_git_warning.py -x` | ❌ |
| WS-12 | sync-folder warning from a fake home with `.dropbox/info.json` and name-heuristic paths (monkeypatched home/env) | unit | `pytest tests/doctor/test_syncfolders.py -x` | ❌ |
| WS-13 | `state.json` schema requires workbooks, counters.evidence/tag and chunks | unit | `pytest tests/schemas/test_state_schema.py -x` | ❌ |
| D-09 | newer workspace exits 4; older auto-upgrades with backup on a mutating command only | integration | `pytest tests/store/test_upgrade.py -x` | ❌ |
| D-13 | magic bytes beat extension; mismatch recorded; same results on 3.11 and 3.14 | unit | `pytest tests/core/test_mime.py -x` | ❌ |
| BLD-01 | format constants equal the transcribed contract (30 headers, widths, 10 rows, enums) | unit | `pytest tests/formats/test_contract.py -x` | ❌ |
| BLD-02 | `=`, `+`, `-`, `@` stay text; `0`, a 20-digit ID and `2020-09` stay strings; control chars removed; raw XML has no `<f>` and only inlineStr | unit (writes to tmp_path) | `pytest tests/formats/test_writer.py -x` | ❌ |
| BLD-03 | each rejection class: blank Description/Type, non-exact enum, non-string, formula, >32,767, bad CoC; minimal pack passes; prototype pack yields `LIST_FRAGMENT_UNBALANCED` | unit | `pytest tests/formats/test_validator.py -x` | ❌ |
| BLD-08 | metadata 10 rows exact; Total Evidence Items equals rows; attachments headers only | unit | `pytest tests/formats/test_metadata.py -x` | ❌ |
| D-16 | smoke pack builds and validates and the checklist covers every A10 value | unit | `pytest tests/tools/test_smoke_pack.py -x` | ❌ |
| PKG-01 / D-01 / D-02 | manifests are valid JSON; equal name and version; the Codex one has `skills` and the Claude one doesn't; marketplace `source == "./plugin"`; `claude plugin validate --strict` (skip if absent) | unit + optional CLI | `pytest tests/packaging/test_manifests.py -x` | ❌ |
| PKG-01 (install) | isolated `CLAUDE_CONFIG_DIR` install from the repo path; cache has `skills/evidence-pack/SKILL.md` and no `docs/` (opt-in `EPB_HOST_TESTS=1`, skip if no claude) | optional integration | `EPB_HOST_TESTS=1 pytest tests/packaging/test_host_install.py` | ❌ |
| PKG-03 | `plugin/AGENTS.md` exists and mentions each required rule heading | unit | `pytest tests/packaging/test_plugin_agents_md.py -x` | ❌ |
| D-04 lint | each SKILL.md: frontmatter parses, only the 6 spec keys, name regex equals folder, description ≤1,024, ≤150 lines | unit | `pytest tests/packaging/test_skill_lint.py -x` | ❌ |
| PKG-05 | every error class maps to the right exit code; `--json` usage error gives an envelope with exit 2; uncaught exception gives 4 `INTERNAL_ERROR` | unit + subprocess | `pytest tests/cli/test_exit_codes.py -x` | ❌ |
| PKG-06 | launcher parses under old syntax (`ast.parse(feature_version=(3, 6))`); missing env gives 3 `ENV_NOT_SET_UP`; re-exec into a fake env; stdlib-only import test | unit + subprocess | `pytest tests/launcher -x` | ❌ |
| PKG-06 (real setup) | `doctor --setup` into a tmp data root actually creates the venv and installs (network, slow) | manual / opt-in | `EPB_NETWORK_TESTS=1 pytest tests/launcher/test_setup_real.py` (excluded from the default run) | ❌ |
| PKG-07 | registry rows have all fields; a missing tool gives "optional, not installed" and exit unchanged; `--json` lists every tool with all-OS commands | unit (fake `which`) | `pytest tests/doctor/test_probes.py -x` | ❌ |
| PKG-08 | requirements contain the PKG-08 floors; extras files have licence headers; no GPL package in core or dev | unit | `pytest tests/packaging/test_requirements.py -x` | ❌ |
| PKG-09 | age-check and licence-check logic on canned metadata (OR/AND, classifier mapping, exceptions, stale exceptions) | unit; real run is a CI step | `pytest tests/tools/test_dependency_checks.py -x` | ❌ |
| PKG-11 | root AGENTS.md bytes equal CLAUDE.md; ≤150 lines | unit | `pytest tests/repo/test_instructions_mirror.py -x` | ❌ |
| TST-01 | no-network fixture active; optional-tool tests skip with a reason | meta | `pytest tests/repo/test_no_network.py -x` | ❌ |
| DOC-04/05 | manual has the privacy chapter keywords and Windows/macOS sections carrying "not yet tested on this system"; doctor golden block matches | unit | `pytest tests/docs/test_manual.py -x` | ❌ |
| SC4 smoke import | owner imports `scratch/smoke/evidence-pack-smoke.xlsx` into a ProbeMatrix test incident | **manual (owner)** | `python tools/make-smoke-pack.py` → owner checklist | n/a |
| SC5 host install | install via `/plugin` in Claude Code on Linux and ask the agent to set up a case folder | **manual (owner/UAT)** | UAT procedure | n/a |

### Sampling Rate
- **Per task commit:** the quick run for the area touched, plus `ruff check` on changed files.
- **Per wave merge:** the full suite command.
- **Phase gate:** the full suite green on CI (3.11 + 3.14), the dependency-age and licence steps green, then `/gsd-verify-work 1` with the owner-run smoke import and host install.

### Wave 0 Gaps
- [ ] `pyproject.toml`: ruff and pytest config only (no packaging metadata)
- [ ] `requirements-dev.txt`, `plugin/requirements.txt`, extras stubs with licence headers, `requirements-dev-full.txt` stub
- [ ] `tests/conftest.py`: no-network guard, `make_case(tmp_path)` factory, `run_epb()` subprocess helper using `sys.executable`, in-process `cli(argv)` helper, fake home/env fixtures for the sync-folder tests
- [ ] `.github/workflows/ci.yml` skeleton
- [ ] `.gitignore`: add `scratch/`
- [ ] Dev env: `python3 -m venv .venv && .venv/bin/python -m pip install -U "pip>=26.1" && .venv/bin/python -m pip install --uploaded-prior-to P14D -r requirements-dev.txt` (behind the legitimacy checkpoint)

## Security Domain

`security_enforcement: true`, ASVS level 1 (`.planning/config.json`, read this session).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local CLI, no accounts |
| V3 Session Management | no | n/a |
| V4 Access Control | partial | Filesystem only: never write into `inputs/`; `private/` ignored by git; sync-folder warning |
| V5 Validation, Sanitization and Encoding | yes | jsonschema on every write; strict YAML loader; text-only xlsx cells (formula injection); control-character sanitising; argparse with no abbreviations |
| V6 Stored Cryptography | no (hashing for integrity only) | `hashlib` SHA-256; never hand-rolled |
| V7 Error Handling and Logging | yes | JSON envelope with stable codes; tracebacks on stderr only; no names on argv (title only in Phase 1) |
| V10 Malicious Code | yes (supply chain) | Two-week dependency rule + exceptions list; licence allow-list; no `yaml.load` with an unsafe loader (ruff S506); no pickle |
| V12 Files and Resources | yes | `os.walk(followlinks=False)`; NFC relative keys; safe generated names (reserved names, `<>:"/\|?*`); zip-slip deferred to Phase 2 (WS-05); defusedxml for XLSX parsing |
| V14 Configuration | yes | Private env isolated from the system Python (PEP 668); minimum pins; CI checks |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Spreadsheet formula injection (`=`, `+`, `-`, `@` leading text from inputs or titles) | Tampering / Elevation | Force `t=inlineStr`; on-disk scan rejects any `<f>`; never prepend `'` (that changes the text) |
| YAML deserialisation / type confusion | Elevation / Tampering | SafeLoader subclass with no implicit resolvers, a dup-key check and a text-only walk |
| Symlink or junction in `inputs/` escaping the case folder | Information disclosure | Don't follow; list as `ignored: link` |
| XML bombs / XXE in a validated workbook (e.g. the prototype or user-supplied pack) | DoS | defusedxml (openpyxl auto-uses it; the validator's raw scan uses `defusedxml.ElementTree`) |
| Malicious fresh release of a dependency | Tampering | `--uploaded-prior-to P14D` + age check + reviewed exceptions |
| Raw-text files leaking via git or a sync client | Information disclosure | `.epb/.gitignore` list (A2), git check, sync-folder warning, manual chapter (DOC-04) |
| Lock-holder kill via PID probing on Windows | DoS | OS advisory lock; no `os.kill` |
| Path traversal in generated names (slug from title or folder) | Tampering | `safe_component()` with a reserved-name guard and a length cap |

## Sources

### Primary (HIGH confidence, executed or read this session)
- Parent importer (read-only): `../server/services/evidenceExportService.ts` lines 4-7, 80-91, 129-160, 197-204, 209-244, 259-385; `../shared/schema.ts` 615-634, 687, 690; `../server/routes.ts` 645-720.
- Local probes (Python 3.14.4, 3.11.17 via uv; openpyxl 3.1.5, PyYAML 6.0.3, jsonschema 4.26.0, defusedxml 0.7.1, pip-licenses 5.5.5, ruff 0.16.10, pip 25.1.1/26.2.1): formula coercion, truncation, inlineStr, SheetJS 0.18.5 round trip, strict YAML, jsonschema formats, mimetypes on 3.11 and 3.14, licence metadata, `--uploaded-prior-to`.
- `claude` 2.1.302: `plugin validate --strict`, isolated `CLAUDE_CONFIG_DIR` marketplace add and install (local path).
- `codex-cli` 0.154.0: isolated `CODEX_HOME` marketplace add, `plugin add`, manifest preference, name-match error.
- PyPI JSON API: upload dates, licences, project URLs. GitHub API: actions/checkout v7.0.1 and actions/setup-python v7.0.0 (2026-07-20); repo is public.
- Prototype pack `docs/reference/hazira-2020/prototype-evidence-pack-hazira-2020.xlsx`: structure, column XML and list-fragment counts (no content copied).

### Secondary (MEDIUM)
- https://code.claude.com/docs/en/skills: `${CLAUDE_SKILL_DIR}`/`${CLAUDE_PLUGIN_ROOT}` textual substitution; six portable frontmatter keys; 1,536-character listing cap; `compatibility` ≤500 characters.
- https://developers.openai.com/codex/plugins/build: `.codex-plugin/plugin.json` as compatibility layer; the scaffold declares `skills: "./skills/"`; legacy `.claude-plugin/marketplace.json` is read; `codex plugin marketplace add` forms.
- https://help.dropbox.com/installs/locate-dropbox-folder: `info.json` locations and `path` field.
- Prior project research: `.planning/research/STACK.md`, `ARCHITECTURE.md`, `PITFALLS.md`, `SUMMARY.md` (2026-10-17).

### Tertiary (LOW)
- Community pages on the OneDrive env vars (`OneDrive`, `OneDriveConsumer`, `OneDriveCommercial`): uwaterloo.atlassian.net, winhelponline.com.
- Cowork runtime capabilities: undocumented.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH. Resolved and installed under the cutoff this session. The licence sweep was executed.
- Importer contract and writer/validator: HIGH. Source read line by line, plus a round trip through the importer's own library.
- Packaging (Claude Code + Codex on Linux, local path): HIGH. Executed. GitHub `owner/repo` route: MEDIUM (A8).
- Transaction, lock, launcher design: MEDIUM. Standard stdlib patterns with no executed prototype. Windows branches are LOW (A9 untested).
- Sync-folder heuristics: LOW–MEDIUM.
- Pitfalls: HIGH for the 9 verified items; MEDIUM–LOW for the host sandboxes.

**Research date:** 2026-10-17
**Valid until:** 2026-11-16 for the stack and format. Host CLI behaviour moves fast, so re-check `claude` and `codex` behaviour at Phase 10 (PKG-10).
