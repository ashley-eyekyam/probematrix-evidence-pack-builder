---
phase: 01-foundations
reviewed: 2026-10-18T11:35:00Z
depth: standard
files_reviewed: 115
files_reviewed_list:
  - plugin/skills/evidence-pack/scripts/epb/casefile.py
  - plugin/skills/evidence-pack/scripts/epb/cli.py
  - plugin/skills/evidence-pack/scripts/epb/commands/__init__.py
  - plugin/skills/evidence-pack/scripts/epb/commands/init.py
  - plugin/skills/evidence-pack/scripts/epb/commands/status.py
  - plugin/skills/evidence-pack/scripts/epb/errors.py
  - plugin/skills/evidence-pack/scripts/epb/faults.py
  - plugin/skills/evidence-pack/scripts/epb/fsio.py
  - plugin/skills/evidence-pack/scripts/epb/index.py
  - plugin/skills/evidence-pack/scripts/epb/__init__.py
  - plugin/skills/evidence-pack/scripts/epb/launcher.py
  - plugin/skills/evidence-pack/scripts/epb/lock.py
  - plugin/skills/evidence-pack/scripts/epb.py
  - plugin/skills/evidence-pack/scripts/epb/runs.py
  - plugin/skills/evidence-pack/scripts/epb/schema.py
  - plugin/skills/evidence-pack/scripts/epb/schemas/case.schema.json
  - plugin/skills/evidence-pack/scripts/epb/schemas/chunks.schema.json
  - plugin/skills/evidence-pack/scripts/epb/schemas/envelope.schema.json
  - plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json
  - plugin/skills/evidence-pack/scripts/epb/schemas/state.schema.json
  - plugin/skills/evidence-pack/scripts/epb/state.py
  - plugin/skills/evidence-pack/scripts/epb/txn.py
  - plugin/skills/evidence-pack/scripts/epb/upgrade.py
  - plugin/skills/evidence-pack/scripts/epb/workspace.py
  - plugin/skills/evidence-pack/scripts/epb/yamlio.py
  - plugin/skills/evidence-pack/scripts/epb/commands/doctor.py
  - plugin/skills/evidence-pack/scripts/epb/commands/scan.py
  - plugin/skills/evidence-pack/scripts/epb/doctor/gitcheck.py
  - plugin/skills/evidence-pack/scripts/epb/doctor/__init__.py
  - plugin/skills/evidence-pack/scripts/epb/doctor/probes.py
  - plugin/skills/evidence-pack/scripts/epb/doctor/report.py
  - plugin/skills/evidence-pack/scripts/epb/doctor/setup.py
  - plugin/skills/evidence-pack/scripts/epb/doctor/syncfolders.py
  - plugin/skills/evidence-pack/scripts/epb/doctor/tools.py
  - plugin/skills/evidence-pack/scripts/epb/formats/__init__.py
  - plugin/skills/evidence-pack/scripts/epb/formats/probematrix_v2.py
  - plugin/skills/evidence-pack/scripts/epb/formats/validate.py
  - plugin/skills/evidence-pack/scripts/epb/formats/writer.py
  - plugin/skills/evidence-pack/scripts/epb/schemas/source.schema.json
  - plugin/skills/evidence-pack/scripts/epb/sources/classify.py
  - plugin/skills/evidence-pack/scripts/epb/sources/expanders/__init__.py
  - plugin/skills/evidence-pack/scripts/epb/sources/__init__.py
  - plugin/skills/evidence-pack/scripts/epb/sources/scan.py
  - plugin/skills/evidence-pack/scripts/epb/sources/sidecars.py
  - plugin/skills/evidence-pack/scripts/epb/mime.py
  - AGENTS.md
  - CLAUDE.md
  - .claude-plugin/marketplace.json
  - docs/design/2026-10-17-evidence-pack-builder-design.md
  - docs/USER-MANUAL.md
  - .github/workflows/ci.yml
  - .gitignore
  - plugin/AGENTS.md
  - plugin/.claude-plugin/plugin.json
  - plugin/.codex-plugin/plugin.json
  - plugin/requirements-docs.txt
  - plugin/requirements-email.txt
  - plugin/requirements-media.txt
  - plugin/requirements.txt
  - plugin/security-exceptions.json
  - plugin/skills/evidence-pack/references/evidence-pack-v2.md
  - plugin/skills/evidence-pack/references/workspace-contract.md
  - plugin/skills/evidence-pack/SKILL.md
  - pyproject.toml
  - README.md
  - requirements-dev-full.txt
  - requirements-dev.txt
  - tools/check_dependency_age.py
  - tools/check_licences.py
  - tools/install-codex.py
  - tools/licence-allowlist.json
  - tools/make-smoke-pack.py
  - tests/cli/test_exit_codes.py
  - tests/conftest.py
  - tests/core/test_mime.py
  - tests/core/test_yamlio.py
  - tests/docs/test_manual.py
  - tests/doctor/test_gitcheck.py
  - tests/doctor/test_probes.py
  - tests/doctor/test_syncfolders.py
  - tests/epbtest/crash.py
  - tests/epbtest/envkit.py
  - tests/epbtest/packkit.py
  - tests/formats/test_contract.py
  - tests/formats/test_validator.py
  - tests/formats/test_writer.py
  - tests/index/test_index.py
  - tests/launcher/test_launcher.py
  - tests/launcher/test_setup.py
  - tests/launcher/test_setup_real.py
  - tests/packaging/test_host_install.py
  - tests/packaging/test_install_codex.py
  - tests/packaging/test_manifests.py
  - tests/packaging/test_plugin_agents_md.py
  - tests/packaging/test_references.py
  - tests/packaging/test_requirements.py
  - tests/packaging/test_skill_lint.py
  - tests/repo/test_ci_workflow.py
  - tests/repo/test_instructions_mirror.py
  - tests/repo/test_no_network.py
  - tests/schemas/test_state_schema.py
  - tests/sources/test_scan_classify.py
  - tests/sources/test_scan_fingerprint.py
  - tests/sources/test_sidecars.py
  - tests/store/test_crash_resume.py
  - tests/store/test_lock.py
  - tests/store/test_upgrade.py
  - tests/store/test_validate.py
  - tests/tools/test_dependency_checks.py
  - tests/tools/test_smoke_pack.py
  - tests/workspace/test_git_warning.py
  - tests/workspace/test_init_defaults.py
  - tests/workspace/test_init.py
  - tests/workspace/test_layout.py
  - tests/workspace/test_status.py
findings:
  critical: 5
  warning: 38
  info: 36
  total: 79
status: issues_found
---

# Phase 01: Code Review Report

Merged from four parallel standard-depth reviews (each by gsd-code-reviewer, each claim verified against source):

| Part | Scope | Critical | Warning | Info |
|---|---|---|---|---|
| A | CLI shell, store/txn, lock, upgrade, workspace, init/status | 2 | 9 | 11 |
| B | scan/sources, MIME, format writer/validator, doctor/setup | 1 | 11 | 9 |
| C | tools, CI, manifests, skill + references, manual, repo config | 1 | 9 | 9 |
| D | pytest suite and test helpers | 1 | 9 | 7 |
| **All** | 115 files | **5** | **38** | **36** |

---

## Part A: CLI shell, store/txn, lock, upgrade, workspace, init/status

## Phase 01, Part A: Code Review Report

**Reviewed:** 2026-10-18T11:28:11Z
**Depth:** standard
**Files Reviewed:** 25
**Status:** issues_found

### Summary

Part A covers the CLI shell and launcher, error codes, the journalled store (`txn`, `fsio`, `faults`), state and schema checks, the workspace lock, the D-09 upgrade, the workspace layout, INDEX.md rendering, run records, YAML and case-file handling, the `init` and `status` commands, and their JSON schemas.

The transaction design (state.json written last, the manifest rename as the commit point, roll-forward recovery) is sound under the `os._exit` crash model the tests use. The YAML loader holds up well: every adversarial title tried round-tripped, except the C1 case in A-WR-03. I confirmed the main defects by running the real CLI against throwaway folders in the scratchpad:

- **A-CR-01:** a crafted input file name injects arbitrary Markdown headings and lines into INDEX.md. This breaks the "exactly six level-2 headings" must-have and the fixed tick-line contract.
- **A-CR-02:** a failed `init` still creates `.epb/`, `.epb/lock` and `.epb/tmp/`. This breaks the 01-09 must-have "writes nothing". The test that should catch it is weaker than the truth it claims to cover.
- **A-WR-01:** if a crash lands between applying INDEX.md and applying state.json, and the user then touches INDEX.md, the case folder can never be recovered. The error tells the user to restore `.epb`, which does not help.
- **A-WR-02:** `--wait nan` makes a mutating command wait for the lock forever.

The remaining warnings cover:

- power-cut durability gaps in the journal
- recovery applying blobs without checking their hashes
- containment that only checks path text, so symbolic links get through
- `--case ""` silently meaning the current folder
- read-only sessions validating older workspaces against the current schemas
- raw input file names in the "shareable" INDEX.md
- a Windows clean-up failure that turns a successful commit into exit 4

### Narrative Findings (AI reviewer)

### Critical Issues

#### A-CR-01: Input file names inject arbitrary Markdown into INDEX.md (extra headings, forged tick lines)

**File:** `plugin/skills/evidence-pack/scripts/epb/index.py:324-352` (also `:156-157`, `:166-170`)
**Issue:** `open_issues()` puts input paths straight into list lines: `label = f"{display_id(source)} ({_path_text(source)})"` and `f"- {entry.get('path')} was skipped: ..."`. Only table cells go through `_cell()`, which flattens CR and LF. On POSIX a file name may contain `\n`, and nothing upstream rejects it. The run schema's `input_path` is only `^inputs/`, and `re.search` semantics allow embedded newlines.

Reproduced: I created the symlink `inputs/link\n## Injected heading` in a fresh case and ran `epb scan`. INDEX.md then contained a real `## Injected heading` line under "5. Open issues". This breaks:
- the 01-11 must-have "INDEX.md has exactly six level-2 headings in the order 1 to 6";
- research Pattern 7 / design §6.1. A name such as `x\n- [x] Imported: evidence-pack-<slug>-master.xlsx` forges a tick line. Phase 6 will read ticks back, and a tick locks a workbook, so an input file name can lock or claim a workbook as imported.

The `mime_mismatch` values in the same function are not sanitised either.
**Fix:** route every interpolated value in non-table lines through a single-line sanitiser. Also reject or escape C0, C1 and Unicode line separators.
```python
_LINE_BREAKS = re.compile(r"[\x00-\x1f\x7f-\x9f  ]")

def _inline(value) -> str:
    """Text safe on one Markdown list line: no line breaks or other control characters."""
    return _LINE_BREAKS.sub(" ", str(value))

## open_issues
label = f"{display_id(source)} ({_inline(_path_text(source))})"
...
issues.append(f"- {_inline(entry.get('path'))} was skipped: it is {reason}.")
```
Add a regression test that scans a newline-bearing file name and asserts INDEX.md still has exactly six `## ` lines and no `- [x]` line.

#### A-CR-02: A failed `init` writes `.epb/`, `.epb/lock` and `.epb/tmp/` (breaks the 01-09 "writes nothing" must-have)

