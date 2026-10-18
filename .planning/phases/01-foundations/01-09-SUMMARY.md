---
phase: 01-foundations
plan: 09
subsystem: workspace-store
tags: [python, pyyaml, yaml-1.1, zoneinfo, jsonschema, case-yaml, init, d-15]

# Dependency graph
requires:
  - phase: 01-foundations (01-07)
    provides: Transaction.stage_record/set_state, recover(), new_state/load_state, schema.validate/check, fsio.utc_now_iso, the epb init command
  - phase: 01-foundations (01-03)
    provides: EpbError codes BAD_ARGUMENT, WORKSPACE_EXISTS, TIMEZONE_REQUIRED, STATE_INVALID and the ALREADY_SET_UP warning
provides:
  - epb/yamlio.py strict text-only YAML (TextLoader, YamlTextError, assert_text_only, load_text_yaml, dump_yaml, dump_yaml_bytes)
  - schemas/case.schema.json, the closed case.yaml contract with every scalar as text
  - epb/casefile.py (CASE_FILE, CaseSettings, derive_slug, derive_prefix, detect_timezone, validate_timezone, resolve_settings, new_case_record, load_case, differences)
  - epb init --title/--slug/--prefix/--timezone writing .epb/case.yaml in the same transaction as state.json, with fixed-once re-run rules
affects: [01-10 skill and INDEX.md, 01-11 workspace layout (same init transaction), 01-12 locking and upgrade, phase 2+ commands that read case settings (ID prefix, timezone, slug in file names)]

# Actuals (#2632)
actuals:
  tokens: 10613
  tasks: 2
  commits: 3
plan_head_before: 811c33013f9390cc4104ef30dbba9ea9a861b3d7
plan_head_after: 8e0f5fc64b84c59df3fc11a944b9f20e5ef98e4e

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Strict YAML: a SafeLoader subclass with yaml_implicit_resolvers = {} (class-level copy), a mapping constructor that refuses duplicate and non-text keys, then a text-only walk that catches explicit tags such as !!int"
    - "Persisted YAML records go through Transaction.stage_record(rel, obj, schema, yamlio.dump_yaml_bytes), so they are schema-checked at staging like JSON records"
    - "Usage errors are raised by resolve_settings before any staging, so a failed init leaves no case.yaml and no state.json"
    - "Timezone detection is injectable (environ, etc_timezone, localtime) and never uses datetime.astimezone()"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb/yamlio.py
    - plugin/skills/evidence-pack/scripts/epb/casefile.py
    - plugin/skills/evidence-pack/scripts/epb/schemas/case.schema.json
    - tests/core/test_yamlio.py
    - tests/workspace/test_init_defaults.py
  modified:
    - plugin/skills/evidence-pack/scripts/epb/commands/init.py
    - plugin/skills/evidence-pack/scripts/epb/errors.py
    - tests/workspace/test_init.py

key-decisions:
  - "WORKSPACE_EXISTS carries data.fields with the differing flag names (title, slug, prefix, timezone) and the message lists them as --flags"
  - "A re-run with --title compares the stripped, NFC-normalised title, so whitespace or a decomposed form of the same title is not a difference"
  - "validate_timezone also refuses localtime, posixrules and Factory, which ZoneInfo opens but are not IANA zone names"
  - "An explicit --slug that is a Windows reserved name (con, prn, aux, nul, com1-9, lpt1-9) is refused; only derived slugs get the -case suffix"
  - "init on a set-up folder now loads state.json (load_state) and case.yaml before anything else, so damage to either exits 4 STATE_INVALID instead of ALREADY_SET_UP"
  - "The ALREADY_SET_UP re-run also reports data.case with the stored settings, so the skill can show them"

patterns-established:
  - "Case settings are fixed once set up: init never rewrites case.yaml"
  - "Every case.yaml scalar is a string, including numbers such as draft_warning_days '7'"

requirements-completed: [WS-01, WS-08]

