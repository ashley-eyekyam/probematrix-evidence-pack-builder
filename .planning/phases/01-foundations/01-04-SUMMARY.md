---
phase: 01-foundations
plan: 04
subsystem: formats
tags: [openpyxl, defusedxml, xlsx, evidence-pack-v2, validator, smoke-pack]

requires:
  - phase: 01-foundations (plan 01-01)
    provides: dev venv with openpyxl 3.1.5 and defusedxml, pytest/ruff config, scratch/ in .gitignore
provides:
  - "epb.formats: format seam (FORMATS, get_format) and the importer-exact probematrix_v2 constants module"
  - "epb.formats.writer: write_pack, PackMetadata, PackInvalid; text-only cells, temp sibling, validate from disk, then os.replace"
  - "epb.formats.validate: validate_rows, validate_workbook, Finding with 23 stable finding codes"
  - "tools/make-smoke-pack.py: repo-only synthetic smoke workbook (8 ACM rows) and the owner's numbered import checklist"
affects: [01-15 evidence-pack-v2 reference doc, phase 05 build/render, phase 06 delta packs, phase 10 definition of done]

actuals:
  tokens: 20898
  tasks: 3
  commits: 4
plan_head_before: 018b0ec5bec0f911386de3c9ca7480ac6b44a5f8
plan_head_after: aecd66cdffe5789e4745bc6aac32e305bb9e5d2d

tech-stack:
  added: []
  patterns:
    - "Every pack cell goes through _put_text: str only, C0 controls removed, data_type 's' and number_format '@' forced"
    - "Workbooks are saved through openpyxl ExcelWriter so the injected created/modified time is kept"
    - "Validator runs a value pass (openpyxl read_only) and a raw XML pass (zipfile + defusedxml); repeats of one code on one cell are dropped and findings are sorted by sheet, row, column, code"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb/formats/__init__.py
    - plugin/skills/evidence-pack/scripts/epb/formats/probematrix_v2.py
    - plugin/skills/evidence-pack/scripts/epb/formats/writer.py
    - plugin/skills/evidence-pack/scripts/epb/formats/validate.py
    - tests/formats/test_writer.py
    - tests/formats/test_validator.py
    - tests/formats/test_contract.py
    - tests/epbtest/packkit.py
    - tools/make-smoke-pack.py
    - tests/tools/test_smoke_pack.py
  modified: []

key-decisions:
  - "Writer saves through openpyxl ExcelWriter, not Workbook.save, because Workbook.save overwrites the modified property with the wall clock"
  - "validate_workbook opens the file as a binary handle, because openpyxl refuses a .tmp file name and the writer validates <path>.tmp"
  - "A cell with an <f> element gets CELL_FORMULA only, not CELL_NOT_TEXT as well; one finding per cell and code"
  - "REQUIRED_BLANK also covers a blank Evidence ID (stricter than the importer, which ignores the value)"
  - "The writer writes no cell for None or an empty string; whitespace-only text is written as is and the validator judges it"
  - "Chain of Custody problems in one cell are reported as a single CUSTODY_ENTRY finding whose message names each entry number and key"

patterns-established:
  - "Format tests build synthetic rows with tests/epbtest/packkit.py (valid_row, with_values, metadata) and plant on-disk defects with plain openpyxl or by editing the sheet XML in the zip"
  - "Repo tools under tools/ put plugin/skills/evidence-pack/scripts on sys.path and import epb directly; tests load them with importlib.util.spec_from_file_location"

requirements-completed: [BLD-01, BLD-02, BLD-03, BLD-08]

