---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: A-CR-01
    severity: critical
    disposition: open
    title: "Input file names inject arbitrary Markdown into INDEX.md (extra headings, forged tick lines)"
  - id: A-CR-02
    severity: critical
    disposition: open
    title: "A failed `init` writes `.epb/`, `.epb/lock` and `.epb/tmp/` (breaks the 01-09 \"writes nothing\" must-have)"
  - id: A-WR-01
    severity: warning
    disposition: open
    title: "Recovery bricks the case folder if INDEX.md is touched after a crash, and the hint gives the wrong remedy"
  - id: A-WR-02
    severity: warning
    disposition: open
    title: "`--wait nan` makes a mutating command wait for the lock forever"
  - id: A-WR-03
    severity: warning
    disposition: open
    title: "Case titles containing C1 controls or NEL are accepted but do not round-trip, so re-running `init` fails"
  - id: A-WR-04
    severity: warning
    disposition: open
    title: "Power-cut durability: new directory entries are never fsynced"
  - id: A-WR-05
    severity: warning
    disposition: open
    title: "Recovery renames journal blobs into place without checking them against the manifest hash"
  - id: A-WR-06
    severity: warning
    disposition: open
    title: "Transaction containment only checks the path text, so a symlinked `outputs/` or `.epb/<dir>` can make it write outside the case folder"
  - id: A-WR-07
    severity: warning
    disposition: open
    title: "`--case \"\"` silently means the current folder"
  - id: A-WR-08
    severity: warning
    disposition: open
    title: "Read-only sessions validate older-version files against current schemas, so UPGRADE_PENDING can never be reached"
  - id: A-WR-09
    severity: warning
    disposition: open
    title: "INDEX.md, classified \"shareable\", shows raw input file names (design \u00a76.1 says no personal names)"
  - id: A-IN-01
    severity: info
    disposition: open
    title: "A Windows clean-up failure after a successful commit reports exit 4"
  - id: A-IN-02
    severity: info
    disposition: open
    title: "The manifest `schema_version` is written but never checked"
  - id: A-IN-03
    severity: info
    disposition: open
    title: "The path guard is case-sensitive and allows writing `.epb/lock`"
  - id: A-IN-04
    severity: info
    disposition: open
    title: "`.epb/lock` is \"structural\" and not git-ignored"
  - id: A-IN-05
    severity: info
    disposition: open
    title: "A pending `init` journal makes `status` and other commands say NOT_A_WORKSPACE"
  - id: A-IN-06
    severity: info
    disposition: open
    title: "The launcher prints a traceback and no envelope on Ctrl-C while the env child runs"
  - id: A-IN-07
    severity: info
    disposition: open
    title: "`CORE_IMPORT_NAMES` omits transitive imports"
  - id: A-IN-08
    severity: info
    disposition: open
    title: "Source records are never checked against their file name"
  - id: A-IN-09
    severity: info
    disposition: open
    title: "`detect_timezone` can store non-canonical `posix/\u2026` or `right/\u2026` names"
  - id: A-IN-10
    severity: info
    disposition: open
    title: "The root JSON pointer is \"/\" instead of \"\""
  - id: A-IN-11
    severity: info
    disposition: open
    title: "Schema patterns allow traversal and line breaks in path-like fields; `REMOVED` is duplicated"
  - id: B-CR-01
    severity: critical
    disposition: open
    title: "Most UTF-16LE text files are detected as `audio/mpeg`, and the content type overrides the name"
  - id: B-WR-01
    severity: warning
    disposition: open
    title: "The git check reports \"safe\" whenever git refuses or errors"
  - id: B-WR-02
    severity: warning
    disposition: open
    title: "On Windows, doctor runs `git`, `7z`, `ffmpeg` and the other tools from the current directory first"
  - id: B-WR-03
    severity: warning
    disposition: open
    title: "Setup runs `python -m venv` and `python -m pip` without isolation, so modules in the current directory are imported"
  - id: B-WR-04
    severity: warning
    disposition: open
    title: "`doctor --setup` can delete the environment it is running from"
  - id: B-WR-05
    severity: warning
    disposition: open
    title: "The extras install command is an unquoted shell string that falls back to a bare relative file name"
  - id: B-WR-06
    severity: warning
    disposition: open
    title: "`DATE_PRECISION` accepts impossible dates and a trailing newline"
  - id: B-WR-07
    severity: warning
    disposition: open
    title: "The validator raises instead of returning findings on some malformed input"
  - id: B-WR-08
    severity: warning
    disposition: open
    title: "`validate_workbook` trusts the sheet's declared `<dimension>`, so it can skip rows and report a false total mismatch"
  - id: B-WR-09
    severity: warning
    disposition: open
    title: "Renaming a known file never refreshes its stored MIME type or mismatch"
  - id: B-WR-10
    severity: warning
    disposition: open
    title: "NFC path keys cannot reopen a non-NFC file name on Linux or Windows"
  - id: B-WR-11
    severity: warning
    disposition: open
    title: "One pre-1970 file timestamp aborts the whole scan with `RECORD_INVALID`"
  - id: B-IN-01
    severity: info
    disposition: open
    title: "Junk filtering is inconsistent about letter case and silent about what it drops"
  - id: B-IN-02
    severity: info
    disposition: open
    title: "A note whose content is identical to its target file is reported as an orphan with a false message"
  - id: B-IN-03
    severity: info
    disposition: open
    title: "Some HEIF/HEIC brands are classed as `video/mp4`"
  - id: B-IN-04
    severity: info
    disposition: open
    title: "The git checks inherit `GIT_DIR`, `GIT_WORK_TREE` and `GIT_INDEX_FILE` and do not disable fsmonitor"
  - id: B-IN-05
    severity: info
    disposition: open
    title: "The pip self-upgrade bypasses the two-week rule"
  - id: B-IN-06
    severity: info
    disposition: open
    title: "Removing control characters silently joins words in quoted text"
  - id: B-IN-07
    severity: info
    disposition: open
    title: "The 32,767 limit is counted in code points, while Excel counts UTF-16 code units"
  - id: B-IN-08
    severity: info
    disposition: open
    title: "The 7-Zip version regex misses common builds"
  - id: B-IN-09
    severity: info
    disposition: open
    title: "`write_pack` uses a fixed temporary sibling name"
  - id: C-CR-01
    severity: critical
    disposition: open
    title: "INDEX.md and the \"structural\" records expose input file names, contradicting the manual's de-identification promise"
  - id: C-WR-01
    severity: warning
    disposition: open
    title: "`check_dependency_age.py --pins` emits unvalidated exception text into a pip requirements file (option injection), unlike `doctor --setup`"
  - id: C-WR-02
    severity: warning
    disposition: open
    title: "The age check uses the EARLIEST file upload time, so a wheel added later to an old release passes"
  - id: C-WR-03
    severity: warning
    disposition: open
    title: "The licence check passes a package whose classifiers list both an allowed and a disallowed licence"
  - id: C-WR-04
    severity: warning
    disposition: open
    title: "Licence overrides apply to every future version of the package"
  - id: C-WR-05
    severity: warning
    disposition: open
    title: "CI actions are pinned to mutable tags, with no `permissions:` block and persisted credentials"
  - id: C-WR-06
    severity: warning
    disposition: open
    title: "The D-02 `claude plugin validate --strict` gate never runs in CI"
  - id: C-WR-07
    severity: warning
    disposition: open
    title: "pip itself is exempt from the age rule and installed unpinned (`pip>=26.1`)"
  - id: C-WR-08
    severity: warning
    disposition: open
    title: "The documented Ubuntu 22.04 route (\"Setup finds Python 3.11 on its own\") leaves every other command failing with PYTHON_TOO_OLD"
  - id: C-WR-09
    severity: warning
    disposition: open
    title: "`.gitignore` protects `.epb/` of a case run inside the repo, but not its `inputs/`, `outputs/` or `INDEX.md`"
  - id: C-IN-01
    severity: info
    disposition: open
    title: "`check_licences.load_config` crashes with a traceback (exit 1) on a malformed but valid-JSON config"
  - id: C-IN-02
    severity: info
    disposition: open
    title: "plugin/AGENTS.md tells agents to pass names \"on standard input\", but the CLI never reads stdin"
  - id: C-IN-03
    severity: info
    disposition: open
    title: "plugin/AGENTS.md's generic exit-code rules conflict with SKILL.md for several codes"
  - id: C-IN-04
    severity: info
    disposition: open
    title: "SKILL.md omits some codes and commands the CLI emits"
  - id: C-IN-05
    severity: info
    disposition: open
    title: "install-codex leaves hidden staging copies inside the skills folder on failure"
  - id: C-IN-06
    severity: info
    disposition: open
    title: "make-smoke-pack accepts any `--out` path, and its docstring overstates the cleanup"
  - id: C-IN-07
    severity: info
    disposition: open
    title: "The manual says the fallback setup command \"starts with `python3`\", but it starts with an absolute interpreter path"
  - id: C-IN-08
    severity: info
    disposition: open
    title: "The bare `BSD` alias and the `BSD License` classifier map to BSD-3-Clause"
  - id: C-IN-09
    severity: info
    disposition: open
    title: "The GitHub handle in committed files contains a personal first name"
  - id: D-CR-01
    severity: critical
    disposition: open
    title: "The suite fails under CI's `PYTHONWARNDEFAULTENCODING=1`: 86 failed and 2 errors, while the local run is green"
  - id: D-WR-01
    severity: warning
    disposition: open
    title: "The opt-in skip matches keywords, not markers, so a parametrize id `host` or `network` silently skips an ordinary test"
  - id: D-WR-02
    severity: warning
    disposition: open
    title: "The git isolation is incomplete: `GIT_CONFIG_GLOBAL`, `GIT_DIR`, `GIT_INDEX_FILE` and `GIT_WORK_TREE` leak into tests"
  - id: D-WR-03
    severity: warning
    disposition: open
    title: "`test_claude_validate_strict` runs the real Claude Code CLI in the default suite, against the `host` marker's contract and the no-network rule"
  - id: D-WR-04
    severity: warning
    disposition: open
    title: "The stdlib-only bootstrap guard never imports `epb.doctor.setup` or runs `doctor`, which are the code that runs before any package exists"
  - id: D-WR-05
    severity: warning
    disposition: open
    title: "The \"parses as Python 3.6\" guard cannot see several 3.7\u20133.9 constructs that would crash the launcher before its friendly version message"
  - id: D-WR-06
    severity: warning
    disposition: open
    title: "The upgrade transaction is outside the \"crash at every transaction step\" harness"
  - id: D-WR-07
    severity: warning
    disposition: open
    title: "The crash helper fails open, and the \"every checkpoint\" assertions are tautological"
  - id: D-WR-08
    severity: warning
    disposition: open
    title: "`make_fake_env` writes its `.pth` to a folder the venv never reads when the suite runs under a Debian or Ubuntu system Python"
  - id: D-WR-09
    severity: warning
    disposition: open
    title: "`test_findings_sorted_and_stable` never checks on-disk ordering, because it builds defect rows and then writes a valid default pack"
  - id: D-IN-01
    severity: info
    disposition: open
    title: "Several \"never does X\" static guards match one spelling only"
  - id: D-IN-02
    severity: info
    disposition: open
    title: "`test_no_absolute_path_is_rendered` cannot fail"
  - id: D-IN-03
    severity: info
    disposition: open
    title: "`pytest.raises(EpbError)` without checking the error code"
  - id: D-IN-04
    severity: info
    disposition: open
    title: "The launcher test runs `init` with the real repo checkout as its working folder, and its `case_dir` fixture is unused"
  - id: D-IN-05
    severity: info
    disposition: open
    title: "The network guard does not cover DNS or UDP"
  - id: D-IN-06
    severity: info
    disposition: open
    title: "Schema-hygiene tests cover two of the six schemas"
  - id: D-IN-07
    severity: info
    disposition: open
    title: "Small helper and assumption issues"
