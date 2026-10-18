---
phase: 01-foundations
plan: 08
subsystem: cli
tags: [doctor, stdlib-only, subprocess, git, sync-folders, d-17, pkg-07]

requires:
  - phase: 01-foundations (plan 01-03)
    provides: "launcher (env_dir, env_python, marker_is_current, locate_plugin_file, epb_script, data_root, BOOTSTRAP_COMMANDS routes doctor to the current interpreter), epb.errors (ENV_NOT_SET_UP, CORE_PACKAGE_MISSING, SYNC_FOLDER, GIT_* warning codes), epb.cli Result/Context, tests/epbtest/envkit.make_fake_env"
provides:
  - "epb doctor command (MUTATING = False): full machine report under --json, the D-17 checklist for people; exit 0 when ready, 3 ENV_NOT_SET_UP / CORE_PACKAGE_MISSING otherwise, always with the report"
  - "epb.doctor.tools: ToolSpec, ExtraSpec, REGISTRY (7z, ffmpeg, tesseract, soffice, pandoc, git), EXTRAS (email, media, docs), os_id(), OS_IDS"
  - "epb.doctor.probes: probe_tool, core_requirements, probe_environment, env_packages, collect"
  - "epb.doctor.report: render_human (pure function of the report), current_os, command_text, HEADINGS"
  - "epb.doctor.syncfolders: PROVIDERS, SyncHit, check(path, home=, environ=, platform=), warning_for(hit) -> SYNC_FOLDER"
  - "epb.doctor.gitcheck: check(case_root, which=, run=) -> GIT_TRACKS_PRIVATE / GIT_PRIVATE_NOT_IGNORED / GIT_UNAVAILABLE"
affects: [01-10, 01-11, 01-15, 01-16]

plan_head_before: 535fcfe94f7fd3af4e698f8d28987e1478d71825
plan_head_after: 2a4978110770380ba93b81215bba0794b385be0c
actuals:
  tokens: 18000
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Doctor is a data-driven registry: adding a tool, extra or sync provider is one row; output order is registry order"
    - "External programs are run only as argv lists with a timeout and read with a fixed regex; never a shell"
    - "Package versions are read inside the private environment by running its interpreter with a short importlib.metadata script, so doctor itself stays stdlib-only"
    - "render_human reads os and home from the report, never the live system, so the checklist is a pure, golden-testable function"
    - "Folder checks (sync, git) take injectable home/environ/platform or which/run, so tests never touch the real home or a real repository outside tmp_path"

key-files:
  created:
    - plugin/skills/evidence-pack/scripts/epb/commands/doctor.py
    - plugin/skills/evidence-pack/scripts/epb/doctor/__init__.py
    - plugin/skills/evidence-pack/scripts/epb/doctor/tools.py
    - plugin/skills/evidence-pack/scripts/epb/doctor/probes.py
    - plugin/skills/evidence-pack/scripts/epb/doctor/report.py
    - plugin/skills/evidence-pack/scripts/epb/doctor/syncfolders.py
    - plugin/skills/evidence-pack/scripts/epb/doctor/gitcheck.py
    - tests/doctor/test_probes.py
    - tests/doctor/test_syncfolders.py
    - tests/doctor/test_gitcheck.py
  modified: []

key-decisions:
  - "The report carries two keys beyond the planned list: home (so render_human can abbreviate folders to ~ without reading the live system) and setup_command (the argv the checklist and the error hint quote for doctor --setup)"
  - "Folders are shown with ~ but commands keep absolute paths, so every command in the checklist can be copied as is; parts containing spaces are double-quoted"
  - "The short checklist tells the user to ask the agent to install an extra; the exact pip command (env python -m pip install --uploaded-prior-to P14D -r <file>) is shown under --verbose and is always in the JSON"
  - "A core package is ok only when installed and, for a plain >=X.Y pin, at least that version; anything the stdlib cannot compare is accepted"
  - "A generic CloudStorage provider ('a cloud sync service') catches macOS File Provider folders of services not in the table, and is reported only when no named provider matched"
  - "Google Drive on Linux is detected from the GVFS mount component name (google-drive:...), so detection needs no listing of /run/user"
  - "On the human error path the checklist is the error message and the hint is omitted, because What to do next already carries the setup command; under --json the hint is kept"
  - "Git is called with GIT_OPTIONAL_LOCKS=0; a git that cannot be run falls back to the .git walk-up and warns GIT_UNAVAILABLE with 'git could not be run'"

