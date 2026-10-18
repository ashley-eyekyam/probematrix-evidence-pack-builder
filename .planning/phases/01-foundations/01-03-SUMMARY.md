---
phase: 01-foundations
plan: 03
subsystem: cli
tags: [argparse, launcher, venv, exit-codes, json-envelope, jsonschema, stdlib-only]

requires:
  - phase: 01-foundations (plan 01-01)
    provides: "dev .venv, pytest config with the scripts folder on pythonpath, conftest fixtures run_epb, cli, case_dir, home_dir and the autouse fake home"
provides:
  - "scripts/epb.py: stdlib-only, Python 3.6-parseable entry point calling launcher.main"
  - "epb.__version__ = 0.1.0-dev.1 (single source)"
  - "epb.errors: EXIT_* constants, ERROR_CODES (STATE_INVALID -> 4), WARNING_CODES, EpbError, warning(); docstring catalogue for the troubleshooting chapter"
  - "epb.launcher: version gate (PYTHON_TOO_OLD), fixed D-03 env path, epb-env.json marker, find_python, route, locate_plugin_file, subprocess re-exec with EPB_IN_ENV=1"
  - "epb.cli: EpbArgumentParser (errors -> USAGE), global options before or after the command, Context, Result, envelope, exception-to-exit mapping, CORE_IMPORT_NAMES"
  - "epb.commands.discover(): command-module contract NAME/HELP/MUTATING/add_arguments/run"
  - "epb/schemas/envelope.schema.json (Draft 2020-12)"
  - "tests/epbtest/envkit.make_fake_env(): real venv at the fixed env path under the fake home"
affects: [01-06, 01-07, 01-08, 01-10, 01-11, 01-13, 01-15]

plan_head_before: 7c89b3f7b03d0fee65b2388307bcb8bccc9d80d8
plan_head_after: 31885f590b8acc129426282be81be0184904dd51
actuals:
  tokens: 14000
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Launcher and entry point are stdlib-only and Python 3.6-parseable; an ast feature_version=(3, 6) test guards them"
    - "Every command prints one envelope under --json; usage errors are enveloped because --json is detected before parsing"
    - "Exceptions map to stable codes in cli.main; tracebacks go to stderr only and the envelope names only the exception type"
    - "Command modules import third-party packages inside run() only; a subprocess test blocks every core import name and builds the parser"
    - "Tests that need a private environment build a real venv with envkit.make_fake_env() under the autouse fake home"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb.py
    - plugin/skills/evidence-pack/scripts/epb/__init__.py
    - plugin/skills/evidence-pack/scripts/epb/launcher.py
    - plugin/skills/evidence-pack/scripts/epb/errors.py
    - plugin/skills/evidence-pack/scripts/epb/cli.py
    - plugin/skills/evidence-pack/scripts/epb/commands/__init__.py
    - plugin/skills/evidence-pack/scripts/epb/schemas/envelope.schema.json
    - tests/cli/test_exit_codes.py
    - tests/launcher/test_launcher.py
    - tests/epbtest/envkit.py
  modified: []

key-decisions:
  - "commands.discover() skips modules whose name starts with an underscore, so later plans can add private helper modules to epb/commands/ without them being treated as commands"
  - "launcher.command_token() is the one command-token parser; cli.main uses it so a usage error after a known command still names that command in the envelope"
  - "The envelope schema also enforces ok == (exit_code == 0) and that a failing envelope carries at least one error"
  - "A stale marker and a missing env interpreter with a marker both read as 'out of date'; no marker reads as 'setup has not been run'"

patterns-established:
  - "Command module contract: NAME, HELP, MUTATING, add_arguments(parser), run(args, ctx) -> Result; module-level imports stdlib or epb.errors/launcher/doctor only"
  - "RED evidence for pytest: run with --junitxml into git-ignored scratch/tdd/ and classify with gsd-tools check tdd-red-evidence"

requirements-completed: [PKG-05, PKG-06]

