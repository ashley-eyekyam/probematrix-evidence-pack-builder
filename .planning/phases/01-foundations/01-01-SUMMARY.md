---
phase: 01-foundations
plan: 01
subsystem: infra
tags: [pip, requirements, pytest, ruff, venv, fixtures, supply-chain]

requires: []
provides:
  - "plugin/requirements.txt: permissive core with plain >= floors plus Windows-only tzdata (PKG-08, D-11, D-20)"
  - "requirements-dev.txt (core + pytest + ruff==0.16.10) and requirements-dev-full.txt (dev + GPL extras, D-12)"
  - "Optional extras plugin/requirements-email.txt, -media.txt, -docs.txt with licence headers"
  - "pyproject.toml: pytest config (pythonpath, importlib mode, network/host markers, EncodingWarning as error) and ruff config"
  - "tests/conftest.py: autouse _no_network and _isolated_home, plus home_dir, case_dir, run_epb, cli, need_tool fixtures"
  - "Dev environment at the main checkout's .venv (pip 26.2.1, installed with --uploaded-prior-to P14D)"
affects: [01-02, 01-03, 01-04, 01-05, 01-06, 01-07, 01-08, 01-09, 01-10, 01-11, 01-12, 01-13, 01-14, 01-15, 01-16]

plan_head_before: a24d0d475bda0f34e1c7ffa666a73846593dedc4
plan_head_after: c4eed0d9c7bf8f7e3aa007022ea6150449d32940
actuals:
  tokens: 3250
  tasks: 3
  commits: 2

tech-stack:
  added: [jsonschema, PyYAML, openpyxl, defusedxml, lxml, charset-normalizer, pdfplumber, pypdf, Pillow, rapidfuzz, python-docx, python-pptx, beautifulsoup4, markdownify, tzdata (win32), pytest, ruff]
  patterns:
    - "Minimum pins only (>=), no lock file or hashes; the only exact pin is the dev tool ruff==0.16.10"
    - "Dev venv lives at the main checkout; worktrees symlink .venv to it"
    - "Tests import epb from plugin/skills/evidence-pack/scripts via pytest pythonpath, never an install"
    - "Every test is network-refused and runs under a fake HOME/USERPROFILE/APPDATA with a fixed git identity"
    - "network and host tests are opt-in via EPB_NETWORK_TESTS=1 and EPB_HOST_TESTS=1"

key-files:
  created:
    - plugin/requirements.txt
    - plugin/requirements-email.txt
    - plugin/requirements-media.txt
    - plugin/requirements-docs.txt
    - requirements-dev.txt
    - requirements-dev-full.txt
    - pyproject.toml
    - tests/conftest.py
    - tests/packaging/test_requirements.py
  modified:
    - .gitignore

key-decisions:
  - "Owner approved all 16 packages, the PKG-08 floors and ruff==0.16.10 at the blocking-human legitimacy checkpoint before the first install"
  - "ruff excludes .planning/ because ruff 0.16.10 formats Python code blocks inside Markdown and the GSD research docs hold illustrative snippets"

patterns-established:
  - "Run tests as .venv/bin/python -m pytest and lint as .venv/bin/ruff check . && .venv/bin/ruff format --check ."
  - "Optional extras open with a header comment that names the extra and its licence; GPL extras say GPL"

requirements-completed: [PKG-08, TST-01]

coverage:
  - id: D1
    description: "Core requirement manifest with the exact PKG-08 floors, >= pins only, and the win32 tzdata line"
    requirement: PKG-08
    verification:
      - kind: unit
        ref: "tests/packaging/test_requirements.py#test_core_requirements_exact_set"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_requirements.py#test_core_floors"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_requirements.py#test_core_uses_minimum_pins_only"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_requirements.py#test_tzdata_windows_marker"
        status: pass
    human_judgment: false
  - id: D2
    description: "Dev, dev-full and optional extras files with licence headers; no GPL package in core or dev"
    requirement: PKG-08
    verification:
      - kind: unit
        ref: "tests/packaging/test_requirements.py#test_dev_requirements"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_requirements.py#test_extras_have_licence_headers"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_requirements.py#test_no_gpl_in_core_or_dev"
        status: pass
      - kind: unit
        ref: "tests/packaging/test_requirements.py#test_dev_full_composition"
        status: pass
    human_judgment: false
  - id: D3
    description: "Dev environment at the main checkout's .venv with pip >= 26.1, built from requirements-dev.txt under the two-week rule"
    verification:
      - kind: other
        ref: ".venv/bin/python -c \"import pip, sys; v = tuple(int(x) for x in pip.__version__.split('.')[:2]); sys.exit(0 if v >= (26, 1) else 1)\""
        status: pass
      - kind: other
        ref: ".venv/bin/python -c \"import yaml, jsonschema, openpyxl, defusedxml, pytest\""
        status: pass
      - kind: other
        ref: ".venv/bin/ruff check . && .venv/bin/ruff format --check ."
        status: pass
    human_judgment: false
  - id: D4
    description: "Shared fixtures: autouse no-network guard and fake home, run_epb, cli, case_dir, home_dir, need_tool, opt-in network/host markers"
    requirement: TST-01
    verification:
      - kind: other
        ref: "Throwaway smoke test (not committed): socket.create_connection, socket.connect and connect_ex raise the refusal; Path.home() is the fake home; need_tool skips a missing tool; network/host tests skip by default and run with EPB_HOST_TESTS=1"
        status: pass
    human_judgment: true
    rationale: "No committed test exercises the fixtures yet; they were proven only by a throwaway smoke test. The first plans that use them (run_epb, cli) will provide committed coverage."
  - id: D5
    description: "Owner package-legitimacy approval before the first pip install"
    verification:
      - kind: manual_procedural
        ref: "Task 2 checkpoint:human-verify gate=blocking-human, owner reply \"approved\""
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-10-18
status: complete
---