coverage:
  - id: D1
    description: "epb init --title [--slug] [--prefix] [--timezone] writes .epb/case.yaml with all eleven required keys in the same transaction as state.json, and it re-loads through load_case as exact text"
    requirement: WS-01
    verification:
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_init_writes_case_yaml_from_flags"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_case_yaml_starts_with_text_schema_version"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "D-15 defaults without prompting: slug from the folder name, prefix from the title's initials, timezone from TZ, /etc/timezone or the /etc/localtime link; non-ASCII titles stored in NFC with ASCII defaults (olpumpe-storfall-2026, OS)"
    requirement: WS-01
    verification:
      - kind: unit
        ref: "tests/workspace/test_init_defaults.py#test_derive_slug"
        status: pass
      - kind: unit
        ref: "tests/workspace/test_init_defaults.py#test_derive_prefix"
        status: pass
      - kind: unit
        ref: "tests/workspace/test_init_defaults.py#test_detect_timezone_falls_back_to_the_localtime_link"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_defaults_come_from_folder_title_and_system_zone"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_title_is_stored_in_nfc_form"
        status: pass
    human_judgment: false
  - id: D3
    description: "Validation that writes nothing on failure: missing or blank --title, bad --slug, --prefix or --timezone exit 2 BAD_ARGUMENT; no detectable zone exits 2 TIMEZONE_REQUIRED; a title with no ASCII letters needs --prefix"
    requirement: WS-01
    verification:
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_init_without_title_is_bad_argument"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_init_with_a_bad_setting_is_bad_argument"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_init_without_a_detectable_timezone_is_timezone_required"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_title_without_ascii_letters_needs_a_prefix"
        status: pass
    human_judgment: false
  - id: D4
    description: "Re-run rules: no flags or equal flags exit 0 ALREADY_SET_UP and change no byte of case.yaml or state.json; differing flags exit 2 WORKSPACE_EXISTS naming them"
    requirement: WS-01
    verification:
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_rerun_with_no_or_equal_flags_changes_nothing"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_rerun_with_different_flags_is_workspace_exists"
        status: pass
    human_judgment: false
  - id: D5
    description: "Strict text-only YAML: the fifteen YAML 1.1 boundary values round-trip as text, duplicate keys and non-text explicit tags are rejected, output is UTF-8 with non-ASCII kept literally"
    requirement: WS-08
    verification:
      - kind: unit
        ref: "tests/core/test_yamlio.py"
        status: pass
    human_judgment: false
  - id: D6
    description: "A missing, empty, comment-only, non-UTF-8, non-text or schema-invalid case.yaml (and a damaged state.json) in a set-up folder exits 4 STATE_INVALID naming .epb/case.yaml"
    requirement: WS-08
    verification:
      - kind: unit
        ref: "tests/workspace/test_init_defaults.py#test_load_case_refuses_damage"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_rerun_on_a_damaged_case_yaml_is_state_invalid"
        status: pass
      - kind: integration
        ref: "tests/workspace/test_init_defaults.py#test_rerun_on_a_damaged_state_json_is_state_invalid"
        status: pass
    human_judgment: false

# Metrics
duration: 7min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 09: case.yaml settings and strict text-only YAML Summary

**`epb init --title` now writes `.epb/case.yaml` in the same transaction as `state.json`. It derives the slug, ID prefix and IANA timezone without prompting, validates every setting before anything is written, refuses changes to the settings after setup, and reads the file back through a YAML loader that keeps every value as exact text.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-18T10:10:37Z
- **Completed:** 2026-10-18T10:17:44Z
- **Tasks:** 2
- **Files modified:** 8 (5 created, 3 modified)

## Accomplishments

- `epb/yamlio.py`: `TextLoader` resolves every plain scalar to a string. It refuses duplicate keys and keys that are not text, and a walk afterwards rejects `!!int`, `!!timestamp`, `!!binary` and other explicit tags. `dump_yaml` is deterministic and keeps non-ASCII literally. `yaml.SafeLoader` itself is unchanged.
- `schemas/case.schema.json` (`epb:case`) is a closed contract. It has eleven required string fields plus the optional `case_number`, so later phases need no migration.
- `epb/casefile.py` implements the D-15 defaults:
  - `derive_slug`: ASCII, at most 40 characters, Windows reserved names get `-case`.
  - `derive_prefix`: initials, or the first three letters of a one-word title.
  - `detect_timezone`: `TZ`, then `/etc/timezone`, then the `/etc/localtime` link. Abbreviations such as `IST` are ignored.
  - `resolve_settings` validates every flag, and `load_case` is guarded: any damage is `STATE_INVALID`.
- `epb init` stages `case.yaml` before `set_state`, so both files commit together. On a set-up folder it loads `state.json` and `case.yaml` and compares the flags. Equal or absent flags give `ALREADY_SET_UP` and change no byte. Different flags give `WORKSPACE_EXISTS` with `data.fields`.