coverage:
  - id: D1
    description: "Stable exit classes 0-4 and error/warning catalogue; STATE_INVALID exits 4; unknown codes rejected"
    requirement: PKG-05
    verification:
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_catalogue_exit_classes"
        status: pass
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_unknown_code_rejected"
        status: pass
    human_judgment: false
  - id: D2
    description: "Usage errors (unknown command, missing command) exit 2 with a USAGE envelope even with --json before the command, end to end through epb.py"
    requirement: PKG-05
    verification:
      - kind: integration
        ref: "tests/cli/test_exit_codes.py#test_usage_error_envelope_subprocess"
        status: pass
      - kind: integration
        ref: "tests/cli/test_exit_codes.py#test_missing_command_is_usage"
        status: pass
    human_judgment: false
  - id: D3
    description: "Exception mapping: INTERNAL_ERROR exit 4 with traceback on stderr only, CORE_PACKAGE_MISSING exit 3, KeyboardInterrupt -> 'The command was interrupted.'"
    requirement: PKG-05
    verification:
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_internal_error_traceback_on_stderr_only"
        status: pass
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_core_package_missing"
        status: pass
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_keyboard_interrupt"
        status: pass
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_internal_error_plain_language"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every cli and launcher envelope validates against envelope.schema.json"
    requirement: PKG-05
    verification:
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_success_envelope_matches_schema"
        status: pass
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_failure_keeps_data_and_warnings"
        status: pass
      - kind: unit
        ref: "tests/cli/test_exit_codes.py#test_launcher_envelopes_match_schema"
        status: pass
    human_judgment: false
  - id: D5
    description: "Launcher: fixed D-03 env path per OS (XDG ignored), marker check, ENV_NOT_SET_UP without a current env, re-exec under the env interpreter passing exit code and output through"
    requirement: PKG-06
    verification:
      - kind: unit
        ref: "tests/launcher/test_launcher.py#test_data_root_linux_ignores_xdg"
        status: pass
      - kind: unit
        ref: "tests/launcher/test_launcher.py#test_stale_marker_is_env_not_set_up"
        status: pass
      - kind: integration
        ref: "tests/launcher/test_launcher.py#test_reexec_passes_through_exit_code_and_output"
        status: pass
      - kind: integration
        ref: "tests/cli/test_exit_codes.py#test_not_in_env_without_setup"
        status: pass
    human_judgment: false
  - id: D6
    description: "Version gate and interpreter discovery: PYTHON_TOO_OLD below 3.11, doctor --setup re-runs under find_python()'s interpreter, fixed candidate order on POSIX and Windows"
    requirement: PKG-06
    verification:
      - kind: unit
        ref: "tests/launcher/test_launcher.py#test_python_too_old_for_normal_command"
        status: pass
      - kind: unit
        ref: "tests/launcher/test_launcher.py#test_python_too_old_setup_uses_found_interpreter"
        status: pass
      - kind: unit
        ref: "tests/launcher/test_launcher.py#test_find_python_posix_order"
        status: pass
      - kind: unit
        ref: "tests/launcher/test_launcher.py#test_find_python_windows_py_launcher"
        status: pass
    human_judgment: false
  - id: D7
    description: "Bootstrap guards: entry files parse as Python 3.6, the parser builds with every core import blocked, nothing under epb/ prompts or reads stdin"
    requirement: PKG-06
    verification:
      - kind: unit
        ref: "tests/launcher/test_launcher.py#test_parses_as_python_36"
        status: pass
      - kind: integration
        ref: "tests/launcher/test_launcher.py#test_bootstrap_imports_stdlib_only"
        status: pass
      - kind: unit
        ref: "tests/launcher/test_launcher.py#test_never_prompts"
        status: pass
    human_judgment: false
  - id: D8
    description: "Launcher behaviour on real Windows and macOS (py launcher, LOCALAPPDATA path, Application Support path, subprocess re-exec stdio)"
    requirement: PKG-06
    verification: []
    human_judgment: true
    rationale: "Only simulated on Linux by patching sys.platform; Windows and macOS are untested until after v0.1.0 (A9, research assumption A2)."