**File:** `plugin/skills/evidence-pack/scripts/epb/commands/init.py:65-87`, `plugin/skills/evidence-pack/scripts/epb/workspace.py:138-140`
**Issue:** `open_for_init` creates `.epb/`, opens or creates `.epb/lock` and creates `.epb/tmp/` before `init.run` calls `casefile.resolve_settings()`. Every BAD_ARGUMENT or TIMEZONE_REQUIRED failure therefore happens after those writes.

Reproduced: `epb init --case <empty dir> --timezone Europe/London --json` (no `--title`) exits 2 BAD_ARGUMENT and leaves `.epb/`, `.epb/tmp/` and `.epb/lock` behind. The 01-09 truth says "On a folder that is not set up, init without --title, or with a blank or whitespace-only title, exits 2 with BAD_ARGUMENT and **writes nothing**". `tests/workspace/test_init_defaults.py:194-196` (`_assert_nothing_written`) only checks for `case.yaml` and `state.json`, so the violation goes unnoticed.

The practical harm: an agent that runs `init` in the wrong folder (for example a home folder or a repository root) leaves a `.epb` folder there even though the command was refused.
**Fix:** resolve and validate the settings before touching the disk when the folder is not yet set up, and only then open the session.
```python
if not (case / STATE_FILE).exists() and not txn.pending_journals(case):
    _refuse_foreign_index(case, index.INDEX_FILE)
    settings = casefile.resolve_settings(args, case)   # validate first: a refusal writes nothing
else:
    settings = None
with workspace.open_for_init(case, ctx) as session:
    ...
    settings = settings or casefile.resolve_settings(args, case)
```
Also tighten `_assert_nothing_written` to `assert not (case_dir / ".epb").exists()`.

### Warnings

#### A-WR-01: Recovery bricks the case folder if INDEX.md is touched after a crash, and the hint gives the wrong remedy

**File:** `plugin/skills/evidence-pack/scripts/epb/txn.py:212-225`
**Issue:** when a journal blob is already gone, `_apply` requires the final file's SHA-256 to match exactly, and raises STATE_INVALID otherwise. INDEX.md is the one file in a transaction the user is invited to edit ("Do not edit it, except to tick an Imported? box").

Reproduced:
1. `EPB_TEST_CRASH_AT=apply:5 epb init ...`. INDEX.md is applied, state.json is not.
2. Append a line to INDEX.md.
3. Every later `init` exits 4: "INDEX.md does not match what the change wrote".
4. `status` says NOT_A_WORKSPACE.

The hint "Restore the .epb folder from a backup" cannot fix it, because the mismatch is in INDEX.md, outside `.epb`. Following the advice ("do not edit it by hand") leaves the case unrecoverable. The same happens if the user deletes INDEX.md after the crash.
**Fix:** INDEX.md is regenerated on every run, so tolerate a mismatched or missing INDEX.md during recovery (or re-stage it from the journal). For example, keep the INDEX.md blob until cleanup by copying it instead of renaming it. Or, in `_apply`, when `entry["final"] == INDEX_FILE` and the blob is gone, skip the hash check. Recovery should still be strict for `.epb/**` and `outputs/**`.

#### A-WR-02: `--wait nan` makes a mutating command wait for the lock forever

**File:** `plugin/skills/evidence-pack/scripts/epb/lock.py:111-122`, `plugin/skills/evidence-pack/scripts/epb/cli.py:106-112`
**Issue:** `--wait` is `type=float`, so it accepts `nan`, `inf` and negative values. With NaN:
- `max(nan, 0.0)` returns `nan`, so `deadline` is NaN;
- `remaining <= 0` is always False;
- `min(poll_s, nan)` is `poll_s`;

so the loop polls forever and never raises LOCK_TIMEOUT. Reproduced: with the lock held, `lock.acquire(p, wait_s=float('nan'), ...)` was still waiting when `timeout 4` killed it. `inf` behaves the same. This breaks WS-07 ("wait up to --wait seconds before exiting 4"), and an agent loop would hang.
**Fix:** validate in the parser.
```python
def _wait_seconds(text):
    value = float(text)
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError("--wait must be a number of seconds, 0 or more")
    return value
parser.add_argument("--wait", type=_wait_seconds, ...)
```
Also guard `lock.acquire` with `if not math.isfinite(wait_s): raise EpbError("BAD_ARGUMENT", ...)`.

#### A-WR-03: Case titles containing C1 controls or NEL are accepted but do not round-trip, so re-running `init` fails

**File:** `plugin/skills/evidence-pack/scripts/epb/casefile.py:29,175-180`, `plugin/skills/evidence-pack/scripts/epb/schemas/case.schema.json` (`title.pattern`)
**Issue:** `_CONTROL = [\x00-\x1f\x7f]` and the schema pattern only exclude C0 and DEL. A title containing U+0085 (NEL, a YAML line break) passes validation and is written to case.yaml. On reload it reads back as a different string.

Reproduced: `init --title $'Pump\u0085Trip'` exits 0, and `status` then reports the title as `"Pump Trip"`. Re-running the identical `init --title $'Pump\u0085Trip'` exits 2 WORKSPACE_EXISTS (`fields: ["title"]`), which breaks the "running it again changes nothing" contract. The raw C1 character also lands in the `# title` heading of INDEX.md.
**Fix:** widen the character class in both places to `[\x00-\x1f\x7f-\x9f  ]` (schema: `^[^\u0000-\u001f\u007f-\u009f  ]*\S[^...]*$`). Add a dump-then-load round-trip assertion in `new_case_record` or in the tests.

#### A-WR-04: Power-cut durability: new directory entries are never fsynced

**File:** `plugin/skills/evidence-pack/scripts/epb/txn.py:170-173,195,219-222`
**Issue:** the module promises durability against "what a power cut would leave behind", but:
1. `txn_dir.mkdir()` (line 173) is never followed by `fsync_dir(tmp_root)` before the commit point. The blob entries in `txn_dir` are also only fsynced after the manifest rename (line 195). On a filesystem that does not order metadata, the journal folder can vanish after a power cut while some finals were already renamed into place and fsynced. Recovery then has nothing to roll forward, and the folder is torn (for example a new case.yaml or sources file with an old state.json).
2. `_apply` runs `final.parent.mkdir(parents=True, exist_ok=True)` (line 220) for new directories such as `.epb/runs/001/` and the first `.epb/sources/`. It fsyncs only `final.parent`, never the grandparent that holds the new directory entry, so the folder holding a just-applied record can disappear while state.json (applied later and fsynced) survives.

The `os._exit` crash tests cannot detect either case.
**Fix:** run `fsio.fsync_dir(tmp_root)` right after `txn_dir.mkdir()`. Run `fsio.fsync_dir(txn_dir)` before the manifest `os.replace` (and keep the one after it). In `_apply`, after creating any missing ancestors, fsync each newly created directory's parent. A helper `_mkdirs_durable(path, stop=case_root)` that fsyncs every parent it created would cover this.

#### A-WR-05: Recovery renames journal blobs into place without checking them against the manifest hash

**File:** `plugin/skills/evidence-pack/scripts/epb/txn.py:219-222`
**Issue:** the manifest records a `sha256` for every blob, but `_apply` checks it only when the blob is already gone. A blob that is present but truncated or corrupted (filesystem damage, a sync client rewriting files under `.epb/tmp`, or a partial write that A-WR-04 made possible) is renamed straight onto `state.json`, `case.yaml` or a source record. Damaged state then turns up later, away from its cause.
**Fix:** in the recovery path (`point == "recover"`), verify before applying:
```python
if tmp.exists():
    if point == "recover" and fsio.sha256_file(tmp) != entry["sha256"]:
        raise _journal_error(txn_dir, f"the saved copy of {entry['final']} is damaged")
```

#### A-WR-06: Transaction containment only checks the path text, so a symlinked `outputs/` or `.epb/<dir>` can make it write outside the case folder

**File:** `plugin/skills/evidence-pack/scripts/epb/txn.py:54-69,218-222`, `plugin/skills/evidence-pack/scripts/epb/workspace.py:155-159`
**Issue:** `_path_problem` checks only the relative string. `_apply` then writes to `case_root / entry["final"]`, and `os.replace` and `mkdir` follow any directory symlink on the way. The 01-07 truth says "No transaction can write under inputs/ or outside the case folder". A case folder received as an archive or through a sync client, with `outputs`, `.epb/runs` or `.epb/tmp` as a symlink, sends run records, workbooks and journals outside the case. `recover()` would also `rmtree` `txn-*` directories inside the symlink target. `create_layout` uses `mkdir(exist_ok=True)`, which accepts an existing symlink silently.
**Fix:** before applying, resolve `final.parent` and require `final.parent.resolve().is_relative_to(case_root.resolve())`, and refuse symlinked ancestors under the case root (`os.path.islink` on each component). In `create_layout`, refuse `inputs`, `outputs` and `.epb/*` when they are symlinks.

#### A-WR-07: `--case ""` silently means the current folder

**File:** `plugin/skills/evidence-pack/scripts/epb/cli.py:224-229`
**Issue:** `case=Path(args.case)... if args.case else Path.cwd()` treats an empty string as "not given". An agent that runs `epb init --case "$CASE_DIR"` with an unset variable will set up or scan whatever folder the shell is in (the plugin folder, a repository root, a home folder) instead of failing.
**Fix:** distinguish `None` from `""`.
```python
if args.case is None:
    case = Path.cwd()
elif not args.case.strip():
    raise EpbError("BAD_ARGUMENT", "--case was given an empty folder name.", hint="Pass --case with the case folder.")
else:
    case = Path(args.case).expanduser().absolute()
```

#### A-WR-08: Read-only sessions validate older-version files against current schemas, so UPGRADE_PENDING can never be reached

**File:** `plugin/skills/evidence-pack/scripts/epb/workspace.py:210-238`, `plugin/skills/evidence-pack/scripts/epb/state.py:77-78`
**Issue:** for an older workspace, `load_state` deliberately returns state unvalidated. `_load` then runs `casefile.load_case` (current `case` schema) and `load_sources` (`schema.check(..., "source")`, current schema) before `open_read_only` checks `needs_upgrade`. As soon as a future version changes the case or source schema, `status` on an un-upgraded folder exits 4 STATE_INVALID or RECORD_INVALID ("damaged, restore from backup") instead of warning UPGRADE_PENDING, as D-09 and the module docstring promise. `status` also uses the unvalidated older `state` (`session.state.get("workbooks")`). This is latent today because `SCHEMA_VERSION == 1`. The 01-12 upgrade test only patches the state version, so the gap is not covered.
**Fix:** in `open_read_only`, call `load_state` first. If `needs_upgrade`, warn and build the session from `upgrade.load_snapshot(...)` (or run the upgrade steps in memory without writing) instead of `_load`, so validation happens only against the matching schema version.

#### A-WR-09: INDEX.md, classified "shareable", shows raw input file names (design §6.1 says no personal names)

