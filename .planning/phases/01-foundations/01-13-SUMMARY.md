---
phase: 01-foundations
plan: 13
subsystem: sources-scan
tags: [python, scan, sha256, mime, magic-bytes, jsonschema, classification, ws-02, ws-03]

# Dependency graph
requires:
  - phase: 01-foundations (01-11)
    provides: workspace.find_workspace / open_for_mutation / Session, runs.new_run / run_json_path, index.render_index / IndexInputs / MIME_LABELS, run.schema.json scan summary
  - phase: 01-foundations (01-07)
    provides: txn.Transaction (stage_json, stage_text, set_state, commit), fsio.utc_now_iso, schema.check
  - phase: 01-foundations (01-03)
    provides: warning codes MIME_MISMATCH, LINK_IGNORED, INPUT_REMOVED; the command-module contract and Result
provides:
  - epb scan (MUTATING) - walk inputs/ read-only, fingerprint, classify, commit records + fingerprints + run + INDEX.md in one transaction
  - epb/sources/scan.py (JUNK_PATTERNS, FileFact, Ignored, WalkResult, rel_key, is_junk, walk_inputs, run_scan, NO_FILES, NO_CHANGES)
  - epb/sources/classify.py (classify, ScanPlan, src_number, format_src_id) - pure content-centred classification
  - epb/sources/expanders/__init__.py (Expander, REGISTRY, register, expanders_for) - the PF-11 seam, empty in Phase 1
  - epb/mime.py (EXTENSION_TABLE, MAGIC_RULES, AMBIGUOUS_FAMILIES, HEAD_BYTES, by_extension, sniff, detect)
  - schemas/source.schema.json (epb:source) with parents[] (D-08) and the pending status (Q2)
affects: [01-14 change corpus, sidecars and scan crash coverage, 01-15 skill and workspace contract (reverted content, content wins), 01-16 manual (scan messages), Phase 2 expanders and conversion]

# Actuals (#2632)
actuals:
  tokens: 16529
  tasks: 3
  commits: 5
plan_head_before: 13264a58a7cd116a40df7a8e445bd6fbbb567f40
plan_head_after: 6b8ae8ad1319acfb5398dc39a0d9f40ac0848155

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Classification is a pure function (previous fingerprints, source records, file facts) -> ScanPlan; run_scan only applies the plan, so 01-14's corpus can test classify without the CLI"
    - "Read inputs/ through os.open(O_NOFOLLOW|O_NONBLOCK) + fstat: a link is never followed and a pipe never waited on, even if a file is swapped mid-scan"
    - "No-change short-circuit: when no record and no fingerprint would differ, scan opens no transaction and allocates no run"
    - "MIME: authoritative extension table, then a private MimeTypes() instance, then octet-stream; content sniffing wins, with family and container exceptions"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb/commands/scan.py
    - plugin/skills/evidence-pack/scripts/epb/sources/__init__.py
    - plugin/skills/evidence-pack/scripts/epb/sources/scan.py
    - plugin/skills/evidence-pack/scripts/epb/sources/classify.py
    - plugin/skills/evidence-pack/scripts/epb/sources/expanders/__init__.py
    - plugin/skills/evidence-pack/scripts/epb/schemas/source.schema.json
    - plugin/skills/evidence-pack/scripts/epb/mime.py
    - tests/sources/test_scan_fingerprint.py
    - tests/core/test_mime.py
  modified: []

key-decisions:
  - "classify takes keyword arguments run_id (the number the scan's run would get) and source_counter (state counters.source), so IDs come from the counter and are never reused even past deleted records"
  - "A touched file whose content is unchanged keeps its previous fingerprint (mtime included), so touching a file is not a change and creates no run"
  - "A removed source's last known paths (its current versions entry) count as 'had this path' for the new-version rule, so a file that reappears with new content becomes S00Nv2"
  - "renamed pairs the source's vanished paths with its new paths in sorted order; any extra new paths are reported as duplicates"
  - "AMBIGUOUS_FAMILIES also maps MP4 content to .mov and .m4a, and a container type (ZIP, OLE2, MP4, Matroska, Ogg) never mismatches a name outside the extension table (.epub, .3gp, .opus): the name is the more precise type there"
  - "ODF is recognised from the stored 'mimetype' member in the first local header; the value is accepted only if it matches application/vnd.oasis.opendocument.<x>, else the file is plain ZIP"
  - "Source mime fields are pattern-checked (lower-case type/subtype, underscore allowed), so text from a hostile file can never reach a record unvalidated"
  - "INPUT_REMOVED is warned for each source removed from the folder; LINK_IGNORED for each link; MIME_MISMATCH in plain words naming both types"