duration: 8min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 03: CLI Shell, Launcher and Exit Codes Summary

**A stdlib-only `epb.py` launcher that gates Python 3.11, finds a newer interpreter for setup, and re-runs commands in a version-keyed private environment at the fixed D-03 path, in front of an argparse CLI. The CLI prints one schema-valid JSON envelope and maps every failure to a stable code with exit classes 0 to 4.**

## Performance

- **Duration:** about 8 min
- **Started:** 2026-10-18T09:21:31Z
- **Completed:** 2026-10-18T09:29:00Z
- **Tasks:** 3 of 3 (Task 1 tracer, Tasks 2 and 3 TDD)
- **Files created:** 10

## Accomplishments

- **Tracer (Task 1).** `epb.py` → `epb.launcher` → `epb.cli` → envelope works end to end. `EPB_IN_ENV=1 .venv/bin/python plugin/skills/evidence-pack/scripts/epb.py --json frobnicate` exits 2 with `errors[0].code == "USAGE"`. Without a set-up environment the launcher exits 3 `ENV_NOT_SET_UP` with `next: ["doctor --setup"]`.
- **Launcher (Task 2).** The private environment lives at `~/.local/share/probematrix-epb/envs/<version>` on Linux, `~/Library/Application Support/...` on macOS and `%LOCALAPPDATA%\probematrix-epb\...` on Windows. It never reads `XDG_DATA_HOME`. An atomic `epb-env.json` marker records `plugin_version` and `requirements_sha256`, and a mismatch reports "out of date". `doctor` runs in the current interpreter. Every other command re-runs under the environment's Python through `subprocess`, and the exit code and output pass through unchanged, which a real-venv test proves.
- **Version gate.** Below 3.11, normal commands exit 3 `PYTHON_TOO_OLD` and point to the manual's "Install Python" chapter. `doctor --setup` re-runs itself under the first fixed-name candidate that reports 3.11 or newer.
- **Error contract (Task 3).** `envelope.schema.json` closes every object except `data`. In `cli.main`, an unexpected exception becomes `INTERNAL_ERROR` (exit 4). Its traceback goes to stderr only, and the envelope names only the exception type, never the message. A missing core package becomes `CORE_PACKAGE_MISSING` (exit 3), and Ctrl-C becomes "The command was interrupted."
- **Guards that protect later plans.** One subprocess test blocks every import name from `plugin/requirements.txt` and still builds the parser with all discovered commands. An `ast` test forbids `input()` and `sys.stdin` anywhere under `epb/` (D-15). A mapping test fails if a new requirement is added without its import names.

## Task Commits

1. **Task 1: Tracer, epb.py → launcher → cli → envelope.** `d5297bb` (feat)
2. **Task 2: Complete the launcher.** RED `ac47c9e` (test), GREEN `6c91051` (feat)
3. **Task 3: Envelope schema, exception mapping, bootstrap guard.** RED `7f8ad38` (test), GREEN `31885f5` (feat)

No refactor commits; neither GREEN step needed cleanup.

## TDD Gate Compliance