# Phase 1 Plan 01: Dev Toolchain and Test Harness Summary

**Permissive core manifest with exact PKG-08 floors, licence-headed GPL extras kept out of core and dev, a pip 26.2.1 dev venv installed under the 14-day upload cutoff, and autouse no-network and fake-home pytest fixtures.**

## Performance

- **Duration:** about 10 min of executor time, split across two sessions by the Task 2 checkpoint
- **Started:** 2026-10-18T09:04:57Z
- **Completed:** 2026-10-18T09:14:25Z
- **Tasks:** 3 of 3 (Task 1 tracer, Task 2 owner checkpoint, Task 3 environment and fixtures)
- **Files modified:** 10

## Accomplishments

- `plugin/requirements.txt` lists the 14 permissive core packages with plain `>=` floors (`lxml>=6.1.0`, `pdfplumber>=0.11.9`, `Pillow>=12.3.0`, `pypdf>=6.19.0`) and `tzdata; sys_platform == "win32"`. Eight manifest tests assert this.
- The optional extras (`requirements-email.txt` GPL-3.0, `requirements-media.txt` with GPL codec binaries, `requirements-docs.txt` MIT) are only declared, not installed. `requirements-dev-full.txt` adds just the GPL extras, for the Phase 10 media CI job.
- The dev venv sits at the main checkout. pip was upgraded from 25.1.1 to 26.2.1, then `requirements-dev.txt` was installed with `--uploaded-prior-to P14D`, which resolved pytest 9.1.1, ruff 0.16.10, lxml 6.1.3, pypdf 6.19.0, Pillow 12.3.0 and pdfplumber 0.11.10.
- `tests/conftest.py` gives every later plan its no-network guard, fake home, CLI runners (`run_epb` for subprocesses, `cli` for in-process calls), `case_dir`, `need_tool`, and opt-in `network` and `host` markers.

## Task Commits

1. **Task 1: Tracer, core requirements manifest proven by a manifest test under the pytest config.** `c11ee43` (feat)
2. **Task 2: Owner package-legitimacy check before the first pip install.** No commit. The owner replied **"approved"**: they reviewed all 16 packages in `plugin/requirements.txt` and `requirements-dev.txt`, the floors `lxml>=6.1.0`, `pdfplumber>=0.11.9`, `Pillow>=12.3.0`, `pypdf>=6.19.0`, and the exact pin `ruff==0.16.10`. The optional extras (extract-msg, faster-whisper, docling) are declared only, not installed, and each gets its own check in the phase that installs it.
3. **Task 3: Build the dev environment, add the extras files and the shared test fixtures.** `c4eed0d` (feat)

## Files Created/Modified

- `plugin/requirements.txt`: permissive core runtime requirements (PKG-08, D-11, D-20)
- `plugin/requirements-email.txt`: optional `.msg` extra, GPL-3.0 header
- `plugin/requirements-media.txt`: optional transcription extra; the header warns about GPL codec binaries
- `plugin/requirements-docs.txt`: optional docling extra, MIT header, floor 2.132.0
- `requirements-dev.txt`: core plus `pytest>=9.0` and `ruff==0.16.10`
- `requirements-dev-full.txt`: dev plus the email and media extras (D-12)
- `pyproject.toml`: pytest and ruff config only, with no `[project]` table
- `tests/conftest.py`: shared fixtures and the opt-in marker hook
- `tests/packaging/test_requirements.py`: 8 manifest tests, stdlib only, so they also pass under the system pytest
- `.gitignore`: adds `scratch/` and a bare `.venv` (symlink-safe)

## Decisions Made

- The `cli` fixture also catches `SystemExit` from `epb.cli.main` and reports its code as `exit_code`, so it works whether `main` returns a code or raises one.
- Everything else followed the plan as specified.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff format failed on Python snippets inside planning Markdown**
- **Found during:** Task 3 verification (`.venv/bin/ruff format --check .`)
- **Issue:** ruff 0.16.10 also formats Python code blocks in `.md` files. Two GSD research documents (`.planning/phases/01-foundations/01-RESEARCH.md` and `.planning/research/ARCHITECTURE.md`) contain illustrative snippets in non-ruff style, so the verify command exited 1.
- **Fix:** added `.planning` to `[tool.ruff] extend-exclude` in `pyproject.toml`, with a comment. The planning docs were not edited.
- **Files modified:** `pyproject.toml`
- **Verification:** `ruff check .`, `ruff format --check .` (7 files already formatted) and pytest all exit 0.
- **Committed in:** `c4eed0d` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** This was a config-only fix needed for the plan's own verify command, with no scope creep. Markdown under `docs/` and `plugin/` is still format-checked.

## Issues Encountered

None.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Every later Phase 1 plan can run `.venv/bin/python -m pytest` and `.venv/bin/ruff`.
- Plans that run in a git worktree must first symlink `.venv` to the main checkout's `.venv`.
- `run_epb` and `cli` expect `plugin/skills/evidence-pack/scripts/epb.py` and `epb.cli.main`, which later plans create.

## Self-Check: PASSED

- All 10 key files exist on disk.
- Commits `c11ee43` and `c4eed0d` are ancestors of HEAD on `phase-01-foundations`.
- Plan verification: `.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/python -m pytest -q` exits 0 (8 passed).
- Acceptance: pip 26.2.1 >= 26.1; core imports succeed; conftest contains the refusal string and all five fixture names; `git status --porcelain` lists no `.venv` entry.

---
*Phase: 01-foundations*
*Completed: 2026-10-18*