patterns-established:
  - "Doctor registry rows: ToolSpec(id, label, names, version_args, version_regex, enables, in_use, install{linux,macos,windows}, extra_paths{os: paths})"
  - "Detection modules reused by init (plan 01-11): syncfolders.check + warning_for, gitcheck.check, both returning envelope warning dicts"

requirements-completed: [PKG-07, WS-11, WS-12]

coverage:
  - id: D1
    description: "Data-driven registry of six optional tools (7-Zip via 7z/7za/7zz plus the Windows install folder, ffmpeg, Tesseract, LibreOffice, pandoc, git) and three extras, each with per-OS install commands, in fixed order"
    requirement: PKG-07
    verification:
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_registry_rows_are_complete"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_seven_zip_row"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_version_regex_reads_real_banner"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_registry_order"
        status: pass
    human_judgment: false
  - id: D2
    description: "Probes: alternative names and the Windows fallback folder are found; a crashed or unreadable version probe is found with version None; argv-only with a 10 s timeout"
    requirement: PKG-07
    verification:
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_probe_alternative_name"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_probe_windows_extra_path"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_crashed_version_probe_is_found_without_version"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_probe_finds_first_name_and_reads_version"
        status: pass
    human_judgment: false
  - id: D3
    description: "epb doctor exits 3 ENV_NOT_SET_UP before setup and 0 after, with the full report, launch paths and every core package installed; missing optional tools never change the exit code"
    requirement: PKG-07
    verification:
      - kind: integration
        ref: "tests/doctor/test_probes.py#test_doctor_json_before_setup"
        status: pass
      - kind: integration
        ref: "tests/doctor/test_probes.py#test_doctor_json_after_setup"
        status: pass
      - kind: integration
        ref: "tests/doctor/test_probes.py#test_missing_optional_tools_never_change_the_exit_code"
        status: pass
    human_judgment: false
  - id: D4
    description: "D-17 checklist: exactly Ready / Optional, not installed / What to do next, this OS's install command only unless --verbose, deterministic across runs"
    requirement: PKG-07
    verification:
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_render_has_exactly_three_headings_in_order"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_render_optional_line_uses_this_os_only"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_probes.py#test_two_collects_render_identically"
        status: pass
      - kind: integration
        ref: "tests/doctor/test_probes.py#test_doctor_human_after_setup"
        status: pass
    human_judgment: false
  - id: D5
    description: "Checklist wording reads as plain language for a non-technical investigator"
    requirement: PKG-07
    verification: []
    human_judgment: true
    rationale: "Wording quality and whether the checklist is short enough are judgements no test asserts; the manual (plan 01-16) will quote it"
  - id: D6
    description: "Sync-folder detection for Dropbox (info.json, guarded), OneDrive, Google Drive, iCloud Drive and the whole-component name heuristic; one hit per provider; SYNC_FOLDER warning"
    requirement: WS-12
    verification:
      - kind: unit
        ref: "tests/doctor/test_syncfolders.py#test_dropbox_personal_path_from_info_json"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_syncfolders.py#test_name_heuristic"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_syncfolders.py#test_name_heuristic_needs_a_whole_component"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_syncfolders.py#test_provider_reported_once"
        status: pass
    human_judgment: false
  - id: D7
    description: "Read-only git check: tracked and unignored .epb/private at the repo root and nested (space and non-ASCII path), .git unchanged, GIT_UNAVAILABLE without git, argv with -C"
    requirement: WS-11
    verification:
      - kind: integration
        ref: "tests/doctor/test_gitcheck.py#test_tracked_and_not_ignored"
        status: pass
      - kind: integration
        ref: "tests/doctor/test_gitcheck.py#test_git_folder_is_unchanged"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_gitcheck.py#test_no_git_binary_inside_a_repository"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_gitcheck.py#test_git_argv_uses_dash_c_and_never_a_shell"
        status: pass
      - kind: unit
        ref: "tests/doctor/test_gitcheck.py#test_source_uses_only_read_only_subcommands"
        status: pass
    human_judgment: false
  - id: D8
    description: "doctor adds sync and git warnings to the envelope and data.folder only inside a case folder"
    requirement: WS-12
    verification:
      - kind: integration
        ref: "tests/doctor/test_syncfolders.py#test_doctor_warns_inside_a_case_folder"
        status: pass
      - kind: integration
        ref: "tests/doctor/test_syncfolders.py#test_doctor_checks_nothing_outside_a_case_folder"
        status: pass
      - kind: integration
        ref: "tests/doctor/test_gitcheck.py#test_doctor_reports_git_warning_in_a_case_folder"
        status: pass
    human_judgment: false
  - id: D9
    description: "Sync-folder heuristics other than Dropbox info.json behave correctly on real macOS and Windows machines"
    requirement: WS-12
    verification: []
    human_judgment: true
    rationale: "Research assumption A5; macOS and Windows are not tested until after v0.1.0 (Linux-only CI)"