coverage:
  - id: D1
    description: "probematrix_v2.py holds the importer-exact marker, sheet names and order, 30 headers and widths, 11 attachment headers and widths, enums, list separator and 10-row metadata layout"
    requirement: BLD-01
    verification:
      - kind: unit
        ref: "tests/formats/test_contract.py#test_constant_matches_contract"
        status: pass
      - kind: unit
        ref: "tests/formats/test_writer.py#test_header_and_width_never_shift"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every written cell is text: =, +, -, @ prefixes, 0, 20-digit numbers and YYYY-MM dates stay exact strings; raw sheet XML has no <f> and only inlineStr/s/str cells"
    requirement: BLD-02
    verification:
      - kind: unit
        ref: "tests/formats/test_writer.py#test_edge_values_survive_as_exact_strings"
        status: pass
      - kind: unit
        ref: "tests/formats/test_writer.py#test_raw_xml_has_no_formula_and_only_text_cells"
        status: pass
    human_judgment: false
  - id: D3
    description: "Validator rejects every class with a stable code (23 codes), in memory and on disk, including the 32,766/32,767/32,768 boundary, exact enums and ChainOfCustodyEntry shape"
    requirement: BLD-03
    verification:
      - kind: unit
        ref: "tests/formats/test_validator.py#test_row_defect_in_memory"
        status: pass
      - kind: unit
        ref: "tests/formats/test_validator.py#test_row_defect_on_disk"
        status: pass
      - kind: unit
        ref: "tests/formats/test_validator.py#test_structure_defect_on_disk"
        status: pass
      - kind: unit
        ref: "tests/formats/test_validator.py#test_length_boundary_on_disk"
        status: pass
    human_judgment: false
  - id: D4
    description: "Validator fails the prototype reference pack with SHEETS_INVALID, 24 LIST_FRAGMENT_UNBALANCED and 24 LIST_SEMICOLON in Linked Equipment, and 1 LIST_SEMICOLON in Linked Individuals (DEF-14)"
    requirement: BLD-03
    verification:
      - kind: unit
        ref: "tests/formats/test_validator.py#test_prototype_pack_fails_on_list_fragments"
        status: pass
    human_judgment: false
  - id: D5
    description: "Pack Metadata is exactly 10 rows (blank row 7, notes in rows 8-10), Total Evidence Items is a plain decimal count, Total Attachments is 0, Attachments Manifest has headers only; write_pack never leaves a partial or invalid file at the target"
    requirement: BLD-08
    verification:
      - kind: unit
        ref: "tests/formats/test_writer.py#test_sheet_order_and_metadata_layout"
        status: pass
      - kind: unit
        ref: "tests/formats/test_writer.py#test_total_evidence_items_is_plain_decimal"
        status: pass
      - kind: unit
        ref: "tests/formats/test_writer.py#test_failed_disk_validation_leaves_target_untouched"
        status: pass
    human_judgment: false
  - id: D6
    description: "tools/make-smoke-pack.py builds the synthetic edge-case workbook at git-ignored scratch/smoke/evidence-pack-smoke.xlsx, validates it and prints the owner checklist"
    verification:
      - kind: unit
        ref: "tests/tools/test_smoke_pack.py#test_build_validates_and_checklist_covers_a10"
        status: pass
      - kind: integration
        ref: "tests/tools/test_smoke_pack.py#test_cli_writes_workbook_and_prints_checklist"
        status: pass
      - kind: other
        ref: ".venv/bin/python tools/make-smoke-pack.py --out scratch/smoke/evidence-pack-smoke.xlsx && git check-ignore -q scratch/smoke/evidence-pack-smoke.xlsx"
        status: pass
    human_judgment: false
  - id: D7
    description: "Owner smoke import into ProbeMatrix (SC4): 8 items import with no error and every checklist value displays exactly as written"
    verification: []
    human_judgment: true
    rationale: "ProbeMatrix runs only on Replit and the owner does every import; the agent never reports the import result. Follow the Task 3 human-check procedure in 01-04-PLAN.md."

duration: 10min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 04: EVIDENCE_PACK_V2 Format Module, Writer, Validator and Smoke Pack Summary

**Importer-exact `EVIDENCE_PACK_V2` constants, a text-only openpyxl writer that validates its own saved file before replacing the target, a two-pass validator (openpyxl values plus a defusedxml raw-XML scan) with 23 stable finding codes that flags the prototype pack's 24 comma-split equipment fragments, and a repo-only synthetic smoke-pack tool with the owner's import checklist.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-18T09:32:25Z
- **Completed:** 2026-10-18T09:42:35Z
- **Tasks:** 3
- **Files modified:** 10 (all created)

## Accomplishments