**File:** `plugin/skills/evidence-pack/scripts/epb/index.py:150-157,264-303,324-352`, `plugin/skills/evidence-pack/scripts/epb/workspace.py:64`
**Issue:** the design (§6.1, line 221) says "No personal names appear in INDEX.md. Input file names that contain a person's name are shown with the name replaced by its role label". In incident cases, file names such as `interview-<name>.docx` are common. `CONTRACT_PATHS` marks INDEX.md as `shareable` ("de-identified output meant to be read or shared"), and the module docstring says only that no absolute path or account name is written. Phase 1 has no name map yet, so INDEX.md copies `paths` verbatim into the inputs table and the open-issues list. No ignore rule, warning or documented deferral covers this, so a user who commits or shares INDEX.md as told publishes names.
**Fix:** until the roster or name map exists, either classify INDEX.md as `raw-text-confidential` in `CONTRACT_PATHS` and the workspace contract and add it to a case-level `.gitignore` hint, or render inputs by `display_id` and type only. Record the deferral explicitly in the phase plan or STATE so the later phase owns the substitution.

### Info

#### A-IN-01: A Windows clean-up failure after a successful commit reports exit 4

**File:** `plugin/skills/evidence-pack/scripts/epb/txn.py:197`
**Issue:** `shutil.rmtree(txn_dir)` runs after every blob has been applied. On Windows, an antivirus or indexer handle on the folder raises PermissionError, and the command exits 4 INTERNAL_ERROR even though the change is complete. Agents are told to stop on exit 4. (Classed as info because the next command recovers cleanly.)
**Fix:** retry the clean-up like `replace_with_retry`, then fall back to `shutil.rmtree(txn_dir, ignore_errors=True)`. The next `recover()` already deletes leftovers.

#### A-IN-02: The manifest `schema_version` is written but never checked

**File:** `plugin/skills/evidence-pack/scripts/epb/txn.py:244-266`
**Issue:** `_read_manifest` ignores `schema_version`. An older plugin would roll forward a newer plugin's journal under whatever new semantics it has.
**Fix:** raise WORKSPACE_TOO_NEW when `manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION`.

#### A-IN-03: The path guard is case-sensitive and allows writing `.epb/lock`

**File:** `plugin/skills/evidence-pack/scripts/epb/txn.py:54-69,95-107`
**Issue:** on case-insensitive filesystems (Windows, macOS), `.epb/State.json` passes the `rel == STATE_FILE` check and `.epb/TMP/x` passes the TMP_DIR check. `.epb/lock` is also writable, and replacing its inode breaks `flock` mutual exclusion. The paths are chosen by the plugin today, so this is hardening only.
**Fix:** compare `rel.casefold()` against the reserved names, and forbid `lock.LOCK_FILE` as a final path.

#### A-IN-04: `.epb/lock` is "structural" and not git-ignored

**File:** `plugin/skills/evidence-pack/scripts/epb/workspace.py:40,95`
**Issue:** every mutating command rewrites `.epb/lock` (pid, command, time), so a tracked case shows churn in git. A `git checkout` or `git pull` that replaces it while a command holds it splits the lock.
**Fix:** add `lock` to `GITIGNORE_LINES` (and to the design A2 list).

#### A-IN-05: A pending `init` journal makes `status` and other commands say NOT_A_WORKSPACE

**File:** `plugin/skills/evidence-pack/scripts/epb/workspace.py:162-172,224-230`
**Issue:** `find_workspace` runs before the pending-journal check. After `init` crashes past its commit point, `status` reports "not set up" instead of RECOVERY_PENDING (confirmed while reproducing A-WR-01).
**Fix:** in `find_workspace`, accept a folder whose `txn.pending_journals()` is non-empty, or warn RECOVERY_PENDING before raising.

#### A-IN-06: The launcher prints a traceback and no envelope on Ctrl-C while the env child runs

**File:** `plugin/skills/evidence-pack/scripts/epb/launcher.py:361-364`
**Issue:** the parent does not catch KeyboardInterrupt around `subprocess.run`. The child prints its own envelope, but the parent then prints a traceback and exits outside the 0 to 4 contract.
**Fix:** wrap the call in `try/except KeyboardInterrupt: return 4` (the child has already reported).

#### A-IN-07: `CORE_IMPORT_NAMES` omits transitive imports

**File:** `plugin/skills/evidence-pack/scripts/epb/cli.py:22-41`
**Issue:** a missing `pdfminer`, `attrs`, `jsonschema_specifications`, `soupsieve` or `et_xmlfile` (pulled in by the core packages) maps to INTERNAL_ERROR (exit 4) instead of CORE_PACKAGE_MISSING (exit 3, "run doctor --setup").
**Fix:** add the transitive top-level names, or treat any ModuleNotFoundError whose module is not under `epb` as CORE_PACKAGE_MISSING.

#### A-IN-08: Source records are never checked against their file name

**File:** `plugin/skills/evidence-pack/scripts/epb/workspace.py:182-196`, `plugin/skills/evidence-pack/scripts/epb/upgrade.py:87-89,148`
**Issue:** `load_sources` sorts by the file stem but never checks `record["src_id"] == path.stem`. The upgrade re-stages each source at `{src_id}.json` taken from the content, so a mismatched record is duplicated rather than reported as damaged.
**Fix:** raise STATE_INVALID when the stem and `src_id` differ, in both places.

#### A-IN-09: `detect_timezone` can store non-canonical `posix/…` or `right/…` names

**File:** `plugin/skills/evidence-pack/scripts/epb/casefile.py:104-113`
**Issue:** a `/etc/localtime` link to `.../zoneinfo/posix/Europe/London` yields `posix/Europe/London`, which `ZoneInfo` accepts and the shape regex allows (three parts).
**Fix:** strip a leading `posix/` and reject `right/` in `_zone_from`.

#### A-IN-10: The root JSON pointer is "/" instead of ""

**File:** `plugin/skills/evidence-pack/scripts/epb/schema.py:44-46`
**Issue:** RFC 6901 uses `""` for the whole document. `"/"` means the key `""`.
**Fix:** `return "/" + "/".join(parts) if parts else ""` (and update the envelope consumers and tests).

#### A-IN-11: Schema patterns allow traversal and line breaks in path-like fields; `REMOVED` is duplicated

**File:** `plugin/skills/evidence-pack/scripts/epb/schemas/run.schema.json` (`input_path`), `plugin/skills/evidence-pack/scripts/epb/schemas/state.schema.json` (`fingerprints.propertyNames`, `item_ref.workbook`), `plugin/skills/evidence-pack/scripts/epb/schemas/chunks.schema.json` (`chunk_id`), `plugin/skills/evidence-pack/scripts/epb/commands/status.py:12` vs `plugin/skills/evidence-pack/scripts/epb/index.py:31`
**Issue:**
- `^inputs/` accepts `inputs/../x` and embedded newlines (which feeds A-CR-01).
- `chunk_id` `^[A-Za-z0-9._-]+$` accepts `.` and `..`.
- `item_ref.workbook` is only `minLength: 1`, while the other workbook references use the `workbook_file` pattern.
- The string `"removed from folder"` is defined twice.

**Fix:**
- Use `^inputs/(?!.*(^|/)\.\.?(/|$))[^\u0000-\u001f\u007f]+$` for input paths.
- Use `^(?!\.{1,2}$)[A-Za-z0-9._-]+$` for `chunk_id`.
- Point `item_ref.workbook` at `#/$defs/workbook_file`.
- Import `REMOVED` from `epb.index` in `status.py`.

---

_Reviewed: 2026-10-18T11:28:11Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

## Part B: scan/sources, MIME, format writer/validator, doctor/setup

## Phase 01 (part B): Code Review Report

**Reviewed:** 2026-10-18T11:29:14Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

### Summary

Group B covers `epb scan` (walk, fingerprint, classify, sidecars), MIME magic-byte detection, the EVIDENCE_PACK_V2 constants, writer and validator, and `epb doctor` (probes, report, setup, sync-folder and git checks). I reran the questionable paths against the repo's `.venv` (Python 3.14.4, openpyxl 3.1.5). Throwaway scripts in the scratchpad confirmed the reproducible claims below.

What holds up:
- The writer always produces inline-string cells. Values with a leading `=`, `0` and `2026-09` stay text, and CR/LF round-trip intact.
- The scan never writes under `inputs/`.
- Every subprocess runs from an argv list with a timeout. There is no shell injection.
- The reviewed-pin regexes stop option smuggling into pip.

The main defects:
- **MIME sniffing reports most UTF-16LE text files as MP3 audio.** Because "content wins", that text evidence gets an audio type and a false mismatch warning (verified).
- **The git check goes quiet when git refuses the repository**, for example with dubious ownership. The warning that protects `.epb/private/` then disappears.
- **Two Windows / working-directory code-planting paths:**
  - `shutil.which` looks in the current directory first on Windows.
  - `python -m pip` and `python -m venv` run without `-I`.
- **Validator gaps:**
  - It accepts impossible dates, and dates with a trailing newline (verified).
  - It crashes on deeply nested JSON instead of returning findings (verified).
  - It trusts a stale `<dimension>` and skips rows (verified).
- **Source records are not refreshed** when a known file is renamed (stale MIME data). Paths that are not in NFC form cannot be opened again from the record on Linux or Windows.

### Critical Issues

#### B-CR-01: Most UTF-16LE text files are detected as `audio/mpeg`, and the content type overrides the name

**File:** `plugin/skills/evidence-pack/scripts/epb/mime.py:129-137` (rule order at `:142-160`, decision at `:229-248`)

**Issue:** `_mpeg_frame` accepts any file whose first byte is `0xFF` and whose second byte has the top three bits set. A UTF-16LE byte-order mark is `FF FE`, so it passes:
- version = 3 and layer = 3.
- Byte 2 is the first ASCII character. Bitrate is never `0xF` for printable ASCII, and the sample-rate bits are 3 only for some letters.

So any UTF-16LE file whose first character is not one of those letters is classed as MP3. Verified with the repo venv:

```
log.txt   fffe4100 ('audio/mpeg', {'by_extension': 'text/plain', 'by_content': 'audio/mpeg'})
p.ps1.txt fffe4700 ('audio/mpeg', {'by_extension': 'text/plain', 'by_content': 'audio/mpeg'})
```

`audio/mpeg` is not in `_CONTAINERS`, so `detect()` returns the content type plus a mismatch. Two things follow:
- `scan` stores `versions[].mime = "audio/mpeg"` and warns the user "looks like MP3 audio but its name says text".
- The design's "content wins" rule (D-13) means Phase 2 will route this text evidence to audio handling (transcription) instead of text extraction.

UTF-16LE with a BOM is common for Windows evidence: Notepad "Unicode" saves, Excel "Unicode Text" exports, `reg export`, and PowerShell 5.1 `>` and `Out-File` output. Those are exactly the log and record exports investigators collect.

**Fix:** Check for text byte-order marks before any audio rule, and require more than one plausible frame header before calling a file MPEG audio without an ID3 tag:

```python
_TEXT_BOMS = (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")

def sniff(path):
    with open(path, "rb") as handle:
        head = handle.read(HEAD_BYTES)
    if head.startswith(_TEXT_BOMS) and not head.startswith(b"\xff\xfe\x00\x00"):
        return None  # text: let the extension decide
    ...
```

Alternatively, have `_mpeg_frame` compute the frame length and confirm that a second sync word (`0xFFE`) appears at that offset. Add regression tests for UTF-16LE and UTF-16BE `.txt` and `.csv` files.

