---
phase: 01-foundations
plan: 11
subsystem: workspace-store
tags: [python, jsonschema, init, index-md, runs, status, git, sync-folders, ws-09]

# Dependency graph
requires:
  - phase: 01-foundations (01-07)
    provides: Transaction (stage_json/stage_record/stage_text/set_state/commit), recover, pending_journals, new_state/load_state, schema.check/validate, fsio
  - phase: 01-foundations (01-08)
    provides: epb.doctor.syncfolders.check + warning_for, epb.doctor.gitcheck.check (envelope warning dicts)
  - phase: 01-foundations (01-09)
    provides: casefile.resolve_settings/new_case_record/load_case/differences, yamlio.dump_yaml_bytes, the case.yaml step of init
provides:
  - epb/workspace.py layout contract (CASE_DIRS, EPB_DIRS, GITIGNORE_LINES/TEXT, GITATTRIBUTES_TEXT, PRIVATE_GITIGNORE_TEXT, CLASSIFICATIONS, CONTRACT_PATHS) and sessions (find_workspace, open_for_init, open_for_mutation, open_read_only, load_sources, Session)
  - epb/index.py six-section INDEX.md renderer (SECTION_TITLES, NONE_YET, INDEX_FILE, IndexInputs, PROVIDERS, render_index, render_import_line, display_id)
  - epb/runs.py run allocation and loading (RUNS_DIR, new_run, run_json_path, load_runs)
  - schemas/run.schema.json (epb:run) including the scan and upgrade summaries
  - epb status (read-only, MUTATING = False)
  - epb init creating the full layout, run 001 and INDEX.md in one transaction, then warning about sync folders and git
affects: [01-12 lock and upgrade inside open_for_init/open_for_mutation, 01-13 scan (open_for_mutation, new_run, render_index), 01-14 scan corpus and sidecars (run summary keys, INDEX open issues), 01-15 skill and workspace-contract.md (CONTRACT_PATHS), 01-16 manual (INDEX.md sections)]

# Actuals (#2632)
actuals:
  tokens: 19269
  tasks: 3
  commits: 5
plan_head_before: 48bb723f54f4c0c1aad51be3c1ed9e48ca8dbadb
plan_head_after: 8f87b56fa5d8e4f61c86e51c9a237f0f2bef86b3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "INDEX.md is a pure function of (case, state, sources, runs): six ordered providers, each body 'none yet' when empty, rendered inside the same transaction as state.json"
    - "Run records allocate their number from state.counters.run in the same transaction, so a run number is never reused; runs are reports and load_runs skips damaged ones"
    - "Read-only commands go through open_read_only: no lock, no recovery, no writes, RECOVERY_PENDING only"
    - "Post-commit, read-only folder checks: each wrapped so any exception becomes no warning"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb/workspace.py
    - plugin/skills/evidence-pack/scripts/epb/index.py
    - plugin/skills/evidence-pack/scripts/epb/runs.py
    - plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json
    - plugin/skills/evidence-pack/scripts/epb/commands/status.py
    - tests/workspace/test_layout.py
    - tests/index/test_index.py
    - tests/workspace/test_status.py
    - tests/workspace/test_git_warning.py
  modified:
    - plugin/skills/evidence-pack/scripts/epb/commands/init.py
    - tests/workspace/test_init.py
    - tests/workspace/test_init_defaults.py

key-decisions:
  - "The INDEX.md Inputs table has an ID column first (display_id, e.g. S004v2) ahead of the planned Path...Items columns, so a new version is visible in INDEX as plan 01-14 requires"
  - "init's data.created lists the layout folders that did not exist before (with a trailing /) followed by every staged file in apply order, state.json last"
  - "The foreign-INDEX.md refusal runs before anything is created when no journal is pending, and again after recovery, so a refusal leaves the folder untouched"
  - "run.json finished_at is stamped when the run is allocated, just before the commit; INDEX shows run times in UTC (YYYY-MM-DD HH:MM UTC), not the case timezone"
  - "run.schema.json scan.sidecars[].target is a source id (^S\\d{3,}$), matching sidecar_of on source records; scan.new_versions[].version is at least 2; upgrade.backup_dir must be .epb/runs/<NNN>/pre-upgrade/"
  - "load_sources: an unparseable record is STATE_INVALID (D-19); a schema failure is RECORD_INVALID through schema.check, as the plan specifies; only files named S<3+ digits>.json are read"
  - "open_read_only is a plain function returning a Session; open_for_init and open_for_mutation are context managers, so 01-12 can add the lock around their yield"
  - "status message is five plain lines ending with a pointer to INDEX.md; data has exactly case, inputs, runs, last_run, workbooks"