- **Task 2 RED:** 21 of 25 new launcher tests failed. The target `test_route` failed with `AttributeError: module 'epb.launcher' has no attribute 'route'`. The JUnit XML report went through `gsd-tools check tdd-red-evidence` and returned `RED_EVIDENCE_OK` (`target_test_failed`). Semantic assessment: the test module collected and imported cleanly, and the target ran and failed only because the planned public function did not exist yet. The 4 passing tests cover behaviour Task 1 already shipped (the missing-env message) and the 3.6 parse guard. GREEN: 30 passed.
- **Task 3 RED:** the target `test_keyboard_interrupt` failed on its explicit `pytest.fail("KeyboardInterrupt escaped epb.cli.main")`, and the classifier returned `RED_EVIDENCE_OK`. Semantic assessment: the target ran and failed on the planned behaviour. The schema-dependent tests errored at fixture setup because the schema file did not exist yet, which is expected. `test_bootstrap_imports_stdlib_only` and `test_never_prompts` passed at RED, as expected, because they guard properties that Task 1's code already had. GREEN: 45 passed.
- The gate log shows each `test(01-03)` commit before its `feat(01-03)` commit. The evidence records sit in the git-ignored `scratch/tdd/`.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb.py`: stdlib-only entry point, old-syntax-safe
- `plugin/skills/evidence-pack/scripts/epb/__init__.py`: `__version__ = "0.1.0-dev.1"`
- `plugin/skills/evidence-pack/scripts/epb/launcher.py`: version gate, env paths, marker, interpreter discovery, routing, re-exec
- `plugin/skills/evidence-pack/scripts/epb/errors.py`: exit constants, error and warning catalogues, `EpbError`, `warning()`, and a docstring with each code's plain-language meaning
- `plugin/skills/evidence-pack/scripts/epb/cli.py`: argparse shell, `Context`, `Result`, envelope, exception mapping, `CORE_IMPORT_NAMES`
- `plugin/skills/evidence-pack/scripts/epb/commands/__init__.py`: `discover()` and the documented command-module contract
- `plugin/skills/evidence-pack/scripts/epb/schemas/envelope.schema.json`: Draft 2020-12 envelope schema
- `tests/cli/test_exit_codes.py`: 17 tests (catalogue, usage, env gate, schema, exception mapping)
- `tests/launcher/test_launcher.py`: 28 tests (paths, marker, re-exec, version gate, discovery, routing, plugin files, the 3.6 parse, bootstrap and never-prompts guards)
- `tests/epbtest/envkit.py`: `make_fake_env()`

## Decisions Made

- `commands.discover()` skips `_`-prefixed modules, so helper modules can live in `epb/commands/`.
- `launcher.command_token()` is shared with `cli.main`, so a usage error after a known command still sets `command` in the envelope. An unknown command gives `command: null`.
- The schema also enforces `ok` ⇔ `exit_code == 0` and requires at least one error when `ok` is false. Both rules follow from the envelope contract and cost nothing.
- The `KeyboardInterrupt` hint is "Run the command again when you are ready." It makes no recovery claim, because journal recovery arrives in a later plan.

## Deviations from Plan

None. The plan was executed as written. The additions under "Decisions Made" are within the builder's discretion and change no contract the plan names.

## Issues Encountered

None.

## Known Stubs

None. With no command modules yet, the usage message reads `choose from )`; plans 01-07, 01-08, 01-11 and 01-13 add `doctor`, `init`, `status` and `scan`.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Later plans add commands as new files in `epb/commands/` following the contract in its docstring. Third-party imports belong inside `run()`. `test_bootstrap_imports_stdlib_only` fails otherwise.
- Plan 01-10 (`doctor --setup`) should write the marker with `launcher.write_marker(env, launcher.marker_record(version))` and report `data.launch = [env_python, epb.py]`.
- Plan 01-06 manifests must use the version `0.1.0-dev.1` from `epb/__init__.py`.
- On Windows and macOS the launcher has been simulated only (D8, human judgment).

## Self-Check: PASSED

- All 10 key files exist on disk.
- Commits `d5297bb`, `ac47c9e`, `6c91051`, `7f8ad38` and `31885f5` are ancestors of HEAD on `phase-01-foundations`. The measured count since `7c89b3f` is 5.
- Plan verification: `.venv/bin/python -m pytest -q tests/cli tests/launcher` passes 45. `.venv/bin/ruff check .` and `ruff format --check .` exit 0. The full suite passes 53.
- Acceptance: the `EPB_IN_ENV=1 ... --json frobnicate` call exits 2 with USAGE. The 3.6 `ast.parse` of the three entry files exits 0. `~/.local/share/probematrix-epb` does not exist on the real machine after the run.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