## Task Commits

1. **Task 1: Tracer, init flags → case.yaml in the init transaction → read back through the strict loader.** `fe84b58` (feat). The tracer gate re-ran its automated verify (8 passed) and then expansion continued. The mode was interactive, `end-of-phase`, with an automated-only verify.
2. **Task 2: D-15 defaults, validation, re-run rules and the strict-YAML edge corpus.** RED `4742b06` (test), GREEN `8e0f5fc` (feat). No REFACTOR commit was needed.

## TDD Evidence

- **Task 2 RED:** JUnit XML from `pytest --junitxml` was classified by `gsd-tools check tdd-red-evidence` as `RED_EVIDENCE_OK` (142 tests, 66 failing). The target was `test_init_without_title_is_bad_argument`.
  - **Semantic check:** the target ran and failed on its planned assertion, `assert 4 == 2`. Without `--title`, the tracer passed `None` settings to the case schema and exited 4 `RECORD_INVALID` instead of 2 `BAD_ARGUMENT`.
  - **Other failures:** an `AttributeError` for each function that did not exist yet (`derive_slug`, `derive_prefix`, `detect_timezone`, `validate_timezone`, `differences`), plus assertion failures for the missing re-run and validation behaviour. All 142 tests were collected, with no import or collection errors.
  - **The 76 that passed at RED** cover behaviour the Task 1 tracer already delivered: the YAML corpus and rejections in `yamlio`, `load_case` refusing damage, writing `case.yaml` from flags, and the plain `ALREADY_SET_UP` re-run.
