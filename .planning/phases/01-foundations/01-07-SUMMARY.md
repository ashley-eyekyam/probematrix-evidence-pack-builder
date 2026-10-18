---
phase: 01-foundations
plan: 07
subsystem: workspace-store
tags: [python, jsonschema, journal, fsync, importlib-resources, state-json, init]

# Dependency graph
requires:
  - phase: 01-foundations (01-03)
    provides: epb.errors codes and EpbError, epb.cli Context/Result, the command-module contract and the stdlib-only bootstrap guard
provides:
  - epb/fsio.py durable-write primitives (write_durable, fsync_dir, replace_with_retry, sha256_bytes, sha256_file, json_bytes, read_json, utc_now_iso)
  - epb/schema.py schema loading through importlib.resources plus validate/check (RECORD_INVALID with JSON pointers)
  - epb/txn.py Transaction (manifest-rename commit point, state.json last, path rules), recover(), pending_journals()
  - epb/state.py SCHEMA_VERSION, STATE_FILE, new_state(), guarded load_state() (D-09, D-19)
  - schemas/state.schema.json, the complete WS-13 state contract (workbooks, items, chunks, imports, counters, fingerprints)
  - schemas/chunks.schema.json, the D-07 chunk-plan contract for ledger/chunks.json
  - epb init command (idempotent, ALREADY_SET_UP and RECOVERED warnings)
affects: [01-09 case.yaml, 01-11 workspace layout and INDEX.md, 01-12 locking, crash injection and D-09 upgrade, phase 2 scan, phase 3 extraction planner, phase 5-6 build and mark-imported]

# Actuals (#2632)
actuals:
  tokens: 13688
  tasks: 3
  commits: 5
plan_head_before: 535fcfe94f7fd3af4e698f8d28987e1478d71825
plan_head_after: 987e7c1c2822af8bec24f9b6629344698f999acd

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Redo journal: blobs to .epb/tmp/txn-<id>/NNNN, manifest.json.tmp renamed to manifest.json as the single commit point, state.json always the last entry"
    - "Validate at staging: every stage_json/stage_record/set_state calls schema.check before anything is held, so an invalid record never reaches disk"
    - "Path allow-list for transactions: INDEX.md, .epb/ and outputs/ only; never inputs/, absolute, '..', backslash, .epb/tmp/ or a direct state.json write"
    - "Schemas closed everywhere (additionalProperties false; maps use propertyNames plus a value schema) and pattern-only (no format keywords)"
    - "Version check in code, not in the schema: load_state refuses newer, validates equal, returns older raw for the D-09 upgrade"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb/fsio.py
    - plugin/skills/evidence-pack/scripts/epb/schema.py
    - plugin/skills/evidence-pack/scripts/epb/txn.py
    - plugin/skills/evidence-pack/scripts/epb/state.py
    - plugin/skills/evidence-pack/scripts/epb/schemas/state.schema.json
    - plugin/skills/evidence-pack/scripts/epb/schemas/chunks.schema.json
    - plugin/skills/evidence-pack/scripts/epb/commands/init.py
    - tests/workspace/test_init.py
    - tests/schemas/test_state_schema.py
    - tests/store/test_validate.py
  modified: []

key-decisions:
  - "Schema issue pointers are RFC 6901 escaped (~0, ~1), so a fingerprint key like inputs/a.pdf shows as /fingerprints/inputs~1a.pdf; the root is '/' as the plan specifies"
  - "Transaction refuses .epb/tmp/ targets, a second staging of the same path and a direct stage of .epb/state.json (state goes only through set_state), in addition to the plan's path rule"
  - "recover() distrusts a manifest whose entries have a non-NNNN tmp name, a bad sha256 or a final path outside the allow-list (STATE_INVALID), so a tampered journal cannot write into inputs/"
  - "load_state treats schema_version below 1 (or a bool) as damaged STATE_INVALID; only 1 <= version < SCHEMA_VERSION is returned raw for upgrade"
  - "Workbook records require at least one entry in writes (a record exists only after a first write)"
  - "init on an already set-up folder returns data.created = [] with the ALREADY_SET_UP warning and exit 0"

