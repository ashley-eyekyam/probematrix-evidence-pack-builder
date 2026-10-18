---
phase: "1"
slug: "foundations"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-18"
---

# Phase 1 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail. Register authored at plan time (16 plans); mitigations verified by gsd-security-auditor on 2026-10-18 at branch head 131e775 (ASVS L1, block_on: high).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PyPI → dev environment | Third-party packages are downloaded and executed on the developer machine |  |
| test process → network | Tests could reach the network and make results depend on outside state |  |
| owner decisions → design text | A transcription error would make the spec contradict a locked decision |  |
| agent/user argv → CLI | Arguments come from an agent and may be malformed |  |
| launcher → interpreter found on PATH | The launcher executes an interpreter it discovered |  |
| CLI → agent (stdout) | Error output is read by an AI agent |  |
| item text → spreadsheet cell | Text later derived from evidence may start with formula characters |  |
| workbook file → validator | The validator parses workbooks that may come from outside (the prototype pack, user files) |  |
| workbook → ProbeMatrix importer | The importer reads every cell through String(...) |  |
| PyPI → CI environment | CI installs and runs third-party code on every push |  |
| GitHub Actions marketplace → CI | Workflow actions are third-party code |  |
| package metadata → licence check | Licence metadata is self-declared by each package |  |
| repo → user's skill folder | The installer writes into $HOME/.agents/skills, shared with other skills |  |
| marketplace → host | Hosts trust the manifest names to choose what to install |  |
| process crash → .epb state | A crash can stop a write at any point |  |
| .epb/state.json on disk → CLI | The file may be hand-edited, damaged, or written by a newer plugin |  |
| doctor → external binaries | doctor executes tools found on PATH to read their versions |  |
| case folder → sync service / git | Raw-text state under .epb/private could be uploaded or committed |  |
| argv (title, slug, prefix, timezone) → case.yaml | User and agent text becomes persisted settings and, later, file names |  |
| case.yaml on disk → loader | The file could be edited or damaged |  |
| PyPI → user's private environment | End users download and run third-party packages |  |
| setup → user's file system | Setup creates and removes folders under the per-user data folder |  |
| host sandbox → setup | Codex or Claude Code may block network or writes outside the project |  |
| case folder → git / sync services | Raw-text state could leave the machine through git or a sync client |  |
| workspace files → shareable artefacts | INDEX.md and trackable state may be shared with other people |  |
| two CLI processes → one case folder | Agents may launch overlapping commands, including parallel subagents |  |
| plugin version → workspace version | A workspace may be older or newer than the installed plugin |  |
| inputs/ (user files, possibly hostile) → scan | scan reads arbitrary user-supplied files, links and archives |  |
| scan → .epb records | File names and paths become persisted state |  |
| user edits in inputs/ → custody record | How a change is classified decides which source and version later evidence cites |  |
| SKILL.md → end user's agent | The agent follows these instructions with the user's files and permissions |  |
| marketplace → host plugin cache | The install copies whatever the marketplace source points at |  |
| manual → non-technical user | Users act on what the manual tells them about privacy and setup |  |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Tampering | dependency resolution in Task 3 | high | mitigate | Install with `pip --uploaded-prior-to P14D` after upgrading pip to >= 26.1, so no release younger than 14 days is resolved | closed |
| T-01-02 | Information disclosure | test suite | low | mitigate | Autouse `_no_network` fixture refuses socket connections; autouse `_isolated_home` keeps tests away from the real profile | closed |
| T-01-SC (01-01) | Tampering | pip installs of plugin/requirements.txt and requirements-dev.txt | high | mitigate | Blocking-human legitimacy checkpoint (Task 2) before the first install; every package was flagged SUS and is confirmed by the owner against its PyPI page and source repository | closed |
| T-01-03 | Repudiation | §20 amendment rows | low | mitigate | Every row cites its D-NN or research question so a reviewer can trace it to CONTEXT.md; A1 to A15 stay untouched (checked in acceptance criteria) | closed |
| T-01-SC (01-02) | Tampering | package installs | low | accept | This plan installs no packages; the 01-01 legitimacy gate covers the dev set | closed |
| T-01-04 | Information disclosure | cli.main exception mapping | medium | mitigate | Tracebacks go to stderr only; the envelope carries the exception type and a stable code, not the traceback | closed |
| T-01-05 | Elevation of privilege | launcher.find_python and re-exec | medium | mitigate | Only fixed candidate names are probed via `shutil.which`; every subprocess uses an argv list (never `shell=True`) with a timeout; the re-exec target is the env interpreter at the fixed D-03 path | open — below high threshold (non-blocking): re-exec subprocess calls (launcher.py:340, :362) have no timeout; probes do |
| T-01-06 | Tampering | argparse option parsing | low | mitigate | `allow_abbrev=False` so a truncated flag never silently matches another option | closed |
| T-01-SC (01-03) | Tampering | package installs | low | accept | This plan installs no packages; the 01-01 legitimacy gate covers the dev set | closed |
| T-01-07 | Tampering | writer._put_text | high | mitigate | Force `data_type = "s"` and `number_format = "@"` on every cell; the raw XML scan rejects any `<f>` element (CELL_FORMULA); never prepend an apostrophe, which would change the text | closed |
| T-01-08 | Denial of service | validate_workbook XML parsing | medium | mitigate | Parse sheet XML with `defusedxml.ElementTree` and load through openpyxl with defusedxml installed (billion-laughs, XXE) | closed |
| T-01-09 | Tampering | silent truncation by openpyxl | medium | mitigate | `validate_rows` runs before writing; 32,767 and longer cells are rejected before and after writing | closed |
| T-01-SC (01-04) | Tampering | package installs | low | accept | This plan installs no packages; the 01-01 legitimacy gate covers the dev set | closed |
| T-01-10 | Tampering | CI dependency install | high | mitigate | `--uploaded-prior-to P14D` at install plus `check_dependency_age.py` after tests; exceptions only from the reviewed `plugin/security-exceptions.json` | closed |
| T-01-11 | Spoofing | licence metadata | low | accept | Metadata is self-declared; the allow-list plus reviewed overrides with reasons are the agreed control (D-11 calibration) | closed |
| T-01-12 | Tampering | actions/checkout@v7, actions/setup-python@v7 | medium | accept | Major-version tags were checked to be older than 14 days; SHA pinning is extra hardening the owner declined (D-11) | closed |
| T-01-SC (01-05) | Tampering | package installs | low | accept | CI installs the same dev set approved at the 01-01 legitimacy checkpoint | closed |
| T-01-13 | Tampering | tools/install-codex.py | medium | mitigate | Replace only folders carrying this installer's `.epb-installed` marker; refuse and exit 1 on a foreign folder; copy without symlinks | closed |
| T-01-14 | Spoofing | manifests and marketplace entry | low | mitigate | Parity test: identical name across all three files and identical version to `epb.__version__` (Codex rejects mismatched names) | closed |
| T-01-SC (01-06) | Tampering | package installs | low | accept | This plan installs no packages | closed |
| T-01-15 | Tampering | txn.commit / recover | high | mitigate | Redo journal with a single commit point (manifest rename), durable writes with fsync, state.json last, idempotent roll-forward in `recover()` | closed |
| T-01-16 | Tampering | schema.check on staging | medium | mitigate | Every record validated against its closed schema before staging; RECORD_INVALID lists every issue and nothing is written | closed |
| T-01-17 | Tampering | load_state | medium | mitigate | Damaged or schema-invalid state exits 4 STATE_INVALID; newer workspace exits 4 WORKSPACE_TOO_NEW; never silently repaired (D-19) | closed |
| T-01-SC (01-07) | Tampering | package installs | low | accept | This plan installs no packages | closed |
| T-01-18 | Elevation of privilege | probes.probe_tool | medium | mitigate | Fixed tool names only, argv lists (never `shell=True`), 10 s timeouts, version read from output with a fixed regex | closed |
| T-01-19 | Information disclosure | case folder inside a sync service | high | mitigate | syncfolders.check warns with SYNC_FOLDER from both init (plan 01-11) and doctor; the manual explains why (plan 01-16) | closed |
| T-01-20 | Information disclosure | .epb/private tracked by git | high | mitigate | gitcheck warns GIT_TRACKS_PRIVATE / GIT_PRIVATE_NOT_IGNORED; init writes the ignore files (plan 01-11) | closed |
| T-01-21 | Tampering | gitcheck | medium | mitigate | Read-only subcommands only (rev-parse, ls-files, check-ignore); a test proves .git is unchanged | closed |
| T-01-SC (01-08) | Tampering | package installs | low | accept | This plan installs no packages | closed |
| T-01-22 | Tampering | yamlio.load_text_yaml | high | mitigate | SafeLoader subclass with no implicit resolvers, duplicate-key rejection and a text-only walk (explicit tags rejected); ruff S506 forbids unsafe loaders | closed |
| T-01-23 | Tampering | casefile.derive_slug and --slug | medium | mitigate | Slug restricted to ^[a-z0-9]+(-[a-z0-9]+)*$, at most 40 characters, Windows reserved names suffixed, so it is safe in later workbook file names | closed |
| T-01-SC (01-09) | Tampering | package installs | low | accept | This plan installs no packages | closed |
| T-01-24 | Tampering | core install in run_setup | high | mitigate | pip >= 26.1 then `--uploaded-prior-to P14D`; exception pins only from the reviewed shipped file (D-18) | closed |
| T-01-25 | Elevation of privilege | run_setup | high | mitigate | Installs only into the private venv with its own interpreter; never the system Python, never sudo; elevated commands (apt) are printed for the user, not run | closed |
| T-01-26 | Tampering | stale rebuild | medium | mitigate | Removes only `data_root()/envs/<this version>` after checking its parent; sibling versions untouched (tested) | closed |
| T-01-27 | Denial of service | hung pip or venv | low | mitigate | Timeouts on every subprocess (300 s venv, 900 s pip); failure leaves no marker so the next run rebuilds | closed |
| T-01-SC (01-10) | Tampering | pip installs of plugin/requirements.txt | high | mitigate | Same package list the owner approved at the 01-01 blocking-human legitimacy checkpoint (precondition on Task 1); no new package is added here | closed |
| T-01-28 | Information disclosure | .epb raw-text folders | high | mitigate | `.epb/.gitignore` with the exact A2 list, `.epb/private/.gitignore` of `*`, post-commit git and sync warnings | closed |
| T-01-29 | Information disclosure | trackable state and INDEX.md | medium | mitigate | Case-relative paths only; test proves no absolute path, home folder, account name or host name appears (prohibition) | closed |
| T-01-30 | Tampering | init over an existing INDEX.md | low | mitigate | Refuse with BAD_ARGUMENT instead of overwriting a file the plugin did not create | closed |
| T-01-SC (01-11) | Tampering | package installs | low | accept | This plan installs no packages | closed |
| T-01-31 | Denial of service | lock.acquire | medium | mitigate | OS advisory lock released on process death, bounded wait with exit 4 LOCK_TIMEOUT naming the holder; no stale-lock heuristics | closed |
| T-01-32 | Tampering | transaction under crash | high | mitigate | Crash at every recorded checkpoint is tested with real `os._exit`; recovery is idempotent, including a crash during recovery | closed |
| T-01-33 | Tampering | older or newer workspace | medium | mitigate | Newer exits 4 WORKSPACE_TOO_NEW; older upgrades only on a mutating command with a pre-upgrade backup in one transaction | closed |
| T-01-34 | Denial of service | Windows PID probing | low | mitigate | No PID liveness checks and no `os.kill` anywhere (os.kill terminates processes on Windows) | closed |
| T-01-SC (01-12) | Tampering | package installs | low | accept | This plan installs no packages | closed |
| T-01-35 | Information disclosure | walk_inputs | high | mitigate | `os.walk(followlinks=False)`; links and junctions are listed as ignored and never read, so nothing outside the case folder is hashed or recorded | closed |
| T-01-36 | Tampering | scan writes | high | mitigate | scan only reads inputs/; the transaction layer refuses any final path under inputs/; a test hashes inputs/ before and after every scan (prohibition) | closed |
| T-01-37 | Denial of service | mime.sniff on hostile files | low | mitigate | Read at most 4,096 bytes; ZIP inspection lists member names only inside try/except; FIFOs and devices are never opened | closed |
| T-01-SC (01-13) | Tampering | package installs | low | accept | This plan installs no packages | closed |
| T-01-38 | Repudiation | classify | medium | mitigate | Deterministic content-centred rules; records are never deleted; every change is written to the run record and shown in INDEX.md, so custody history is reconstructable | closed |
| T-01-39 | Spoofing | sidecar pairing | low | accept | Pairing is by exact file name only; a misnamed note becomes an orphan and is reported, which is the honest outcome | closed |
| T-01-SC (01-14) | Tampering | package installs | low | accept | This plan installs no packages | closed |
| T-01-40 | Tampering | agent behaviour on exit 4 | medium | mitigate | SKILL.md and AGENTS.md tell the agent to stop and report on exit 4 and never edit `.epb/` or evidence (A11, D-19) | closed |
| T-01-41 | Elevation of privilege | agent running setup | medium | mitigate | SKILL.md forbids the agent from running sudo or elevated commands; setup only prints them | closed |
| T-01-42 | Information disclosure | install contents | low | mitigate | Marketplace source `./plugin`; the isolated install test proves no docs/, tests/, tools/ or .planning/ reach the cache | closed |
| T-01-43 | Denial of service | non-spec SKILL.md keys breaking a host | low | mitigate | In-house lint restricts frontmatter to the six portable keys and checks name and length | closed |
| T-01-SC (01-15) | Tampering | package installs | low | accept | This plan installs no packages (the UAT's setup installs the 01-01-approved list) | closed |
| T-01-44 | Information disclosure | privacy chapter | medium | mitigate | Chapter 2 states what reaches the AI host's provider and why sync folders are unsafe; a test checks the required terms; the owner reads it (human-check) | open — below high threshold (non-blocking): owner read-through of manual chapter 2 not yet recorded |
| T-01-45 | Repudiation | manual versus real output | low | mitigate | Golden test keeps quoted doctor and setup output equal to the renderer | closed |
| T-01-SC (01-16) | Tampering | package installs | low | accept | This plan installs no packages | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

Evidence (file:line and enforcing tests) for every closed `mitigate` row is in the auditor's verdict, summarised in the audit trail below.

### Auditor advisories (no status change)

1. T-01-10: CI has never run on this branch (push pending owner approval); `check_dependency_age.py --pins` does not regex-validate exception entries the way `doctor/setup.py:58-59` does (also code-review C-WR-01).
2. T-01-35 / T-01-37: `mime.detect` re-opens the file by path without O_NOFOLLOW / O_NONBLOCK after the hardened fingerprint read.
3. T-01-23: the reserved-name refusal lives only in `derive_slug` / `--slug`; a hand-edited `case.yaml` slug `con` passes the schema.
4. Mitigations not pinned by a test: `allow_abbrev=False` (T-01-06), launcher probe timeout (T-01-05), hostile-XML input (T-01-08); the `os.kill` source test (T-01-34) scans only `lock.py`.
5. T-01-SC (01-01): summary says 16 packages, checkpoint listed 17 names — wording only.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-01-SC (01-02) | This plan installs no packages; the 01-01 legitimacy gate covers the dev set | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-02 | T-01-SC (01-03) | This plan installs no packages; the 01-01 legitimacy gate covers the dev set | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-03 | T-01-SC (01-04) | This plan installs no packages; the 01-01 legitimacy gate covers the dev set | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-04 | T-01-11 | Metadata is self-declared; the allow-list plus reviewed overrides with reasons are the agreed control (D-11 calibration) | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-05 | T-01-12 | Major-version tags were checked to be older than 14 days; SHA pinning is extra hardening the owner declined (D-11) | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-06 | T-01-SC (01-05) | CI installs the same dev set approved at the 01-01 legitimacy checkpoint | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-07 | T-01-SC (01-06) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-08 | T-01-SC (01-07) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-09 | T-01-SC (01-08) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-10 | T-01-SC (01-09) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-11 | T-01-SC (01-11) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-12 | T-01-SC (01-12) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-13 | T-01-SC (01-13) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-14 | T-01-39 | Pairing is by exact file name only; a misnamed note becomes an orphan and is reported, which is the honest outcome | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-15 | T-01-SC (01-14) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-16 | T-01-SC (01-15) | This plan installs no packages (the UAT's setup installs the 01-01-approved list) | owner (plan-time, D-11 where cited) | 2026-10-17 |
| AR-17 | T-01-SC (01-16) | This plan installs no packages | owner (plan-time, D-11 where cited) | 2026-10-17 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-18 | 61 | 59 | 2 (0 blocking) | gsd-security-auditor via /gsd-execute-phase 1 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-18 (2 medium threats remain open below the high block threshold: T-01-05, T-01-44)