patterns-established:
  - "A new pipeline-level command: runs.new_run(state, NAME, ...) → stage_json(run_json_path(id), record, 'run') → stage INDEX.md from render_index(IndexInputs(case, state, sources, runs + [record])) → set_state → commit"
  - "Only the five CLASSIFICATIONS are used in CONTRACT_PATHS, and every A2-ignored folder is raw-text-confidential or private-never-shared (test-enforced)"

requirements-completed: [WS-01, WS-09, WS-11, WS-12]

coverage:
  - id: D1
    description: "init in an empty folder creates inputs/, outputs/, INDEX.md and .epb/ with case.yaml, state.json, .gitignore, .gitattributes, inbox/, tmp/, runs/ and private/ (own .gitignore of *), files committed in one transaction, no journal left"
    requirement: WS-01
    verification:
      - kind: integration
        ref: "tests/workspace/test_layout.py#test_init_creates_every_folder_and_file"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_layout.py#test_existing_inputs_are_kept"
        status: pass
    human_judgment: false
  - id: D2
    description: ".epb/.gitignore is exactly the seven A2 lines in order, .gitattributes is '* -text', private/.gitignore is '*'; in a real git repository .epb/private, runs and tmp stay out of git status"
    requirement: WS-11
    verification:
      - kind: integration
        ref: "tests/workspace/test_layout.py#test_ignore_files_have_exact_bytes"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_git_warning.py#test_init_in_a_repository_ignores_the_raw_text_folders"
        status: pass
    human_judgment: false
  - id: D3
    description: "INDEX.md has a title, the do-not-edit note and six '## N. Title' sections in order with blank lines around each heading; empty sections read 'none yet'; tick line '- [ ] Imported: <file>' / '- [x]'; inputs sorted by path with pending shown as waiting for conversion; open issues for removed inputs, MIME mismatches, orphan sidecars and skipped links/special files; run history sorted by number"
    requirement: WS-09
    verification:
      - kind: unit
        ref: "tests/index/test_index.py"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_layout.py#test_index_has_six_sections_in_order"
        status: pass
    human_judgment: false
  - id: D4
    description: "init writes run 001 (valid against run.schema.json, counters.run 1) and INDEX run history shows exactly that run; run ids have at least three digits and grow past 999; load_runs skips missing or invalid records"
    requirement: WS-09
    verification:
      - kind: integration
        ref: "tests/workspace/test_status.py#test_init_writes_run_001"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_status.py#test_index_run_history_shows_run_001"
        status: pass
      - kind: unit
        ref: "tests/workspace/test_status.py#test_run_ids_have_at_least_three_digits"
        status: pass
      - kind: unit
        ref: "tests/workspace/test_status.py#test_load_runs_skips_missing_and_invalid_and_sorts"
        status: pass
    human_judgment: false
  - id: D5
    description: "epb status: NOT_A_WORKSPACE outside a case folder; after init exit 0 with zero inputs, 1 run and 0 workbooks; no byte or path in the case folder changes; a committed journal gives RECOVERY_PENDING and is left in place"
    requirement: WS-01
    verification:
      - kind: integration
        ref: "tests/workspace/test_status.py#test_status_after_init"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_status.py#test_status_changes_nothing"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_status.py#test_status_reports_but_never_finishes_an_interrupted_change"
        status: pass
    human_judgment: false
  - id: D6
    description: "init warns with exit 0: SYNC_FOLDER 'appears to be inside Dropbox' from a fake-home info.json, GIT_TRACKS_PRIVATE for a force-added private file, GIT_UNAVAILABLE with no git binary under a .git folder; checks run after the commit and a raising or timed-out check never fails init"
    requirement: WS-12
    verification:
      - kind: integration
        ref: "tests/workspace/test_git_warning.py"
        status: pass
    human_judgment: false
  - id: D7
    description: "init refuses (exit 2 BAD_ARGUMENT) to overwrite an INDEX.md it did not make, leaving the folder untouched; no absolute path, home folder, account name or host name appears in any file init writes"
    requirement: WS-01
    verification:
      - kind: integration
        ref: "tests/workspace/test_layout.py#test_foreign_index_is_refused"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_layout.py#test_no_absolute_path_user_or_host_in_any_file"
        status: pass
    human_judgment: false
  - id: D8
    description: "INDEX.md, status and warning wording reads as plain language for a non-technical investigator"
    requirement: WS-09
    verification: []
    human_judgment: true
    rationale: "Wording quality is a judgement no test asserts; the 01-15 UAT and the 01-16 manual quote this text"