patterns-established:
  - "New persisted record: add schemas/<name>.schema.json (closed, pattern-only, schema_version field) and stage it with Transaction.stage_json(rel, obj, name)"
  - "RED for a schema that does not exist yet commits an inert skeleton schema so RED fails on assertions, not FileNotFoundError"

requirements-completed: [WS-01, WS-06, WS-08, WS-13]

coverage:
  - id: D1
    description: "epb init writes a schema-valid .epb/state.json through a journalled transaction, leaves no txn folder, is idempotent (ALREADY_SET_UP, bytes unchanged) and refuses a missing --case folder with BAD_ARGUMENT"
    requirement: WS-01
    verification:
      - kind: integration
        ref: "tests/workspace/test_init.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Journalled store: manifest-rename commit point, state.json last, manifest and apply in staging order, empty commit writes nothing, idempotent recover() roll-forward, uncommitted and stray manifest.json.tmp journals discarded, hash-mismatch and unreadable manifests refused with STATE_INVALID"
    requirement: WS-06
    verification:
      - kind: unit
        ref: "tests/store/test_validate.py#test_manifest_and_apply_order_put_state_last"
        status: pass
      - kind: unit
        ref: "tests/store/test_validate.py#test_recover_rolls_forward_idempotently"
        status: pass
      - kind: unit
        ref: "tests/store/test_validate.py#test_recover_refuses_a_missing_blob_with_a_different_final"
        status: pass
    human_judgment: false
  - id: D3
    description: "Validate-on-write: an invalid record is refused at staging with RECORD_INVALID (exit 4) listing every issue with its JSON pointer, and the case folder is byte-identical afterwards; forbidden paths are refused with INTERNAL_ERROR before staging"
    requirement: WS-08
    verification:
      - kind: unit
        ref: "tests/store/test_validate.py#test_set_state_with_two_problems_is_refused"
        status: pass
      - kind: unit
        ref: "tests/store/test_validate.py#test_forbidden_paths_are_refused_before_staging"
        status: pass
    human_judgment: false
  - id: D4
    description: "Complete WS-13 state contract (workbook registry, counters, items, per-chunk status without raw text, import records) and the D-07 chunk-plan schema, every object closed and pattern-only"
    requirement: WS-13
    verification:
      - kind: unit
        ref: "tests/schemas/test_state_schema.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Guarded state loading (D-19): NOT_A_WORKSPACE when missing, STATE_INVALID with a restore hint when unparseable or schema-invalid, WORKSPACE_TOO_NEW for a newer schema_version, older state returned raw"
    requirement: WS-06
    verification:
      - kind: unit
        ref: "tests/store/test_validate.py#test_load_state_unreadable_is_state_invalid"
        status: pass
      - kind: unit
        ref: "tests/store/test_validate.py#test_load_state_too_new"
        status: pass
    human_judgment: false

# Metrics
duration: 7min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 07: Journalled workspace store and epb init Summary

**`epb init` now writes `.epb/state.json` through a redo-journal store with a single manifest-rename commit point, state.json applied last, schema validation at staging, idempotent hash-checked recovery and D-19 guarded loading, backed by the complete WS-13 state schema and the D-07 chunk-plan schema.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-18T10:00:46Z
- **Completed:** 2026-10-18T10:07:24Z
- **Tasks:** 3
- **Files modified:** 10 (all created)

## Accomplishments