patterns-established:
  - "A scan event list is defined once in ScanPlan and copied into both the run record (with mime_mismatches, sidecars, orphan_sidecars) and the envelope (with changed, run, ignored, sources_total)"
  - "TDD RED for a new interface commits an interface-only stub (NotImplementedError) so RED fails on assertions, never on import"

requirements-completed: [WS-02, WS-03]

coverage:
  - id: D1
    description: "epb scan registers new inputs end to end: S001/S002 in sorted path order with SHA-256, size, mtime and type matching the files, parents [], status pending; state fingerprints and counters.source; run 002 with command scan; INDEX.md Inputs rows 'waiting for conversion (coming in a later version)'; every record validates against source.schema.json"
    requirement: WS-02
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_scan_registers_two_new_inputs"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_scan_updates_state_and_writes_run_002"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_every_source_record_validates_with_empty_parents"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_index_lists_both_inputs_as_waiting"
        status: pass
    human_judgment: false
  - id: D2
    description: "OS junk (.DS_Store, Thumbs.db in any case, desktop.ini, ~$*, ._*, .~lock.*#, *.tmp) listed as ignored junk and never registered; file and folder links ignored as link with LINK_IGNORED and never followed; a FIFO ignored as special and never opened; inputs/ unchanged by every scan"
    requirement: WS-02
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_junk_is_listed_and_never_registered"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_links_and_fifos_are_ignored_and_never_opened"
        status: pass
    human_judgment: false
  - id: D3
    description: "Empty or missing inputs/ in a case with no sources, and an unchanged rescan, give exit 0, changed false, run null, the plain message, no new run and a byte-identical case folder; a zero-byte file gets the empty SHA-256; identical new files are one source with sorted paths; new IDs follow NFC code-point order"
    requirement: WS-02
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_empty_inputs_writes_nothing"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_unchanged_rescan_writes_nothing"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_zero_byte_file_gets_the_empty_hash"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_identical_new_files_are_one_source_with_two_paths"
        status: pass
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_new_ids_follow_nfc_code_point_order"
        status: pass
    human_judgment: false
  - id: D4
    description: "Content-centred classification of changes (new version, rename, duplicate, moved, restored, removed from folder; content wins per Q4)"
    requirement: WS-03
    verification: []
    human_judgment: true
    rationale: "The full classify algorithm ships here, but this plan's tests cover first sight only; the change corpus (versions, renames, removals, swaps) is plan 01-14's test scope. An ad-hoc run (new version, rename, removal, unchanged rescan) behaved correctly but is not a committed test"
  - id: D5
    description: "Magic-byte detection (PDF, ZIP/OOXML/ODF, OLE2, PNG, JPEG, GIF, WAV, AVI, ftyp brands, Matroska, 7z, gzip, MP3, Ogg, TIFF); content wins with mime_mismatch on the record, MIME_MISMATCH warning, run mime_mismatches and an INDEX Open issues line; family exceptions; corrupt ZIPs never raise; at most 4,096 bytes read and nothing extracted; extension table fixed and independent of mimetypes; no python-magic"
    requirement: WS-02
    verification:
      - kind: unit
        ref: "tests/core/test_mime.py"
        status: pass
      - kind: integration
        ref: "tests/core/test_mime.py#test_scan_records_and_reports_a_mismatch"
        status: pass
    human_judgment: false
  - id: D6
    description: "A .7z input is an ordinary pending source; the expander registry is empty and expanders_for returns []; a registered expander is found by MIME type (PF-11, D-14)"
    requirement: WS-02
    verification:
      - kind: integration
        ref: "tests/sources/test_scan_fingerprint.py#test_7z_is_an_ordinary_pending_source"
        status: pass
      - kind: unit
        ref: "tests/sources/test_scan_fingerprint.py#test_expander_registry_is_empty_in_phase_1"
        status: pass
      - kind: unit
        ref: "tests/sources/test_scan_fingerprint.py#test_registered_expander_is_found_by_mime"
        status: pass
    human_judgment: false
  - id: D7
    description: "Scan messages and warnings (No files found..., No changes since the last scan., LINK_IGNORED, MIME_MISMATCH, INPUT_REMOVED) read as plain language for a non-technical investigator"
    verification: []
    human_judgment: true
    rationale: "Wording quality is a judgement no test asserts; the 01-15 UAT and the 01-16 manual quote this text"

