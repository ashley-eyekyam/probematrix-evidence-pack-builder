# Phase 1: Foundations - Context

**Gathered:** 2026-10-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 lays the plugin's skeleton, with no evidence logic yet:
- `plugin/` packaging for Claude Code and Codex
- `epb init` and `epb scan`, with journalled, atomic, locked state
- the importer-exact `EVIDENCE_PACK_V2` format module and a validator stricter than the importer
- guided setup through `epb.py` and `epb doctor --setup`
- Linux CI (pytest, ruff, dependency age, licence allow-list, AGENTS/CLAUDE mirror)
- the first edition of the non-technical manual
- a synthetic edge-case smoke workbook that the owner imports into ProbeMatrix

The scope is fixed by the ROADMAP Phase 1 requirements and success criteria: WS-01…04, 06…09, 11…13; BLD-01…03, 08; PKG-01, 03, 05…09, 11; TST-01, 07; DOC-04, 05.

Already decided, not reopened here: design §20 A1–A15, which cover the `plugin/` subfolder, Python 3.11+, guided setup, Linux-only CI, exit code 4, the `.epb/.gitignore` list, sync-folder warnings, the smoke-import content and the mirrored root AGENTS.md/CLAUDE.md. Lock behaviour (OD-19) is settled by WS-07: wait 60 s, and read-only commands take no lock.

</domain>

<decisions>
## Implementation Decisions