- `epb/formats/probematrix_v2.py` transcribes the importer contract from 01-RESEARCH.md: the marker, three sheets in order, 30 headers with `wch` widths, 11 attachment headers and widths, all enums, the custody entry shape, `", "` and the 10-row metadata layout (blank row 7, notes in rows 8 to 10). `test_contract.py` checks every constant against literals re-typed from the research.
- `epb/formats/writer.py` writes every cell as text (`t="inlineStr"`, no `<f>`), removes only C0 control characters, writes no cell for an empty value, and keeps widths at `wch + 0.83203125`. It runs `validate_rows` before writing and `validate_workbook` on `<path>.tmp` before `os.replace`, so a failure leaves the target untouched.
- `epb/formats/validate.py` collects every finding, never stopping at the first. It covers sheet order, metadata layout, marker, totals, header rows, required fields, exact enums, date precision, Chain of Custody JSON and entries, text-only cells, formulas, the length boundary, bad characters and the DEF-14 list-fragment rules. Findings are sorted deterministically.
- `tools/make-smoke-pack.py` writes the eight synthetic ACM rows from the plan table to `scratch/smoke/evidence-pack-smoke.xlsx` (git-ignored) and prints a 21-line numbered checklist covering every A10 edge value.

## Task Commits

1. **Task 1: Tracer — one-item pack written and re-read clean.** `8a3d372` (feat)
2. **Task 2: Complete the validator.** RED `0a961d8` (test), GREEN `418e16e` (feat). No refactor commit was needed.
3. **Task 3: Smoke-pack tool and the owner's import checklist.** `aecd66c` (feat)

**Plan metadata:** recorded in the docs commit that adds this SUMMARY.

## TDD Gate Compliance (Task 2)

- **RED:** `test_validator.py` and `test_contract.py` were committed in `0a961d8` before any Task 2 code. Run: `.venv/bin/python -m pytest -q tests/formats --junitxml=scratch/tdd/red-01-04.xml`. Result: 65 failed and 111 passed. The target `test_prototype_pack_fails_on_list_fragments` failed with `assert 0 == 24` on the Linked Equipment `LIST_FRAGMENT_UNBALANCED` count, after its `SHEETS_INVALID` assertion passed. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`).
- **Semantic assessment:** the module collected and imported cleanly, and the target ran and failed on the planned assertion because the list-fragment check did not exist yet. The 111 passing tests covered behaviour Task 1 had already shipped: contract constants, required and core-enum rules, sheet and metadata structure, and valid packs. The remaining failures were missing codes. One of them was `test_broken_sheet_xml`, where a lazy `ParseError` escaped because the raw XML pass did not exist yet.
- **GREEN:** `418e16e`, with 176 passed in `tests/formats`.
- **REFACTOR:** none needed.

## Tracer Gate (Task 1)

The run was interactive in `end-of-phase` mode, and the tracer's verify was automated only. The verify was re-run after the commit and passed (24 passed), so expansion went ahead with no checkpoint.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/formats/__init__.py`: the `FORMATS` seam and `get_format(name)`.
- `plugin/skills/evidence-pack/scripts/epb/formats/probematrix_v2.py`: data-only importer-exact constants.
- `plugin/skills/evidence-pack/scripts/epb/formats/writer.py`: `PackMetadata`, `PackInvalid` and `write_pack`.
- `plugin/skills/evidence-pack/scripts/epb/formats/validate.py`: `Finding`, `validate_rows` and `validate_workbook`.
- `tests/epbtest/packkit.py`: synthetic row, metadata and XML helpers shared by the format tests.
- `tests/formats/test_writer.py`: round-trip, raw XML, edge strings, widths, layout, totals, header order, control characters and the atomic-write tests (24).
- `tests/formats/test_validator.py`: a planted defect for each code, in memory and on disk, plus boundaries and the prototype counts.
- `tests/formats/test_contract.py`: the independent importer-contract transcription, the format seam and the totals.
- `tools/make-smoke-pack.py`: the repo-only smoke workbook builder (`--out`, `--export-date`, `build`, `main`, `ChecklistItem`).
- `tests/tools/test_smoke_pack.py`: the build, exact read-back, A10 checklist coverage and CLI subprocess tests.

## Decisions Made

