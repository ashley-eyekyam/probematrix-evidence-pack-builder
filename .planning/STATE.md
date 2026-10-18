---
gsd_state_version: "1.0"
milestone: v0.1.0
milestone_name: First public release
current_phase: 01
current_phase_name: Foundations
status: executing
stopped_at: Completed 01-16-PLAN.md (merged from worktree)
last_updated: "2026-10-18T15:19:05.061Z"
last_activity: 2026-10-18
last_activity_desc: Phase 01 execution started
state_head: 2614803c5b12485be6457f2ee319a65f44e7c1a0
progress:
  total_phases: 10
  completed_phases: 0
  total_plans: 22
  completed_plans: 16
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-10-17)

**Core value:** Every item in a pack is traceable and trustworthy: each quote is verbatim on the cited page or time, people appear only as role labels, no source conclusion, lesson or recommendation is treated as evidence, and the workbook imports into ProbeMatrix cleanly without duplicates.
**Current focus:** Phase 01 — Foundations

## Current Position

Phase: 01 (Foundations) — EXECUTING
Plan: 1 of 22
Status: Executing Phase 01
Last activity: 2026-10-18 — Phase 01 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
**Per-Plan Metrics:**

| Plan | Duration | Tasks | Files |
|------|----------|-------|-------|
| Phase 01 P01 | 10 min | 3 tasks | 10 files |
| Phase 01 P02 | 3 min | 2 tasks | 2 files |
| Phase 01 P03 | 8 min | 3 tasks | 10 files |
| Phase 01 P04 | 10 min | 3 tasks | 10 files |
| Phase 01 P05 | 7 min | 3 tasks | 9 files |
| Phase 01 P06 | 5 min | 3 tasks | 8 files |
| Phase 01 P07 | 7min | 0 tasks | 11 files |
| Phase 01 P08 | 11min | 2 tasks | 11 files |
| Phase 01 P09 | 7min | 2 tasks | 9 files |
| Phase 01 P10 | 7min | 2 tasks | 7 files |
| Phase 01 P11 | 10min | 3 tasks | 13 files |
| Phase 01 P12 | 9min | 3 tasks | 10 files |
| Phase 01 P13 | 13min | 3 tasks | 1 files |
| Phase 01 P14 | 11min | 3 tasks | 10 files |
| Phase 01 P15 | 6min | 2 tasks | 7 files |
| Phase 01 P16 | 7min | 3 tasks | 6 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 10 phases in the owner-approved kickoff §5 order. Research Phase-Order Fixes PF-01…PF-20 are applied, which moves contracts earlier without reordering phases.
- [Roadmap]: Design §20 amendments A1–A14 win over earlier sections: no samples, `plugin/` subfolder, Python 3.11+, Linux-only CI, Phase 1 smoke import, and a non-technical manual grown per phase.
- [Roadmap]: Design defects are referred to only as DEF-01…DEF-18, never by their original short design-section labels, to avoid clashing with GSD decision tokens.
- [Roadmap]: Owner ProbeMatrix imports happen at Phase 1 (smoke workbook), Phase 5 (master), Phase 6 (delta) and Phase 10 (definition of done).
- [Phase 01]: Owner approved all 16 packages, the PKG-08 floors and ruff==0.16.10 at the blocking-human legitimacy checkpoint before the first install
- [Phase 01]: ruff excludes .planning/ because ruff 0.16.10 formats Python code blocks inside Markdown and the GSD research docs hold illustrative snippets
- [Phase 01]: Design §20 records Phase 1 decisions as A16-A30; each row's first cell cites its D-NN (01-CONTEXT.md) or research reference (01-RESEARCH.md)
- [Phase 01]: Design §5 manual is docs/USER-MANUAL.md (A14), replacing INSTALL.md and USER-GUIDE.md; CHANGELOG/CONTRIBUTING/SECURITY stay at the root
- [Phase 01]: Command modules: epb/commands/<name>.py with NAME, HELP, MUTATING, add_arguments, run; underscore-prefixed modules are helpers and are skipped by discover()
- [Phase 01]: Private env at the fixed D-03 path keyed by plugin version; the epb-env.json marker must match plugin_version and requirements_sha256, else ENV_NOT_SET_UP (exit 3)
- [Phase 01]: Envelope schema enforces ok == (exit_code == 0) and at least one error when ok is false; tracebacks go to stderr only
- [Phase 01]: Writer saves through openpyxl ExcelWriter so the injected created/modified time survives; Workbook.save stamps the wall clock
- [Phase 01]: validate_workbook opens the file as a binary handle because openpyxl rejects the .tmp name write_pack validates
- [Phase 01]: Validator: a formula cell reports only CELL_FORMULA; one finding per cell and code; blank Evidence ID is REQUIRED_BLANK
- [Phase 01]: Licence check: a License field counts only as a known alias or a parseable SPDX expression without placeholder ids; free text falls through to classifiers
- [Phase 01]: Dependency age: any PyPI lookup still failing after one retry exits 2 (age unknown); a 404 (not on PyPI) is a violation
- [Phase 01]: TDD RED for a not-yet-existing tool commits an inert interface skeleton so RED fails on assertions, not on import
- [Phase 01]: Codex installer replaces only folders carrying its .epb-installed marker; a foreign same-name folder stops the install with exit 1 before any write
- [Phase 01]: Plugin manifests carry epb.__version__; a parity test fails on any name or version drift across marketplace, Claude and Codex manifests
- [Phase 01]: plugin/AGENTS.md is proven clean-room by test: no eight-word run shared with the reference report and no honorific-plus-name
- [Phase 01]: Schema issue pointers are RFC 6901 escaped (~0, ~1), so a fingerprint key like inputs/a.pdf shows as /fingerprints/inputs~1a.pdf; the root is '/' as the plan specifies
- [Phase 01]: Transaction refuses .epb/tmp/ targets, a second staging of the same path and a direct stage of .epb/state.json (state goes only through set_state), in addition to the plan's path rule
- [Phase 01]: recover() distrusts a manifest whose entries have a non-NNNN tmp name, a bad sha256 or a final path outside the allow-list (STATE_INVALID), so a tampered journal cannot write into inputs/
- [Phase 01]: load_state treats schema_version below 1 (or a bool) as damaged STATE_INVALID; only 1 <= version < SCHEMA_VERSION is returned raw for upgrade
- [Phase 01]: Workbook records require at least one entry in writes (a record exists only after a first write)
- [Phase 01]: init on an already set-up folder returns data.created = [] with the ALREADY_SET_UP warning and exit 0
- [Phase 01]: The report carries two keys beyond the planned list
- [Phase 01]: Folders are shown with ~ but commands keep absolute paths, so every command in the checklist can be copied as is; parts containing spaces are double-quoted
- [Phase 01]: The short checklist tells the user to ask the agent to install an extra; the exact pip command (env python -m pip install --uploaded-prior-to P14D -r <file>) is shown under --verbose and is always in the JSON
- [Phase 01]: A core package is ok only when installed and, for a plain >=X.Y pin, at least that version; anything the stdlib cannot compare is accepted
- [Phase 01]: A generic CloudStorage provider ('a cloud sync service') catches macOS File Provider folders of services not in the table, and is reported only when no named provider matched
- [Phase 01]: Google Drive on Linux is detected from the GVFS mount component name (google-drive
- [Phase 01]: On the human error path the checklist is the error message and the hint is omitted, because What to do next already carries the setup command; under --json the hint is kept
- [Phase 01]: Git is called with GIT_OPTIONAL_LOCKS=0; a git that cannot be run falls back to the .git walk-up and warns GIT_UNAVAILABLE with 'git could not be run'
- [Phase 01]: WORKSPACE_EXISTS carries data.fields with the differing flag names (title, slug, prefix, timezone) and the message lists them as --flags
- [Phase 01]: A re-run with --title compares the stripped, NFC-normalised title, so whitespace or a decomposed form of the same title is not a difference
- [Phase 01]: validate_timezone also refuses localtime, posixrules and Factory, which ZoneInfo opens but are not IANA zone names
- [Phase 01]: An explicit --slug that is a Windows reserved name (con, prn, aux, nul, com1-9, lpt1-9) is refused; only derived slugs get the -case suffix
- [Phase 01]: init on a set-up folder now loads state.json (load_state) and case.yaml before anything else, so damage to either exits 4 STATE_INVALID instead of ALREADY_SET_UP
- [Phase 01]: The ALREADY_SET_UP re-run also reports data.case with the stored settings, so the skill can show them
- [Phase 01]: A current environment that fails verification is rebuilt (status rebuilt), not reported ready
- [Phase 01]: The ready path emits the existing ALREADY_SET_UP warning so agents see nothing was changed
- [Phase 01]: pip steps also pass --disable-pip-version-check and --no-input so pip never prompts (the CLI never prompts, D-15)
- [Phase 01]: Verify runs the env interpreter with -I (isolated) so PYTHONPATH or user site-packages cannot make a broken env look complete
- [Phase 01]: Exception pins are checked against package/version regexes; a malformed file is SETUP_FAILED before any download
- [Phase 01]: render_human was split into shared helpers so render_setup_human shows identical Optional lines; golden doctor tests unchanged
- [Phase 01]: The INDEX.md Inputs table has an ID column first (display_id, e.g. S004v2) ahead of the planned Path...Items columns, so a new version is visible in INDEX as plan 01-14 requires
- [Phase 01]: init's data.created lists the layout folders that did not exist before (with a trailing /) followed by every staged file in apply order, state.json last
- [Phase 01]: The foreign-INDEX.md refusal runs before anything is created when no journal is pending, and again after recovery, so a refusal leaves the folder untouched
- [Phase 01]: run.json finished_at is stamped when the run is allocated, just before the commit; INDEX shows run times in UTC (YYYY-MM-DD HH
- [Phase 01]: run.schema.json scan.sidecars[].target is a source id (^S\d{3,}$), matching sidecar_of on source records; scan.new_versions[].version is at least 2; upgrade.backup_dir must be .epb/runs/<NNN>/pre-upgrade/
- [Phase 01]: load_sources
- [Phase 01]: open_read_only is a plain function returning a Session; open_for_init and open_for_mutation are context managers, so 01-12 can add the lock around their yield
- [Phase 01]: status message is five plain lines ending with a pointer to INDEX.md; data has exactly case, inputs, runs, last_run, workbooks
- [Phase 01]: recover
- [Phase 01]: open_for_init creates .epb/ before taking the lock and .epb/tmp/ only after it, so a LOCK_TIMEOUT on a folder whose .epb/ already exists changes nothing
- [Phase 01]: The lock file is never deleted or truncated on release; the next holder overwrites it. Deleting lock files races with waiters that already opened the old file
- [Phase 01]: The upgrade reads case.yaml and source records raw (no schema check) because they follow the older version's schemas; the upgraded versions are validated when staged
- [Phase 01]: The upgrade also stamps state.plugin_version with the running plugin and records the run summary 'Case folder upgraded from workspace version <a> to <b>.'
- [Phase 01]: LOCK_TIMEOUT data is {lock
- [Phase 01]: classify takes keyword arguments run_id (the number the scan's run would get) and source_counter (state counters.source), so IDs come from the counter and are never reused even past deleted records
- [Phase 01]: A touched file whose content is unchanged keeps its previous fingerprint (mtime included), so touching a file is not a change and creates no run
- [Phase 01]: A removed source's last known paths (its current versions entry) count as 'had this path' for the new-version rule, so a file that reappears with new content becomes S00Nv2
- [Phase 01]: renamed pairs the source's vanished paths with its new paths in sorted order; any extra new paths are reported as duplicates
- [Phase 01]: AMBIGUOUS_FAMILIES also maps MP4 content to .mov and .m4a, and a container type (ZIP, OLE2, MP4, Matroska, Ogg) never mismatches a name outside the extension table (.epub, .3gp, .opus)
- [Phase 01]: ODF is recognised from the stored 'mimetype' member in the first local header; the value is accepted only if it matches application/vnd.oasis.opendocument.<x>, else the file is plain ZIP
- [Phase 01]: Source mime fields are pattern-checked (lower-case type/subtype, underscore allowed), so text from a hostile file can never reach a record unvalidated
- [Phase 01]: INPUT_REMOVED is warned for each source removed from the folder; LINK_IGNORED for each link; MIME_MISMATCH in plain words naming both types
- [Phase 01]: Two files whose names differ only in Unicode normalisation (one NFC key) stop the scan with BAD_ARGUMENT (exit 2) and change nothing, rather than silently keeping one of them; the message asks the user to rename one
- [Phase 01]: Pairing reflects the folder now
- [Phase 01]: A source_kind other than null or sidecar (set by a later phase) is never overwritten by pairing; a sidecar renamed to an ordinary name goes back to null
- [Phase 01]: When one note's content sits at several sidecar paths, every target lists it and sidecar_of is the target of its first path in sorted order; run and envelope sidecars hold one {src_id, target} entry per pair, so run.schema.json needed no widening
- [Phase 01]: SIDECAR_ORPHAN is warned on every scan while the orphan exists (like LINK_IGNORED); INPUT_REMOVED only on the scan that marks the source removed
- [Phase 01]: When a removed source's path still exists but holds other content (content wins), the change line and INPUT_REMOVED say the earlier content is gone rather than that the file is gone
- [Phase 01]: Finding codes are extracted from formats/validate.py by AST (upper-case snake-case string literals) because the validator has no code-list constant; a sanity test requires at least 20
- [Phase 01]: The Codex install test checks the same file list as the Claude one (schemas, AGENTS.md, requirement files), not only SKILL.md, since the Codex cache was observed to hold them all
- [Phase 01]: SKILL.md tells the agent to always pass --timezone to init (01-09 carry-over
- [Phase 01]: The workspace contract states content wins and that restoring an older version counts as new content, in one sentence each (01-13 carry-over)
- [Phase 01]: The manual is a single file, docs/USER-MANUAL.md (plan's location decision); chapters are '## N. Title' so the order is testable
- [Phase 01]: The fake golden report uses a neutral home folder (/home/investigator) and env version 0.1.0, so the quoted path reads ~/.local/share/probematrix-epb/envs/0.1.0
- [Phase 01]: Chapter 2 also quotes the real SYNC_FOLDER message and hint for OneDrive, checked against syncfolders.warning_for by a test
- [Phase 01]: Chapter 2 states that excerpts can contain names and that the provider's handling is governed by the user's agreement with it, not by the plugin (flagged assumption DOC-04)

### Pending Todos

None yet.

### Blockers/Concerns

- [Phase 1]: OD-13, OD-17 (dev-requirements part), OD-20, OD-21, OD-22, OD-23 and OD-29 are open for Phase 1 discussion.
- [Phase 1]: The Codex manifest route and the Cowork runtime are LOW-confidence. Research is recommended before planning.
- [Phase 5]: This is the largest phase, with 39 requirements. Expect many plans.
- [Phase 7]: Tesseract and ocrmypdf are not yet installed on the dev machine.
- [Process]: Gate phase completion on the VERIFICATION result. The executor may tick ROADMAP and STATE as complete before verification (kickoff §9).

## Deferred Items

Items acknowledged and deferred at milestone close, most recent first:

| Category | Item | Status | Deferred At | Milestone |
|----------|------|--------|-------------|-----------|
| *(none)* | | | | |

## Session Continuity

Last session: 2026-10-18T11:20:06.504Z
Stopped at: Completed 01-16-PLAN.md (merged from worktree)
Resume file: None