# Metrics
duration: 10min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 11: Case-folder layout, INDEX.md, run records and epb status Summary

**`epb init` now sets up the complete documented case folder in one journalled transaction. That means `inputs/`, `outputs/`, the `.epb` folders, the A2 `.gitignore`, `.gitattributes`, the private folder's own ignore file, run `001`, and a six-section `INDEX.md` written just before `state.json`. After the commit, init warns in plain words about sync folders and git. A new read-only `epb status` summarises the case without locking or writing anything.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-18T10:22:43Z
- **Completed:** 2026-10-18T10:32:26Z
- **Tasks:** 3
- **Files modified:** 12 (9 created, 3 modified)

## Accomplishments

- `epb/workspace.py` holds the layout contract:
  - `CONTRACT_PATHS` classifies all 23 design §6 and D-06 paths into five sharing classes, ready for `references/workspace-contract.md` (01-15).
  - It also holds the A2 ignore list and the three sessions: `open_for_init`, `open_for_mutation` and `open_read_only`.
- `epb/index.py` renders `INDEX.md` as a pure function of the case, state, sources and runs:
  - Six ordered providers, with `none yet` for anything empty.
  - The fixed tick syntax `- [ ] Imported: <file>`.
  - Inputs show their display ID (`S004v2`), short SHA-256, size, type label and waiting-for-conversion status.
  - Open issues cover removed inputs, MIME mismatches, orphan note files, and links or special files skipped by the latest scan.
- `epb/runs.py` and `run.schema.json`:
  - Run numbers come from `counters.run` in the same transaction, have at least three digits, and grow past 999.
  - The schema already declares the full scan summary that 01-13 and 01-14 fill, plus the upgrade summary that 01-12 fills.
- `epb init`:
  - Refuses a foreign `INDEX.md` and leaves the folder untouched.
  - Creates the layout and stages `case.yaml`, the three ignore files, `runs/001/run.json` and `INDEX.md`, with `state.json` last. It returns `next: ["scan"]`.
  - Then runs the 01-08 sync-folder and git detectors. Each is guarded, so it can only add warnings.
- `epb status` reports the case settings, input counts, runs, the last run and the number of workbooks, under the 01-03 stdlib-only bootstrap guard.

## Task Commits

1. **Task 1 (tracer): init writes the complete layout and a six-section INDEX.md in one transaction.** `164447c` (feat). Tracer gate: the run is interactive and end-of-phase, and the verify is automated only. I re-ran it (121 passed) and expansion continued.
2. **Task 2: Runs, run history and the read-only status command.** RED `05704a1` (test), GREEN `47ffbee` (feat).
3. **Task 3: Plain-language sync-folder and git warnings on init.** RED `b141b13` (test), GREEN `8f87b56` (feat).

No REFACTOR commits were needed.

## TDD Gate Compliance

- **Task 2 RED (`05704a1`):**
  - JUnit XML from `pytest --junitxml` was classified by `gsd-tools check tdd-red-evidence` as `RED_EVIDENCE_OK` (`target_test_failed`): 43 tests, 27 failing.
  - Target: `test_init_writes_run_001`, which failed on its planned assertion that `.epb/runs/001/run.json` is a file (init allocated no run yet).
  - Semantic check: the RED commit carried interface-only stubs (`runs.py` and the workspace functions raising `NotImplementedError`, plus an inert `run.schema.json`). Every failure was therefore an assertion or a `NotImplementedError` on planned behaviour, with no import or collection fault.
  - The 16 tests that passed at RED cover the Task 1 layout, which this task does not change.
- **Task 3 RED (`b141b13`):**
  - `RED_EVIDENCE_OK` (`target_test_failed`): 14 tests, 5 failing.
  - Target: `test_init_inside_dropbox_warns`, which failed with `assert [] == ['SYNC_FOLDER']` because init ran no folder checks yet.
  - The 9 that passed at RED:
    - the ignore rules already shipped by Task 1;
    - the quiet baseline;
    - the re-run;
    - the six failing-check cases. These were vacuous at RED, because init did not call the checks yet, and became meaningful at GREEN.