duration: 11min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 08: epb doctor Summary

**`epb doctor` is a stdlib-only health check. A data-driven registry covers six optional tools (7-Zip found as 7z, 7za or 7zz) and three extras. Package versions are read through the private environment's own interpreter. The output is the D-17 checklist (Ready / Optional, not installed / What to do next) or a full JSON report, and the exit code is 0 or 3. Inside a case folder, read-only detectors warn about sync folders and git.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-18T10:01:01Z
- **Completed:** 2026-10-18T10:12:30Z
- **Tasks:** 2
- **Files modified:** 10 (all new)

## Accomplishments

- `epb doctor` works before first-time setup, in whatever Python launched `epb.py`. The 01-03 bootstrap test still passes with the doctor command importable. Doctor reports Python, the private environment (path, current, launch argv, other versions), every core package with its installed version, every optional tool with its version and per-OS install commands, and every optional extra with its licence and install command.
- The human output is exactly three groups. Each lists this OS's install command only, and `--verbose` adds versions, all three OSes' commands and other environment versions. Before setup, the checklist becomes the error message, so a person sees it on stderr with exit 3.
- `syncfolders.check` and `gitcheck.check` return envelope warning dicts that `init` (plan 01-11) can reuse unchanged. Doctor runs them only when `<case>/.epb` exists.

## Task Commits

1. **Task 1 (tracer): epb doctor end to end.** `c11b3b5` (test, RED), `4a9b66f` (feat, GREEN)
2. **Task 2: Sync-folder and git warnings.** `15477f8` (test, RED), `2a49781` (feat, GREEN)

No refactor commit; none was needed.

## TDD Gate Compliance

- **Task 1 RED:** `c11b3b5`. Command: `.venv/bin/python -m pytest -q tests/doctor/test_probes.py --junitxml=scratch/tdd/red-01-08-t1.xml`. Result: 49 failed, 0 passed, exit 1. The target `test_doctor_json_before_setup` failed with `assert 2 == 3`, because `doctor` was not yet a command and the CLI answered USAGE. `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` (`target_test_failed`). Semantic assessment: the module collected cleanly against interface-only stubs (dataclass shells, empty REGISTRY/EXTRAS, functions raising NotImplementedError). Every failure was an assertion or a NotImplementedError on planned behaviour, with no import or collection fault. GREEN: 79 passed with tests/launcher.
- **Task 2 RED:** `15477f8`. Command: `.venv/bin/python -m pytest -q tests/doctor/test_syncfolders.py tests/doctor/test_gitcheck.py --junitxml=scratch/tdd/red-01-08-t2.xml`. Result: 50 failed, 18 passed, exit 1. The target `test_dropbox_personal_path_from_info_json` failed with `assert [] == ['Dropbox']`. `RED_EVIDENCE_OK` (`target_test_failed`). Semantic assessment: the stubs returned no hits and no warnings. The 18 passing tests are the negative cases (damaged info.json, whole-component negatives, outside a repo, no git outside a repo), which correctly expect an empty result. GREEN: 147 passed for tests/doctor plus tests/launcher.
- Both RED commits include small interface stubs alongside the tests, so the RED run failed on assertions rather than on a collection-time ImportError. The GREEN commits replaced the stubs entirely.

## Files Created/Modified