open: 79
total: 79
recorded: 2026-10-18T11:59:59.443047+00:00
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| A-CR-01 | critical | open | - |
| A-CR-02 | critical | open | - |
| A-WR-01 | warning | open | - |
| A-WR-02 | warning | open | - |
| A-WR-03 | warning | open | - |
| A-WR-04 | warning | open | - |
| A-WR-05 | warning | open | - |
| A-WR-06 | warning | open | - |
| A-WR-07 | warning | open | - |
| A-WR-08 | warning | open | - |
| A-WR-09 | warning | open | - |
| A-IN-01 | info | open | - |
| A-IN-02 | info | open | - |
| A-IN-03 | info | open | - |
| A-IN-04 | info | open | - |
| A-IN-05 | info | open | - |
| A-IN-06 | info | open | - |
| A-IN-07 | info | open | - |
| A-IN-08 | info | open | - |
| A-IN-09 | info | open | - |
| A-IN-10 | info | open | - |
| A-IN-11 | info | open | - |
| B-CR-01 | critical | open | - |
| B-WR-01 | warning | open | - |
| B-WR-02 | warning | open | - |
| B-WR-03 | warning | open | - |
| B-WR-04 | warning | open | - |
| B-WR-05 | warning | open | - |
| B-WR-06 | warning | open | - |
| B-WR-07 | warning | open | - |
| B-WR-08 | warning | open | - |
| B-WR-09 | warning | open | - |
| B-WR-10 | warning | open | - |
| B-WR-11 | warning | open | - |
| B-IN-01 | info | open | - |
| B-IN-02 | info | open | - |
| B-IN-03 | info | open | - |
| B-IN-04 | info | open | - |
| B-IN-05 | info | open | - |
| B-IN-06 | info | open | - |
| B-IN-07 | info | open | - |
| B-IN-08 | info | open | - |
| B-IN-09 | info | open | - |
| C-CR-01 | critical | open | - |
| C-WR-01 | warning | open | - |
| C-WR-02 | warning | open | - |
| C-WR-03 | warning | open | - |
| C-WR-04 | warning | open | - |
| C-WR-05 | warning | open | - |
| C-WR-06 | warning | open | - |
| C-WR-07 | warning | open | - |
| C-WR-08 | warning | open | - |
| C-WR-09 | warning | open | - |
| C-IN-01 | info | open | - |
| C-IN-02 | info | open | - |
| C-IN-03 | info | open | - |
| C-IN-04 | info | open | - |
| C-IN-05 | info | open | - |
| C-IN-06 | info | open | - |
| C-IN-07 | info | open | - |
| C-IN-08 | info | open | - |
| C-IN-09 | info | open | - |
| D-CR-01 | critical | open | - |
| D-WR-01 | warning | open | - |
| D-WR-02 | warning | open | - |
| D-WR-03 | warning | open | - |
| D-WR-04 | warning | open | - |
| D-WR-05 | warning | open | - |
| D-WR-06 | warning | open | - |
| D-WR-07 | warning | open | - |
| D-WR-08 | warning | open | - |
| D-WR-09 | warning | open | - |
| D-IN-01 | info | open | - |
| D-IN-02 | info | open | - |
| D-IN-03 | info | open | - |
| D-IN-04 | info | open | - |
| D-IN-05 | info | open | - |
| D-IN-06 | info | open | - |
| D-IN-07 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved.
