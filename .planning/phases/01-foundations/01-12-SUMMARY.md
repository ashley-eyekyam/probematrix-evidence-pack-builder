---
phase: 01-foundations
plan: 12
subsystem: workspace-store
tags: [python, crash-injection, os-exit, fcntl, flock, msvcrt, lock, upgrade, d-09, d-19, journal]

# Dependency graph
requires:
  - phase: 01-foundations (01-07)
    provides: Transaction (stage_json/stage_record/stage_text/set_state/commit), recover, pending_journals, state.SCHEMA_VERSION, load_state (older state returned raw)
  - phase: 01-foundations (01-11)
    provides: workspace.open_for_init/open_for_mutation/open_read_only, load_sources, SOURCES_DIR, runs.new_run/run_json_path/load_runs, index.render_index/IndexInputs/SECTION_TITLES, casefile.load_case/CASE_FILE, yamlio.dump_yaml_bytes
provides:
  - epb/faults.py test-only crash seam (checkpoint, CRASH_EXIT_CODE = 97; EPB_TEST_CRASH_AT, EPB_TEST_RECORD_CHECKPOINTS)
  - txn.py checkpoints stage:<i>, pre-manifest, manifest, apply:<i>, cleanup, recover:<i>, and Transaction.stage_backup (raw copies only under .epb/runs/<NNN>/pre-upgrade/)
  - epb/lock.py OS advisory workspace lock (LOCK_FILE, acquire, LockHandle) with a --wait poll and LOCK_TIMEOUT naming the holder
  - epb/upgrade.py D-09 upgrade (UPGRADE_STEPS empty, needs_upgrade, load_snapshot, run_upgrade)
  - sessions that lock, recover and then upgrade (mutating) or warn UPGRADE_PENDING (read-only)
  - tests/epbtest/crash.py (list_checkpoints, assert_workspace_consistent) for 01-14's scan crash test
affects: [01-13 scan (runs inside the locked, upgraded open_for_mutation), 01-14 scan crash test (reuses list_checkpoints and assert_workspace_consistent), 01-15 skill and workspace contract (.epb/lock), 01-16 manual (LOCK_TIMEOUT, WORKSPACE_UPGRADED, UPGRADE_PENDING wording), every later mutating command]

# Actuals (#2632)
actuals:
  tokens: 11298
  tasks: 3
  commits: 5
plan_head_before: 13264a58a7cd116a40df7a8e445bd6fbbb567f40
plan_head_after: 57df8c2e54fc4d55bbf244e32d18910a544b1408

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Crash seam: faults.checkpoint(name) at every transaction step; tests enumerate the names from a recorded real run and crash each with os._exit(97) in a child process"
    - "Session order for every mutating command: take .epb/lock (wait --wait), recover journals, load_state (TOO_NEW / STATE_INVALID stop here), upgrade if older, then do the command's work"
    - "Upgrade steps are pure functions on an in-memory snapshot {state, case, sources} keyed by the version they upgrade from; the runner owns backup, schema_version stamping, run record, INDEX.md and the single commit"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb/faults.py
    - plugin/skills/evidence-pack/scripts/epb/lock.py
    - plugin/skills/evidence-pack/scripts/epb/upgrade.py
    - tests/epbtest/crash.py
    - tests/store/test_crash_resume.py
    - tests/store/test_lock.py
    - tests/store/test_upgrade.py
  modified:
    - plugin/skills/evidence-pack/scripts/epb/txn.py
    - plugin/skills/evidence-pack/scripts/epb/workspace.py

key-decisions:
  - "recover:<i> and apply:<i> fire for every manifest entry, including one found already applied, so a crash during recovery is reachable at recover:0 even after an earlier partial apply"
  - "open_for_init creates .epb/ before taking the lock and .epb/tmp/ only after it, so a LOCK_TIMEOUT on a folder whose .epb/ already exists changes nothing"
  - "The lock file is never deleted or truncated on release; the next holder overwrites it. Deleting lock files races with waiters that already opened the old file"
  - "The upgrade reads case.yaml and source records raw (no schema check) because they follow the older version's schemas; the upgraded versions are validated when staged"
  - "The upgrade also stamps state.plugin_version with the running plugin and records the run summary 'Case folder upgraded from workspace version <a> to <b>.'"
  - "LOCK_TIMEOUT data is {lock: .epb/lock, waited_seconds}; the message names the holder's command and start time when the lock file can be read, else 'Another epb command'"