- **GREEN:** the plan verification (`tests/core tests/workspace tests/store tests/launcher`) gives 207 passed. The full suite gives 611 passed (469 after 01-07). `ruff check` and `ruff format --check` are clean, and the 01-03 bootstrap guard (`test_bootstrap_imports_stdlib_only`) passes, so `init.py` still imports only stdlib and `epb.errors` at module level.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/yamlio.py`: the strict text-only loader and the deterministic dumper.
- `plugin/skills/evidence-pack/scripts/epb/casefile.py`: case settings defaults, validation, record creation, guarded load and re-run comparison.
- `plugin/skills/evidence-pack/scripts/epb/schemas/case.schema.json`: the case.yaml contract.
- `plugin/skills/evidence-pack/scripts/epb/commands/init.py`: the new flags, the case.yaml staging and the re-run rules.
- `plugin/skills/evidence-pack/scripts/epb/errors.py`: docstring only. `WORKSPACE_EXISTS`, `ALREADY_SET_UP` and `STATE_INVALID` now describe what `init` actually does.
- `tests/core/test_yamlio.py`: the YAML corpus and rejection tests.
- `tests/workspace/test_init_defaults.py`: tests for defaults, timezone detection, validation, encoding, re-runs and damaged files.
- `tests/workspace/test_init.py`: 01-07's tests now pass the case flags and expect `created == [case.yaml, state.json]`.

## Decisions Made

See `key-decisions` in the frontmatter. In short:

- `WORKSPACE_EXISTS` names the differing flags in its message and in `data.fields`.
- Titles are compared in stripped NFC form.
- `localtime`, `posixrules` and `Factory` are not accepted as timezones.
- An explicit reserved `--slug` is refused.
- A re-run loads both state files first.
- A re-run reports the stored settings in `data.case`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 01-07's `test_init.py` now passes the case flags**
- **Found during:** Task 1
- **Issue:** The acceptance criterion allowed `test_init.py` to change only where `data.created` changes. But `init` on a new folder now requires `--title`. In the tracer it also required the other three flags, because the defaults only arrive in Task 2. Without the flags, every test in the file would fail.
- **Fix:** A shared `INIT` argument list passes `--title`, `--slug`, `--prefix` and `--timezone UTC`. No assertion was weakened, and `created` now expects `[.epb/case.yaml, .epb/state.json]`.
- **Files modified:** `tests/workspace/test_init.py`
- **Verification:** all 5 tests in the file pass.
- **Committed in:** `fe84b58`

**2. [Rule 2 - Missing critical] `validate_timezone` refuses non-zone files in the zoneinfo folder**
- **Found during:** Task 2
- **Issue:** `zoneinfo.ZoneInfo` accepts `localtime`, `posixrules` and `Factory` (checked on this machine). A `--timezone localtime`, or a `TZ` or `/etc/localtime` value naming one of them, would have stored a name that is not an IANA zone.
- **Fix:** `_is_zone` rejects these three names. The test covers each one.
- **Files modified:** `epb/casefile.py`, `tests/workspace/test_init_defaults.py`
- **Committed in:** `8e0f5fc`

**3. [Rule 2 - Missing critical] An explicit `--slug` that Windows reserves is refused (T-01-23)**
- **Found during:** Task 2
- **Issue:** The plan suffixes reserved names only for derived slugs. `--slug con` would still have produced an unusable workbook file name on Windows.
- **Fix:** `_resolve_slug` refuses reserved names with `BAD_ARGUMENT`.
- **Files modified:** `epb/casefile.py`
- **Committed in:** `8e0f5fc`

**4. [Rule 2 - Carry-over from 01-07] The re-run checks state.json as well as case.yaml**
- **Found during:** Task 2
- **Issue:** 01-07 left `init` checking only that `state.json` exists, so a damaged state file got `ALREADY_SET_UP`. This plan's re-run path is in scope.
- **Fix:** The re-run calls `load_state()` before `load_case()`. Damage now exits 4 `STATE_INVALID`, and a newer workspace gives `WORKSPACE_TOO_NEW`.
- **Files modified:** `epb/commands/init.py`
- **Verification:** `test_rerun_on_a_damaged_state_json_is_state_invalid`
- **Committed in:** `8e0f5fc`

**5. [Rule 2 - Carry-over from 01-07] The error-code docstring matches the behaviour**
- **Found during:** Task 2
- **Issue:** The `epb/errors.py` docstring feeds the manual's troubleshooting chapter, and three entries were wrong:
  - `ALREADY_SET_UP` described only the private environment.
  - `WORKSPACE_EXISTS` described an init on any set-up folder, which this plan's design does not do.
  - `STATE_INVALID` named only `state.json`.
- **Fix:** All three now describe what `init` does. The file is outside `files_modified`, but no concurrent plan touches it (01-08 lists only doctor files), and only the docstring changed.
- **Files modified:** `epb/errors.py`
- **Committed in:** `8e0f5fc`

**6. [Rule 1 - Test bug] The slug-cap test now exercises the trailing-hyphen strip**
- **Found during:** Task 2 GREEN
- **Issue:** The RED input's 40-character cut fell inside a word, so the test never checked that a trailing hyphen is removed.
- **Fix:** The input now puts a hyphen at position 40, and the test asserts the exact 39-character result.
- **Files modified:** `tests/workspace/test_init_defaults.py`
- **Committed in:** `8e0f5fc`

---

**Total deviations:** 6 auto-fixed: 1 blocking, 4 missing-critical (two of them 01-07 carry-overs) and 1 test bug.
**Impact on plan:** Each change closes a gap in the plan's own must-haves, its threat mitigations or the 01-07 carry-over. The only interface additions are `data.fields` on `WORKSPACE_EXISTS` and `data.case` on the `ALREADY_SET_UP` re-run. There is no scope creep.

## Issues Encountered

- **Timezone detection on Windows and macOS:** `detect_timezone` reads only `TZ`, `/etc/timezone` and `/etc/localtime`. On Windows it therefore usually finds nothing, and `init` exits 2 `TIMEZONE_REQUIRED` unless the skill passes `--timezone`. macOS uses an `/etc/localtime` link into `zoneinfo/`, so it should work, but this was not tested here. This matches research Pattern 6 and Linux-only CI. The skill (01-10) should always propose a timezone and pass it explicitly.
- **WORKSPACE_EXISTS is now used**, so the 01-07 note that it was unused no longer applies.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- 01-10 (skill) can ask only for the title. It can read the proposed slug, prefix and timezone from `data.case` in the `init --json` envelope and confirm them in one line (D-15). The skill should always pass `--timezone` on Windows.
- 01-11 can stage `.epb/.gitignore`, `.gitattributes` and `INDEX.md` in the same `init` transaction, after `case.yaml` and before `set_state`.
- Later phases read `id_prefix`, `timezone` and `slug` through `casefile.load_case()`. Every value comes back as a string.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*

## Self-Check: PASSED

- All 5 created and 3 modified key files exist on disk.
- Commits `fe84b58`, `4742b06` and `8e0f5fc` are ancestors of HEAD on `gsd-wt-01-09`.
- STATE.md, ROADMAP.md and REQUIREMENTS.md are untouched, and nothing was written in the main checkout.