### Warnings

#### B-WR-01: The git check reports "safe" whenever git refuses or errors

**File:** `plugin/skills/evidence-pack/scripts/epb/doctor/gitcheck.py:198-210`

**Issue:**
- When `rev-parse --show-toplevel` exits non-zero, `check()` returns `[]` (line 201-202). That covers "not a repo", but it also covers:
  - `fatal: detected dubious ownership` (exit 128). This is common on Windows external drives, WSL `/mnt/c`, and shared or network folders.
  - A corrupt `.git` or an unreadable config.
- In those cases the folder *is* inside a repository that the user or another account can commit from, yet no `GIT_UNAVAILABLE` warning appears. The `_inside_git_by_walk` fallback is only used when git cannot be spawned at all.
- Likewise, `check-ignore` exiting 128 (fatal) is treated as "ignored", because only `returncode == 1` warns.

The result is that doctor and init stay silent exactly where the `.epb/private/` name map is at risk (WS-11).

**Fix:**
```python
if top.returncode != 0:
    return [_unavailable(installed=True)] if _inside_git_by_walk(case_root) else []
...
if ignored.returncode not in (0, 1):
    warnings.append(_unavailable(installed=True))
elif ignored.returncode == 1:
    warnings.append(_private_not_ignored())
```

#### B-WR-02: On Windows, doctor runs `git`, `7z`, `ffmpeg` and the other tools from the current directory first

**File:** `plugin/skills/evidence-pack/scripts/epb/doctor/probes.py:262-271, 274-289`; `plugin/skills/evidence-pack/scripts/epb/doctor/gitcheck.py:194-198`

**Issue:** On Windows, `shutil.which` puts `os.curdir` at the front of the search path unless `NoDefaultCurrentDirectoryInExePath` is set (confirmed in the stdlib source, `_win_path_needs_curdir`). PATHEXT includes `.BAT` and `.CMD`.

- `probe_tool` runs the returned path with `[path, *version_args]`.
- `gitcheck.check` runs it with `rev-parse`, `ls-files` and `check-ignore`.