- **GREEN:**
  - Plan verification (`tests/workspace tests/doctor tests/index`) gives 280 passed, with none skipped, so the git cases ran.
  - The full suite gives 803 passed (730 before this plan), and the failing file set is empty.
  - `ruff check` and `ruff format --check` are clean.
  - The 01-03 bootstrap guard `test_bootstrap_imports_stdlib_only` passes with `status.py` discovered.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/workspace.py`: the layout constants, `CONTRACT_PATHS`, `missing_layout`/`create_layout`, `find_workspace`, `load_sources`, the `Session`/`InitSession` classes and the three sessions.
- `plugin/skills/evidence-pack/scripts/epb/index.py`: the INDEX.md renderer and its six providers.
- `plugin/skills/evidence-pack/scripts/epb/runs.py`: run allocation, paths and loading.
- `plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json`: the run record contract (`epb:run`).
- `plugin/skills/evidence-pack/scripts/epb/commands/status.py`: the read-only `status` command.
- `plugin/skills/evidence-pack/scripts/epb/commands/init.py`: the full layout, run 001, INDEX.md, the foreign-INDEX refusal and the post-commit warnings.
- `tests/workspace/test_layout.py`, `tests/index/test_index.py`, `tests/workspace/test_status.py`, `tests/workspace/test_git_warning.py`: new tests.
- `tests/workspace/test_init.py`, `tests/workspace/test_init_defaults.py`: the `created` assertions now check membership and order (`case.yaml` present, `state.json` last).

## Decisions Made

See `key-decisions` in the frontmatter. In short:

- INDEX.md gets an ID column.
- The order of `data.created` is fixed.
- The foreign-INDEX check runs before anything is created.
- INDEX shows run times in UTC.
- `scan.sidecars[].target` is a source ID.
- An unparseable source record is `STATE_INVALID`.
- The sessions take the forms 01-12 needs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The `created` assertions in 01-07 and 01-09 tests follow the new layout**
- **Found during:** Task 1
- **Issue:** `test_init.py` and `test_init_defaults.py` asserted `data.created == [case.yaml, state.json]`. The plan requires `created` to list the folders and files init creates, so the exact list could no longer hold.
- **Fix:** Both now assert that `case.yaml` is in `created` and that `state.json` is last. The exact list is asserted once, in `test_layout.py`. No other assertion changed.
- **Files modified:** `tests/workspace/test_init.py`, `tests/workspace/test_init_defaults.py`
- **Committed in:** `164447c`

**2. [Rule 2 - Missing critical] An ID column in the INDEX.md Inputs table**
- **Found during:** Task 1
- **Issue:** The planned Inputs columns (Path … Items) give a source's version no place to appear. The interface still exports `display_id`, and plan 01-14 requires INDEX.md to show `S001v2` after a new version.
- **Fix:** `ID` is the first column, filled by `display_id` (`S001`, `S004v2`). The planned columns follow in the planned order.
- **Files modified:** `epb/index.py`, `tests/index/test_index.py`
- **Committed in:** `164447c`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical).
**Impact on plan:** Both keep the planned interfaces. The ID column adds to the planned columns and removes none of them. There is no scope creep.

## Issues Encountered

- My first Task 1 inputs-table test counted the Markdown separator row as a data row. I fixed it before the commit; it was a test bug only.
- `scan.sidecars[].target` is constrained to a source ID. If plan 01-14 records a path there instead, it will need to widen this single property in `run.schema.json`.
- The INDEX columns `Segments`, `Claims` and `Items` and the Outputs column "Inputs that contributed items" read `none yet` by design until the later phases that produce them. They are the planned rendering, not stubs.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- **01-12:** can add the lock (and the upgrade) inside `open_for_init` and `open_for_mutation` around their `yield`. `runs.new_run(state, "upgrade", ..., upgrade={from, to, steps, backup_dir})` validates against `run.schema.json` now.
- **01-13 (scan):** can use `workspace.find_workspace` and `open_for_mutation(case_root, ctx, "scan")` (session `case_root`, `case`, `state`, `sources`, `runs`), then `runs.new_run(..., scan=<summary with all eleven lists>)`, and `render_index(IndexInputs(case, state, sources, runs + [record]))`. `load_sources` validates against `source.schema.json`, which 01-13 creates.
- **01-15:** can generate the `workspace-contract.md` table from `workspace.CONTRACT_PATHS`.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED

- All 9 created and 3 modified key files exist on disk.
- Commits `164447c`, `05704a1`, `47ffbee`, `b141b13` and `8f87b56` are ancestors of HEAD on `gsd-wt-01-11` (`git rev-list --count 48bb723..HEAD` = 5 before this SUMMARY commit).
- Plan verification: `.venv/bin/python -m pytest -q` gives 803 passed, and `.venv/bin/ruff check .` passes.
- STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched, and nothing was written in the main checkout.