### Packaging and hosts
- **D-01 (OD-13):** Ship `plugin/.codex-plugin/plugin.json` next to `plugin/.claude-plugin/plugin.json` from Phase 1, so the layout is final from day one. The primary Codex route is `codex plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder`. The fallback is a cross-platform Python installer, `tools/install-codex.py`, which copies the plugin's skills into `$HOME/.agents/skills`. It replaces design §5's `install-codex.sh`. Thin `.sh`/`.ps1` wrappers are optional. There is **no** committed `.agents/skills` symlink. A CI test checks that both manifests are valid JSON with the required fields. Which manifest Codex actually reads is proved only in Phase 10 (PKG-10).
- **D-02 (OD-22):** Omit the `skills` key from the Claude manifest, because the default `skills/` scan finds them. Keep `skills` only in the Codex manifest. CI runs `claude plugin validate --strict` when the `claude` CLI is available and skips cleanly otherwise. The root-`CLAUDE.md` half of OD-22 is already settled by A4 and A15: the root is no longer the plugin root.
- **D-03:** The private Python environment lives in **one fixed per-user folder shared by every host**: `~/.local/share/probematrix-epb/` on Linux, `%LOCALAPPDATA%\probematrix-epb\` on Windows and `~/Library/Application Support/probematrix-epb/` on macOS. It does not use `${CLAUDE_PLUGIN_DATA}`. The environment is keyed by plugin version, so an upgrade rebuilds cleanly. The manual names the exact path and explains manual removal. — **Reversibility:** costly — the manual, troubleshooting text and existing user installs all point at this path.
- **D-04:** Phase 1 ships the router skill `plugin/skills/evidence-pack/SKILL.md` in its final location. Its scope is what exists: first-time setup (`doctor --setup`), `init`, `scan` and reading `INDEX.md`, plus a line saying later stages are coming. It carries `scripts/epb.py`, the `scripts/epb/` package and `references/`, with `workspace-contract.md` and `evidence-pack-v2.md` written in Phase 1. Later phases extend this file rather than replace it. The Phase 1 UAT is run the way a user would run it: asking the agent to set up a case folder.

### Schemas and persisted state
- **D-05 (OD-20):** There is a single canonical schema copy, at `plugin/skills/evidence-pack/scripts/epb/schemas/`, loaded through `importlib.resources`. There is **no** root `schemas/` folder or mirror, which amends the design §5 layout. Every install route carries the schemas because they sit inside `skills/`. — **Reversibility:** costly — validate-on-write and every install route depend on the path.
- **D-06 (OD-21):** Add `.epb/inbox/`, `.epb/tmp/`, `.epb/ledger/chunks.json` and `.epb/.gitattributes` (`* -text`) to the workspace contract now. `init` creates `inbox/`, `tmp/` and `.gitattributes`. `chunks.json` is declared now and created on first extraction. `references/workspace-contract.md` documents every path and marks it raw-text/confidential or shareable.
- **D-07 (resolves a WS-13 vs OD-21 conflict):** Chunk data is **split**. `state.json` holds the authoritative per-chunk *status* (chunk id, segment-ID range, `pending|in_progress|done`, claim count) and no raw text, so WS-13 holds and `state.json` stays trackable. `ledger/chunks.json` holds the chunk *plan*, including section headings. Those headings are raw text, and `ledger/` is git-ignored under A2. Both are declared in the Phase 1 schemas.
- **D-08 (OD-29):** Source records carry `parents: [...]`, a list that is empty for top-level inputs, instead of a single `parent`. An identical attachment delivered by two emails is one source with two parents, and Chain of Custody gets one entry per carrier. — **Reversibility:** one-way — it fixes the persisted source schema and the custody output contract.
- **D-09:** Every persisted file carries `schema_version`. A workspace **newer** than the plugin exits 4 (A11). A workspace **older** than the plugin is upgraded automatically on the next *mutating* command: a backup of the `.epb/` state files goes to `.epb/runs/<NNN>/pre-upgrade/`, the registered upgrade steps run in one journalled transaction, and a plain-language report follows. Read-only commands never upgrade. v0.1.0 has no upgrade steps, but the mechanism and its test exist from Phase 1.
- **D-10:** Record D-01, D-02, D-05, D-06, D-07, D-08 and D-12…D-14 as new design §20 amendments (A16 onwards) in Phase 1. Also update §5 (layout and requirements files), §6 (workspace contract) and §8.1 (`parents`) to match, so the design stays the source of truth.

### Dependencies and file-type detection
- **D-11:** Dependencies use plain **minimum pins** (`>=`, per PKG-08), resolved at install. There is no lock file and no hash pinning. The owner's own words: "Just chill on such strict requirements." Calibrate the rest of the phase the same way: meet the requirements, and don't add extra hardening machinery beyond them.
- **D-12 (OD-17, dev part):** The plugin requirements are split this way:
  - `plugin/requirements.txt` holds the permissive core.
  - Each optional extra has its own file, with its licence stated in a header comment.
  - The root `requirements-dev.txt` holds core + pytest + ruff + only the permissively licensed extras, and the licence allow-list check covers it.
  - `requirements-dev-full.txt` adds the GPL/LGPL extras, for the Phase 10 media CI job only.

  This replaces design §5's rule that dev requirements include all optional extras.
- **D-13 (OD-23, MIME):** File types are detected with stdlib `mimetypes` (by extension) plus an in-house magic-byte table covering PDF, ZIP/OOXML, OLE2, PNG, JPEG, GIF, WAV, MP4/MOV, MKV, 7z and gzip, at minimum. When extension and content disagree, **content wins**, and the mismatch is recorded on the source and shown in the scan report. No `python-magic`.
- **D-14 (OD-23, .7z):** `.7z` files are handled only through an external `7z`/`7za`/`7zz` binary. Without one, the input is `unprocessed: 7z tool not installed`. `doctor` lists the tool with per-OS install commands. No py7zr (LGPL). Expansion itself is Phase 2 (WS-05).

### Setup, doctor and smoke workbook
- **D-15:** The `epb` CLI never prompts. `epb init --title "…" [--slug …] [--prefix …] [--timezone …]`. The skill has the agent ask the user only for the case title. It then proposes the slug, the ID prefix (for example `ACM` → `EVD-ACM-001`) and the system timezone, and confirms them in one line. Missing values get defaults: slug from the folder name, prefix from the title's initials, the system timezone.
- **D-16:** The smoke workbook is built by a **repo-only** script, `tools/make-smoke-pack.py`, which is not shipped in `plugin/`. It uses the real format module and validator and writes to a git-ignored scratch path (for example `scratch/smoke/evidence-pack-smoke.xlsx`; add `scratch/` to `.gitignore`). It also prints a checklist of every edge-case value as written. A pytest test builds and validates the same workbook. Nothing generated is committed (A3). The UAT gives the exact command, the file path and the comparison checklist. The owner reports the import result, and the agent never claims it.
- **D-17:** `epb doctor` output for humans is a short, grouped plain-text checklist:
  - **Ready**, for example "Python 3.12 — ready".
  - **Optional, not installed**: what each tool would enable and the single install command for *this* OS.
  - **What to do next.**

  Versions and the install commands for all three OSes appear under `--verbose`. `--json` gives the full machine report, which satisfies PKG-07. The manual quotes this output exactly.

### Added at plan-phase (owner answers to research questions, 2026-10-17)
- **D-18 (RESEARCH Q1):** `epb doctor --setup` applies the same two-week package-age rule as CI. It upgrades pip to 26.1 or later in the private environment, installs the core requirements with `--uploaded-prior-to P14D`, and then installs a small shipped file of reviewed security-exception pins (newer than the cutoff) as a second step. CI's dependency-age check honours the same exceptions file.
- **D-19 (RESEARCH Q8):** A hand-edited or otherwise invalid `.epb/state.json` (schema-invalid or unparseable) exits **4** with the stable error code `STATE_INVALID` and a plain-language message saying the workspace state is damaged and how to restore it. It never exits 1, and the agent is told not to hand-repair the file.
- **D-20 (RESEARCH Q10):** Add `tzdata; sys_platform == "win32"` (Apache-2.0) to `plugin/requirements.txt`, which amends the PKG-08 core list. Timezone validation then behaves the same on every OS. Record it with the D-10 design amendments.

### Claude's Discretion
- How a new version of a source (`S004v2`) is stored: versions inside `S004.json` or separate records. The `S004v2` ID form is fixed by WS-03.
- Source ID padding beyond 999 inputs (for example letting it grow to `S1000` with 3-digit minimum padding).
- On-disk JSON formatting (key order, indentation), provided it is deterministic.
- Which later-phase schemas get drafted in Phase 1, as governed by the roadmap's phase-order fixes (PF-01, PF-04…07, PF-11, PF-16, PF-18, PF-20).
- Exact wording of manual sections and doctor lines, within D-17's structure.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Specification (design wins over everything else; §20 wins within the design)
- `docs/design/2026-10-17-evidence-pack-builder-design.md` §5: repository layout. Amended by A4, A15 and D-01, D-05, D-12 above.
- `docs/design/2026-10-17-evidence-pack-builder-design.md` §6, §6.1: workspace contract and `INDEX.md` sections. Amended by A2 and D-06.
- `docs/design/2026-10-17-evidence-pack-builder-design.md` §7.1: scan rules (new version, rename, duplicate, removed, junk, archives, email).
- `docs/design/2026-10-17-evidence-pack-builder-design.md` §8.1: source record. Amended by D-08 (`parents`).
- `docs/design/2026-10-17-evidence-pack-builder-design.md` §8.4 (including the "Importer re-check" block) and §8.5: importer-exact `EVIDENCE_PACK_V2` format, enums, list separators, 10-row metadata, text-only cells.
- `docs/design/2026-10-17-evidence-pack-builder-design.md` §12.5, §15.2, §15.3, §18: concurrency and safety, CLI and exit codes, host specifics, dependency rules.
- `docs/design/2026-10-17-evidence-pack-builder-design.md` §20: amendments A1–A15 (owner decisions, binding).

### Scope and requirements
- `.planning/ROADMAP.md` (Phase 1): goal, the five success criteria, UAT shape and phase-order fixes.
- `.planning/REQUIREMENTS.md`: the WS-, BLD-, PKG-, TST- and DOC- IDs listed in the boundary above.
- `.planning/PROJECT.md`: core value and key decisions.
- `docs/GSD-KICKOFF.md` §6, §6a, §7, §8: quality bar, evidence-bank entry rule, engineering conventions, UAT format.

### Research (inputs to the decisions above)
- `.planning/research/SUMMARY.md` "Owner Decisions Needed": OD-13, OD-17, OD-19…OD-23, OD-29 (the source of this discussion).
- `.planning/research/STACK.md`: C6/C7/C8 and "Host packaging" (Codex marketplace, manifests, `$HOME/.agents/skills`, LOW confidence). Also C10/C11 (MIME, `.7z`), the dependency and licence notes, and the launcher guidance.
- `.planning/research/ARCHITECTURE.md`: C1 (schema location), C6 (workspace additions), transactions and journal design.
- `.planning/research/PITFALLS.md`: atomic writes and locking on Windows, YAML scalar coercion, spreadsheet formula and number coercion.

### Boundaries
- `../` (parent ProbeMatrix checkout) is read-only reference only. The importer facts are already transcribed in design §8.4, so copy no ProbeMatrix code (clean-room).
- `docs/reference/hazira-2020/` is study material. It is never a source of examples, fixtures or prose, and every fixture must be synthetic.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None. The repo is greenfield: only `README.md`, `LICENSE`, `.gitignore`, the mirrored root `AGENTS.md`/`CLAUDE.md`, `docs/` and `.planning/` exist.

### Established Patterns
- Root `AGENTS.md` and `CLAUDE.md` are byte-identical, at most 150 lines. PKG-11's CI test must enforce this.
- `.gitignore` already ignores `.epb/`, `.venv/` and OS junk. `scratch/` must be added for D-16.

### Integration Points
- `.planning/config.json` uses branch template `phase-{phase}-{slug}`, so the work happens on `phase-01-foundations`, merged `--no-ff` after verification. Ask before pushing a new branch.

</code_context>

<specifics>
## Specific Ideas

- The owner wants pragmatism over extra strictness (see D-11): meet the requirements without adding hardening that nobody asked for.
- Examples in committed files use synthetic values only (for example the prefix `ACM`), never names or prefixes taken from the reference incident.

</specifics>

<deferred>
## Deferred Ideas

None. The discussion stayed within the phase scope.

</deferred>

---

*Phase: 01-foundations*
*Context gathered: 2026-10-17*