patterns-established:
  - "Crash coverage for a new command: list_checkpoints(run_epb, args, case) on a dry run, then crash at each point, rerun normally and call assert_workspace_consistent"
  - "Lock tests use a holder subprocess that prints 'locked' after epb.lock.acquire, so the lock is held by a real separate process"

requirements-completed: [WS-06, WS-07, TST-07]

coverage:
  - id: D1
    description: "A real os._exit crash at each of the 17 recorded init checkpoints (stage:0-6, pre-manifest, manifest, apply:0-6, cleanup) is followed by a normal init that exits 0 and leaves a consistent workspace: no journal, every record valid, counters.run equal to the run records, no ID reused, six INDEX.md headings"
    requirement: WS-06
    verification:
      - kind: integration
        ref: "tests/store/test_crash_resume.py#test_init_resumes_after_crash_at_every_checkpoint"
        status: pass
      - kind: integration
        ref: "tests/store/test_crash_resume.py#test_checkpoints_recorded_in_order"
        status: pass
    human_judgment: false
  - id: D2
    description: "A crash during recovery (apply:1, then recover:0) is itself recovered by the next run; a crash before the manifest rename is discarded, one after it rolls forward to the same state.json a clean run writes; a state-only transaction survives a crash at each of its 5 checkpoints"
    requirement: TST-07
    verification:
      - kind: integration
        ref: "tests/store/test_crash_resume.py#test_crash_during_recovery_is_recovered"
        status: pass
      - kind: integration
        ref: "tests/store/test_crash_resume.py#test_pre_and_post_manifest"
        status: pass
      - kind: integration
        ref: "tests/store/test_crash_resume.py#test_state_only_transaction"
        status: pass
    human_judgment: false
  - id: D3
    description: "While another process holds .epb/lock, init --wait 1 exits 4 LOCK_TIMEOUT naming the holder within 5 s and changes nothing; status exits 0 at once; init --wait 20 waits for a release about 2 s later; a SIGKILLed holder frees the lock at once; the lock file holds only pid, command and started; --wait defaults to 60; lock.py never probes or signals a process"
    requirement: WS-07
    verification:
      - kind: integration
        ref: "tests/store/test_lock.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "D-09 upgrade: with a synthetic 1 to 2 step, status only warns UPGRADE_PENDING and changes nothing; the next init warns WORKSPACE_UPGRADED, keeps byte-identical copies of state.json and case.yaml in .epb/runs/002/pre-upgrade/, writes a valid version-2 state, run 002 (upgrade, steps ['1 → 2']) and a re-rendered INDEX.md, once; a missing step is INTERNAL_ERROR and changes nothing; v0.1.0 ships no step"
    requirement: WS-06
    verification:
      - kind: integration
        ref: "tests/store/test_upgrade.py#test_mutating_command_upgrades_with_a_backup"
        status: pass
      - kind: integration
        ref: "tests/store/test_upgrade.py#test_status_only_warns_upgrade_pending"
        status: pass
      - kind: integration
        ref: "tests/store/test_upgrade.py#test_missing_upgrade_step_changes_nothing"
        status: pass
      - kind: unit
        ref: "tests/store/test_upgrade.py#test_shipped_plugin_registers_no_step"
        status: pass
    human_judgment: false
  - id: D5
    description: "A workspace newer than the plugin exits 4 WORKSPACE_TOO_NEW, and invalid JSON or an unknown key in state.json or a damaged case.yaml exits 4 STATE_INVALID (naming .epb/case.yaml), for both status and init"
    requirement: WS-06
    verification:
      - kind: integration
        ref: "tests/store/test_upgrade.py#test_newer_workspace_exits_4"
        status: pass
      - kind: integration
        ref: "tests/store/test_upgrade.py#test_damaged_workspace_exits_4"
        status: pass
    human_judgment: false
  - id: D6
    description: "LOCK_TIMEOUT, WORKSPACE_UPGRADED and UPGRADE_PENDING messages read as plain language for a non-technical investigator"
    verification: []
    human_judgment: true
    rationale: "Wording quality is a judgement no test asserts; the 01-16 manual's troubleshooting chapter quotes these messages"

# Metrics
duration: 9min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 12: Crash safety, the workspace lock and the D-09 upgrade Summary

**`epb init` now survives a real `os._exit` crash at all 17 of its transaction checkpoints, including a crash during recovery itself. Every mutating session holds an OS advisory lock on `.epb/lock`, waiting up to `--wait` (default 60 s) before exiting 4 with `LOCK_TIMEOUT` and naming the holder. A workspace older than the plugin is upgraded on the next mutating command, after a byte-for-byte backup to `.epb/runs/<NNN>/pre-upgrade/`, in one journalled transaction.**