# Metrics
duration: 13min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 13: epb scan, content-centred classification and magic-byte MIME detection Summary

**`epb scan` now walks `inputs/` read-only without following links. It fingerprints every regular file (SHA-256, size, mtime, and type by extension table plus magic bytes) and lists OS junk, links and special files as ignored. A pure content-centred classifier turns new content into stable `S001…` sources with `parents: []`. The new source records, fingerprints, a run record and a fresh `INDEX.md` are committed in one transaction. A scan that finds nothing new writes nothing.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-10-18T10:35:19Z
- **Completed:** 2026-10-18T10:48:26Z
- **Tasks:** 3
- **Files modified:** 9 (all created)

## Accomplishments

- **`epb scan` (`MUTATING = True`)** runs inside `open_for_mutation(case_root, ctx, "scan")`, which is the only call into `workspace.py`. When anything changed, it stages:
  - each new or changed `.epb/sources/<id>.json`, checked against `source.schema.json`;
  - `runs/<NNN>/run.json` with all eleven scan lists;
  - the re-rendered `INDEX.md`;
  - `state.json` (fingerprints and `counters.source`), last.

  The envelope `data` is `changed`, `run`, `new`, `new_versions`, `renamed`, `duplicates`, `moved`, `removed`, `restored`, `ignored` and `sources_total`.
- **`sources/classify.py`** is the complete content-centred algorithm from the plan (steps 1–5). A source keeps the paths that still hold its current content. New content becomes a new version of the lowest source whose content is gone and which had one of its paths. Anything else becomes a new source. Unclaimed sources become `removed from folder`, and records are never deleted.
- **`sources/scan.py`** handles the folder itself:
  - Junk matching uses `JUNK_PATTERNS`, with the fixed names matched in any letter case.
  - Links and junctions are reported as `link` and pruned from the walk. Anything else that is not a regular file is reported as `special`.
  - Files are read through `O_NOFOLLOW|O_NONBLOCK` and checked with `fstat`.
  - There are two short-circuits: empty or missing `inputs/` with no known sources, and nothing changed.
  - It warns `LINK_IGNORED`, `INPUT_REMOVED` and `MIME_MISMATCH`, and hands every new source and new version to the expander seam.