So a `git.exe`, `git.bat` or `7z.cmd` in the folder where doctor is launched (the case folder or wherever the agent's cwd is) is executed on every `doctor` and `init`. This contradicts the T-01-18 / T-01-21 safety claims in the module docstrings.

**Fix:** Reject results that are not absolute paths or that sit in the current directory, or set the opt-out before searching:
```python
os.environ.setdefault("NoDefaultCurrentDirectoryInExePath", "1")  # once, Windows only
path = which(name)
if path and not os.path.isabs(path):
    path = None
```

#### B-WR-03: Setup runs `python -m venv` and `python -m pip` without isolation, so modules in the current directory are imported

**File:** `plugin/skills/evidence-pack/scripts/epb/doctor/setup.py:392, 461`

**Issue:** `-m` puts the current working directory at the front of `sys.path`. A `pip.py`, `venv.py` or a shadowing stdlib module in the folder setup is launched from runs inside the setup process. `env_packages` (`probes.py:348`) and `_verify` (`setup.py:367`) already pass `-I`; the two `-m` calls that execute the most code do not.

**Fix:**
```python
_call(run, [sys.executable, "-I", "-m", "venv", str(env)], VENV_TIMEOUT)
pip = [str(env_python), "-I", "-m", "pip", "install", *PIP_QUIET]
```
Alternatively, pass `cwd=str(env.parent)` to `run`.

#### B-WR-04: `doctor --setup` can delete the environment it is running from

**File:** `plugin/skills/evidence-pack/scripts/epb/doctor/setup.py:262-264, 379-392, 444-458`

**Issue:** doctor is a bootstrap command, so it runs in whatever interpreter launched `epb.py`. The report's `environment.launch` (`probes.py:415`) tells the agent to launch the CLI with the private env's python. An agent that does this for `doctor --setup` on a broken environment (verify fails) hits the rebuild path:
- On Linux, `_remove(env)` succeeds. Then `_create` runs `[sys.executable, "-m", "venv", ...]`, where `sys.executable` is the deleted `env/bin/python`. The result is SETUP_FAILED, the environment is gone, and the hint (`terminal_command()`, also built from `sys.executable`) points at a path that no longer exists.
- On Windows, `rmtree` fails on the locked `python.exe` and leaves a half-removed folder.

**Fix:** Build from the base interpreter, and refuse to remove the active prefix:
```python
base = getattr(sys, "_base_executable", None) or sys.executable
if Path(sys.prefix).resolve() == env.resolve():
    raise EpbError("SETUP_FAILED", "Setup cannot rebuild the environment it is running in.",
                   hint="Run: " + command_text([base, str(launcher.epb_script()), "doctor", "--setup"]))
```
Use `base` in both `_create` and `terminal_command()`.

#### B-WR-05: The extras install command is an unquoted shell string that falls back to a bare relative file name

**File:** `plugin/skills/evidence-pack/scripts/epb/doctor/probes.py:467-468`

**Issue:** `"%s -m pip install --uploaded-prior-to %s -r %s"` interpolates the env python path and the requirements path without quoting. Both live under the user's home folder (on Windows, `%LOCALAPPDATA%` under `C:\Users\<First Last>\...`), so the command breaks on any path with a space.

Two further problems:
- When `locate_plugin_file` returns None, the command names a bare `requirements-email.txt`, which resolves against whatever the cwd is.
- `--json` exposes this as a single string rather than an argv list, which invites the agent to run it through a shell. The rest of doctor uses `command_text` and argv lists.

**Fix:** Emit an argv list and render it with `report.command_text`:
```python
argv = [environment["python"], "-I", "-m", "pip", "install", *setup.PIP_QUIET,
        "--uploaded-prior-to", CUTOFF, "-r", str(extra_file)] if extra_file else None
... "install": argv, "install_text": command_text(argv) if argv else None
```

#### B-WR-06: `DATE_PRECISION` accepts impossible dates and a trailing newline

**File:** `plugin/skills/evidence-pack/scripts/epb/formats/validate.py:99, 233-245`

**Issue:** `_DATE = r"^\d{4}(-\d{2}(-\d{2})?)?$"` is applied with `.match`, and Python's `$` also matches before a final `\n`. Verified: a pack with Collection Date `'2026-02-31\n'` in one row and `'2026-13'` in another wrote and re-validated with **zero findings**. The validator is meant to be stricter than the importer, and design §8 requires date precision without padding. An out-of-range month or day reaches ProbeMatrix unchecked, and the newline is preserved in the cell.

**Fix:**
```python
_DATE = re.compile(r"(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?")
m = _DATE.fullmatch(date)
ok = m is not None
if ok and m.group(2):
    try:
        datetime(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
    except ValueError:
        ok = False
```
Also switch `_TIMESTAMP` to `fullmatch` for consistency. `fromisoformat` currently catches the newline there.

#### B-WR-07: The validator raises instead of returning findings on some malformed input

**File:** `plugin/skills/evidence-pack/scripts/epb/formats/validate.py:268-271, 682-695`

**Issue:**
- `_custody_findings` catches only `ValueError` from `json.loads`. A Chain of Custody cell of `"[" * 100000` raises `RecursionError` (verified with the repo venv). That propagates out of `validate_rows`, so `write_pack` crashes instead of raising `PackInvalid`, and out of `validate_workbook` for an externally supplied workbook.
- In `_raw_findings`, a shared-string cell with an empty `<v/>` makes `int(value.text)` raise `TypeError`, which is not in the caught tuple. A negative index silently picks the wrong string.

The module contract is "every finding is collected; validation never stops at the first problem".

**Fix:** Catch `(ValueError, RecursionError)` around `json.loads` and return `bad_json("is not valid JSON.")`. Add `TypeError` to the `_raw_findings` except tuple, and bounds-check the shared-string index (`0 <= i < len(shared)`).

#### B-WR-08: `validate_workbook` trusts the sheet's declared `<dimension>`, so it can skip rows and report a false total mismatch

**File:** `plugin/skills/evidence-pack/scripts/epb/formats/validate.py:422-432, 719-740`

**Issue:** In `read_only=True` mode, `ws.max_row` and `ws.max_column` come from the `<dimension ref>` element. Verified: I rewrote a valid two-item pack's dimension to `A1:AD2` and made both rows' Type invalid. The validator then:
- reported only `ENUM_INVALID` on B2, so row 3's invalid Type was never checked;
- raised a spurious `METADATA_TOTAL_MISMATCH`.

The raw XML pass still sees the cells, but the enum, custody, list and required-field checks do not. The writer's own output is safe; packs from other tools, or ones the user edited, are not.

**Fix:** Call `ws.reset_dimensions()` before iterating in read-only mode and iterate without bounds:
```python
ws.reset_dimensions()
rows = [tuple(r) for r in ws.iter_rows(values_only=True)]
width = max((len(r) for r in rows), default=0)
return [r + (None,) * (width - len(r)) for r in rows]
```

#### B-WR-09: Renaming a known file never refreshes its stored MIME type or mismatch

**File:** `plugin/skills/evidence-pack/scripts/epb/sources/classify.py:144-174, 208-209`

**Issue:** Step 2 (a known source whose content is still present) updates `paths`, `presence` and the current version's `paths`. It never recomputes `mime_mismatch`, `versions[current].mime` or `plan.mime_mismatches` from the new `FileFact`s. Those are only set for new content in step 3. Consequences:
- Renaming `photo.jpg` (JPEG) to `photo.png` creates a real mismatch, but the record keeps `mime_mismatch: null` and no `MIME_MISMATCH` warning is raised.
- Renaming `report.txt` (PDF content, mismatch recorded) to `report.pdf` keeps a stale mismatch for ever.
- For types where the name wins (`_agree`: OLE2 `.msg`/`.doc`, unrecognised text such as `.txt` to `.md`), the stored `mime` is stale. Phase 2 converter selection will read a type the file no longer has.
- Duplicate copies with different extensions record only `paths[0]`'s verdict.

**Fix:** In step 2, after setting `record["paths"]`, recompute from `facts[new_paths[0]]`. Assign `record["mime_mismatch"]` and `_current(record)["mime"]` from that fact, and when the mismatch differs from the stored value, append to `plan.mime_mismatches`.

#### B-WR-10: NFC path keys cannot reopen a non-NFC file name on Linux or Windows

**File:** `plugin/skills/evidence-pack/scripts/epb/sources/scan.py:115-118, 226-240, 454-468`

**Issue:** `rel_key` normalises every path to NFC, and `FileFact.rel` and the source records keep only that form. That is safe on macOS (APFS is normalisation-insensitive). It is not safe on ext4 or NTFS, which store and match names byte-for-byte. A file named in NFD form, which is typical for content unzipped from a macOS-made archive, is registered as `inputs/Rapport_e\u0301te.pdf` → `inputs/Rapport_\u00e9te.pdf`. `case_root / record["paths"][0]` then does not exist.

`_run_expanders` already opens files this way (latent while the registry is empty). Every Phase 2 converter that reads a source by its recorded path will hit `FileNotFoundError` for these files.

**Fix:** Record the on-disk name next to the NFC key. For example, add a `disk_path` to `FileFact` and to the fingerprint entry, or keep a `{nfc_rel: on_disk_rel}` map in the scan result. Open files through it, and add a Linux test with an NFD-named input.

#### B-WR-11: One pre-1970 file timestamp aborts the whole scan with `RECORD_INVALID`

**File:** `plugin/skills/evidence-pack/scripts/epb/schemas/source.schema.json:199-202` (and `state.schema.json:182-185`); producer `sources/scan.py:163-168`

**Issue:** `mtime_ns` has `"minimum": 0`, but `os.fstat().st_mtime_ns` is negative for any file dated before 1970-01-01. That happens with archive extractions carrying bogus dates, `touch -d`, and some device exports. Staging the source record or state then fails schema validation (`txn.stage_json` → `schema.check`). The user gets a RECORD_INVALID error with JSON pointers and none of the other inputs are registered. The mtime is informational only, since classification is content-based.

**Fix:** Drop the `minimum` from both schemas (an integer is enough), or clamp to 0 when fingerprinting and record the raw value separately.

### Info

#### B-IN-01: Junk filtering is inconsistent about letter case and silent about what it drops

**File:** `plugin/skills/evidence-pack/scripts/epb/sources/scan.py:73-75, 121-125, 399-406`

**Issue:** Fixed names match in any case, but the globs use `fnmatchcase`, so `notes.tmp` is ignored while `NOTES.TMP` is registered. A legitimate evidence file with a `.tmp` extension is dropped with no warning (`_warn_ignored` warns only for links). It shows up only in `data.ignored`.

**Fix:** Lower-case the name for the glob checks too, and emit an `INPUT_IGNORED` warning for each junk item that is not one of the fixed OS names.

#### B-IN-02: A note whose content is identical to its target file is reported as an orphan with a false message

**File:** `plugin/skills/evidence-pack/scripts/epb/sources/sidecars.py:326-335`; `plugin/skills/evidence-pack/scripts/epb/sources/scan.py:409-420`

**Issue:** If `x.pdf` and `x.pdf.note.md` have the same bytes (for example, both empty), they are one source. `target != src_id` then excludes the pairing, the note becomes an orphan, and the warning says "that file is not in inputs/" even though it is.

**Fix:** Detect `target == src_id` and give it a specific message, such as "the note has the same content as the file it describes".

#### B-IN-03: Some HEIF/HEIC brands are classed as `video/mp4`

**File:** `plugin/skills/evidence-pack/scripts/epb/mime.py:106, 109-120`

**Issue:** Only `heic`, `heix` and `mif1` are recognised. A `.heic` file with major brand `hevc`, `hevx`, `heim`, `heis` or `msf1` (image sequences, burst shots) falls through to `video/mp4`. `image/heic` is in the table, so the photo is recorded as video with a mismatch.

**Fix:** Extend `_HEIC_BRANDS` with those brands, or scan the compatible-brands list in the `ftyp` box.

#### B-IN-04: The git checks inherit `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE` and do not disable fsmonitor

**File:** `plugin/skills/evidence-pack/scripts/epb/doctor/gitcheck.py:178-188`

**Issue:** `env=dict(os.environ, ...)` passes any `GIT_DIR`/`GIT_WORK_TREE` from the agent's environment, which overrides `-C` discovery and checks the wrong repository. A repository's `core.fsmonitor` setting can also make `ls-files` run a configured command.

**Fix:** Drop `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and `GIT_CEILING_DIRECTORIES` from the child environment, and pass `-c core.fsmonitor=false` before the subcommand.

#### B-IN-05: The pip self-upgrade bypasses the two-week rule

**File:** `plugin/skills/evidence-pack/scripts/epb/doctor/setup.py:242, 461-462`

**Issue:** `pip install --upgrade "pip>=26.1"` takes the newest pip, including one published minutes ago, and it runs with full privileges before the cutoff applies. This is consistent with D-18 as written, but it is the single largest supply-chain exposure in setup.

**Fix:** Consider pinning an exact reviewed pip version (`pip==26.1.x`) through `security-exceptions.json`. Alternatively, run a second `pip install --uploaded-prior-to P14D "pip>=26.1"` immediately after.

#### B-IN-06: Removing control characters silently joins words in quoted text

**File:** `plugin/skills/evidence-pack/scripts/epb/formats/writer.py:222-225, 238`

**Issue:** This is per the plan ("C0 controls are removed"), but a form feed from PDF text extraction (`"end of page\x0cNext"`) becomes `"end of pageNext"` with no finding. That alters citation-exact text.

**Fix:** Replace C0 controls with a space, or at least return an info-level finding for each changed cell, so later phases can surface the change.

#### B-IN-07: The 32,767 limit is counted in code points, while Excel counts UTF-16 code units

**File:** `plugin/skills/evidence-pack/scripts/epb/formats/validate.py:112-133`; `writer.py:239`

**Issue:** Text heavy in emoji or other characters outside the BMP can pass at, say, 20,000 code points but exceed Excel's 32,767-unit cell limit when the owner opens the pack.

**Fix:** Measure `len(text.encode("utf-16-le")) // 2` for the limit checks.

#### B-IN-08: The 7-Zip version regex misses common builds

**File:** `plugin/skills/evidence-pack/scripts/epb/doctor/tools.py:306`

**Issue:** `7zz` prints `7-Zip (z) 24.08 ...` and p7zip prints `7-Zip [64] 16.02 ...`. The pattern `7-Zip\s+(\d+...)` matches neither, so verbose doctor shows "Version unknown".

**Fix:** Use `r"7-Zip(?:\s+\([^)]*\)|\s+\[[^\]]*\])?\s+(\d+(?:\.\d+)+)"`.

#### B-IN-09: `write_pack` uses a fixed temporary sibling name

**File:** `plugin/skills/evidence-pack/scripts/epb/formats/writer.py:324-333`

**Issue:** `<name>.tmp` overwrites, and then deletes, any existing file with that name. Two concurrent builds to the same target also collide.

**Fix:** Use `tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")` and clean up only that file.

---

_Reviewed: 2026-10-18T11:29:14Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

## Part C: tools, CI, manifests, skill + references, manual, repo config

## Phase 1: Code Review Report (part C: tooling, CI, manifests, skill docs, manual)

**Reviewed:** 2026-10-18T11:27:16Z
**Depth:** standard
**Files Reviewed:** 27
**Status:** issues_found

### Summary

Part C covers the repo tooling (licence check, dependency-age check, Codex installer, smoke-pack builder), the CI workflow, the requirement and plugin manifests, the router SKILL.md and its two references, the user manual, README, the root instruction mirror and the §20 design amendments (`git diff 306dc89..HEAD -- docs/design/`).

I checked each claim against the code. SKILL.md, the references and the manual quote error codes, exit codes, flags, INDEX.md sections, scan `data` keys, validator finding codes and column widths. Almost all of them match `epb/errors.py`, `epb/cli.py`, `epb/commands/*`, `epb/index.py`, `epb/sources/scan.py`, `epb/formats/probematrix_v2.py` and `validate.py`. `AGENTS.md` and `CLAUDE.md` are byte-identical (`cmp`). Both `actions/checkout@v7` and `actions/setup-python@v7` exist upstream (`git ls-remote`). pip 26.2 accepts `--uploaded-prior-to P14D`. The licence check passes on the local venv.

Main concerns:

1. **Privacy promise not kept.** The manual and the workspace contract promise that `INDEX.md` and the "structural" files hold no names. In fact they record every input's file path verbatim, and investigators often name files after the people involved.
2. **Supply-chain gates weaker than they look.** CI's exception-pin path does not validate its input, although `doctor --setup` does. The age check takes the earliest file upload time. The licence check passes mixed MIT+GPL classifiers. pip and the GitHub Actions are never age-checked or pinned. The `claude plugin validate` gate never runs on GitHub runners.
3. **The documented Ubuntu 22.04 route is a dead end** for every command except `doctor --setup`.

### Critical Issues

#### C-CR-01: INDEX.md and the "structural" records expose input file names, contradicting the manual's de-identification promise

**File:** `docs/USER-MANUAL.md:58-66`, `plugin/skills/evidence-pack/references/workspace-contract.md:24-27,58-62`, `plugin/skills/evidence-pack/SKILL.md:84`

**Issue:** The manual tells non-technical users that de-identification "is always on". It says: "Everything the plugin makes for you to share, such as the evidence pack workbook and `INDEX.md`, uses role labels instead of names." The workspace contract classes `INDEX.md` as **shareable**. It classes `.epb/sources/` and `.epb/state.json` as **structural**, "hold no source text. Safe to keep in version control", and `.epb/.gitignore` does not ignore them.

The code does not support either claim:
- `epb/index.py:264-303` (`inputs_snapshot`) writes a `Path` column with every input's relative path (`_path_text(source)`). Open issues and scan warnings also embed paths (`epb/sources/scan.py:357-405`).
- `schemas/source.schema.json` requires `paths` in every `.epb/sources/S*.json` record. `workspace.GITIGNORE_LINES` does not cover `sources/`.
- No version of the plugin de-identifies anything yet. The manual even says the plugin "does not yet read the contents of your files".

Investigators routinely name files after witnesses, for example `inputs/statements/Statement - <name>.pdf`. A user who trusts the manual will share `INDEX.md`, or commit the case folder, and leak those names. That breaks the product's core privacy guarantee and the plugin's own "Roles only" rule. Under the brief, data loss and privacy risk rate as a blocker.

**Fix:** Make the documents match what the code does now, and plan the code fix:
```markdown
<!-- USER-MANUAL.md §2, replace the first bullet under "De-identification is always on" -->
- The evidence pack workbook uses role labels instead of names (in a later version).
- INDEX.md and the plugin's records list your files by their file names. If a file name
  contains a person's name, rename the file before you put it in inputs/, and do not share
  INDEX.md until you have checked it.
```
In the contract, reclassify `INDEX.md` as "shareable after review" and `.epb/sources/` and `.epb/state.json` as confidential until paths are de-identified. Alternatively, add `sources/` to `GITIGNORE_LINES`. Also add a SKILL.md rule telling the agent to warn the user when an input file name looks like it contains a personal name. Longer term, INDEX.md should show `S001` plus a de-identified label rather than the raw path.

### Warnings

#### C-WR-01: `check_dependency_age.py --pins` emits unvalidated exception text into a pip requirements file (option injection), unlike `doctor --setup`

**File:** `tools/check_dependency_age.py:98-116, 236-239`; `.github/workflows/ci.yml:30-37`

**Issue:** `load_exceptions` only checks that `package` and `version` are non-empty strings. CI then feeds the output of `--pins` to `pip install -r "$RUNNER_TEMP/pins.txt"`. I reproduced it: an entry with `"version": "1.0\n--index-url https://evil.example/simple"` makes `--pins` print:
```
foo==1.0
--index-url https://evil.example/simple
```
pip honours that line in a requirements file. `epb/doctor/setup.py:56-59,140-166`, which reads the same file, rejects such entries with `_PACKAGE`/`_VERSION`. So CI is laxer than the runtime. A malformed exceptions file passes CI, then fails `doctor --setup` with `SETUP_FAILED` for every user. A PR that only touches the JSON can also redirect CI's package index.

**Fix:** Apply the same regexes in `load_exceptions` and fail with exit 2:
```python
_PACKAGE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")
_VERSION = re.compile(r"[0-9][A-Za-z0-9.+!_-]*")
...
if not _PACKAGE.fullmatch(entry["package"]) or not _VERSION.fullmatch(entry["version"]):
    raise ValueError(f"security exception {number} ({label}) has an invalid package or version")
```
Better still, move both regexes into one shared place, or add a test that runs both validators on the same fixtures. Install pins in CI one at a time (`pip install "$pin"`), as setup does.

#### C-WR-02: The age check uses the EARLIEST file upload time, so a wheel added later to an old release passes

**File:** `tools/check_dependency_age.py:159-166`

**Issue:** `parse_upload_time` returns `min(times)` across all files of a release. PyPI lets maintainers, or an attacker holding a maintainer token, add new wheels to an existing old release. pip's `--uploaded-prior-to` filters per file. This backstop check does not: a wheel uploaded yesterday to a 2024 release reports as 2024. That matters most for the security-exception pins and their dependencies, which CI installs with no cutoff (`ci.yml:34`).

**Fix:** Use the newest file time (`max(times)`). That is conservative, so a release with any fresh file is flagged. Or better, match the exact installed file: read `direct_url.json` or the wheel tag, and compare against that file's `upload_time_iso_8601`.

#### C-WR-03: The licence check passes a package whose classifiers list both an allowed and a disallowed licence

**File:** `tools/check_licences.py:194-212`

**Issue:** `_classifier_licence` drops every unmapped classifier as soon as one classifier maps. Reproduced: classifiers `MIT License` plus `GNU General Public License v3 (GPLv3)` give `('MIT', 'classifier')`, which passes. Several classifiers often mean parts under different licences (AND), not a choice (OR). The gate fails open on exactly the GPL case D-12 exists to catch.

**Fix:** When `unmapped` is non-empty, return `None` with source `classifier (unmapped: ...)` even if some classifiers mapped. That forces a reviewed override:
```python
if unmapped:
    return None, "classifier (unmapped: " + "; ".join(unmapped) + ")"
if mapped:
    return " OR ".join(mapped), "classifier"
```

#### C-WR-04: Licence overrides apply to every future version of the package

**File:** `tools/check_licences.py:215-220`, `tools/licence-allowlist.json:39-45`

**Issue:** The `pypdfium2` override was reviewed on 2026-10-17 against one release. `licence_of` applies it to any version, so a later relicensing (or a malicious takeover that changes the licence) passes the gate unseen. `plugin/requirements.txt` uses floor pins only, so new versions arrive automatically.

**Fix:** Add a `versions` field (an exact list or a specifier) to each override and apply it only on a match. Otherwise report `VIOLATION ... override does not cover version X`.

#### C-WR-05: CI actions are pinned to mutable tags, with no `permissions:` block and persisted credentials

**File:** `.github/workflows/ci.yml:8-22`

**Issue:** The project enforces a two-week rule and reviewed pins for PyPI, but trusts `actions/checkout@v7` and `actions/setup-python@v7`. Those are moving tags that run with the job's token. The workflow sets no `permissions:`, so the token gets the repository or organisation default, which can be read/write. `actions/checkout` persists that token into `.git/config` for every later step, including the `pip install` steps that run third-party build code.

**Fix:**
```yaml
permissions:
  contents: read
jobs:
  core:
    steps:
      - uses: actions/checkout@<full-commit-sha>  # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-python@<full-commit-sha>  # v7.0.0
```
Update `tests/repo/test_ci_workflow.py::test_uses_the_agreed_actions` to match.

#### C-WR-06: The D-02 `claude plugin validate --strict` gate never runs in CI

**File:** `.github/workflows/ci.yml:54-60`; design §20 A17

**Issue:** GitHub's `ubuntu-24.04` image does not include the `claude` CLI, so this step always takes the `else` branch, prints "skipping" and passes. Manifest validation, the only check that `.claude-plugin/marketplace.json` and `plugin/.claude-plugin/plugin.json` load in the real host, is effectively dead. Meanwhile `test_ci_workflow.py` asserts the command text is present, which gives false assurance.

**Fix:** Install a pinned CLI in CI, for example `npm install -g @anthropic-ai/claude-code@<exact version>`, ideally under the same two-week rule. Then run the validation unconditionally. If that is deliberately out of scope until v0.1.0, make the skip visible: use `echo "::warning::..."` and record it as a known gap in the design row.

#### C-WR-07: pip itself is exempt from the age rule and installed unpinned (`pip>=26.1`)

**File:** `.github/workflows/ci.yml:24-25`, `tools/check_dependency_age.py:38-43`

**Issue:** CI runs `pip install --upgrade "pip>=26.1"` with no cutoff. That always takes the newest pip, even one released an hour ago, and `EXEMPT` hides it from the age report. The tool that resolves and installs every other package is the one dependency never checked. The same pattern is in `doctor --setup` (`epb/doctor/setup.py:49,269`), so every user's machine runs the newest pip.

**Fix:** Pin an exact reviewed pip, for example `pip==26.1.1`, in CI and in setup, and drop the blanket exemption. Alternatively, follow the upgrade with `python -m pip install --uploaded-prior-to P14D --force-reinstall "pip>=26.1"`, so pip resolves itself under the cutoff, and then remove `pip` from `EXEMPT`.

#### C-WR-08: The documented Ubuntu 22.04 route ("Setup finds Python 3.11 on its own") leaves every other command failing with PYTHON_TOO_OLD

**File:** `docs/USER-MANUAL.md:134-136`, `plugin/skills/evidence-pack/SKILL.md:30,39-42`

**Issue:** On a system where `python3` is 3.10 and `python3.11` is installed alongside, the steps go like this:
- SKILL.md tells the agent to run `python3 ".../epb.py" doctor --json`.
- `epb/launcher.py:335-341` refuses every command, including plain `doctor`, with `PYTHON_TOO_OLD`. Only `doctor --setup` re-runs itself under a newer interpreter. `init` and `scan` also fail, even when the private environment already exists, because the version gate runs before the environment check.
- SKILL.md step 4 only says "Pass on the install step from the hint", which sends a user who already has 3.11 round in a loop.

The agent only gets `data.environment.launch` if it happens to run `doctor --setup`.

**Fix:** In SKILL.md step 4, add: "If the user has already installed a newer Python, run `doctor --setup --json`. It finds the newer Python by itself, and its envelope carries `data.environment.launch`. Use that prefix for every later command." In the launcher (another review part), route non-bootstrap commands to the env interpreter when the marker is current, whatever the launching Python version.

#### C-WR-09: `.gitignore` protects `.epb/` of a case run inside the repo, but not its `inputs/`, `outputs/` or `INDEX.md`

**File:** `.gitignore:10-13`

**Issue:** The comment anticipates "a case folder is run inside the repo" and ignores `.epb/`. But the same case folder's `inputs/` (real incident material), `outputs/` (packs) and `INDEX.md` (file names, see C-CR-01) stay committable. CLAUDE.md's hard rule is "Never commit a published sample or real-incident output", and this partial ignore gives false comfort.

**Fix:** Require cases inside the repo to live under the ignored `scratch/` folder, and say so in the comment. Or add explicit patterns such as `**/inputs/`, `**/outputs/` and `**/INDEX.md`, scoped so they cannot hide repo files (no such repo paths exist today). A test could assert that no tracked file sits beside a `.epb/` folder.

### Info

#### C-IN-01: `check_licences.load_config` crashes with a traceback (exit 1) on a malformed but valid-JSON config

**File:** `tools/check_licences.py:247-263`

**Issue:** If the top-level JSON is a list, `config.get` raises `AttributeError` (reproduced). The same happens if an override entry is not an object. The docstring promises exit 2 for an unusable allow-list, but this path ends in a traceback with exit 1, which reads like a licence violation.

**Fix:** Add `if not isinstance(config, dict): raise ValueError(...)` and `isinstance(entry, dict)` checks. Also check that `aliases`, `classifier_map` and `overrides` are dicts.

#### C-IN-02: plugin/AGENTS.md tells agents to pass names "on standard input", but the CLI never reads stdin

**File:** `plugin/AGENTS.md:69-70`

**Issue:** `epb/cli.py` states "The CLI never prompts and never reads stdin (D-15)". An agent following AGENTS.md may pipe personal names to a command and expect them to be used.

**Fix:** Say "in a file under `.epb/inbox/` when a later command asks for one", and drop "or on standard input" until a command really reads it.

#### C-IN-03: plugin/AGENTS.md's generic exit-code rules conflict with SKILL.md for several codes

**File:** `plugin/AGENTS.md:60-65`, `plugin/skills/evidence-pack/SKILL.md:44,96`

**Issue:** AGENTS.md says exit 3 means "run `doctor --setup`". That cannot fix `PYTHON_TOO_OLD` (when no newer Python exists) or `VENV_UNAVAILABLE`, both exit 3. It says exit 4 means "stop", but SKILL.md step 6 says `SETUP_FAILED` (exit 4) should show the user a terminal command. AGENTS.md also says to follow "the stricter of the two", so on a sandboxed host the agent may never offer the terminal workaround.

**Fix:** Add to AGENTS.md: "except where the skill gives a code-specific step (for example `SETUP_FAILED`, `VENV_UNAVAILABLE`, `PYTHON_TOO_OLD`)".

#### C-IN-04: SKILL.md omits some codes and commands the CLI emits

**File:** `plugin/skills/evidence-pack/SKILL.md:75,95`

**Issue:**
- Scan also warns `LINK_IGNORED` (`epb/sources/scan.py:357`), but step 4 does not list it.
- The exit-2 list leaves out `WORKSPACE_EXISTS`, which is exit 2 (`errors.py:67`). Its generic advice, "Fix the command and run it again", contradicts step 5's "change nothing".
- The `status` command (`epb/commands/status.py`) is not mentioned.

**Fix:** Add `LINK_IGNORED` to step 4, add `WORKSPACE_EXISTS (see step 5)` to the exit-2 line, and give one line on `status --json`.

#### C-IN-05: install-codex leaves hidden staging copies inside the skills folder on failure

**File:** `tools/install-codex.py:104-122, 140-145`

**Issue:** The staging and backup folders (`.evidence-pack.epb-new-*` and `.epb-old-*`) are created inside the Codex skills folder. If the process is killed, or `shutil.rmtree(old, ignore_errors=True)` partly fails (Windows file locks), a complete copy with a `SKILL.md` named `evidence-pack` is left there. A host that scans dot-folders would load the skill twice. Separately, the foreign-target loop returns after the first name, so a user with two conflicts finds them one run at a time.

**Fix:** Stage in a sibling of `dest` on the same filesystem (for example `dest.parent / ".epb-staging"`), report a failed cleanup instead of ignoring it, and collect all foreign names before returning 1.

#### C-IN-06: make-smoke-pack accepts any `--out` path, and its docstring overstates the cleanup

**File:** `tools/make-smoke-pack.py:208-213, 243-248`

**Issue:** AGENTS.md says to keep any `--out` path under `scratch/`, but the tool does not enforce it. `build()` says "nothing is left at `out_path`" when validation fails. In fact `write_pack` leaves any earlier workbook at that path untouched, so a stale workbook can remain and be imported.

**Fix:** Warn (or refuse without `--force`) when `out_path` is not inside `REPO_ROOT / "scratch"`. Change the docstring to "the file at `out_path` is not changed".

#### C-IN-07: The manual says the fallback setup command "starts with `python3`", but it starts with an absolute interpreter path

**File:** `docs/USER-MANUAL.md:253-254`

**Issue:** `setup.terminal_command()` uses `sys.executable`, for example `/usr/bin/python3 /home/.../epb.py doctor --setup`, or a `C:\...\python.exe` path on Windows. A non-technical user told to look for `python3` may doubt the command.

**Fix:** Say "a command that ends with `doctor --setup`".

#### C-IN-08: The bare `BSD` alias and the `BSD License` classifier map to BSD-3-Clause

**File:** `tools/licence-allowlist.json:22-23,34`

**Issue:** "BSD" and the `BSD License` classifier are ambiguous: a BSD-4-Clause (advertising clause) package also passes as BSD-3-Clause. This is low risk but undocumented.

**Fix:** Record the assumption in the allow-list `note`, or map the bare forms to `null` so they need a reviewed override.

#### C-IN-09: The GitHub handle in committed files contains a personal first name

**File:** `plugin/.claude-plugin/plugin.json:8-9`, `docs/USER-MANUAL.md:194,219`, design §20 A16

**Issue:** CLAUDE.md says "Never write real names in committed files." The `ashley-eyekyam` handle is the owner's account and the install route needs it, so this is almost certainly intended. It is listed only so the owner can confirm the exception explicitly, for example by naming it in CLAUDE.md beside the `docs/reference/` exception.

**Fix:** Either note the exception in CLAUDE.md/AGENTS.md, or move the repo to an organisation handle.

---

_Reviewed: 2026-10-18T11:27:16Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

---

## Part D: pytest suite and test helpers

## Phase 1: Code Review Report, Part D (test suite)

**Reviewed:** 2026-10-18T11:34:23Z
**Depth:** standard
**Files Reviewed:** 43
**Status:** issues_found

### Summary

I read the full pytest suite and its helpers (`conftest.py`, `tests/epbtest/*`). Where a test depends on product behaviour, I checked the product code under `plugin/skills/evidence-pack/scripts/epb/` and `tools/`. Baseline: `.venv/bin/python -m pytest -q` gives 1255 passed and 3 skipped on Python 3.14. The 3 skips are the expected `network` and `host` opt-ins.

The suite is broad and mostly well-aimed. Its crash, lock and scan-corpus tests are real subprocess tests with meaningful assertions. The main problem is that the green local run does not match what CI will do:

- **CI will fail.** CI sets `PYTHONWARNDEFAULTENCODING=1`, and pytest turns `EncodingWarning` into an error. Under that variable the suite gives 86 failed and 2 errors (D-CR-01). The phase branch has not been pushed since planning, so CI has never run this code.
- **The isolation guards have gaps.** The test-environment guards let some git configuration and a real host CLI through, and the opt-in skip logic can silently skip ordinary tests.
- **Some guards are weaker than their names claim.** This covers the stdlib-only bootstrap check, the "parses as Python 3.6" check, and the crash test for the upgrade transaction.

I checked every finding below against the current source. I reproduced D-CR-01, D-WR-02 and D-WR-03 by running commands.

### Critical Issues

#### D-CR-01: The suite fails under CI's `PYTHONWARNDEFAULTENCODING=1`: 86 failed and 2 errors, while the local run is green

**File:** `.github/workflows/ci.yml:16-17` together with `pyproject.toml` (`filterwarnings = ["error::EncodingWarning"]`). Failing set: `tests/formats/test_contract.py`, `tests/formats/test_validator.py`, `tests/formats/test_writer.py`, `tests/launcher/test_launcher.py` (3 `test_find_python_*` tests), and `tests/tools/test_smoke_pack.py` (2 collection or fixture errors).

**Issue:** The CI job sets `PYTHONWARNDEFAULTENCODING: "1"`, and pytest escalates every `EncodingWarning` to an error. Local runs do not set the variable, so the warnings never appear. Reproduce with `PYTHONWARNDEFAULTENCODING=1 .venv/bin/python -m pytest -q`, which gives `86 failed, 1167 passed, 3 skipped, 2 errors`. There are two root causes:

1. **openpyxl.** Every workbook write in `epb/formats/writer.py:122` (`_save`) goes through openpyxl's `create_temporary_file()`. That function calls `tempfile.NamedTemporaryFile(mode="w+")` with no encoding. Python 3.11 emits the same warning: I confirmed it with the local uv-managed `python3.11`.
2. **The launcher's own probe.** `epb/launcher.py:216-223` (`_probe`) calls `subprocess.run(..., universal_newlines=True)` without `encoding=`.

So the Phase 1 exit bar ("Linux CI ... all green") cannot be met as the code stands. The validation map also never tells contributors to run with the CI variable.

**Fix:**
```toml
## pyproject.toml: keep the guard for our own code, and silence only openpyxl's temp-file call
filterwarnings = [
    "error::EncodingWarning",
    "ignore:'encoding' argument not specified:EncodingWarning:tempfile",
]
```
```python
## epb/launcher.py _probe (encoding= exists on subprocess.run since 3.6, so the old-syntax rule still holds)
completed = subprocess.run(
    list(prefix) + ["-c", _PROBE_CODE],
    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    universal_newlines=True, encoding="utf-8", errors="replace", timeout=PROBE_TIMEOUT,
)
```
If the tempfile-module ignore is too broad, wrap the `wb.save()` in `writer._save` in `warnings.catch_warnings()` and filter only `EncodingWarning` there. Either way, set `PYTHONWARNDEFAULTENCODING=1` in `[tool.pytest.ini_options]` through an `env`-setting conftest hook, or document it in the quick-run command, so that local runs match CI.

### Warnings

#### D-WR-01: The opt-in skip matches keywords, not markers, so a parametrize id `host` or `network` silently skips an ordinary test

**File:** `tests/conftest.py:167-175`

**Issue:** `if marker in item.keywords` is true for any keyword named `network` or `host`, not only for the marker. pytest adds parametrize ids, function names and parent node names to `item.keywords`. I confirmed this with a scratch test: `@pytest.mark.parametrize("x", ["host", ...])` gives `"host" in request.node.keywords == True`. A future `parametrize(..., ["host", ...])`, for example over doctor report fields or sync providers, or a `tests/network/` folder, would be skipped without notice. Nothing triggers this today: there are only 3 skips.

**Fix:**
```python
for item in items:
    if item.get_closest_marker(marker) is not None:
        item.add_marker(skip)
```

#### D-WR-02: The git isolation is incomplete: `GIT_CONFIG_GLOBAL`, `GIT_DIR`, `GIT_INDEX_FILE` and `GIT_WORK_TREE` leak into tests

**File:** `tests/conftest.py:27-44` (`_ENV_TO_CLEAR`, `_ENV_TO_SET`)

**Issue:** The fake home hides `~/.gitconfig`, and `GIT_CONFIG_NOSYSTEM` hides `/etc/gitconfig`. But git still honours `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_COUNT/KEY_n/VALUE_n`, `GIT_CONFIG_PARAMETERS`, `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and `GIT_CEILING_DIRECTORIES` from the caller's environment. The `repo` fixtures (`test_gitcheck.py:25-34`, `test_git_warning.py:43-52`) and `epb.doctor.gitcheck` (`env=dict(os.environ, ...)`) inherit all of them.

I reproduced the failure: with `GIT_CONFIG_GLOBAL` pointing at a file that sets `commit.gpgsign=true`, `tests/doctor/test_gitcheck.py` and `tests/workspace/test_git_warning.py` give `20 passed, 15 errors`. If the suite runs from a git hook, an inherited absolute `GIT_INDEX_FILE` or `GIT_DIR` could also point the fixtures' `git add` and `git commit` at the real repository.

**Fix:** Add `"GIT_CONFIG_GLOBAL"`, `"GIT_CONFIG_PARAMETERS"`, `"GIT_CONFIG_COUNT"`, `"GIT_DIR"`, `"GIT_WORK_TREE"`, `"GIT_INDEX_FILE"`, `"GIT_OBJECT_DIRECTORY"`, `"GIT_ALTERNATE_OBJECT_DIRECTORIES"` and `"GIT_CEILING_DIRECTORIES"` to `_ENV_TO_CLEAR`. Also clear any `GIT_CONFIG_KEY_*` and `GIT_CONFIG_VALUE_*` variables in a loop over `os.environ`.

#### D-WR-03: `test_claude_validate_strict` runs the real Claude Code CLI in the default suite, against the `host` marker's contract and the no-network rule

**File:** `tests/packaging/test_manifests.py:97-114`

**Issue:** `pyproject.toml` defines `host` as "drives a real Claude Code or Codex CLI; runs only when EPB_HOST_TESTS=1". This test drives the real `claude` binary but carries no marker, so it runs on every developer machine that has the CLI. It took 1.28 s here, the 5th-slowest test.

The child inherits the fake `HOME` but not a cleared `CLAUDE_CONFIG_DIR`, and it inherits every `CLAUDE_CODE_*` session variable. The in-process socket guard does not cover subprocesses, so any update check or telemetry from the CLI is real network traffic. That conflicts with the CLAUDE.md rule "Tests: pytest (no network ...)" and with the conftest docstring's claim that "tests spawn only `epb` ... and never pip".

Real tool probes have the same footprint. `probes.collect()` in `run_setup` (`epb/doctor/setup.py:291`) and the `doctor` subprocess tests execute the host's real `soffice`, `ffmpeg`, `7z`, `tesseract`, `pandoc` and `git`.

**Fix:** Mark the test `@pytest.mark.host`. CI already runs `claude plugin validate` as its own guarded step. Pass `env=dict(os.environ, CLAUDE_CONFIG_DIR=str(tmp_path / "claude"))` and drop the `CLAUDE_CODE_*` variables. Correct the conftest docstring to say which binaries tests do spawn. Where tool probes are not under test, inject `which=lambda name: None` into `probes.collect`.

#### D-WR-04: The stdlib-only bootstrap guard never imports `epb.doctor.setup` or runs `doctor`, which are the code that runs before any package exists

**File:** `tests/launcher/test_launcher.py:276-325`

**Issue:** `_BLOCKING_SCRIPT` imports `epb.launcher`, `epb.errors` and `epb.cli`, then calls `build_parser()`. That covers the module-level imports of the command modules. But `commands/doctor.py:60` imports `epb.doctor.setup` lazily, inside `run()`, and the guard never runs any command. I confirmed that `'epb.doctor.setup' in sys.modules` is `False` after the guard's imports.

Every other `doctor` and `doctor --setup` test runs in the dev venv, which has all of the third-party packages installed. A `import yaml` or `import jsonschema` added to `setup.py`, or a lazy third-party import inside `probes.collect()`, would therefore pass the whole suite. It would then crash first-time setup for every new user (PKG-06).

**Fix:** In the blocking script, also do `import epb.doctor.setup, epb.doctor.probes, epb.doctor.report`. Then exercise the bootstrap path, for example `epb.cli.main(["--json", "doctor"])` with the env missing, inside the blocker, and assert that no blocked module is in `sys.modules` afterwards.

#### D-WR-05: The "parses as Python 3.6" guard cannot see several 3.7–3.9 constructs that would crash the launcher before its friendly version message

**File:** `tests/launcher/test_launcher.py:247-249`

**Issue:** `ast.parse(..., feature_version=(3, 6))` is only a partial grammar check. I verified on 3.14 that it does **not** flag any of these:

- `from __future__ import annotations` (a SyntaxError before 3.7)
- `f"{x=}"`-style specifiers, tested with `f"{a=}"` (3.8+)
- unparenthesised `return *a, *b` (3.8+)
- relaxed decorators `@a.b[c]` (3.9+)
- runtime-evaluated annotations such as `def f() -> str | None` or `list[str]` (a TypeError at import on 3.8 and 3.9)

Ubuntu 20.04 ships 3.8 and Debian 11 ships 3.9, so these are exactly the users who need the `PYTHON_TOO_OLD` message. The launcher is clean today: I ran `epb.py --json status` under the local uv Python 3.9 and it returned `PYTHON_TOO_OLD` with exit 3. But the test would not catch a regression.

**Fix:** Add a real execution test that skips when the interpreter is absent. Run `epb.py --json status` under the oldest interpreter found by `shutil.which("python3.8")` or `"python3.9"`, or a uv-managed one, and assert the `PYTHON_TOO_OLD` envelope. Also add AST checks that reject `from __future__ import annotations` and any `BinOp(BitOr)` or `Subscript` inside annotations in the three `OLD_SYNTAX_FILES`.

#### D-WR-06: The upgrade transaction is outside the "crash at every transaction step" harness

**File:** `tests/store/test_crash_resume.py` (whole file) and `tests/store/test_upgrade.py`

**Issue:** Plan 01-12 calls for "real `os._exit` crashes at every transaction step", and `Transaction.stage_backup` and `run_upgrade` belong to that plan. The crash matrix covers `init`, `scan` and a state-only transaction. It never crashes the D-09 upgrade, which is the transaction that backs up and rewrites every record (`test_upgrade_backs_up_and_rewrites_source_records`).

A crash between applying the restamped source records and `state.json` has no coverage. Neither does a crash during the `pre-upgrade/` backup copy. Upgrade tests only run in-process with a monkeypatched `SCHEMA_VERSION`, and a subprocess crash run cannot see that patch.

**Fix:** Add a child-process script, in the style of `STATE_ONLY_SCRIPT`, that patches `state.SCHEMA_VERSION = 2`, registers the synthetic step and runs `cli.main(["init", "--json", "--case", case])`. Record its checkpoints with `EPB_TEST_RECORD_CHECKPOINTS`, crash at each one, then `txn.recover` and re-run. Assert `assert_workspace_consistent`, exactly one `pre-upgrade/` backup, and `schema_version == 2` on every record.

#### D-WR-07: The crash helper fails open, and the "every checkpoint" assertions are tautological

**File:** `tests/epbtest/crash.py:19-29`; `tests/store/test_crash_resume.py:107-126, 174-195, 240-269`

**Issue:** `list_checkpoints` returns `[]` when the record file was never written, for example if the variable name drifts or `faults.checkpoint` stops being called. `test_init_resumes_after_crash_at_every_checkpoint` never asserts that `points` is non-empty. Its only guard is `assert len(tried) == len(points)`, and `tried` is appended once per element of `points`, so that assertion can never fail. The test therefore passes vacuously on an empty list. It is saved today only by the sibling `test_checkpoints_recorded_in_order`, which a `-k resumes` run skips. The same tautology appears in `test_state_only_transaction` and `test_scan_resumes_after_crash_at_every_checkpoint`.

**Fix:** In `list_checkpoints`, `assert record.is_file(), "no checkpoint was recorded; is EPB_TEST_RECORD_CHECKPOINTS still read by epb.faults?"`, and return a non-empty list or fail. Replace `assert len(tried) == len(points)` with `assert points` before the loop. For init, also compare the resumed `state.json` and `case.yaml` with a clean run through `_strip_volatile`, as `test_pre_and_post_manifest` already does for one point.

#### D-WR-08: `make_fake_env` writes its `.pth` to a folder the venv never reads when the suite runs under a Debian or Ubuntu system Python

**File:** `tests/epbtest/envkit.py:20-26`

**Issue:** `sysconfig.get_path("purelib", vars={"base": path, ...})` uses the running interpreter's default scheme. Under a dev venv or setup-python that is `posix_prefix` or `venv`, giving `<env>/lib/pythonX.Y/site-packages`. Under Debian or Ubuntu's system `/usr/bin/python3` it is `posix_local`. I verified that here: `get_default_scheme() == 'posix_local'`, and the path resolves to `/X/local/lib/python3.14/dist-packages`, which a venv never puts on `sys.path`.

`dev_paths` then also points at `/usr/local/...` rather than where apt or `--user` packages live. With a system pytest, `test_doctor_json_after_setup` and `test_doctor_human_after_setup` would report missing core packages, as would `test_missing_optional_tools_never_change_the_exit_code` and `test_reexec_passes_through_exit_code_and_output`. `tests/packaging/test_requirements.py` explicitly expects to run "under a system pytest". CI uses setup-python and is not affected.

**Fix:**
```python
env_purelib = Path(sysconfig.get_path("purelib", scheme="venv",
                                      vars={"base": str(path), "platbase": str(path)}))
dev_paths = list(dict.fromkeys(p for p in sys.path if p.endswith(("site-packages", "dist-packages"))))
```

#### D-WR-09: `test_findings_sorted_and_stable` never checks on-disk ordering, because it builds defect rows and then writes a valid default pack

**File:** `tests/formats/test_validator.py:396-412`

**Issue:** `rows` (Low priority, `a,b` tags, blank Type, bad QA Status) is built, but `_pack(tmp_path)` is called with no `rows`, so the on-disk workbook holds one valid row. The disk half therefore only checks that one `FORMAT_MARKER` finding is deterministic. The in-memory half compares `validate_rows(rows)` with `validate_rows(list(rows))`, which is the same list in the same order, so it cannot detect order dependence. No test anywhere asserts the order of more than one `validate_workbook` finding: `test_plain_openpyxl_number_formula_boolean` compares a `Counter`.

**Fix:** Use `path = _pack(tmp_path, rows=[valid_row(1), valid_row(2)])`, then plant the same four defects with `_mutate`. Assert the exact `[(f.sheet, f.cell, f.code) ...]` list from `validate_workbook`. Compare `validate_rows(metadata(), rows)` with `validate_rows(metadata(), rows[::-1])` after sorting, or assert that the output is sorted by `(sheet, row, column, code)`.

### Info

#### D-IN-01: Several "never does X" static guards match one spelling only

**File:** `tests/store/test_lock.py:158-160`; `tests/launcher/test_launcher.py:332-343`; `tests/doctor/test_gitcheck.py:197-214`

**Issue:** These guards each catch one spelling and miss the others:

- `"os.kill" not in source` misses `from os import kill`, `signal.pthread_kill` and `os.waitpid`.
- `test_never_prompts` misses `getpass.getpass`, `from sys import stdin` and `open(0)`.
- The gitcheck subcommand check only scans double-quoted literals.

**Fix:** Use AST walks for `Name`/`Attribute`/`ImportFrom` nodes over the forbidden symbols, for example any reference to `kill` or `pthread_kill` from `os` or `signal`, and to `getpass`, and check single-quoted literals as well.

#### D-IN-02: `test_no_absolute_path_is_rendered` cannot fail

**File:** `tests/index/test_index.py:333-337`

**Issue:** None of the synthetic inputs (`CASE`, `state`, `synthetic_sources`, `run`) contains an absolute path, and `IndexInputs` carries no case root. The renderer would have to invent one for this test to fail. The real protection is `tests/workspace/test_layout.py::test_no_absolute_path_user_or_host_in_any_file`.

**Fix:** Feed a source whose `versions[].paths` or a run summary holds `/home/someone/x.pdf`, and assert that it is not echoed. Otherwise delete the test.

#### D-IN-03: `pytest.raises(EpbError)` without checking the error code

**File:** `tests/workspace/test_status.py:213-214`; `tests/launcher/test_setup.py:394-395, 406-407`

**Issue:** Any `EpbError` satisfies these blocks, including a different one caused by a regression, for example `INTERNAL_ERROR` instead of `NOT_A_WORKSPACE` or `SETUP_FAILED`.

**Fix:** Bind with `as caught` and assert `caught.value.code`.

#### D-IN-04: The launcher test runs `init` with the real repo checkout as its working folder, and its `case_dir` fixture is unused

**File:** `tests/launcher/test_setup.py:405-411`

**Issue:** `case_dir` is requested but never used. `launcher.main(["init", "--json"])` runs with the pytest cwd, which is the repo root. If a regression made the failed environment count as current, the launcher would route `init` at the developer's checkout.

**Fix:** Call `monkeypatch.chdir(case_dir)`, or pass `["--case", str(case_dir), "init", "--json"]`.

#### D-IN-05: The network guard does not cover DNS or UDP

**File:** `tests/conftest.py:47-60`

**Issue:** Only `connect`, `connect_ex` and `create_connection` are refused. `socket.getaddrinfo` and `sendto`/`sendmsg` still reach the resolver and the network. `test_no_network.py` asserts only the three patched calls.

**Fix:** Also patch `socket.getaddrinfo` (allowing `localhost` and numeric hosts if needed), `socket.socket.sendto` and `socket.socket.sendmsg`. Add matching meta-tests.

#### D-IN-06: Schema-hygiene tests cover two of the six schemas

**File:** `tests/schemas/test_state_schema.py:292-308`

**Issue:** `test_every_object_is_closed` and `test_no_format_keywords` run only for `state` and `chunks`. I checked `run`, `case` and `source` by hand and they are closed today, and `envelope.data` is open on purpose. A future open object or `format` keyword in those schemas would pass unnoticed.

**Fix:** Parametrize over every `*.schema.json` in `epb/schemas/`, and list `envelope:#/properties/data` as the one allowed open map.

#### D-IN-07: Small helper and assumption issues

**File:** `tests/epbtest/packkit.py:311-331`; `tests/store/test_lock.py:570`; `tests/doctor/test_gitcheck.py:114-118`, `tests/workspace/test_git_warning.py:99-101`

**Issue:** Three small problems:

- `valid_row(n, **overrides)` says that overrides "use header names via a dict". Most headers contain spaces and cannot be keyword names, which is why every caller uses `with_values` instead.
- `socket.gethostname() not in text` has no minimum length. `test_layout.py` uses `len(host) >= 4`, but here a one- or two-character hostname could falsely match the pid or the timestamp.
- The "outside any repository" tests assume `tmp_path` is not inside a git work tree or a sync-named folder. That fails if `TMPDIR` or `--basetemp` sits inside a dotfiles repo under `$HOME`.

**Fix:** Drop `**overrides` from `valid_row` or correct its docstring. Apply the same `len(host) >= 4` guard in `test_lock.py`. Set `GIT_CEILING_DIRECTORIES=str(tmp_path.parent)` in those tests, or skip with a reason when `git -C tmp_path rev-parse` succeeds.

---

_Reviewed: 2026-10-18T11:34:23Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