## Performance

- **Duration:** about 9 min
- **Started:** 2026-10-18T10:36:57Z
- **Completed:** 2026-10-18T10:46:00Z
- **Tasks:** 3
- **Files modified:** 9 (7 created, 2 modified)

## Accomplishments

- **Crash seam (`epb/faults.py`).** `checkpoint(name)` records the name when `EPB_TEST_RECORD_CHECKPOINTS` is set, and calls `os._exit(97)` when `EPB_TEST_CRASH_AT` matches. Both variables are read at call time. The seam is test-only and is not mentioned in any user-facing doc.
- **Transaction checkpoints (`txn.py`).** The checkpoints are `stage:<i>` after each blob, `pre-manifest`, `manifest`, `apply:<i>`, `cleanup`, and `recover:<i>` inside `recover()`. `Transaction.stage_backup` stages raw bytes only under `.epb/runs/<NNN>/pre-upgrade/`.
- **Crash tests.** The checkpoint list comes from a recorded real run, not a hand-kept list. Each point gets a fresh case folder, a real crash, a normal rerun and the full consistency check. Every failing point is reported by name, and the test asserts that the number of points tried equals the number recorded.
- **Workspace lock (`epb/lock.py`).** It uses `fcntl.flock` on POSIX and `msvcrt.locking` on Windows, polling until the deadline. The lock file holds `{pid, command, started}` and no host name. Nothing probes a PID and nothing signals a process.
- **Sessions (`workspace.py`).**
  - `open_for_init` and `open_for_mutation` take the lock, recover, call `load_state` (where `WORKSPACE_TOO_NEW` and `STATE_INVALID` stop the command) and upgrade if needed. They release the lock on exit.
  - `open_read_only` takes no lock and only warns `UPGRADE_PENDING`.
- **D-09 upgrade (`epb/upgrade.py`).** `UPGRADE_STEPS` is empty in v0.1.0. `run_upgrade`:
  - collects the steps first, so a missing step is `INTERNAL_ERROR` before anything is staged;
  - backs up `state.json`, `case.yaml` and the source records;
  - applies the steps, stamps `schema_version` (an integer in state and sources, a string in `case.yaml`), records an `upgrade` run and re-renders `INDEX.md`;
  - commits once, then warns `WORKSPACE_UPGRADED` in the planned wording.

## Task Commits

1. **Task 1 (tracer): a real crash injected into `epb init` at every recorded checkpoint, then a clean resume.** `b194e97` (feat). Tracer gate: the run is interactive and end-of-phase, and the verify is automated only. I re-ran it (5 passed) and expansion continued.
2. **Task 2: OS lock with wait for mutating commands.** RED `a9586ea` (test), GREEN `a51693a` (feat).
3. **Task 3: the D-09 upgrade mechanism and the newer or damaged workspace paths.** RED `0c65d6f` (test), GREEN `57df8c2` (feat).

No REFACTOR commits were needed.

## TDD Gate Compliance

- **Task 2 RED (`a9586ea`):**
  - JUnit XML from `pytest --junitxml` was classified by `gsd-tools check tdd-red-evidence` as `RED_EVIDENCE_OK` (`target_test_failed`): 9 tests, 7 failing.
  - Target: `test_second_init_times_out_while_lock_is_held`.
  - Semantic check: following the 01-11 precedent, the RED commit carried an interface-only `lock.py` whose `acquire` raises `NotImplementedError`. The holder process therefore could not take the lock, and every failure traces to that planned gap, not to an import or collection fault. The 2 tests that passed at RED cover the existing 60-second `--wait` default and the source scan for process signalling.
- **Task 3 RED (`0c65d6f`):**
  - `RED_EVIDENCE_OK` (`target_test_failed`): 13 tests, 5 failing.
  - Target: `test_mutating_command_upgrades_with_a_backup`, which failed on `assert 'WORKSPACE_UPGRADED' in ['ALREADY_SET_UP']` because no upgrade ran.
  - The other failures were the missing `UPGRADE_PENDING` warning, `counters.run` still 1, init exiting 0 where a missing step should give 4, and `needs_upgrade` raising `NotImplementedError` from the stub.
  - The 8 tests that passed at RED are the `WORKSPACE_TOO_NEW` and `STATE_INVALID` paths for `status` and `init`, which 01-07's `load_state` and 01-09's `load_case` already enforce. This plan pins them as regression tests.