- `plugin/skills/evidence-pack/scripts/epb/commands/doctor.py`: the `doctor` command. It collects the report, runs the folder checks, chooses exit 0 or 3 and renders the checklist.
- `plugin/skills/evidence-pack/scripts/epb/doctor/__init__.py`: package marker (stdlib only).
- `plugin/skills/evidence-pack/scripts/epb/doctor/tools.py`: `ToolSpec`, `ExtraSpec`, `REGISTRY`, `EXTRAS`, `os_id()`.
- `plugin/skills/evidence-pack/scripts/epb/doctor/probes.py`: `probe_tool`, `core_requirements`, `probe_environment`, `env_packages`, `collect`.
- `plugin/skills/evidence-pack/scripts/epb/doctor/report.py`: `render_human`, `current_os`, `command_text`.
- `plugin/skills/evidence-pack/scripts/epb/doctor/syncfolders.py`: `PROVIDERS`, `SyncHit`, `check`, `warning_for`.
- `plugin/skills/evidence-pack/scripts/epb/doctor/gitcheck.py`: `check`, limited to read-only git subcommands.
- `tests/doctor/test_probes.py`, `tests/doctor/test_syncfolders.py`, `tests/doctor/test_gitcheck.py`: 147 tests in total.

## Decisions Made

See `key-decisions` in the frontmatter. The two report keys added beyond the plan's list (`home`, `setup_command`) make the renderer a pure function of the report, as the plan requires for the 01-16 golden test. Plan 01-16 should build its golden report with both keys.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Two top-level report keys added: `home` and `setup_command`**
- **Found during:** Task 1
- **Issue:** The plan requires `render_human` to abbreviate the home folder as `~` and to quote `<python> <epb.py path> doctor --setup`, while reading nothing from the live system. The planned report keys carry neither the home folder nor the epb.py path.
- **Fix:** `collect()` records `home` (`str(Path.home())`) and `setup_command` (the argv list). The renderer and the error hint read them.
- **Files modified:** `epb/doctor/probes.py`, `epb/doctor/report.py`, `epb/commands/doctor.py`
- **Verification:** `test_render_ready_lines`, `test_render_next_step_before_setup`, `test_two_collects_render_identically`
- **Committed in:** `4a9b66f`

**2. [Rule 2 - Missing critical] A generic CloudStorage provider, reported only when no named provider matched**
- **Found during:** Task 2
- **Issue:** The plan's name heuristic includes `CloudStorage`, but that folder belongs to no single provider of the four. Without a fallback, a case folder under `~/Library/CloudStorage/<other service>` would go unreported.
- **Fix:** A fifth, `generic` row, named "a cloud sync service". `check()` drops it whenever a named provider already matched.
- **Files modified:** `epb/doctor/syncfolders.py`
- **Verification:** `test_cloudstorage_alone_is_a_sync_folder`, `test_onedrive_macos_cloudstorage` (still exactly one OneDrive hit)
- **Committed in:** `2a49781`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Both are small and keep the planned interfaces. No scope creep.

## Issues Encountered

- One of my own Task 1 assertions was too strict at first: it asserted that the home path never appears anywhere in the checklist. Install commands rightly keep absolute paths so they can be copied, so the assertion now covers only the Ready block, where folders are displayed. Fixed before the GREEN commit.
- The full `tests/` suite passes: 513 passed and none failed, so the failing file set is empty.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Plan 01-10 can add `--setup` to `commands/doctor.py` (`add_arguments` is empty) and reuse `probes.collect` and `render_human` for its final Ready / Optional / What to do next report. `report["environment"]["launch"]` is already the absolute launch argv the skill needs.
- Plan 01-11 (`init`) can call `syncfolders.check(case)` + `warning_for(hit)` and `gitcheck.check(case)` directly. Both return envelope warning dicts and never raise on a missing or broken git.
- WS-11 and WS-12 are also declared by plan 01-11. The detection halves are complete here, and init's use of them lands there.

## Self-Check: PASSED

- All 10 key files exist on disk.
- Commits `c11b3b5`, `4a9b66f`, `15477f8` and `2a49781` are on branch `gsd-wt-01-08` (`git rev-list --count 535fcfe..HEAD` = 4).
- Plan verification: `.venv/bin/python -m pytest -q tests/doctor tests/launcher tests/cli` gives 164 passed. `.venv/bin/ruff check .` passes, and `ruff format --check .` passes.
- Acceptance: `.venv/bin/python plugin/skills/evidence-pack/scripts/epb.py doctor` prints `Ready`, `Optional, not installed` and `What to do next`. `gitcheck.py` names no git subcommand other than rev-parse, ls-files and check-ignore. The git tests ran: 21 passed, none skipped.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
