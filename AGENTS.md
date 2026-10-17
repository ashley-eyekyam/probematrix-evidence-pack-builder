# ProbeMatrix Evidence Pack Builder

An open-source agent plugin (Claude Code, Cowork, Codex) that turns a case folder of incident material into a citation-exact, de-identified `EVIDENCE_PACK_V2` workbook for ProbeMatrix. One Python CLI does the deterministic work, and skills supply the judgement.

## Sources of truth
- The spec is `docs/design/2026-10-17-evidence-pack-builder-design.md`. §20 overrides earlier sections, and the design overrides every other doc.
- Scope, status and decisions live in `.planning/`: `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md` and `STATE.md`. If something seems missing or contradictory, ask the owner. Don't resolve it silently.

## Hard rules
- This repo is standalone. The parent ProbeMatrix checkout (`../`) is read-only reference material: never modify it, depend on it or copy its code.
- Build clean-room. Never paste prose from the Hazira reference files or the prototype (`../tools/evidence-pack-builder/`) into code, skills, docs or tests. Every example and fixture must be synthetic.
- Never write real names in committed files. The only exception is the unmodified official report kept in `docs/reference/`.
- Refer to the design's defects as `DEF-01`…`DEF-18`, never `D1`–`D18`, because GSD reserves `D-NN` for decisions.
- Never commit a published sample or real-incident output. Benchmarks run in git-ignored scratch folders.
- Quality outranks token and API cost.

## Working agreement
- Work goes through GSD: `/gsd-discuss-phase N`, then `/gsd-plan-phase N`, `/gsd-execute-phase N` and `/gsd-verify-work N`. Use `/gsd-quick` for small tasks.
- Each phase gets its own branch, `phase-NN-<slug>`, merged to `main` with `--no-ff` only after verification passes. Ask before pushing a new branch.
- Ask the owner one question at a time, with the recommended option first. Never proceed on a timed-out question.
- Every UAT is a numbered procedure: prerequisites, exact commands, fixture paths, and the exact pass/fail strings.
- The owner does every ProbeMatrix import (it runs only on Replit). Never claim an import worked.

## Stack and commands
- Python 3.11+, `pathlib` everywhere, cross-platform code. CI runs on Linux only until after v0.1.0.
- Tests: `pytest` (no network; tests for optional tools skip when the tool is absent). Lint: `ruff`.
- The plugin ships from `plugin/`; the marketplace file sits at the repo root.

## Maintaining this file
- `AGENTS.md` and `CLAUDE.md` are byte-identical. Edit one, copy it to the other, and commit both together. A CI test fails if they differ.
- Update both whenever scope, workflow or stack changes, and at least at every phase transition.
- Keep the file concise. Aim for 60 lines or fewer, and never exceed 150.
  - Before adding a line, ask whether removing it would cause an agent to make a mistake. If not, leave it out.
  - Point to files instead of copying their content.
  - Use no code snippets or directory trees.
  - Leave style rules to `ruff`.
- Never run `gsd-tools generate-claude-md` on this file, because it writes about 300 lines. If a GSD command appends a section, condense it to its essentials or remove it.