- **GREEN:** the plan verification (`tests/store tests/workspace tests/launcher`) gives 267 passed and 1 skipped (the opt-in network test). The full suite gives 865 passed and 1 skipped, against 838 before this plan, so the failing file set is empty. `ruff check` and `ruff format --check` are clean.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/faults.py`: the test-only crash and checkpoint-recording seam.
- `plugin/skills/evidence-pack/scripts/epb/txn.py`: the checkpoints at every step, `_apply` taking a checkpoint prefix, and `stage_backup`.
- `plugin/skills/evidence-pack/scripts/epb/lock.py`: the OS advisory lock with wait, `LockHandle`, and the holder JSON.
- `plugin/skills/evidence-pack/scripts/epb/upgrade.py`: `UPGRADE_STEPS`, `needs_upgrade`, `load_snapshot` and `run_upgrade`.
- `plugin/skills/evidence-pack/scripts/epb/workspace.py`: the lock, then recovery, then the upgrade in the mutating sessions, and `UPGRADE_PENDING` in the read-only session.
- `tests/epbtest/crash.py`: `list_checkpoints` and `assert_workspace_consistent`.
- `tests/store/test_crash_resume.py`, `tests/store/test_lock.py`, `tests/store/test_upgrade.py`: the new tests.

## Decisions Made

See `key-decisions` in the frontmatter. In short:

- Recovery checkpoints fire for entries that were already applied as well.
- `.epb/` is created before the lock is taken, and `.epb/tmp/` only after it.
- The lock file is never deleted.
- The upgrade reads the old files without a schema check.
- The upgrade stamps `plugin_version`.
- The `LOCK_TIMEOUT` data shape is `{lock, waited_seconds}`.

## Deviations from Plan

None. The plan was executed as written. Two choices filled gaps in the plan text rather than changing it:

- `load_snapshot` is an extra public helper in `upgrade.py` that builds the planned `{state, case, sources}` snapshot.
- The `recover:<i>` checkpoint fires for every manifest entry. The plan's "after each rolled-forward entry" would otherwise make `recover:0` unreachable after a crash at `apply:1`, the very case the plan's own test exercises.

## Issues Encountered

- My first `lock.py` docstring mentioned `os.kill` by name, which tripped the source-scan test. I reworded the docstring before the GREEN commit. The module never called it.
- **Not tested in this plan:** the backup and rewrite of `.epb/sources/*.json` in `run_upgrade`. The source schema arrives with 01-13, which runs in parallel, so no source record can be written yet. The code stages upgraded sources through `stage_json(..., "source")`, so it validates them once 01-13 is merged. A follow-up test with a source record would be worthwhile after the merge.
- **The lock file churns.** `.epb/lock` is classed `structural` in `CONTRACT_PATHS` and is not in the A2 ignore list, so its contents (pid, command, started) change on every mutating command. A user who keeps `.epb/` in git will see it change on every run. This needs an owner decision, either adding `lock` to `.epb/.gitignore` or reclassifying it, so it was not changed here.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- **01-13 (`scan`):** `open_for_mutation(case_root, ctx, "scan")` now locks, recovers and upgrades before it yields, so scan needs no locking code of its own.
- **01-14:** can extend the crash test to `scan` with `list_checkpoints(run_epb, ["scan", "--json"], case)` and `assert_workspace_consistent(case)`. The consistency check already covers sources, `counters.source`, duplicate `src_id`s and fingerprint targets.
- **01-16 (manual):** the troubleshooting chapter can quote the wording of `LOCK_TIMEOUT`, `WORKSPACE_UPGRADED` and `UPGRADE_PENDING`.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED

- All 7 created and 2 modified key files exist on disk (`git diff --stat 13264a5..HEAD` lists all 9).
- Commits `b194e97`, `a9586ea`, `a51693a`, `0c65d6f` and `57df8c2` are on `gsd-wt-01-12` (`git rev-list --count 13264a5..HEAD` = 5 before this SUMMARY commit).
- Plan verification: `.venv/bin/python -m pytest -q` gives 865 passed and 1 skipped, and `.venv/bin/ruff check .` passes.
- Acceptance: `EPB_TEST_*` appear only in `faults.py`, the tests and `conftest.py`. `lock.py` has no `os.kill`. `UPGRADE_STEPS` ships as `{}`. The backup is asserted byte-identical.
- STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched, and nothing was written in the main checkout.
