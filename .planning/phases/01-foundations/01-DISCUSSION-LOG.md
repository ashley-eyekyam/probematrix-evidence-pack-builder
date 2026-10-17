# Phase 1: Foundations - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-17
**Phase:** 01-foundations
**Areas discussed:** Codex route & manifests, Schemas & state shape, Deps & file-type detection, Setup & smoke workbook

---

## Codex route & manifests

| Option | Description | Selected |
|--------|-------------|----------|
| Codex manifest now | `plugin/.codex-plugin/plugin.json` + `tools/install-codex.py` fallback; no committed symlink | ✓ |
| Design as written | `.agents/skills` symlink + `install-codex.sh` | |
| Defer to Phase 10 | Claude packaging only in Phase 1 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Omit `skills` key | Default scan suffices; keep key only in Codex manifest | ✓ |
| Keep it, as designed | Explicit but redundant | |

| Option | Description | Selected |
|--------|-------------|----------|
| One shared folder | Fixed per-user folder on every host, keyed by plugin version | ✓ |
| Host folder, fallback | `${CLAUDE_PLUGIN_DATA}` on Claude, fixed folder on Codex | |

| Option | Description | Selected |
|--------|-------------|----------|
| Router skill, setup only | `evidence-pack/SKILL.md` scoped to setup, init, scan, INDEX.md | ✓ |
| No skill yet | CLI and manifests only | |

**User's choice:** Recommended option in each case.

---

## Schemas & state shape

| Option | Description | Selected |
|--------|-------------|----------|
| Inside the CLI package | Single copy in `scripts/epb/schemas/`, no root mirror | ✓ |
| Package copy + root mirror | CI-checked mirror at root | |
| Root `schemas/` only | As design §5 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Add all four now | `inbox/`, `tmp/`, `ledger/chunks.json`, `.gitattributes` | ✓ |
| Add only what Phase 1 uses | `tmp/` + `.gitattributes` now, rest in Phase 3 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Split: plan vs status | Status in `state.json`, plan (with headings) in `ledger/chunks.json` | ✓ |
| state.json only | Drop `chunks.json` | |
| chunks.json only | Amend WS-13 | |

| Option | Description | Selected |
|--------|-------------|----------|
| `parents` as a list | One source, many carriers; custody per carrier | ✓ |
| Single `parent`, first seen wins | Second carrier noted only in report | |

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-upgrade with backup | Backup to `runs/<NNN>/pre-upgrade/`, journalled upgrade on mutating commands | ✓ |
| Refuse, ask the user | Exit 4, `epb upgrade` | |
| Not until needed | Only write `schema_version` | |

**User's choice:** Recommended option in each case. Claude flagged a conflict between WS-13 (chunk status in `state.json`) and OD-21 (`ledger/chunks.json`) and asked the user to resolve it rather than deciding silently.

---

## Deps & file-type detection

| Option | Description | Selected |
|--------|-------------|----------|
| Permissive dev + separate full | GPL extras only in `requirements-dev-full.txt` | ✓ |
| Design as written | Dev = all optional | |

| Option | Description | Selected |
|--------|-------------|----------|
| Stdlib + magic bytes | `mimetypes` + in-house signature table | ✓ |
| python-magic (libmagic) | Needs system library | |

| Option | Description | Selected |
|--------|-------------|----------|
| External `7z` binary only | Else `unprocessed: 7z tool not installed` | ✓ |
| Optional py7zr extra | LGPL extra | |
| Not supported in v0.1.0 | Always unsupported | |

| Option | Description | Selected |
|--------|-------------|----------|
| Exact lock with hashes | `requirements.lock` with hashes | |
| Minimum pins, resolve at install | `>=` pins | (free text) |

**User's choice (install pins):** "Just chill on such strict requirements". Recorded as minimum pins and no lock file, and the user confirmed that reading. Claude toned down the strictness of the remaining questions.

---

## Setup & smoke workbook

| Option | Description | Selected |
|--------|-------------|----------|
| Agent asks, CLI takes flags | CLI never prompts; agent asks only for the title | ✓ |
| Defaults only, edit later | No input at init | |

| Option | Description | Selected |
|--------|-------------|----------|
| Dev tool to scratch folder | `tools/make-smoke-pack.py` → git-ignored scratch path + checklist | ✓ |
| Hidden CLI command | `epb dev smoke-pack` | |

| Option | Description | Selected |
|--------|-------------|----------|
| Short checklist + next step | Ready / Optional / Next; `--verbose`, `--json` for detail | ✓ |
| Full table always | Everything every time | |

**User's choice:** Recommended option in each case.

---

## Claude's Discretion

- Storage of new source versions (`S004v2`), ID padding beyond 999, deterministic JSON formatting, which later-phase schemas get drafted early, and the exact wording of the manual and `doctor` lines.

## Deferred Ideas

None.