- `epb/txn.py`: `Transaction` stages blobs in memory, writes them durably to `.epb/tmp/txn-<UTC>-<pid>-<6 hex>/NNNN`, commits by renaming `manifest.json.tmp` to `manifest.json`, applies in manifest order with `state.json` last, then removes the journal. A failure before the commit point removes the journal. A failure after it leaves the journal for `recover()`.
- `recover()` rolls committed journals forward and skips entries that are already applied, after checking the final file's hash. It discards uncommitted journals, including a stray `manifest.json.tmp`, and refuses a hash mismatch or an untrustworthy manifest with `STATE_INVALID`. A second call changes nothing.
- `epb/schema.py` loads schemas only from `epb/schemas/` through `importlib.resources` (D-05). It validates with Draft 2020-12 and no format checker, and `check()` raises `RECORD_INVALID`, listing every issue as `pointer: message` with `data.issues`.
- `state.schema.json` defines the full WS-13 contract now, so later phases never migrate it: counters, `inputs/` fingerprints, the workbook registry with its write history, item refs keyed by EVD ID, per-chunk status with no raw text, and import records. `chunks.schema.json` declares the `ledger/chunks.json` plan with its `section_path` headings.
- `load_state()` follows D-09 and D-19, and `epb init` is idempotent, mutating, and uses only stdlib imports at module level.

## Task Commits

1. **Task 1: Tracer, epb init → Transaction → schema check → state.json last.** `7a5716b` (feat). The tracer gate re-ran its verify and passed (5/5), then expansion continued.
2. **Task 2: Complete the WS-13 state contract and the D-07 chunk-plan schema.** RED `e8140ac` (test), GREEN `5346c24` (feat).
3. **Task 3: Validate-on-write refusal, guarded state loading and recovery.** RED `33f9d9f` (test), GREEN `987e7c1` (feat).

No REFACTOR commits were needed.

## TDD Evidence

