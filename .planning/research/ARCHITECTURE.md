# Architecture Research

**Domain:** An agent plugin. Agents supply judgement; a deterministic Python CLI (`epb.py` plus the package `scripts/epb/`) owns all state, conversion, verification and building, over a file-based case-folder workspace.
**Researched:** 2026-10-17
**Confidence:** HIGH for structure, layering, the commit protocol and the dependency-order findings. These come from the approved design plus local experiments run today on Python 3.14.4 / PyYAML 6.0.3 / openpyxl 3.1.5. MEDIUM for host-install specifics (Codex skill locations), which come from vendor docs that move often.

> Scope: this fills only what design §19 leaves open ("exact Python package layout inside `scripts/epb/`, internal APIs, logging format"). Everything else defers to the design. Contradictions and gaps are collected in **"Conflicts with design (need owner decision)"** near the end. No prototype code or real-incident prose is used anywhere below. All examples are synthetic.

---

## Standard Architecture

The shape is a **functional core with an imperative shell, behind a transactional file store**. Agents never touch `.epb/` directly. Every write goes through a CLI command, and every agent-supplied payload passes a *validating gate* before it becomes state. This is the same pattern as git plumbing commands, or a compiler driven by an IDE. The agent is a slow, fallible client. The CLI is the single writer and the source of truth.

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  AGENT LAYER (judgement only; never writes .epb/ directly)                   │
│  evidence-pack (router) · intake · extraction · reconcile · authoring ·      │
│  verify-build · web-snapshot          SKILL.md + references/                 │
│      │ reads:  `epb <cmd> --json` envelopes, `segments show`, `claims list`  │
│      │ writes: submission JSON files → .epb/inbox/  (never final state)      │
└──────┼───────────────────────────────────────────────────────────────────────┘
       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  SHELL: cli/   epb.py shim (stdlib only) → argparse tree → command handlers  │
│  · common flags (--case, --json, --verbose) · JSON envelope · exit codes     │
│  · error() override so usage errors are JSON too · UTF-8 stdout              │
└──────┬───────────────────────────────────────────────────────────────────────┘
       ▼  (handlers call services; services return Result objects; no printing)
┌──────────────────────────────────────────────────────────────────────────────┐
│  SERVICES (one package per pipeline concern; each OWNS its .epb files)       │
│  sources(scan) → convert/ → segments → ledger → deid/roster → conflicts →    │
│  items → coverage → verify(gates) → build → index        doctor · web        │
└──────┬─────────────────────────────┬─────────────────────────────────────────┘
       ▼                             ▼
┌──────────────────────────┐  ┌───────────────────────────────────────────────┐
│ PURE DOMAIN (no I/O)     │  │ STORE: store/                                 │
│ quotes/ (verifier)       │  │ Workspace · State · Transaction (lock +       │
│ text normalise + charmap │  │ staged atomic writes + state.json LAST) ·     │
│ dates (PreciseDate)      │  │ schema validation on every write · migrations │
│ lexicon/ (patterns)      │  │ · stage keys (content-hash incrementality)    │
│ render/ (item → PackRow) │  └──────────────┬────────────────────────────────┘
│ formats/ (V2 adapter)    │                 ▼
└──────────────────────────┘  ┌───────────────────────────────────────────────┐
                              │ CORE: atomic io · OS lock · hashing · strict  │
                              │ YAML · JSONL · paths (Windows-safe) · ids     │
                              └──────────────┬────────────────────────────────┘
                                             ▼
             <case>/inputs (read-only)  .epb/ (state)  outputs/ (xlsx only)  INDEX.md