- **`mime.py`:**
  - A 41-entry extension table, identical on Python 3.11.17 and 3.14.4 (checked with uv's 3.11).
  - `MAGIC_RULES`, 17 ordered rules covering every family D-13 names plus ID3/MPEG frames, Ogg, TIFF and AVI.
  - OOXML is told apart by member names only. ODF is recognised from the stored `mimetype` header.
  - `detect()` lets the content win and records any mismatch.
- **`source.schema.json` (`epb:source`)** is a closed, pattern-only schema with `parents[{src_id, member?}]` (D-08), the §6.1 status vocabulary plus `pending` (Q2), the §8.1 `source_kind` list and `versions[]`.

## Task Commits

1. **Task 1 (tracer): `epb scan` registers two new inputs end to end.** `6b12676` (feat).
   - Tracer gate: the run is interactive and `end-of-phase`, and the verify is automated only. I re-ran it (4 passed) and expansion continued.
2. **Task 2: junk, links, special files, empty inputs, unchanged rescans and the expander seam.** RED `1bb6c26` (test), GREEN `ec0530e` (feat).
3. **Task 3: magic-byte MIME detection with recorded mismatches (D-13).** RED `e4aad63` (test), GREEN `6b8ae8a` (feat).

No REFACTOR commits were needed.

## TDD Gate Compliance

- **Task 2 RED (`1bb6c26`):**
  - JUnit XML from `pytest --junitxml` was classified by `gsd-tools check tdd-red-evidence` as `RED_EVIDENCE_OK` (`target_test_failed`): 15 tests, 7 failing.
  - Target: `test_junk_is_listed_and_never_registered`, which failed on its planned assertion `{} == {'inputs/sub/.DS_Store': 'junk', ...}`.
  - Semantic check:
    - The other failures were planned gaps: `changed` was `True` where no change was expected, links and the FIFO were not listed, and the expander stub raised `NotImplementedError`.
    - There was no import or collection fault.
    - The 8 tests that passed at RED cover Task 1's tracer, the zero-byte hash, identical files, NFC order and the `.7z`-as-source case, all behaviour Task 1's walk already had.
- **Task 3 RED (`e4aad63`):**
  - `RED_EVIDENCE_OK` (`target_test_failed`): 94 tests, 40 failing.
  - Target: `test_docx_named_file_with_pdf_bytes_is_a_pdf_with_mismatch`, which failed with the DOCX type returned in place of `application/pdf`.
  - Semantic check:
    - 37 failures were the `sniff` interface stub's `NotImplementedError`. The others were the empty `MAGIC_RULES` assertion and the missing mismatch in the scan record.
    - The 54 that passed are the extension-table tests (the table shipped in Task 1), plus the family and text cases. Those were vacuous at RED, because `detect` did not sniff yet, and became meaningful at GREEN.
- **GREEN:**
  - Plan verification (`tests/sources tests/core tests/index tests/workspace tests/launcher`) gives 392 passed.
  - The full suite gives 947 passed and 1 skipped (838 before this plan). The failing file set is empty.
  - `ruff check` and `ruff format --check` are clean.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/commands/scan.py`: the `scan` command. It uses only stdlib imports at module level, and the bootstrap guard passes.
- `plugin/skills/evidence-pack/scripts/epb/sources/__init__.py`: the package overview.
- `plugin/skills/evidence-pack/scripts/epb/sources/scan.py`: the walk, junk, links, safe fingerprinting, warnings, expander hook and `run_scan`.
- `plugin/skills/evidence-pack/scripts/epb/sources/classify.py`: the pure classification, `ScanPlan` and the source ID helpers.
- `plugin/skills/evidence-pack/scripts/epb/sources/expanders/__init__.py`: the `Expander` protocol, the empty registry, `register` and `expanders_for`.
- `plugin/skills/evidence-pack/scripts/epb/schemas/source.schema.json`: the source record contract.
- `plugin/skills/evidence-pack/scripts/epb/mime.py`: the extension table, magic bytes, families, `sniff` and `detect`.
- `tests/sources/test_scan_fingerprint.py`: 15 scan tests. Every scan is checked to leave `inputs/` byte- and path-identical.
- `tests/core/test_mime.py`: 94 MIME tests, including the scan-level mismatch case.

## Decisions Made

See `key-decisions` in the frontmatter. In short:

- `classify` takes `run_id` and `source_counter` as keyword arguments.
- Touching a file without changing its content is not a change.
- A removed source's last known paths still count for the new-version rule.
- `renamed` pairs paths in sorted order.
- The family and container exceptions are wider than the plan's two families.
- ODF is detected from the stored header, and the value is validated.
- MIME strings in records are pattern-checked.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Files are opened without following links or blocking on pipes**
- **Found during:** Task 2
- **Issue:** The plan hashes with `fsio.sha256_file`, a plain `open()`. A file swapped for a link or a FIFO between the walk's `lstat` and the read would be followed (T-01-35) or would hang the scan (T-01-37).
- **Fix:** `_fingerprint()` opens with `O_RDONLY|O_NOFOLLOW|O_NONBLOCK` (each only where the OS has it), checks `fstat` for a regular file, then hashes from that descriptor and takes the size and mtime from the same `fstat`.
- **Files modified:** `epb/sources/scan.py`
- **Verification:** `test_links_and_fifos_are_ignored_and_never_opened` and the whole scan suite.
- **Committed in:** `ec0530e`

**2. [Rule 2 - Missing critical] A linked `inputs/` folder is refused as a link**
- **Found during:** Task 2
- **Issue:** `os.walk(followlinks=False)` still walks its top folder. If `inputs/` itself were a link, scan would hash files outside the case folder (T-01-35).
- **Fix:** A linked `inputs/` is listed as `{"path": "inputs/", "reason": "link"}`, with `LINK_IGNORED`, and nothing under it is read.
- **Files modified:** `epb/sources/scan.py`
- **Committed in:** `ec0530e`

**3. [Rule 2 - Missing critical] Unreadable files give a plain-language error**
- **Found during:** Task 2
- **Issue:** A locked or permission-denied file or folder would have surfaced as `INTERNAL_ERROR` with a traceback. `os.walk` would also have skipped an unreadable folder silently, which would hide evidence.
- **Fix:** Either case raises `BAD_ARGUMENT` (exit 2) with "<path> in the inputs folder could not be read (<reason>). Nothing was changed." and a what-to-do hint. A file that vanishes between listing and reading is skipped.
- **Files modified:** `epb/sources/scan.py`
- **Committed in:** `ec0530e`

**4. [Rule 2 - Missing critical] `INPUT_REMOVED` warning**
- **Found during:** Task 2
- **Issue:** The plan lists `INPUT_REMOVED` among the scan's warning codes, but no task emitted it.
- **Fix:** Each source newly marked `removed from folder` gets one plain-language warning that names its last known paths.
- **Files modified:** `epb/sources/scan.py`
- **Committed in:** `ec0530e`

**5. [Rule 1 - Bug] False MIME mismatches on container formats**
- **Found during:** Task 3
- **Issue:** With only the plan's two families, an `.m4a` or `.mov` with a generic `isom`/`mp42` brand, an `.epub` (ZIP) or an `.opus` (Ogg) would be reported as a mismatch, and its precise type would be replaced by the container's.
- **Fix:** `AMBIGUOUS_FAMILIES` adds MP4 content for `.mov` and `.m4a`. Container content (ZIP, OLE2, MP4, Matroska, Ogg) never mismatches a name outside the extension table, and the name's type is kept.
- **Files modified:** `epb/mime.py`
- **Verification:** `test_ambiguous_families_are_not_mismatches` and `test_magic_rules_cover_the_d13_minimum`. A `.docx` holding PDF bytes is still a mismatch.
- **Committed in:** `6b8ae8a`

---

**Total deviations:** 5 auto-fixed (4 missing critical, 1 bug).
**Impact on plan:** All five keep the planned interfaces. Items 1 to 3 close threat-register mitigations (T-01-35, T-01-37) more tightly than the planned code would. There is no scope creep and no change to `workspace.py` or `txn.py`.

## Issues Encountered

- **NFC key collision (left for 01-14).** On Linux a folder can hold two names that differ only in Unicode normalisation (NFC and NFD forms of the same word). Both map to one NFC key, so only one of the two files is registered. Plan 01-14 covers NFD names in its corpus and should decide how to report this, for example as an ignored entry or an error.
- **INDEX can show stale skipped-file issues (left for 01-14).** Because a no-change scan writes nothing, a link or special file added on its own appears in the envelope (and `LINK_IGNORED`) but not in INDEX Open issues until the next scan that changes something. INDEX reads the ignored list from the latest scan run.
- **Fallback types differ by Python version.** Extensions outside the table still go through `mimetypes`, which differ between versions (`.epub` is `application/octet-stream` on 3.11 and `application/epub+zip` on 3.14). Every type the design names is in the table and identical on both. Add an extension to the table if it must be stable.
- **Status counts removed sources as waiting.** `epb status` (01-11) counts a removed source that is still `pending` as "waiting for conversion". Plan 01-14 or 01-15 may want to exclude removed sources from that count.
- **Unrelated test helper bug.** I fixed one test-helper bug of my own before the RED commit (the `_snapshot` helper and the `pytest` import order). There were no production issues.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- **01-14 (change corpus, sidecars, crash coverage):**
  - `classify(previous, sources, files, run_id=..., source_counter=...)` is pure and already implements versions, renames, duplicates, moves (Q4 content wins), restores and removals, so the corpus can be tested directly or through `scan --json`.
  - The run record already carries `sidecars: []` and `orphan_sidecars: []`.
  - `scan.sidecars[].target` in `run.schema.json` is still a source ID.
- **01-15:** the workspace contract needs one sentence each on content wins (Q4) and on reverted content becoming new content (classify step 5).
- **Phase 2:** register the zip, email and 7z expanders in `epb.sources.expanders`. `scan` already calls `expanders_for(mime)` for every new source and new version, passing `(path, src_id, .epb/media/<src_id>/unpacked)`.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