- **Task 2 RED:** JUnit XML from `pytest --junitxml` was classified by `gsd-tools check tdd-red-evidence` as `RED_EVIDENCE_OK` (38 tests, 22 failing). The target was `test_locked_workbook_status_is_invalid`. Semantic check: the target ran and failed on its planned assertion (`[] == ['/workbooks/0/status']`, because the tracer schema's `workbooks` array accepted any record). All 22 failures were `AssertionError`s; none was a load error. `chunks.schema.json` was committed as an inert skeleton so the chunk-plan tests failed on assertions and not on a missing file. The 16 tests that passed at RED cover behaviour the tracer schema already enforced (required fields, the `inputs/` fingerprint keys, schema_version 2 accepted).
- **Task 3 RED:** `RED_EVIDENCE_OK` (32 tests, 19 failing). The target was `test_recover_refuses_a_missing_blob_with_a_different_final`. Semantic check: it ran and failed with `DID NOT RAISE EpbError`, which is the planned gap. The other failures were `DID NOT RAISE`, or raw `FileNotFoundError`, `UnicodeDecodeError` or `JSONDecodeError` from the unguarded loader, which is exactly the behaviour under test. The 13 tests that passed at RED cover behaviour the plan put in the Task 1 tracer: validation at staging, the empty commit, manifest ordering, deterministic JSON, roll-forward, and discarding an uncommitted journal.
- **GREEN:** both tasks pass. Plan verification (`tests/workspace tests/schemas tests/store tests/launcher tests/cli`) gives 120 passed, and the full suite gives 469 passed. `ruff check` and `ruff format --check` are clean.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/fsio.py`: durable write, directory fsync, `os.replace` with Windows retry, sha256, deterministic JSON, UTC timestamps.
- `plugin/skills/evidence-pack/scripts/epb/schema.py`: `load_schema`, `validate`, `check`, `SchemaIssue`.
- `plugin/skills/evidence-pack/scripts/epb/txn.py`: `Transaction`, `recover`, `pending_journals`, path allow-list.
- `plugin/skills/evidence-pack/scripts/epb/state.py`: `SCHEMA_VERSION`, `STATE_FILE`, `new_state`, `load_state`.
- `plugin/skills/evidence-pack/scripts/epb/schemas/state.schema.json`: the WS-13 state contract (`$id` `epb:state`).
- `plugin/skills/evidence-pack/scripts/epb/schemas/chunks.schema.json`: the D-07 chunk plan (`$id` `epb:chunks`).
- `plugin/skills/evidence-pack/scripts/epb/commands/init.py`: the `epb init` command.
- `tests/workspace/test_init.py`: subprocess tests of `epb init`.
- `tests/schemas/test_state_schema.py`: the state and chunk-plan contracts, plus schema hygiene (closed objects, no `format`).
- `tests/store/test_validate.py`: in-process store tests with hand-built journals.

## Decisions Made

See `key-decisions` in the frontmatter. In short:

- Schema issue pointers are RFC 6901 escaped.
- The path rule also refuses `.epb/tmp/`, duplicate staging and a direct `state.json` stage.
- `recover()` validates manifest entries, so a tampered journal cannot write outside the allow-list.
- A `schema_version` below 1 counts as damaged.
- A workbook record needs at least one write.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] A recovery manifest can no longer write outside the allowed paths**
- **Found during:** Task 3
- **Issue:** The plan's path rule guards staging, but `recover()` applied whatever `final` paths a journal manifest listed. A damaged or tampered manifest could therefore write under `inputs/` or outside the case folder, which breaks the must-have "No transaction can write under inputs/ or outside the case folder" (threat T-01-15).
- **Fix:** `_read_manifest()` checks every entry (tmp `^\d{4}$`, sha256 hex, `final` must pass the same path rule) and raises `STATE_INVALID` naming the journal folder otherwise.
- **Files modified:** `epb/txn.py`
- **Verification:** `test_recover_refuses_an_unreadable_manifest` plus the full store suite.
- **Committed in:** `987e7c1`

**2. [Rule 2 - Missing critical] Duplicate and direct state.json staging are refused**
- **Found during:** Task 3
- **Issue:** Staging the same path twice would apply two blobs to one file in an order that depends on staging. Staging `.epb/state.json` through `stage_text` or `stage_json` would bypass the state schema and the "state last" rule.
- **Fix:** Both raise `INTERNAL_ERROR` before anything is staged. Targets under `.epb/tmp/` are refused too.
- **Files modified:** `epb/txn.py`
- **Verification:** `test_same_path_twice_is_refused` and `test_forbidden_paths_are_refused_before_staging[.epb/state.json]`.
- **Committed in:** `987e7c1`

---

**Total deviations:** 2 auto-fixed (both Rule 2).
**Impact on plan:** Both close gaps in the plan's own must-haves and threat mitigations. There is no scope creep and no change to any public interface.

## Issues Encountered

- **The errors docstring now lags the code (deferred, not fixed here).** The `ALREADY_SET_UP` line in the `epb/errors.py` docstring says "The private environment was already current". The plan now also uses that warning for `init` on a folder that is already set up. Separately, the registered error `WORKSPACE_EXISTS` ("init was run on a folder that already has a workspace") is unused, because the plan makes `init` idempotent (exit 0 plus a warning). `errors.py` is outside this plan's `files_modified`, and sibling plans running in parallel (01-08 doctor) may touch it, so it was left unchanged. The docstring feeds the manual's troubleshooting chapter, so a later plan should either widen the `ALREADY_SET_UP` wording or retire `WORKSPACE_EXISTS`.
- **A damaged state.json still reads as already set up.** `init` only checks whether `.epb/state.json` exists, as the plan specifies. A damaged state file therefore gets `ALREADY_SET_UP` and not `STATE_INVALID`. Commands that load state go through `load_state()` and will report the damage. 01-11 or 01-12 may want `init` to call `load_state()`.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- 01-09 (`case.yaml`) and 01-11 (folder layout, `.gitignore`, `.gitattributes`, `INDEX.md`) can stage their files through `Transaction.stage_text` and `stage_json`. `INDEX.md` and every `.epb/` and `outputs/` path are already allowed.
- 01-12 can wrap `Transaction` with the lock, add crash-injection checkpoints at the stage, manifest and cleanup points, and register D-09 upgrade steps. `load_state` already returns older state unvalidated for that path.
- `pending_journals()` is ready for read-only commands to raise `RECOVERY_PENDING`.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED

- All 10 key files exist on disk.
- Commits `7a5716b`, `e8140ac`, `5346c24`, `33f9d9f` and `987e7c1` are all ancestors of HEAD on `gsd-wt-01-07`.
- There is no root `schemas/` folder, and STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched.