```

**Dependency rule:** arrows point down only. `core` imports nothing from `epb`. Pure-domain modules import only `core`. Services import pure domain, store and core, and never each other's private files. They use the owning service's public API. `cli` imports services. An architecture test enforces this (see Pattern 8).

### Component Responsibilities

| Component (package) | Owns (sole writer) | Responsibility | Talks to |
|---|---|---|---|
| `core/` | nothing | `atomic.py` (temp+fsync+`os.replace` with retry), `lock.py` (OS advisory lock), `hashing.py` (streaming SHA-256, canonical-JSON digest), `yamlio.py` (strict YAML), `jsonl.py`, `paths.py` (relative POSIX keys, NFC, reserved names), `ids.py` (allocators), `dates.py` (`PreciseDate`), `clock.py` (injectable now) | — |
| `store/` | `state.json`, `case.yaml`, `runs/`, `tmp/` | Workspace discovery and `init`, State model, **Transaction** (lock → stage → journal → apply → state last), schema validation on write, workspace-format migrations, stage-key bookkeeping, run log | core, schemas |
| `schemas/` (data) | — | JSON Schemas for stored records (`source`, `segment-index`, `claim`, `heldback-claim`, `item`, `conflict`, `roster`, `coverage`, `state`, `case`) **and for agent submissions** (`claims-submission`, `items-submission`, …) | loaded by store and gates |
| `sources/` | `sources/*.json` | `scan`: walk, ignore junk, fingerprint (stat cache → SHA-256), new/changed/renamed/removed classification, version ids (`S004v2`), **sidecar pairing**, child-source expanders (email, archive) | store, convert (expanders) |
| `convert/` | `media/<src>/` | Converter plug-in registry: per-modality primary/fallback selection (per page for PDFs), tool probing for `doctor`, emits a modality-neutral intermediate representation (`RawDocument`) | sources, core |
| `segments/` | `segments/<src>/` | `RawDocument` → segments: raw text, page label vs physical index, section tree, boilerplate marks, **held-back section screening (§11.3 layer 1)**, observation-section tags, confidence carry-through | convert IR, `text/normalise` |
| `text/` (pure) | — | `normalise(raw) → (norm_text, charmap)`, versioned. Whitespace, line-break hyphenation, Unicode quote/dash variants, ligatures, NFC | — |
| `quotes/` (pure) | — | `verify(quote, segments, resolver) → VerifyResult(spans, pages, reason)`. Ellipsis fragments in order, cross-page spans, `[sic]`, bracketed labels via an injected `LabelResolver` | text |
| `ledger/` | `ledger/claims.jsonl`, `ledger/conclusions.jsonl`, `ledger/chunks.json` | `plan-extract` (chunk planner), `claims add` **entry gate (§11.3 layer 2)**, `extract-status`, claim re-anchoring after a source version changes | segments, quotes, lexicon |
| `lexicon/` (data + pure) | — | Pattern sets: conclusion, lesson and recommendation cues; HFACS blocked terms; evaluative and speculative phrases; honorifics per script; ID-in-prose regexes. Versioned, so a change re-runs dependent gates | — |
| `deid/` | `rosters/*.yaml`, `private/name-map.yaml` | Role and equipment rosters with aliases; **only module that reads `private/`**; detection passes (pattern, optional NER); `apply()` (name → `[Role Label]`); `deid-scan` over shareable artefacts; real `LabelResolver` | ledger (entities), formats (xlsx reader) |
| `conflicts/` | `conflicts.yaml` | Event alignment, candidate detection (time, value, actor, sequence, outcome), confirm/dismiss register. Never picks a winner | ledger, deid rosters |
| `items/` | `items/*.yaml` | `author-plan`, `items add` **item gate (§11.3 layer 3)**, server-assigned IDs and tags, draft/locked enforcement, derived `status` and `conflicts` | ledger, conflicts, deid, gates |
| `coverage/` | `coverage.json` | Claim → `in_item` / `merged_into` / `omitted:<reason>`; omission recording; per-section and per-source report | ledger, items, segments |
| `verify/` (gates) | `runs/NNN/report.md` (via store) | Gate registry: hard G1–G12 and soft warnings as pure functions over a read-only `GateContext`; seeded spot-check | everything, read-only |
| `render/` (pure) | — | `Item → PackRow`: generated citation (`Source`), date-at-precision, chain-of-custody JSON, tag/label joins, de-identification applied once more as defence in depth. **The only path from items to a workbook** (raw-text guard, §13.5) | items, deid.apply, segments (labels only) |
| `formats/` | — | `FormatAdapter` protocol; `probematrix_v2.py` (headers, widths, enums, 10-row metadata, text-cell writing) and an **independent validator that re-reads the written file** | nothing in epb except `formats.base` |
| `build/` | `outputs/*.xlsx` | Target selection (draft master / delta-NNN / consolidated), workbook registry in state, "nothing changed" detection by row digest, corrections, `mark-imported`, `rebuild --from` | verify, render, formats, store |
| `index/` | `INDEX.md` | Section providers (§6.1 order), tick read-back parser, file-name de-identification | store, deid, build |
| `doctor/` | — (writes only the capability profile into state) | Probe registry: core-dependency import check, external tools (`shutil.which` + version), Tesseract language packs, long-path and sync-folder warnings | convert (probes) |
| `web/` | `inputs/web/<dated-folder>/` | `snapshot <url>` with stdlib `urllib`; the only writer into `inputs/` | sources |
| `cli/` | stdout and stderr only | Argument parsing, envelope, exit codes, human rendering | services |

---

## Recommended Project Structure

```
skills/evidence-pack/scripts/
├── epb.py                    # STDLIB-ONLY shim: python>=3.10 check, put its own dir on sys.path,
│                             #   import epb.cli.main inside try/except ImportError -> exit 3 + JSON.
└── epb/
    ├── __init__.py           # REQUIRED. Without it, epb.py shadows the package (verified, see Pitfalls)
    ├── __main__.py           # `python -m epb` for tests
    ├── version.py            # PLUGIN_VERSION, WORKSPACE_FORMAT (int)
    ├── errors.py             # EpbError tree -> exit-code mapping, stable error codes
    ├── cli/
    │   ├── main.py           # parser tree; common parent parser; allow_abbrev=False; error() override
    │   ├── envelope.py       # {ok, command, exit_code, data, warnings, errors, next}
    │   └── commands/         # workspace.py intake.py extract.py reconcile.py author.py
    │                         # verify_build.py incremental.py web.py   (thin: parse -> service -> envelope)
    ├── core/                 # atomic.py lock.py hashing.py yamlio.py jsonl.py paths.py ids.py dates.py clock.py
    ├── schemas/              # *.schema.json  (CANONICAL runtime copy; see Conflict C1)
    ├── store/                # workspace.py state.py txn.py stages.py migrate.py runs.py validate.py
    ├── sources/              # scan.py fingerprint.py classify.py sidecars.py expanders/{email,archive}.py
    ├── convert/
    │   ├── base.py           # Converter protocol, RawDocument IR, ToolProbe
    │   ├── registry.py       # modality -> ordered converters; per-page PDF routing
    │   └── pdf_text.py docx.py pptx.py sheet.py email.py html.py text.py      (Phase 2)
    │       pdf_ocr.py docling.py                                               (Phase 7)
    │       image.py audio.py video.py                                          (Phase 8)
    ├── text/                 # normalise.py (versioned, pure)
    ├── segments/             # build.py pagelabels.py sections.py boilerplate.py screening.py store.py
    ├── quotes/               # verifier.py conventions.py resolver.py (LabelResolver protocol + NullResolver)
    ├── ledger/               # chunks.py claims.py entry_gate.py heldback.py reanchor.py
    ├── lexicon/              # loader.py + data/*.txt (pattern lists, versioned)
    ├── deid/                 # roster.py namemap.py detect.py apply.py scan.py resolver.py
    ├── conflicts/            # align.py detect.py register.py
    ├── items/                # model.py plan.py item_gate.py store.py
    ├── coverage/             # matrix.py
    ├── verify/               # context.py registry.py hard.py soft.py spotcheck.py report.py
    ├── render/               # rows.py citation.py custody.py
    ├── formats/              # base.py probematrix_v2.py
    ├── build/                # planner.py builder.py corrections.py imports.py rebuild.py
    ├── index/                # render.py providers.py ticks.py
    ├── doctor/               # probes.py profile.py
    └── web/                  # snapshot.py
```

### Structure Rationale

- **Top-level names follow design §5's comment** (`workspace, convert/, segments, ledger, deid, conflicts, coverage, verify, build, index, formats/`), so nobody reading the design is surprised. `workspace` becomes `store/` because it also holds state and transactions. `sources/`, `quotes/`, `text/`, `lexicon/`, `render/`, `items/` and `doctor/` are the additions the design implies but does not name.
- **One owner per `.epb/` file.** This turns the design's data contracts into code boundaries. Example: the "only `deid` reads `private/`" rule is greppable and testable.
- **`render/` and `formats/` are separate.** `render` knows ProbeMatrix *semantics* (citation strings, date precision). `formats` knows the *file* (headers, widths, the metadata rows). That separation is the §8.5 seam. A future V3 means a new adapter with no pipeline change.
- **Pure modules (`text`, `quotes`, `render`, `lexicon`, `verify` gate functions) do no I/O.** That makes them exhaustively unit-testable, and safe to call from several gates (claims add, items add, verify, re-anchor) with identical results.
- **Converters live one per file behind a registry**, so Phases 7 and 8 add files and need no edits to the dispatcher.

---

## Data Flow

### Stage pipeline: what each stage reads, writes, and keys on

```
inputs/ ─scan─▶ sources/*.json ─convert─▶ media/<src>/raw.json (+bins) ─segment─▶ segments/<src>/{NNNN.md,index.json}
                 ▲ sidecars paired           (RawDocument IR)                 │ held_back / observation section tags
                 │                                                            ▼
           [agent] sources set kind/citation_short          plan-extract ─▶ ledger/chunks.json
                                                                              │
     [agent reads `segments show`, writes inbox/claims-<chunk>.json]          ▼
                                     claims add (ENTRY GATE) ─┬─▶ ledger/claims.jsonl        (evidence kinds)
                                                              └─▶ ledger/conclusions.jsonl   (held-back kinds)
                                                                              │
     [agent] roster add/alias (via file) ─▶ rosters/*.yaml + private/name-map.yaml
     conflicts detect ─▶ conflicts.yaml (candidates) ─[agent] resolve─▶ confirmed/dismissed
                                                                              │
     author-plan ─▶ proposals (stdout) ─[agent writes inbox/items-*.json]─▶ items add (ITEM GATE) ─▶ items/*.yaml
     [agent] coverage omit ─▶ coverage.json                                   │
                                                                              ▼
     verify (G1–G12 + soft) ─▶ runs/NNN/report.md ─ pass ─▶ build ─▶ render ─▶ formats ─▶ outputs/*.xlsx
                                                                              │        └─ validator re-reads file
                                                                              ▼
                                                     index ─▶ INDEX.md (ticks read back first)
                                       state.json is committed LAST in every mutating command
```

| Stage | Command | Reads | Writes | Agent? | Incremental key |
|---|---|---|---|---|---|
| init | `init` | flags | `case.yaml`, `state.json`, `.epb/.gitignore`, `private/.gitignore` | asks the user for slug, prefix and timezone, then passes flags | n/a (refuses to re-init) |
| doctor | `doctor` | env, PATH | capability profile in state | no | none (always re-probes) |
| scan | `scan` | `inputs/**`, state | `sources/*.json`, state.sources | no | `(relpath_nfc, size, mtime_ns)` stat cache → SHA-256 only on a stat change; `--rehash` forces |
| convert | `convert [--src]` | source record, input file | `media/<srcver>/raw.json` + binaries | no | `H(sha256, converter.id, converter.version, tool versions, options, case.languages)` |
| segment | `segment` | raw.json | `segments/<srcver>/` | no | `H(raw.json digest, segmenter_version, normaliser_version, lexicon_version)` |
| source meta | `sources set` *(gap, C4)* | segments | source record (`source_kind`, `citation_short`) | **yes** | n/a |
| plan | `plan-extract` | segment indexes | `ledger/chunks.json` | no | `H(segment digests in chunk, budget)`. A changed key reopens the chunk |
| extract | `claims add --chunk` | inbox file | claims / conclusions JSONL | **yes** (content) | submission digest (idempotent re-submit) |
| reconcile | `roster …`, `conflicts …` | claims | rosters, name map, conflicts | **yes** (labels, confirm/dismiss) | new-claim watermark (`claims_seen_upto`) |
| author | `author-plan`, `items add` | claims, rosters, conflicts | `items/*.yaml` | **yes** | item-submission digest |
| coverage | `coverage`, `coverage omit` *(gap)* | claims, items | `coverage.json` | **yes** (omission reasons) | recomputed (cheap) |
| verify | `verify` | everything | `runs/NNN/report.md` | reviews soft warnings | recomputed every time (never cached) |
| build | `build [--consolidated]` | items, verify result | `outputs/*.xlsx`, state.workbooks | no | `H(rendered rows)`. Equal to the last build means "nothing to write" |
| index | `index` | state, previous INDEX.md | `INDEX.md` | user ticks | recomputed every run |

**Direction is strictly forward.** No stage writes into an upstream stage's files. Back-propagation (a changed input invalidates claims) works by **re-verifying downstream against upstream** (`ledger/reanchor.py`), never by upstream code editing downstream files.

### State management: the transaction (one per unit of work)

```
acquire OS lock (.epb/lock)
  └─ recover(): if tmp/<txn>/manifest.json exists and state.last_txn != txn → roll forward, else discard tmp/<txn>
load state.json (snapshot)
  └─ stage: every new or changed file → validate(schema) → write to tmp/<txn>/… (fsync)
  └─ journal: write tmp/<txn>/manifest.json [(tmp → final) …, state.json LAST] (fsync)
  └─ apply: os.replace each entry in order (retry on Windows PermissionError)
  └─ state.json replaced last (records last_txn, stage keys, counters, digests)
  └─ remove tmp/<txn>
release lock
```

- **The unit of work is one source, one chunk, or one submission, not a whole stage.** A crash loses at most one unit, and `state.json` always describes a consistent world. This is what makes "resume where it stopped" (§7.4, §12.5) true at chunk granularity.
- Read-only commands (`status`, `*list`, `*show`, `segments show`, `extract-status`, `coverage` without `omit`, `verify` with no report write) **take no lock**. `os.replace` guarantees they see either the old or the new `state.json`. This matters because parallel extraction subagents read segments while another subagent's `claims add` holds the lock.
- Mutating commands **wait** for the lock (default 60 s, `--wait N`) instead of failing at once. Otherwise parallel `claims add` calls (§15.3) collide.

### Key Data Flows

1. **Agent JSON → evidence bank (the validating gate).** `inbox/claims-<chunk>.json` → size cap and strict UTF-8 JSON parse (agents never submit YAML) → *submission* schema (`additionalProperties: false`; server-owned fields such as `claim_id`, `char_start/end`, pages and `verified` are **forbidden** in submissions) → reference resolution (chunk, src and seg ids exist; the segs belong to the chunk) → entry gate (held-back section? verdict, lesson or recommendation patterns on an evidence kind? → reject with a "split or reclassify" hint; held-back kinds are routed to `conclusions.jsonl`) → quote verification computes offsets and pages server-side → date precision parsed into `PreciseDate` → **all-or-nothing** commit for the chunk → envelope lists assigned `C####` ids or every error with a JSON Pointer and a fix hint. Exit 1 on any rejection.
2. **Claims → items.** Same gate shape. The item gate calls the **same gate functions** `verify` uses (G1 quotes-in-description ⊆ `item.quotes` and verified, G4 comma-free, G5 no IDs in prose, G6 HFACS, G7 held-back reference and fuzzy match, G8 name scan of this item, G10 length, G11 precision cannot exceed the claims' precision). The agent therefore fails fast at authoring, not only at build. The server assigns `id`, `tag` and `version_added`, and derives `status` and `conflicts`.
3. **Items → workbook.** `build` → `verify` (all hard gates; no `--force` exists) → `render` (citations from anchor segment labels, dates at precision, joins with `, `) → `formats.probematrix_v2.write` (every cell typed as text) → `formats.probematrix_v2.validate(path)` re-reads the file independently → `deid.scan(path)` → commit plus a workbook-registry update.
4. **New version of an input (§12.2).** scan → `S004v2` → convert and segment into a *new* directory (old version kept, because locked items cite it) → `reanchor`: for each claim on v1, re-find the quote text in v2. Found once: link it. Not found: flag it, and if the claim backs a locked item, a correction is proposed.
5. **INDEX ticks (§6.1, §12.1 5a).** `index` first parses the previous `INDEX.md` for ticked boxes against the workbook registry, records the ticks in state (state is authoritative from then on), then regenerates.

---

## Architectural Patterns

### Pattern 1: Single-writer CLI with submission-gated agent input

**What:** Agents write *proposals* to `.epb/inbox/` and hand them to a CLI verb. The verb validates, derives the server-owned fields and commits. Nothing an agent types becomes state unchecked.
**When to use:** Every agent → state boundary: `claims add`, `items add`, `roster add/alias`, `conflicts resolve`, `coverage omit`, `sources set`.
**Trade-offs:** More CLI surface and schemas. In return, invented quotes, mistyped pages and server fields the agent made up become impossible to persist. That is the product's core value.

```python
# ledger/claims.py (shape only)
def add_submission(ws: Workspace, chunk_id: str, payload: bytes) -> AddResult:
    sub = parse_json_strict(payload, max_bytes=2_000_000)
    errs = schemas.validate("claims-submission", sub)            # all errors, with JSON Pointers
    errs += resolve_refs(ws, chunk_id, sub)
    staged = []
    for i, c in enumerate(sub["claims"]):
        r = entry_gate.check(ws, c)                               # §11.3 layer 2
        r = r.then(lambda: quotes.verify_all(c, ws.segments, ws.label_resolver))
        errs += r.errors_at(f"/claims/{i}")
        staged.append(r.value)
    if errs:
        return AddResult.rejected(errs)                           # exit 1, nothing written
    with ws.transaction("claims add") as tx:
        tx.replace_chunk_claims(chunk_id, staged)                 # idempotent per chunk
    return AddResult.accepted(ids=[...])
```

### Pattern 2: Transaction with a redo journal and `state.json` committed last

**What:** See the State-management diagram above. Every artefact is staged and validated, journalled, applied with `os.replace`, then `state.json` is replaced last. Recovery rolls forward when a journal is complete and discards it when it is not.
**When to use:** Every mutating command.
**Trade-offs:** About 100 lines of careful code with crash-injection tests. Plain "temp + rename per file" is **not enough**: a crash between `roles.yaml` and `state.json` leaves the two disagreeing, with nothing to say which is right.

### Pattern 3: Content-hash stage keys (incremental and resumable)

**What:** Each stage-unit records `key = sha256(canonical_json({stage, impl_version, input_digests, tool_versions, config_subset}))` and an output digest in `state.json`. Skip when the key matches **and** the output's digest still matches on disk. `rebuild --from <stage>` clears keys from that stage onward. Allocated IDs are never touched.
**When to use:** The deterministic stages (scan, convert, segment, plan-extract, build). Agent stages are keyed by submission digest and reopened only when their upstream key changes.
**Trade-offs:** Implementation versions (`SEGMENTER_VERSION`, `NORMALISER_VERSION`, `LEXICON_VERSION`) must be bumped by hand when behaviour changes. A test asserting that golden outputs change only together with a version bump catches forgotten bumps.

### Pattern 4: Converter plug-in protocol plus a neutral intermediate representation

**What:**
```python
class Converter(Protocol):
    id: str                                   # "pdfplumber", "ocrmypdf", "faster-whisper"
    modalities: frozenset[str]                # {"pdf"}, {"audio"}, ...
    def probe(self) -> ToolStatus: ...        # found?, version, enables[], install hints (doctor)
    def accepts(self, src: SourceRecord) -> Acceptance: ...   # yes / per-page / no(reason)
    def convert(self, src: SourceRecord, ctx: ConvertContext) -> RawDocument: ...
# RawDocument = units[]: PageUnit(index, text, words?, tables, ocr_conf?) | TimeUnit(start,end,text,conf)
#               | SheetUnit(sheet, row_from,row_to, table) | ImageUnit(exif_sans_gps, ocr_text?)
```
The registry orders converters by the §7.2 primary/fallback table and routes PDF pages individually (text layer → pdfplumber; image-only → OCR). A missing tool returns `unprocessed: <tool> missing`. It never raises and never fails the run.
**Trade-offs:** The IR has to be designed for all modalities in Phase 2, even though media converters arrive in Phase 8 (see dependency issue P10).

### Pattern 5: Raw text plus a recomputable char map (do not persist the map)

**What:** `segments/<src>/NNNN.md` holds **only the exact raw text** (no front matter), written with `newline=""`. `index.json` holds metadata. `norm_text` and the char map come from a pure, versioned `normalise(raw)` at load time. Anchors store **raw** offsets plus `normaliser_version`.
**Why:** One source of truth, and no large map files. Raw offsets survive normaliser upgrades (re-verify, then re-derive).

### Pattern 6: One gate implementation, many call sites

**What:** Each hard and soft check is a pure function `(GateContext, scope) -> list[Finding]` with a stable id (`G01`…`G12`, `W-…`). `items add` runs the item-scoped subset. `verify` runs everything over all items. `build` calls `verify`. The run report renders the findings.
**Why:** It stops the classic drift where the authoring check and the build check disagree. It also gives the agent identical messages at every stage.

### Pattern 7: Next-action protocol for the router skill

**What:** `status --json` (and `run`, see C5) returns `next: [{stage, command, reason, pending_ids}]` computed from state: "3 chunks pending", "2 conflict candidates unresolved", "12 claims unaccounted in observation sections". The `evidence-pack` SKILL.md loops: read `next`, invoke the sub-skill, repeat.
**Why:** It keeps SKILL.md under 150 lines and behaviour identical across hosts. The state machine lives in Python, not in prose that three different agents interpret.

### Pattern 8: Enforced layering (architecture tests, no extra dependency)

**What:** A pytest that walks `epb/**/*.py` with `ast`, builds the import graph and asserts:
- `core` has no `epb` imports
- `formats` imports only `formats.base`
- only `deid.namemap` references `private/`
- only `ledger.heldback` opens `conclusions.jsonl`
- `render` and `formats` never import `segments.store` or `ledger.claims` (the raw-text guard of §13.5, made structural)
- no module except `store.txn` and `core.atomic` calls `open(..., "w")`, `os.replace` or `Path.write_*`

**Why:** It turns the design's privacy rules into checks that fail CI.

---

## CLI Design (decisions)

| Decision | Recommendation | Why |
|---|---|---|
| Framework | **argparse (stdlib)** | Zero dependencies; exits **2** on usage errors by default, which already matches §15.2 (verified). Nested subcommands (`claims add/list/show`) are native. click (BSD-3, no deps) adds nothing the agent needs. **typer** (MIT) pulls in `rich`, `shellingham`, `colorama` and more, and rich's terminal rendering is a hazard for `--json` stdout. Reject both. |
| Common flags | A parent parser carrying `--case`, `--json`, `--verbose`, `--wait`, attached to **every** subparser, so `epb scan --json` works as well as `epb --json scan` | argparse otherwise accepts global flags only before the subcommand. Agents put flags at the end. |
| Abbreviations | `allow_abbrev=False` | Default `True` lets `--cons` silently mean `--consolidated`. Never acceptable for an agent-driven tool. |
| Colour | Explicitly `color=False` | Python 3.14 argparse defaults to `color=True` (verified). Keep help text plain and deterministic. |
| Usage errors in JSON | Subclass `ArgumentParser.error()` to emit the envelope when `--json` is in `argv`, then exit 2 | Agents parse stdout. A bare usage line on stderr is easy to miss. |
| Output | stdout = one JSON envelope (`--json`) or human text; stderr = logs; **never** both on stdout | Lets agents parse reliably. |
| Envelope | `{"ok", "command", "exit_code", "epb_version", "data", "warnings":[…], "errors":[{"code","message","pointer","hint"}], "next":[…]}` | Stable `code` strings (`QUOTE_NOT_FOUND`, `HELD_BACK_SECTION`, `COMMA_IN_LABEL`, …) let skills branch without parsing message text. |
| Encoding | `sys.stdout.reconfigure(encoding="utf-8")` at start-up; `json.dumps(..., ensure_ascii=False)` | On Windows before 3.15, stdio defaults to the ANSI code page. A Devanagari quote would raise `UnicodeEncodeError` (PEP 686 makes UTF-8 the default only from 3.15). |
| Interactivity | **Never prompt.** Missing information means exit 2 with a hint naming the flag | Agent shells can't answer stdin prompts; a prompt hangs the run. The agent asks the user, one question at a time, then passes flags. |
| Names on argv | Name-bearing inputs (`roster add`, alias lists) come **from a file in `.epb/inbox/` or stdin**, never argv | argv lands in shell history, process lists and host transcripts of the command line. |
| Startup cost | Lazy-import heavy libraries inside handlers (openpyxl, pdfplumber, rapidfuzz, jsonschema) | `claims add` runs once per chunk, hundreds of times per case. `epb --help` and `doctor` must work with core dependencies missing. |
| Exit codes | 0 ok (including "nothing to do"); 1 gate failure (any validating-gate rejection, any hard verify finding, build refused); 2 usage; 3 missing dependency (a core import fails in the shim, or the requested command cannot run at all); **unexpected exception and lock timeout: see Conflict C3** | An uncaught Python exception exits 1 by default, which an agent reads as "gate failure, fix your content". The top-level handler must catch everything. |

---

## Schema Validation on Write

- **Library: `jsonschema` (MIT, 4.26.0, Python ≥3.10)** using Draft 2020-12, with validators compiled once per process. It reports **all** errors with paths (`iter_errors`), which an agent needs to repair a 40-claim submission in one pass. Its dependencies (`attrs`, `referencing`, `jsonschema-specifications`, `rpds-py`) are all MIT. `rpds-py` is a compiled Rust extension, with wheels for win/mac/linux including win_arm64 and cp314. The alternative, `fastjsonschema` (BSD-3, zero deps), stops at the first error and supports only up to draft-07. That makes it acceptable for internal records but poor for agent feedback. Not in §5's list: see **C2**.
- **Two schema families:** *stored* schemas (what is on disk) and *submission* schemas (what agents may send). Submissions forbid server-owned fields.
- **Validate on write in `store.txn.stage()`, and on read for `state.json`, `case.yaml`, rosters and items.** Those files are "never hand-edited" but are YAML on disk, so a hand-edit is detected and reported (exit 1, `STATE_INVALID`) rather than silently trusted.
- **Every record carries `schema_version`.** `store/migrate.py` upgrades older workspaces in a journalled transaction. The plugin refuses (with a clear error) to open a workspace whose `WORKSPACE_FORMAT` is newer than its own. Cases live for weeks while the plugin updates underneath them.
- **Strict YAML (`core/yamlio.py`).** PyYAML's `safe_load` applies YAML 1.1 implicit typing. Verified today on PyYAML 6.0.3: `12:30` → `750`, `1:02:03` → `3723`, `2020-09-17` → `datetime.date`, `no` → `False`, `010` → `8`. That would corrupt event times, date precision and IDs inside items and rosters. Use a `SafeLoader` subclass with the int, float, bool and timestamp implicit resolvers removed, so every scalar is a string. Dump with a `SafeDumper` that quotes all strings. JSON Schema then enforces the formats (`^\d{4}(-\d{2}(-\d{2})?)?$` plus `precision`).

---

## Atomic Writes and the Lock File

- **Atomic write:** write to `tmp/<txn>/…` on the **same filesystem**, flush, `os.fsync`, then `os.replace`. On POSIX, also fsync the parent directory after replacing `state.json`. Python documents `os.replace` as atomic only as a POSIX requirement. On Windows it uses MoveFileEx, which fails with `PermissionError` (WinError 5/32) when another process holds the target open, typically Excel holding `outputs/*.xlsx` or an antivirus scanner. So: retry with backoff (for example 5 × 200 ms), then fail with `TARGET_LOCKED` and the hint "close the workbook in Excel".
- **Lock:** an **OS advisory lock** on an open handle to `.epb/lock`: `fcntl.flock` on POSIX, `msvcrt.locking` on Windows, about 40 lines in `core/lock.py`. The OS releases it when the process dies, so there are **no stale locks to detect**. Write `{pid, host, command, started}` into the file for diagnostics only. Do **not** build a PID-file lock with liveness checks: on Windows, `os.kill(pid, 0)` *terminates* the target process (any signal other than CTRL_C/CTRL_BREAK calls `TerminateProcess`, per the Python docs). `filelock` (MIT) does the same job, but recent versions need Python ≥3.11 and add a dependency. In-house code is simpler.
- **Ordering:** `state.json` is always the last entry in the journal manifest. That is the commit point.
- **Excel lock files:** `outputs/~$*.xlsx` (created by Excel while a pack is open) is ignored by `index` and `deid-scan` and never reported as an output.

---

## Windows-Safe Paths

| Rule | Implementation |
|---|---|
| State keys are relative POSIX strings, NFC-normalised | `PurePosixPath(p.relative_to(inputs)).as_posix()`, then `unicodedata.normalize("NFC", …)`. macOS can return NFD names; without NFC the same file looks "renamed" across machines |
| Case-insensitive rename detection | Compare `casefold()` keys when the filesystem is case-insensitive (Windows, default macOS). Hash identity already handles renames |
| Generated names are safe everywhere | `core/paths.safe_component()` replaces `<>:"/\|?*` and control characters, strips trailing dots and spaces, avoids `CON PRN AUX NUL COM1-9 LPT1-9`, and caps length. **No colons** in keyframe or time-based names (`t001234` not `00:12:34`) |
| Byte-exact text files | Always `open(..., encoding="utf-8", newline="")`. Raw-offset anchors break if `\n` becomes `\r\n`. Write `.epb/.gitattributes` with `* -text` so git `autocrlf` cannot rewrite segments |
| No locale encodings | Run tests with `-X warn_default_encoding` and treat `EncodingWarning` as an error |
| Long paths | `doctor` warns when the case-folder path exceeds about 200 characters on Windows and `LongPathsEnabled` is off. Keep internal names short (`S004v2`, `0017.md`) |
| No symlinks at runtime | `scan` does not follow symlinks (no loops; the inputs stay the user's). The `.agents/skills` symlink is a repo convenience only (§15.3) |
| Sync folders | `doctor` warns when the case folder sits under OneDrive, Dropbox or iCloud. Placeholder files trigger downloads on hash, and sync clients hold transient locks that break `os.replace` |

---

## Anti-Patterns

### Anti-Pattern 1: Agents editing `.epb/` files directly
**What people do:** Let the agent write `items/EVD-X-001.yaml` with its file tool "because it's just YAML".
**Why it's wrong:** It skips the entry and item gates, lets the agent choose IDs, page numbers and offsets (DEF-03), and breaks the transaction invariants.
**Do this instead:** Inbox file, then a CLI verb. `verify` also detects hand edits through state digests.

### Anti-Pattern 2: Stage-sized transactions
**What people do:** Write `state.json` once at the end of `convert` across 40 sources.
**Why it's wrong:** A crash after source 39 throws away hours of OCR and transcription, and the lock is held for the whole run.
**Do this instead:** One transaction per source, chunk or submission.

### Anti-Pattern 3: Checking "nothing changed" by file bytes
**What people do:** Compare the new xlsx with the old one.
**Why it's wrong:** openpyxl writes creation and modification timestamps and zip metadata, so the bytes always differ, and §12.1 "a run with no changes writes nothing" fails.
**Do this instead:** Compare the digest of the rendered `PackRow` list stored in the workbook registry.

### Anti-Pattern 4: Assigning values to cells and trusting openpyxl's inference
**What people do:** `ws.cell(r, c, value)` for every field.
**Why it's wrong:** Strings starting with `=` become **formulas** (verified on openpyxl 3.1.5: data_type `f`), so a quote or label beginning with `=` corrupts the pack and is a formula-injection vector. Dates as `date` objects import as Excel serials (§8.4 re-check item 8).
**Do this instead:** Write only `str`, and set `cell.data_type = "s"` explicitly in `formats/probematrix_v2.py`. The validator asserts that no cell has type `f`, `n` or `d`.

### Anti-Pattern 5: Separate copies of the gate logic
**What people do:** A quick check in `items add` and a thorough one in `verify`.
**Why it's wrong:** The two drift, and items pass authoring only to fail at build with different messages.
**Do this instead:** Pattern 6.

### Anti-Pattern 6: Uncaught exceptions as the error path
**Why it's wrong:** Exit code 1 means "gate failure" to the agent, so it will try to "fix" evidence content in response to a crash.
**Do this instead:** A top-level handler maps `EpbError` subclasses to codes and wraps everything else as `INTERNAL_ERROR` (code per C3), with the traceback on stderr only.

### Anti-Pattern 7: A heavy module-level import in `epb.py`
**Why it's wrong:** A missing core dependency gives a traceback with exit 1 instead of a JSON exit 3, and `doctor` can't run to explain it.
**Do this instead:** Keep the shim stdlib-only and use lazy imports.

---

## Scaling Considerations

"Scale" here means case size, not users.

| Case size | Approach |
|---|---|
| One 36-page text report | Everything in memory. JSONL loaded whole. Sub-second commands apart from conversion |
| 500-page reports, about 5k claims, tens of inputs | Still in-memory (`claims.jsonl` of a few MB). Index claims by `src` and `seg` in memory per command. Re-verification at build is O(quotes × segment length): fine |
| Hours of video, GB-sized inputs | First bottleneck: **hashing and transcription time while holding the lock**. Use the stat cache for scan, a per-source transaction for convert, and `--src` targeting |

### Scaling Priorities
1. **First bottleneck:** lock hold time during long conversions blocks parallel `claims add`. Fix: per-source transactions; convert can release and re-acquire the lock between sources.
2. **Second bottleneck:** `claims.jsonl` rewrite cost on every chunk under all-or-nothing replace semantics. Fix: append-with-committed-length recorded in state (lines beyond `state.ledger.committed_lines` are discarded on recovery). Only needed beyond about 50k claims.

---

## Integration Points

### External Services and Tools

| Integration | Pattern | Notes |
|---|---|---|
| Local tools (ffmpeg, tesseract, ocrmypdf, pdftoppm, pandoc, LibreOffice) | `subprocess.run([...], shell=False)`, list args, timeouts, `ToolProbe` for `doctor` | Never `shell=True` (input file names are user-controlled) |
| Claude Code / Cowork | SKILL.md invokes `python3 "${CLAUDE_PLUGIN_ROOT}/skills/evidence-pack/scripts/epb.py"` | `${CLAUDE_PLUGIN_ROOT}` (plugin root) and `${CLAUDE_SKILL_DIR}` are substituted in plugin skill markdown and in `allowed-tools`, so the CLI can be pre-allowed without prompts |
| Codex | Skills discovered from `.agents/skills` (repo) and `$HOME/.agents/skills` (user), symlinks followed. No path-variable substitution documented | SKILL.md must state the path relative to the skill folder. **Only `skills/` is installed, so the runtime must not depend on repo-root files** (C1). On Windows, `python3` is often the Store stub: the docs should give `py -3` / `python` |
| ProbeMatrix | File only (an `EVIDENCE_PACK_V2` xlsx the user uploads) | All importer facts live in `formats/probematrix_v2.py` and are dated |
| Web (optional) | stdlib `urllib` in `web/snapshot.py` only | The only network code. Tests mock it |

### Internal Boundaries

| Boundary | Communication | Notes |
|---|---|---|
| cli ↔ services | Direct calls returning `Result` dataclasses | Services never print and never `sys.exit` |
| services ↔ store | `ws.transaction()` context; read via `ws.state` snapshot | The only write path |
| quotes ↔ deid | `LabelResolver` protocol injected by the caller | Built in Phase 2 with `NullResolver`; the real resolver arrives in Phase 4 |
| ledger ↔ segments | `SegmentReader` (text, labels, section flags) | ledger never opens segment files itself |
| render ↔ deid | `deid.apply(text)` | Defence in depth after items are already de-identified |
| verify ↔ everything | Read-only `GateContext` built once per run | Gates are pure |
| build ↔ formats | `FormatAdapter.write(rows, meta, path)` + `.validate(path)` | The validator never trusts the writer |

---

## Suggested Build Order (components)

Ordering rule: build a component only once everything it **reads** exists, and fix every schema field a later producer will fill **before** the first consumer persists data. That avoids workspace migrations mid-milestone.

1. **core + store + cli skeleton:** atomic, OS lock, transaction and journal, strict YAML, schemas loader, ids, `PreciseDate`, envelope, exit codes, migrations. Includes the *complete* `state.json` schema (sources, stage keys, counters, **workbook registry with draft/imported**, chunk status) and crash-injection tests. CI on **Linux, macOS and Windows from day one**.
2. **formats/probematrix_v2** writer and independent validator, plus an xlsx reader that `deid-scan` will reuse.
3. **sources/scan** with **sidecar pairing**, child-source expander seam, stat cache, versions, renames and removals; **index/** with section providers and a parseable tick syntax; **doctor** probe registry.
4. **convert/** protocol and IR (all unit kinds declared), text converters; **text/normalise**; **segments/** (page labels, sections, boilerplate, **held-back screening**, observation tags, confidence field); **quotes/** with `LabelResolver`; `sources set`; synthetic incident generator v1.
5. **ledger/**: chunk planner, submission schemas, entry gate, held-back ledger, extract-status, inbox; anchor schema covering page, time, sheet-range, visual and web anchors.
6. **deid/** (rosters, name map, detect, apply, scan, real resolver, INDEX file-name substitution), then **conflicts/**.
7. **items/** and the item gate, **render/**, **verify/** gate registry, **coverage/** (+ `omit`), **build/** (master as a draft, IDs never reused), spot-check, next-action protocol and router skill.
8. **build/** incremental: mark-imported, ticks, deltas, `reanchor`, corrections, `rebuild --from`, consolidated.
9. Converters: OCR and docling, then media and images, then web.
10. Evals, sample, docs, release.

### Check against design §17 and kickoff §5

The 10-phase plan in kickoff §5 follows §17 and is broadly sound. The core order (foundations → intake → extraction → reconcile → authoring and build → incremental → OCR → media → web → release) matches the dependency graph above. These are the **dependency-order problems**, things an earlier phase needs that a later phase builds:

| # | Problem | Where | Fix (keeps the phase order) |
|---|---|---|---|
| P1 | **Sidecar notes are scheduled for Phase 8**, but `scan` (Phase 1) must recognise `<file>.note.md` / `.note.yaml` as a sidecar of its file. Otherwise Phase 2 converts it as an ordinary Markdown source, and Phase 8 has to reclassify sources already in state, which is a migration. The renderer (Phase 5) also needs sidecars for Chain of Custody and Collection Conditions (§8.4). | K§5 P1/P2/P5 vs P8 | Pair sidecars in Phase 1 scan. Parse sidecar YAML/MD and use it in custody in Phase 5. Phase 8 adds only media-specific sidecar fields (speaker roles, camera). |
| P2 | **Phase 2's verifier must accept "bracketed role labels"** (§8.2/§13.3), which needs the private name map. That map is built in **Phase 4**. | K§5 P2 vs P4 | Build `quotes/` against an injected `LabelResolver` and test Phase 2 with a stub map. The real resolver and its fixture test land in Phase 4. Phase 2's Hazira check must use only the prototype quotes that contain no ad-hoc placeholders. |
| P3 | **Held-back section screening (§11.3 layer 1) happens "at segmentation"**, but it is not in Phase 2's scope. The Phase 3 entry gate depends on the `held_back_section` flag. | K§5 P2/P3 | Put the section classifier in Phase 2 (`segments/screening.py`), or state explicitly that Phase 3 adds it as an index annotation pass. Either way, it must exist before the first `claims add`. |
| P4 | **INDEX.md generator in Phase 1** needs data from Phases 4–7 (conflicts, omissions, OCR review, outputs and ticks). §6.1 also requires name-bearing *file names* to be shown with role labels, which needs rosters (Phase 4). | K§5 P1 vs P4–P7 | Build section providers in Phase 1, each rendering "none yet" until its producer exists. File-name substitution and `deid-scan` over INDEX.md come in Phase 4. INDEX.md from Phases 1–3 may show raw file names, so test cases must use synthetic names only. Fix the "Imported?" tick syntax in Phase 1 so Phase 6 can parse it. |
| P5 | **Phase 1 exit: "validator fails on the prototype's comma-bearing labels (DEF-14)".** In a finished workbook, a label containing a comma looks the same as two labels. Hard gate 4 is really a check on roster labels before rendering (Phases 4–5). | K§5 P1 vs §14 G4 | Phase 1: a structural workbook check (each `, `-split fragment must have balanced brackets and must not start with a digit or a lower-case word). That catches the prototype's fragments. Phases 4–5: the authoritative label-level G4 at `roster add` and `items add`. |
| P6 | **Crash-resume is listed under §17 step 6 (Incremental)**, but Phase 3's exit criterion already needs resume, and Phase 1 owns the lock and atomic writes. | §17.6 vs K§5 P1/P3 | The full transaction and journal recovery belongs in Phase 1 (with crash-injection tests). Phase 6 adds only delta-specific recovery. |
| P7 | **Master build in Phase 5 needs the workbook registry, ID and tag counters and draft status**: "draft master rewritten each run; IDs never reused; removed drafts leave gaps" (§12.1). Those concepts are filed under Phase 6. | K§5 P5 vs P6 | Define the registry and counters in the Phase 1 state schema, and implement "draft master" in Phase 5. Phase 6 adds mark-imported, deltas and locks. |
| P8 | **Multi-language is scheduled for Phase 7**, but it shapes earlier contracts: NFC and zero-width handling in the normaliser (Phase 2), honorifics in other scripts (Phase 4), `[translation]` in Descriptions versus gate G1's "every quotation is in `item.quotes`" (Phase 5), and the item `language` field (Phase 5 schema). | K§5 P7 vs P2/P4/P5 | Design the language fields and the `[translation]` grammar in Phases 2–5, with Unicode fixtures in the synthetic incident. Phase 7 adds only the Tesseract and Whisper language packs. |
| P9 | **Confidence plumbing:** `low_confidence_source` status and the soft warning are Phase 5 gates; their producers are OCR (Phase 7) and transcripts (Phase 8). | P5 vs P7/P8 | The segment `confidence` field and status derivation go in Phases 2 and 5, tested with a synthetic low-confidence segment. |
| P10 | **Anchor and citation polymorphism:** the claim schema (Phase 3) and the citation renderer (Phase 5) must handle time ranges, sheet row ranges, visual anchors (§7.5) and `[web snapshot …]` (§8.4). Their producers arrive in Phases 8–9. | P3/P5 vs P8/P9 | Declare every anchor type in the Phase 3 schema and every citation form in the Phase 5 renderer, with unit tests. Otherwise claims need a migration later. |
| P11 | **Email attachments and archive members are registered at scan time** (§7.1), but email parsing lands in Phase 2. | K§5 P1 vs P2 | An expander seam in Phase 1 scan; the email expander in Phase 2; the archive expander in Phase 2 (stdlib `zipfile`). `.7z` is optional. |
| P12 | **The synthetic incident fixture belongs to no phase**, yet Phase 3's exit criterion depends on it, and every later phase extends it. | K§5 (all) | Make a fixture generator a Phase 2 deliverable (text PDF via reportlab, DOCX, EML, CSV; planted traps for DEF-01…DEF-18 as they become testable). Phase 7 adds scans; Phase 8 adds wav and mp4. |
| P13 | **Windows and macOS CI come only in Phase 10** (§17.10). CRLF offsets, `os.replace` PermissionError, reserved names, cp1252 stdout and NFD paths would surface after nine phases of code. | §17.10 | A 3-OS CI matrix in Phase 1. The core tests are pure Python and cheap; the media job can still wait. |
| P14 | **Commands the flow needs are missing from §15.2:** `sources set` (Phase 2/3; §8.1 says the agent proposes `source_kind` and `citation_short`), section tagging for observation and held-back sections (Phase 3/5; §11.2 "segments the agent tagged"), `coverage omit` (Phase 5; §11.1 omissions), `items update/remove` for drafts (Phase 5/6; §12.1 step 4), and `run` (Phase 5 router; §15.1). | §15.2 | See C4 and C5. These must be decided before the Phase 3 planning. |
| P15 | **No eval scoring until Phase 10**, yet Phase 5's MVP milestone is "end-to-end on the synthetic incident". | K§5 P5 vs P10 | A minimal scorer in Phase 5 (verbatim rate and page accuracy from `verify`; leak counts from the fixture's gold key). Phase 10 adds host-level agent evals. |

---

## Conflicts with design (need owner decision)

Raise these one at a time.

| # | Conflict or gap | Design ref | Recommendation (first) | Alternative |
|---|---|---|---|---|
| C1 | **Schema location.** §5 puts `schemas/` at the repo root. Codex installs copy only the `skills/` folders (`$HOME/.agents/skills`), so the CLI cannot rely on repo-root files at runtime. | §5, §15.3 | **(Recommended)** Make `scripts/epb/schemas/` the canonical runtime copy, and have a test assert the root `schemas/` is an identical published mirror. | Drop the root `schemas/` entirely. |
| C2 | **No JSON Schema validator in the §5 core list**, though kickoff §7 requires "validate on every write". | §5, K§7 | **(Recommended)** Add `jsonschema` (MIT; its dependency chain is MIT, including the compiled `rpds-py`). It reports all errors with paths for agent repair. | `fastjsonschema` (BSD-3, zero deps, draft-07, first error only). |
| C3 | **Four exit codes can't express an internal error or a lock timeout.** An uncaught exception exits 1, which reads as "gate failure". A workspace newer than the plugin also needs a code. | §15.2 | **(Recommended)** Add exit **4** = internal error, lock timeout or incompatible workspace, with the cause in `errors[].code`. | Fold these into 2, accepting that "usage" becomes overloaded. |
| C4 | **Missing CLI verbs:** `sources set`, `sections tag`, `coverage omit`, `items update/remove`, and an agent-safe `roster add` taking file or stdin input. | §8.1, §11.1–11.2, §12.1, §15.2 | **(Recommended)** Add them to §15.2 as listed. | Overload `items add` as an upsert for drafts, and put omissions into `items add`'s payload. |
| C5 | **`run` appears in §15.1 but not in the §15.2 command list.** | §15.1 vs §15.2 | **(Recommended)** Add `run`: execute the deterministic stages that are due, then return the next-action list (Pattern 7). | Drop `run` and use `status --json` with a `next` field only. |
| C6 | **Workspace additions not named in §6:** `.epb/inbox/` (agent submissions, which contain raw names), `.epb/tmp/` (transaction staging), `ledger/chunks.json`, `.epb/.gitattributes`. | §6 | **(Recommended)** Add them to the §6 tree and to `workspace-contract.md`. | Keep them as undocumented internals. |
| C7 | **`.epb/.gitignore` covers only `private/` and `media/`**, yet `segments/`, `ledger/` and `inbox/` hold raw text with names (§6 rule 4). If a case folder is a git repo, those get committed. | §6 rules, §13.5 | **(Recommended)** Make `.epb/.gitignore` ignore everything except `case.yaml`, `rosters/`, `items/`, `conflicts.yaml` and `coverage.json` (or simply ignore `*`). Have `deid-scan` scope also include `runs/*/run.json`. | Keep the design as written and rely on the `init` warning. |
| C8 | **Python 3.10 floor.** Python 3.10 reached end-of-life on 2026-10-01 (PEP 619). The latest `rpds-py`, `RapidFuzz` and `filelock` already require 3.11 or later. | §15.3, K§3 | Hand this to the STACK research. Architecturally either works. **(Recommended)** Keep 3.10 with pinned minimums that still support it, test 3.10 in CI, and revisit after v0.1.0. | Raise the floor to 3.11. |
| C9 | **CI matrix timing.** §17 puts the CI matrix in step 10. Windows defects would accumulate for nine phases. | §17.1/§17.10 | **(Recommended)** Run the 3-OS core matrix from Phase 1; the media job stays in Phase 10. | Keep §17 as written. |
| C10 | **Lock semantics versus parallel subagents.** §12.5 says one lock "prevents two runs at once", while §15.3 has subagents calling `claims add` in parallel. | §12.5, §15.3 | **(Recommended)** Mutating commands wait for the lock (default 60 s), and read-only commands take no lock. | A hard fail on contention, with subagents retrying. |

---

## Sources

- Approved design `docs/design/2026-10-17-evidence-pack-builder-design.md` §5–§19; `docs/GSD-KICKOFF.md` §3, §5, §7; `.planning/PROJECT.md` (HIGH, primary)
- Local experiments, 2026-10-17, Python 3.14.4: PyYAML 6.0.3 implicit typing (`12:30`→750, dates→`date`, `no`→False, `010`→8); package-vs-script shadowing (without `__init__.py`, `epb.py` imports itself); argparse usage error → exit 2, 3.14 `color=True` and `allow_abbrev=True` defaults; openpyxl 3.1.5 `"=…"` strings inferred as formulas, `data_type="s"` override persists (HIGH, verified)
- Python `os` docs: `os.replace` atomic as a POSIX requirement with no Windows guarantee; Windows `os.kill` with any signal other than CTRL_C/CTRL_BREAK calls `TerminateProcess` — https://docs.python.org/3/library/os.html (HIGH)
- PEP 619 (Python 3.10 EOL 2026-10-01) — https://peps.python.org/pep-0619/ (HIGH)
- PEP 686 (UTF-8 mode default from 3.15) — https://peps.python.org/pep-0686/ ; https://pydevtools.com/blog/python-315-utf8-default/ (MEDIUM)
- PyPI JSON API (2026-10-17): jsonschema 4.26.0 MIT; fastjsonschema 2.22.2 BSD-3; rpds-py 2026.9.1 MIT (≥3.11, wheels incl. win_arm64/cp314); filelock 4.2.0 MIT (≥3.11; released 2026-10-14, inside the two-week embargo); typer 0.27.3 MIT (rich, shellingham, colorama); click 8.5.0 BSD-3; RapidFuzz 3.14.6 (≥3.11) (HIGH)
- Claude Code skills docs: `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PLUGIN_ROOT}` substitution in plugin skills and `allowed-tools` — https://code.claude.com/docs/en/skills (HIGH)
- Codex skills docs: `.agents/skills` repo scan up to root, `$HOME/.agents/skills`, `/etc/codex/skills`, symlinks followed — https://learn.chatgpt.com/docs/build-skills (MEDIUM; vendor docs moved recently)
- Python-dev discussion on MoveFileEx atomicity — https://www.python.org/pipermail/python-dev/2007-April/072887.html (LOW, background only)

---
*Architecture research for: agent plugin with a deterministic Python CLI over a file-based case workspace*
*Researched: 2026-10-17*