See `key-decisions` in the frontmatter. The two forced by openpyxl behaviour are:

- **Saving through `ExcelWriter`.** `Workbook.save` stamps `modified` with the wall clock.
- **Opening the workbook as a file handle.** `load_workbook` rejects a `.tmp` file name.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] openpyxl refuses to load `<path>.tmp` by file name**
- **Found during:** Task 1
- **Issue:** `openpyxl.load_workbook` checks the file extension and raises `InvalidFileException` for `.tmp`, but the plan has the writer validate `<path>.tmp` before replacing the target.
- **Fix:** `validate_workbook` opens the file in binary mode and passes the handle to `load_workbook(read_only=True)`.
- **Files modified:** `epb/formats/validate.py`
- **Verification:** `test_validation_reads_the_saved_temp_file` passes.
- **Committed in:** `8a3d372`

**2. [Rule 1 - Bug] `Workbook.save` overwrote the injected modified time**
- **Found during:** Task 1
- **Issue:** openpyxl's `save_workbook` sets `properties.modified` to `now()`, which defeats "created and modified are set from `created`".
- **Fix:** `_save` writes through `openpyxl.writer.excel.ExcelWriter` with its own `ZipFile`.
- **Files modified:** `epb/formats/writer.py`
- **Verification:** `test_created_and_modified_properties_are_injected` passes.
- **Committed in:** `8a3d372`

**3. [Rule 3 - Blocking] Shared synthetic test helpers**
- **Found during:** Task 1
- **Issue:** Three format test files and the smoke test all need the same synthetic valid row, metadata and XML helpers.
- **Fix:** Added `tests/epbtest/packkit.py`, a file that is not in the plan's list. The `tests/epbtest/` helper folder already existed from plan 01-03.
- **Committed in:** `8a3d372`

**4. [Rule 2 - Missing critical] Stricter than the plan in three places**
- **Found during:** Tasks 1 and 2
- **Issue and fix:**
  - A blank Evidence ID also gives `REQUIRED_BLANK`. The importer requires the header but not a value, and every builder row carries an ID.
  - Two constants were added: `METADATA_BLANK_ROW` and `METADATA_NOTES_FIRST_ROW`.
  - A formula cell reports only `CELL_FORMULA`, never `CELL_NOT_TEXT` as well, which keeps "one finding per cell and code".
- **Committed in:** `8a3d372`, `418e16e`

---

**Total deviations:** 4 auto-fixed: 2 blocking, 1 bug, 1 stricter-validation adjustment.
**Impact on plan:** All four were needed for correctness, or kept to the plan's stated intent. There was no scope creep, and no cell text is ever altered to make a pack pass.

## Issues Encountered

- openpyxl writes `<col>` attributes in the order `width`, `customWidth`, `min`, `max`, so the width test parses the XML instead of matching a regex. The widths on disk are exactly `12.83203125` and `60.83203125`.

## User Setup Required

None. No external service configuration is needed.

## Owner Smoke Import (SC4), not run by the agent

The owner runs the human-check procedure in `01-04-PLAN.md` Task 3:
1. Run `.venv/bin/python tools/make-smoke-pack.py`.
2. Import `scratch/smoke/evidence-pack-smoke.xlsx` into a new test incident.
3. Compare the result against the printed 21-item checklist.

The agent has not imported the workbook and makes no claim about the result.

## Next Phase Readiness

- Plan 01-15 owns `references/evidence-pack-v2.md` (design §8.5). It should document these constants and finding codes, with the `IMPORTER_CHECKED` date `2026-10-17`.
- Phase 5's renderer can call `write_pack` directly. Policy on which QA Status values to emit (`verified`, `disputed` or blank) belongs to the renderer. The validator accepts all eight.
- Plan verification passed: `.venv/bin/python -m pytest -q tests/formats tests/tools/test_smoke_pack.py` gave 179 passed, the full suite gave 232 passed, and `.venv/bin/ruff check .` and `ruff format --check .` were clean.

## Self-Check: PASSED

- All 10 created files exist on disk.
- Commits `8a3d372`, `0a961d8`, `418e16e` and `aecd66c` are ancestors of HEAD.
- The `git status --porcelain` output shows nothing under `scratch/`.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
