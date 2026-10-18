# Requirements: ProbeMatrix Evidence Pack Builder

**Defined:** 2026-10-17
**Core Value:** Every item in a pack is traceable and trustworthy. Every quote is verbatim on the cited page or time of a saved input. Every person appears only as a role label. No source conclusion, lesson or recommendation is ever treated as evidence. The workbook imports into ProbeMatrix cleanly, without duplicates.

**Source of truth:** `docs/design/2026-10-17-evidence-pack-builder-design.md`. Each requirement cites its section (`§n`). §20 (amendments A1–A14) wins over earlier sections. The design's defects D1–D18 are written here as **DEF-01…DEF-18**, to avoid clashing with GSD's `D-NN` decision tokens.
**Repo scope:** this repo only. The parent ProbeMatrix checkout is read-only reference material and is never modified or depended on.

## v1 Requirements (v0.1.0)

### Workspace and state (WS)

- [ ] **WS-01**: The user can run `epb init` in any folder to create `inputs/`, `outputs/`, `INDEX.md` and `.epb/` with `case.yaml` (slug, title, ID prefix, timezone, plugin version). (§6)
- [ ] **WS-02**: `epb scan` fingerprints every input:
  - It records SHA-256, size, MIME type and mtime for each file, walking `inputs/` recursively.
  - It assigns stable `S001…` IDs.
  - It ignores OS junk files and lists them as ignored. (§7.1)
- [ ] **WS-03**: `scan` detects and reports each change of state:
  - **New version:** a known path with changed content becomes `S004v2`.
  - **Rename:** a known hash at a new path is treated as a rename.
  - **Duplicate:** identical content at two paths becomes one source with two paths.
  - **Removed:** a source missing from the folder is marked `removed from folder`. (§7.1)
- [ ] **WS-04**: `scan` pairs `<file>.note.md` and `<file>.note.yaml` sidecars with their input, and hashes them as inputs too. (§7.2, research PF-01)
- [ ] **WS-05**: Archives (`.zip`, plus `.7z` when a `7z` binary exists) and email attachments are registered as child sources with a parent link. Zip-slip paths are refused. (§7.1, PF-11)
- [ ] **WS-06**: All writes to `.epb/` are atomic (temp file plus replace, with a retry on Windows). They are grouped in journalled transactions, with `state.json` written last. A crash at any point resumes cleanly. (§12.5, PF-06)
- [ ] **WS-07**: A lock prevents two mutating runs at once. Mutating commands wait (default 60 s) before giving up. Read-only commands take no lock. (§12.5)
- [x] **WS-08**: Every persisted file is validated against its JSON Schema on write. YAML is read with a strict loader that keeps every scalar as text, so values such as `12:30`, `0123` and `no` survive unchanged. (§5 schemas, §20 A7)
- [x] **WS-09**: `INDEX.md` is regenerated on every run with the six sections in order: case header, what to import where (with an "Imported?" checkbox), inputs snapshot, outputs snapshot, open issues, and run history. A section whose producer does not exist yet shows "none yet". (§6.1, PF-04)
- [ ] **WS-10**: `INDEX.md` shows no personal names. File names that contain names are shown with role-label substitution. (§6.1)
- [x] **WS-11**: `.epb/.gitignore` ignores every file that can hold raw text: `segments/`, `ledger/`, `inbox/`, `tmp/`, `media/`, `runs/` and `private/`. `init` warns when the case folder is a git repo that would track `.epb/private/`. (§6, §20 A2)
- [x] **WS-12**: `init` and `doctor` warn in plain language when the case folder is inside OneDrive, Dropbox, iCloud Drive or Google Drive. (§20 A1)
- [ ] **WS-13**: The `state.json` schema defines the following from Phase 1, so later phases never migrate it: the workbook registry (file, version, draft or imported, fingerprint), the Evidence ID and Tag counters, and chunk status. (PF-07)

### Text intake (INT)

- [ ] **INT-01**: Text PDFs are converted per page with pdfplumber, including words with positions and tables, with pypdf as the fallback. Each PDF is parsed in a separate process with time and memory limits. A failure marks only that input `unprocessed: <reason>`. (§7.2, §20 A6)
- [ ] **INT-02**: Multi-column PDF pages are read in column order, not interleaved line by line. (§7.2, research pitfall 2)
- [ ] **INT-03**: DOCX is converted with paragraph numbers, tables, headers and comments. Tracked insertions and deletions are read from the XML and flagged. (§7.2, §20 A7)
- [ ] **INT-04**: PPTX is converted per slide, including speaker notes. (§7.2)
- [ ] **INT-05**: XLSX and CSV are converted per sheet, with header detection and row-range segments. Very large tables are summarised by schema plus row-range segments. (§7.2)
- [ ] **INT-06**: `.eml` email is converted to a header block (roles, date, subject) plus the body, with RFC 2047 headers decoded. Attachments become child sources. `.msg` is supported only through the optional `requirements-email.txt` extra. (§7.2, §18)
- [ ] **INT-07**: HTML is converted to Markdown with main-content extraction and its retrieval metadata. (§7.2)
- [ ] **INT-08**: TXT, MD and chat exports are converted to line-numbered Markdown, keeping message timestamps. (§7.2)
- [ ] **INT-09**: Every converted source becomes ordered segments (`S001-p017`). Each segment records its printed page label, physical index, section heading path, text, tables, captions and a confidence field. (§7.3, PF-09)
- [ ] **INT-10**: For each source the plugin decides once which page numbering to use: printed labels when they are reliably detected, otherwise physical pages rendered as `PDF p.<n>`. Annexes that restart their numbering use their annex label. (§7.3, §20 A13)
- [ ] **INT-11**: Each source gets a section map (`segments/<src>/index.json`), a heading tree with page ranges. (§7.3)
- [ ] **INT-12**: Running headers, footers and letterheads that repeat across pages are detected and excluded from extraction, but kept in the raw text. (§7.3)
- [ ] **INT-13**: Sections are screened at segmentation as `held_back`, `observation` or `mixed`. The held-back headings are "Root Cause(s)", "Conclusions", "Analysis of the incident", "Lessons learned", "Recommendations", "Improvements / Remedial measures", "Way forward" and "Action plan". (§11.3 layer 1, PF-03)
- [ ] **INT-14**: Document metadata author fields and email display names are captured as person entities for de-identification. They are never passed through raw. (§13.4, PF-17)
- [ ] **INT-15**: Inputs of an unknown type are listed as `unprocessed: unsupported type` and are never silently ignored. (§2 goal 1, §7.2)
- [ ] **INT-16**: Segments are frozen once written. Re-conversion happens only through an explicit `rebuild --from convert`, which reports a diff. (§12.3, research OD-24)

### Quote verification (QV)

- [ ] **QV-01**: A quote verifies only if it matches the cited segments exactly after a fixed, versioned set of folds: whitespace, line-break hyphenation, Unicode quote and dash variants, and ligatures. Fuzzy scores never accept a quote. (§8.2)
- [ ] **QV-02**: A quote containing `…` verifies only if each fragment matches, in order, within the cited segments. (§8.2)
- [ ] **QV-03**: A quote spanning a page break verifies across segments and is cited to both pages (`pp.16–17`). (§8.2, §7.3)
- [ ] **QV-04**: `[sic]` keeps a source error verbatim. The verifier rejects a quote whose typo has been silently corrected. (§8.2)
- [ ] **QV-05**: A bracketed role label inside a quote matches the original name span, with or without its honorific, through the name map. The verifier takes an injected label resolver, so it can be tested before the name map exists. (§13.3, PF-02)
- [ ] **QV-06**: The verifier rejects every case in a negative corpus: an inserted negation, a changed number, a changed case, a paraphrase in quote marks, and a corrected typo. On the bundled reference report it rejects the prototype's quotes known to be invented or paraphrased (DEF-01, DEF-02) and accepts the prototype's genuinely verbatim quotes. (§3, §16)

### Extraction and claim ledger (EXT)

- [ ] **EXT-01**: `epb plan-extract` builds chunks of consecutive segments within one section. Each chunk is about 6–8k tokens, with one segment of overlap. (§7.4)
- [ ] **EXT-02**: `epb claims add --chunk <id> <file>` validates each submitted claim against the claim schema and verifies every anchor quote on write. Any failure rejects the claim and lists every error with its path. (§7.4, §8.2)
- [ ] **EXT-03**: Agent submissions cannot set fields the CLI owns (claim IDs, character offsets, page labels). Those fields are assigned by the CLI. (research architecture)
- [ ] **EXT-04**: Claims carry `kind`, `asserted_by`, `anchor_quotes`, `values` (dates with precision), `entities`, `underlying_artefact`, `event_time` and `artefact_date`. (§7.4)
- [ ] **EXT-05**: The anchor schema declares every anchor type up front: page, cross-page, time range, sheet row range, visual and web snapshot. (§8.4 Source, PF-10)
- [ ] **EXT-06**: `epb extract-status` shows which chunks are done and which are pending. An interrupted extraction resumes at the first unfinished chunk. (§7.4)
- [ ] **EXT-07**: Parallel extraction is safe: chunk-suffixed submission files are merged by `claims add` under the lock. (§15.3)
- [ ] **EXT-08**: Every CLI write to the ledger and items is journalled, so `verify` can detect hand edits that bypassed the CLI. (PF-19)

### Evidence-bank entry rule (EVB)

- [ ] **EVB-01**: Claims of kind `conclusion`, `lesson` or `recommendation` are written only to `ledger/conclusions.jsonl`, never to `claims.jsonl`. (§11.3 layer 2)
- [ ] **EVB-02**: `claims add` rejects an evidence-kind claim if it comes from a `held_back` section, or if its anchor text matches verdict, lesson or recommendation patterns. The message tells the agent to reclassify or split the claim. (§11.3 layer 2)
- [ ] **EVB-03**: A sentence that mixes fact and verdict is split: the fact becomes an evidence claim and the verdict is held back. When in doubt, the claim is held back. The run report lists borderline splits. (§11.3)
- [ ] **EVB-04**: `items add` rejects any item that references a held-back claim. (§11.3 layer 3)
- [ ] **EVB-05**: `conclusions.jsonl` never reaches `outputs/`, items or `INDEX.md`. INDEX shows only its count. No setting turns the rule off. (§11.3)

### De-identification (DEID)

- [ ] **DEID-01**: The pattern pass detects names after honorifics and titles, including Indian honorifics in Latin and Indic scripts (Shri, Smt., Sh., Er., श्री, श्रीमती …). It also detects signature blocks, "Name:" fields, emails, phone numbers and ID patterns. (§13.1, §13.3a)
- [ ] **DEID-02**: Every person mention an agent extracts is captured with its raw string and role context, and mapped to a role label in `.epb/private/name-map.yaml`. (§13.1)
- [ ] **DEID-03**: Role labels follow `<Designation> (<Function / Location>)`. They are comma-free and stable for the life of the case. External people get letter codes. Committees become the body. (§13.2)
- [ ] **DEID-04**: A name inside a quote is replaced, together with its honorific, by its bracketed role label. (§13.3, DEF-15)
- [ ] **DEID-05**: Name variants (surname, first name, initials, possessive, honorific forms, Indic-script and zero-width-stripped forms) are added to the scan list. (§13.1 layer 4)
- [ ] **DEID-06**: `epb deid-scan` scans `items/`, `outputs/*.xlsx`, `INDEX.md`, `runs/*/report.md` and `runs/*/run.json`. Matching is whole-word, with a per-case allow-list where every entry needs a justification. (§13.5, §20 A2)
- [ ] **DEID-07**: A map-independent scan flags capitalised and Indic-script tokens that look like names but are not on the roster or allow-list, so names never captured into the map are still caught. (research pitfall 3)
- [ ] **DEID-08**: GPS EXIF data is stripped from anything rendered, faces are never described, and file names that contain names are substituted in shareable output. (§13.4)
- [ ] **DEID-09**: The renderer is the only route from segments or claims into the workbook, and it applies the name map. (§13.5)
- [ ] **DEID-10**: Optional NER (spaCy small model) runs as a third detection pass when it is installed, and is skipped cleanly when it is not. (§13.1)

### Reconcile and conflicts (REC)

- [ ] **REC-01**: The role and equipment rosters hold labels plus aliases, through `roster list/add/alias`. Input comes from a file or stdin, never from names on the command line, and comma-bearing labels are rejected. (§7.6, §20 A12)
- [ ] **REC-02**: Equipment IDs that differ within a source are recorded as aliases with a source-inconsistency note, and never normalised inside a quote. (§13.4, DEF-18)
- [ ] **REC-03**: Event claims are clustered by referent, using roster entities and times. (§7.6)
- [ ] **REC-04**: `epb conflicts detect` proposes:
  - time conflicts, beyond a tolerance (default 60 s, configurable, precision-aware)
  - value conflicts
  - actor and action conflicts
  - sequence conflicts
  - outcome or framing conflicts (§10.2)
- [ ] **REC-05**: `epb conflicts resolve` confirms or dismisses a conflict, with a reason. It cannot pick a winner. Dismissal is for false positives only. (§10.2)
- [ ] **REC-06**: Each confirmed conflict gets a register entry. Every item touching it gets `status: disputed`, states both versions with citations, and links to the related items. (§10.3, DEF-04)

### Authoring (AUT)

- [ ] **AUT-01**: `epb author-plan` proposes groupings of claims into items, by shared underlying artefact and perspective. (§7.7)
- [ ] **AUT-02**: `epb items add` validates an item YAML on write against the item schema (§8.3). The quotes must come from the item's claims. Items reference claims and never restate anchors by hand. (§7.7, §8.3)
- [ ] **AUT-03**: `epb items update` and `items remove` revise draft items only. A removed item leaves a gap in the IDs, which are never reused. (§12.1, §20 A12)
- [ ] **AUT-04**: The evidence type is assigned from the underlying artefact by the §9.1 rules and tie-breakers, with a stored `type_rationale`. (§9.1, DEF-09)
- [ ] **AUT-05**: Collection Method comes from the controlled list. (§9.1)
- [ ] **AUT-06**: Each item has 2–5 tags from the controlled vocabulary, plus `tags_extra` from `case.yaml`, linted against the HFACS blocked list. (§9.2, DEF-06)
- [ ] **AUT-07**: Priority follows the §9.3 rubric, with a stored `priority_rationale`. (§9.3)
- [ ] **AUT-08**: Descriptions follow the three-part standard: a lead-in naming the artefact and perspective, an anchor, and the operational significance. Every factual sentence in part 3 maps to a claim of the item or of a related item. (§9.4, DEF-05, DEF-10)
- [ ] **AUT-09**: `epb calc` computes durations and date differences, so Descriptions contain no arithmetic slips. (§9.4)
- [ ] **AUT-10**: Non-English quotes stay in their original language and script, followed by an agent-written English rendering marked `[translation]`. Only the original is verified. The item records its `language`. (§13.3a, PF-08)
- [ ] **AUT-11**: A visual observation claim records only what is visible. It is flagged `anchor: visual`, never identifies people, and is listed for review. (§7.5)

### Verification gates (VER)

Each hard gate blocks the build. (§14)

- [ ] **VER-01**: Hard gate 1: every `“…”` quotation in every Description is in `item.quotes` and verifies in the current source version. (DEF-01, DEF-02)
- [ ] **VER-02**: Hard gate 2: the page and time references in `Source` equal the labels of the anchor segments. (DEF-03)
- [ ] **VER-03**: Hard gate 3: the format is importer-exact, as re-read from the saved file on disk. This covers sheets, headers, order, required fields, enums, valid custody JSON and the 10-row metadata layout. (§8.4)
- [ ] **VER-04**: Hard gate 4: list elements are comma-free in Linked Individuals, Linked Equipment, Tags and Regulatory Requirements. (DEF-14)
- [ ] **VER-05**: Hard gate 5: no Evidence IDs, row numbers or "row N" appear in Descriptions. (DEF-07)
- [ ] **VER-06**: Hard gate 6: an HFACS blocked-term lint runs on Descriptions and Tags. (DEF-06)
- [ ] **VER-07**: Hard gate 7: no item references a held-back claim, and no Description fuzzy-matches a held-back claim or verdict or recommendation patterns. (§11.3 layer 4, DEF-13)
- [ ] **VER-08**: Hard gate 8: the de-identification scan has zero hits. (§13.5)
- [ ] **VER-09**: Hard gate 9: the coverage gate passes (COV-02).
- [ ] **VER-10**: Hard gate 10: every Description is at most 1,800 characters. (DEF-16)
- [ ] **VER-11**: Hard gate 11: Collection Date is rendered at its stored precision (`YYYY`, `YYYY-MM` or `YYYY-MM-DD`) and never padded. (DEF-08)
- [ ] **VER-12**: Hard gate 12: every item has at least one claim, and every claim's source is `processed` or `partial`.
- [ ] **VER-13**: Soft warnings are listed in the run report for the agent to review:
  - visual or low-confidence anchors
  - evaluative or speculative phrases
  - type-rule lints
  - critical share above 45%
  - length outside 300–900 characters
  - missing Related Evidence where an aligned event cluster exists
  - a lead-in with no perspective cue
  - a straight-quote quotation (§14, DEF-09, DEF-16)
- [ ] **VER-14**: The spot-check lists 5 seeded, reproducible random items, each with its claims and the de-identified raw context around each anchor. (§14)
- [ ] **VER-15**: An item drawn from a low-confidence OCR or transcript segment gets `status: low_confidence_source` and its Description says so. (§14, PF-09)

### Coverage (COV)

- [ ] **COV-01**: Every claim ends in exactly one state: `in_item`, `merged_into:<claim>`, or `omitted:<reason>`, with the reason from the fixed list. `epb coverage omit` records an omission, and `epb coverage` reports totals per section and per source. (§11.1, §20 A12)
- [ ] **COV-02**: In sections tagged as observation or finding sections, every observation, record, measurement, condition, statement or event claim is in an item or has a recorded reason, otherwise the build is blocked. `epb sections tag` sets the tag. (§11.2, DEF-12)
- [ ] **COV-03**: A density warning fires when a source yields fewer than one item per 1.5 observation pages, or more than 3 per page. There is no item-count target. (§11.2)

### Build and format (BLD)

- [ ] **BLD-01**: `formats/probematrix_v2.py` owns the format marker, sheet names, header order, column widths, enums, list separator and the 10-row metadata layout, all transcribed from the importer. `references/evidence-pack-v2.md` documents the format with the date it was checked. (§8.5, §8.4 importer re-check)
- [x] **BLD-02**: Every cell is written as text, with control characters removed. A cell starting with `=`, `+`, `-` or `@` never becomes a formula, and dates and long IDs never become numbers. (§8.4 re-check item 8)
- [x] **BLD-03**: The validator is stricter than the importer. It rejects:
  - a blank Description or Type
  - non-exact enum values
  - non-string cells
  - formulas
  - cells over 32,767 characters
  - Chain of Custody JSON that does not match `ChainOfCustodyEntry` (§8.4 re-check items 3–6, 10)
- [ ] **BLD-04**: Columns are filled per the §8.4 mapping:
  - `Source` and Chain of Custody are generated
  - Hash/Checksum is `sha256:<hex>`
  - Related Evidence holds Evidence Tags
  - Integrity Verified is `No`
  - QA Status is `verified` or `disputed`
  - Collector and Storage Location are de-identified (§8.4, DEF-07)
- [ ] **BLD-05**: Source citations take the form `p.<n>`, `pp.<a>–<b>`, `PDF p.<n>`, `<annex> p.<n>`, `hh:mm:ss–hh:mm:ss`, `sheet <name> rows <a>–<b>`, or `[web snapshot <date>] <url>`. (§8.4, §20 A13)
- [ ] **BLD-06**: The source documents themselves never become evidence items. (§8.4, DEF-17)
- [ ] **BLD-07**: `epb build` writes `outputs/evidence-pack-<case>-master.xlsx` from all items while the master is a draft. A run with no new or changed items writes nothing and says so. (§12.1)
- [x] **BLD-08**: Pack Metadata uses the exact 10-row layout, with Total Evidence Items equal to the number of items in this file. The Attachments Manifest is written with headers only. (§8.4)

### Incremental runs (INC)

- [ ] **INC-01**: `epb mark-imported <file>`, or a ticked "Imported?" box in `INDEX.md` (read back on the next run), locks a workbook. The plugin never locks a workbook on its own. (§12.1 step 5a)
- [ ] **INC-02**: When a draft was rewritten after a possible upload, `mark-imported` asks the user to confirm the item count and Tag range before locking. Ticks are one-way. (research OD-15)
- [ ] **INC-03**: Once the master is imported, new items go to `evidence-pack-<case>-delta-NNN.xlsx`, which contains only new items. That delta stays a draft until it is marked imported. (§12.1 step 5)
- [ ] **INC-04**: Evidence IDs and Tags continue across master and deltas and are never reused or renumbered. (§12.1)
- [ ] **INC-05**: Unchanged sources reuse their segments and claims. New claims are reconciled against the existing rosters and checked for conflicts against all claims. (§12.1 steps 2–3)
- [ ] **INC-06**: Changed inputs are diffed against the earlier version, and claims whose anchors no longer verify are flagged. (§12.2)
- [ ] **INC-07**: A fix to a locked item is shipped as a correction item in the next delta. Its Description begins "CORRECTION to evidence tagged TAG-…" and it links to the original tag. INDEX lists it with manual clean-up instructions. (§12.4)
- [ ] **INC-08**: An imported workbook is never written to again. (§12.1)
- [ ] **INC-09**: `epb rebuild --from <stage>` recomputes intermediate state without changing any shipped item IDs. (§12.3)
- [ ] **INC-10**: `epb build --consolidated` writes `evidence-pack-<case>-consolidated-<date>.xlsx`, and only on explicit request. (§12.3)
- [ ] **INC-11**: The plugin warns when a draft master has gone un-imported for longer than `draft_warning_days` (default 7). (§12.1)

### Scans and OCR (OCR)

- [ ] **OCR-01**: Scanned or image-only pages are detected one page at a time, and OCR runs only on those pages, so a mixed PDF is handled page by page. (§7.2)
- [ ] **OCR-02**: OCR produces per-page text and a confidence for the quoted span, and the confidence is carried into segments, claims and items. (§7.2, research OD-14)
- [ ] **OCR-03**: Tesseract language packs come from `case.yaml` `languages`, and `doctor` checks that they are installed. (§13.3a)
- [ ] **OCR-04**: Low-confidence OCR pages are flagged in INDEX "Open issues" and on the affected items. (§14)
- [ ] **OCR-05**: The optional docling path converts complex-layout PDFs when docling is installed. (§7.2)

### Media and images (MED)

- [ ] **MED-01**: Audio (wav, mp3, m4a, ogg) is transcribed locally with ffmpeg and faster-whisper, producing time-anchored segments that carry per-segment confidence. If no transcriber is available, the input is marked `unprocessed: transcription unavailable`. (§7.2)
- [ ] **MED-02**: Silent or speech-free audio produces no transcript text. Voice activity detection runs before transcription. (research pitfall: Whisper hallucination)
- [ ] **MED-03**: Video audio tracks are transcribed. Keyframes are extracted at scene changes, with a minimum frequency floor and a frame cap, and keep their media timestamps. (§7.2)
- [ ] **MED-04**: Burned-in CCTV timestamps are read by OCR and give the real-world time. (§7.2)
- [ ] **MED-05**: Images record EXIF capture time and device, and GPS is stripped from anything shareable. The agent describes each image or keyframe as a visual-observation claim. (§7.2, §7.5)
- [ ] **MED-06**: Sidecar notes supply who recorded what, speaker roles, camera and custody, and they are cited when used. (§7.2)
- [ ] **MED-07**: Media citations render as `hh:mm:ss–hh:mm:ss`. (§8.4)
- [ ] **MED-08**: Speaker diarisation is an optional extra and is off by default. (§7.2)

### Web snapshot (WEB)

- [ ] **WEB-01**: The `evidence-web-snapshot` skill runs only when the user asks. It proposes URLs, and the user confirms which to keep. (§7.9)
- [ ] **WEB-02**: `epb snapshot <url>` saves raw HTML, extracted Markdown and `meta.yaml` to `inputs/web/<YYYY-MM-DD>-<domain>-<slug>/`. The metadata covers URL, retrieval time, status, title, a de-identified byline and the publication date. (§7.9)
- [ ] **WEB-03**: A failed or paywalled fetch is recorded and never paraphrased from memory. No web claim exists without a saved snapshot. (§7.9, DEF-11)

### Packaging and setup (PKG)

- [ ] **PKG-01**: The plugin lives in `plugin/`, with `.claude-plugin/plugin.json`. The repo root holds `marketplace.json` (name `probematrix-evidence-pack-builder`, `source: "./plugin"`). (§5, §20 A4)
- [ ] **PKG-02**: Seven skills follow the Agent Skills format, each SKILL.md at most about 150 lines:
  - `evidence-pack` (the router)
  - `evidence-intake`
  - `evidence-extraction`
  - `evidence-reconcile`
  - `evidence-authoring`
  - `evidence-verify-build`
  - `evidence-web-snapshot`

  Shared rules live in `evidence-pack/references/`. (§5, §15.1)
- [ ] **PKG-03**: `AGENTS.md` holds the plugin's host-neutral rules for agents: just culture, roles only, inputs only, facts only, verbatim quotes, and the evidence-bank entry rule. (§5, kickoff §6a)
- [ ] **PKG-04**: The CLI provides every command in §15.2, plus the §20 A12 verbs (`sources set`, `sections tag`, `coverage omit`, `items update/remove`, roster input from a file, and `run` returning `next[]`). Every command accepts `--json`. (§15.2, §20 A12)
- [x] **PKG-05**: Exit codes are 0 OK, 1 gate failure, 2 usage, 3 missing dependency, and 4 internal or environment error, with a stable error code in the JSON. (§15.2, §20 A11)
- [x] **PKG-06**: `epb.py` is a standard-library-only launcher. `epb doctor --setup` finds a suitable Python 3.11+, creates a private environment in the plugin's per-user data folder, installs the core packages, and reports what is ready and what is optional in plain language. Skills launch the CLI from that environment. (§20 A8)
- [x] **PKG-07**: `epb doctor` reports each tool: found or not, its version, the input types it enables, and install commands for each OS. A missing optional tool never fails a run. (§7.2)
- [x] **PKG-08**: Core dependencies are permissively licensed, with minimum versions pinned, including `jsonschema`, `lxml>=6.1.0`, `defusedxml`, `charset-normalizer`, `pdfplumber>=0.11.9`, `Pillow>=12.3.0` and `pypdf>=6.19.0`, and `tzdata` on Windows only (D-20). GPL extras are kept in separate optional requirements files and their licences are documented. (§18, §20 A6–A7)
- [x] **PKG-09**: CI checks dependency age (the two-week rule) against a reviewed security-exception list, and licences against an allow-list. (§20 A6)
- [ ] **PKG-10**: The plugin installs through `/plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder` plus `/plugin install` on Claude Code, through Cowork's plugin upload, and on Codex through its supported route. (§15.3, kickoff §11)
- [ ] **PKG-11**: The repo-root `AGENTS.md` and `CLAUDE.md` are exact copies of each other, holding the developer instructions. They are regenerated and re-copied whenever project context, roadmap, stack or workflow rules change (at least at every phase transition), and a CI test fails if they differ or exceed 150 lines. They are hand-maintained and concise (aim for 60 lines or fewer, pointers rather than copies); GSD's `generate-claude-md` is never run on them. (§20 A15)

### Documentation (DOC)

- [ ] **DOC-01**: A user manual for non-technical users covers, step by step and with exact on-screen text, on Windows, macOS and Linux:
  - installing Python
  - installing the optional tools (Tesseract, ffmpeg)
  - installing the plugin in Claude Code, Cowork and Codex
  - running first-time setup (`doctor --setup`) (§20 A14)
- [ ] **DOC-02**: The manual covers everyday use: creating a case folder, adding inputs, asking the agent to build a pack, reading `INDEX.md`, importing the master and deltas into ProbeMatrix, and marking a workbook imported. (§20 A14)
- [ ] **DOC-03**: The manual has a troubleshooting section that maps every `doctor` message and exit-4 error code to a plain-language fix. (§20 A11, A14)
- [ ] **DOC-04**: The manual explains in plain language what stays local, what the AI host sees, why case folders should not sit in sync folders, and the always-on de-identification. (§20 A1)
- [ ] **DOC-05**: The manual is started in Phase 1 and extended in every phase that adds a tool or user step. Its Windows and macOS sections are marked "not yet tested on this system" until a post-v0.1.0 release tests them. (§20 A9, A14)
- [ ] **DOC-06**: The shared skill references are written: workspace contract, evidence-pack-v2, evidence types, description quality (with synthetic good and bad pairs), de-identification, assertions and conflicts, conclusions policy, tag vocabulary and citation style. (§5)
- [ ] **DOC-07**: README, CHANGELOG, CONTRIBUTING and SECURITY are written for v0.1.0. (§5)

### Testing and release (TST)

- [x] **TST-01**: pytest and ruff run, with no network in tests. Tests for optional tools skip cleanly when the tool is absent. (kickoff §7)
- [ ] **TST-02**: A synthetic incident fixture generator produces a fully fictional incident with planted traps for every DEF class:
  - a contradiction
  - a typo needing `[sic]`
  - a cross-page quote
  - a dropped-finding bait
  - names with honorifics
  - inch marks
  - root-cause, lessons and recommendation sections, and mixed fact-and-verdict sentences
  - a year-only date
  - a printed-versus-physical page offset

  It is started in Phase 2 and extended for scans and media. (§16, PF-12)
- [ ] **TST-03**: A minimal eval scorer measures verbatim-quote rate, page accuracy, conclusions leaked, names leaked and coverage against the gold key, from Phase 5. (§16, PF-15)
- [ ] **TST-04**: Agent evals on the synthetic incident meet these thresholds: verbatim 100%, page accuracy 100%, names leaked 0, conclusions leaked 0. They also report conflicts surfaced and type accuracy, and include the incremental scenario. (§16)
- [ ] **TST-05**: A regression benchmark on the bundled reference report runs in a scratch, git-ignored folder. It reports the numbers for quotes verifiable, page accuracy, coverage of the DEF-12 findings and conclusion leakage. Nothing from it is committed. (§16, §20 A3)
- [ ] **TST-06**: GitHub Actions CI runs the core tests and lint on Linux (Python 3.11 and 3.14), plus a media job with ffmpeg, Tesseract and the faster-whisper `tiny` model. (§16, §20 A9)
- [ ] **TST-07**: Tests inject crashes into each transaction step and confirm the run resumes without corrupting state. (§12.5)
- [ ] **TST-08**: v0.1.0 is released with the version tag pushed, after all phases are verified. (kickoff §11)

## v2 Requirements (deferred)

- **V2-01**: Windows and macOS CI, plus fresh-machine walkthroughs of the manual on those systems (§20 A9).
- **V2-02**: Near-duplicate detection across inputs, e.g. the same report as DOCX and PDF (research OD-30).
- **V2-03**: Full email threading. Splitting quoted reply blocks into their own perspective is decided in Phase 2 discussion (OD-31).
- **V2-04**: A withheld-input register, e.g. for privileged legal advice (OD-32).
- **V2-05**: Cheap audit additions: a de-identification replacement summary, an over-redaction eval metric, and re-hashing inputs at build (OD-33).
- **V2-06**: `epb search <term>` over segments, with private-only output (OD-34).
- **V2-07**: A bundled standalone runtime, so users don't install Python themselves (an OD-07 alternative).
- **V2-08**: docling as the default PDF path, once its footprint and model licence are acceptable (§19, OD-28).

## Out of Scope

| Feature | Reason |
|---------|--------|
| HFACS classification, root-cause analysis, recommendations | ProbeMatrix's job (§2 non-goals) |
| Automatic import or a ProbeMatrix API client | The user uploads the workbook (§2) |
| Output formats other than EVIDENCE_PACK_V2 | `outputs/` holds packs only; the format seam is kept (§2, §8.5) |
| GUI | The agent, the CLI and INDEX.md are the interface (§2) |
| Cloud OCR, transcription or document AI | Conversion is local only (§2, §4) |
| Opt-outs for de-identification or the conclusions rule | Always on (§4, §11.3) |
| Published samples (`samples/`, `make-sample.py`) | The repo ships the plugin only (§20 A3) |
| Copying prototype code or real-incident prose | Clean-room build; DEF-01 came from copied prose (§4, §16) |
| Anything in the parent ProbeMatrix checkout or other repos | This repo is standalone; the parent is read-only reference |
| Evidence-category inventory in INDEX; chronology table | Drifts towards performing the investigation (OD-35, OD-36) |
| Citations API or LangExtract grounding, image/video redaction, Bates stamping, per-user access log | Host-specific or unneeded under the output contract (OD-37) |
| Item-count targets | Replaced by the coverage gate (§11.2) |

## DEF Traceability (design §3 defects → requirements → tests)

The test names are planned names, finalised in each phase's plan.

| Defect | Requirement(s) | Test |
|--------|----------------|------|
| DEF-01 invented quote | QV-01, QV-06, VER-01, TST-02 | `test_verifier_rejects_invented_quote` (reference report), eval verbatim = 100% |
| DEF-02 paraphrase in quotes, corrected typo, cross-page quote | QV-01, QV-03, QV-04, VER-01 | `test_verifier_negative_corpus`, `test_cross_page_quote`, `test_sic_required` |
| DEF-03 wrong page citations | INT-10, VER-02, BLD-05 | `test_source_pages_generated`, `test_printed_vs_physical_fixture` |
| DEF-04 unflagged contradiction | REC-04, REC-05, REC-06 | `test_conflicts_detect_planted`, eval conflicts surfaced |
| DEF-05 author opinion as evidence | AUT-08, VER-13 | `test_part3_sentence_maps_to_claim`, `test_evaluative_phrase_warning` |
| DEF-06 HFACS vocabulary | AUT-06, VER-06 | `test_hfacs_blocked_terms` |
| DEF-07 broken cross-references | VER-05, BLD-04 | `test_no_ids_in_description`, `test_related_uses_tags` |
| DEF-08 fabricated date precision | EXT-04, VER-11 | `test_date_precision_rendering` |
| DEF-09 inconsistent type and method | AUT-04, AUT-05, VER-13 | `test_type_rules_gold_key`, `test_type_lint_warnings` |
| DEF-10 no record of who asserts what | EXT-04, AUT-08 | `test_asserted_by_required`, `test_lead_in_perspective_warning` |
| DEF-11 unverifiable online items | WEB-02, WEB-03 | `test_web_claim_requires_snapshot` |
| DEF-12 silently dropped findings | COV-01, COV-02, TST-05 | `test_coverage_gate_blocks_unaccounted`, reference benchmark |
| DEF-13 official answer leaking | INT-13, EVB-01…05, VER-07 | `test_entry_gate_rejects_verdict`, `test_items_add_rejects_held_back`, eval conclusions leaked = 0 |
| DEF-14 comma corruption | DEID-03, REC-01, VER-04 | `test_comma_gate`, `test_validator_flags_prototype_commas` |
| DEF-15 redaction artefacts in quotes | DEID-04, QV-05 | `test_quote_deid_bracketed_label_verifies` |
| DEF-16 over-long Descriptions | VER-10, VER-13 | `test_description_length_gate` |
| DEF-17 meta-item about the report | BLD-06 | `test_no_source_meta_items` |
| DEF-18 mismatched IDs in the source | REC-02 | `test_equipment_alias_inconsistency_note` |

## Traceability

Filled in by roadmap creation (2026-10-17). Each v1 requirement maps to exactly one phase. Manual extensions after Phase 1 are success criteria in later phases, not extra requirement IDs (DOC-05).

| Requirement | Phase | Status |
|-------------|-------|--------|
| WS-01 | Phase 1 | Pending |
| WS-02 | Phase 1 | Pending |
| WS-03 | Phase 1 | Pending |
| WS-04 | Phase 1 | Pending |
| WS-05 | Phase 2 | Pending |
| WS-06 | Phase 1 | Pending |
| WS-07 | Phase 1 | Pending |
| WS-08 | Phase 1 | Complete |
| WS-09 | Phase 1 | Complete |
| WS-10 | Phase 4 | Pending |
| WS-11 | Phase 1 | Complete |
| WS-12 | Phase 1 | Complete |
| WS-13 | Phase 1 | Pending |
| INT-01 | Phase 2 | Pending |
| INT-02 | Phase 2 | Pending |
| INT-03 | Phase 2 | Pending |
| INT-04 | Phase 2 | Pending |
| INT-05 | Phase 2 | Pending |
| INT-06 | Phase 2 | Pending |
| INT-07 | Phase 2 | Pending |
| INT-08 | Phase 2 | Pending |
| INT-09 | Phase 2 | Pending |
| INT-10 | Phase 2 | Pending |
| INT-11 | Phase 2 | Pending |
| INT-12 | Phase 2 | Pending |
| INT-13 | Phase 2 | Pending |
| INT-14 | Phase 2 | Pending |
| INT-15 | Phase 2 | Pending |
| INT-16 | Phase 2 | Pending |
| QV-01 | Phase 2 | Pending |
| QV-02 | Phase 2 | Pending |
| QV-03 | Phase 2 | Pending |
| QV-04 | Phase 2 | Pending |
| QV-05 | Phase 2 | Pending |
| QV-06 | Phase 2 | Pending |
| EXT-01 | Phase 3 | Pending |
| EXT-02 | Phase 3 | Pending |
| EXT-03 | Phase 3 | Pending |
| EXT-04 | Phase 3 | Pending |
| EXT-05 | Phase 3 | Pending |
| EXT-06 | Phase 3 | Pending |
| EXT-07 | Phase 3 | Pending |
| EXT-08 | Phase 3 | Pending |
| EVB-01 | Phase 3 | Pending |
| EVB-02 | Phase 3 | Pending |
| EVB-03 | Phase 3 | Pending |
| EVB-04 | Phase 5 | Pending |
| EVB-05 | Phase 5 | Pending |
| DEID-01 | Phase 4 | Pending |
| DEID-02 | Phase 4 | Pending |
| DEID-03 | Phase 4 | Pending |
| DEID-04 | Phase 4 | Pending |
| DEID-05 | Phase 4 | Pending |
| DEID-06 | Phase 4 | Pending |
| DEID-07 | Phase 4 | Pending |
| DEID-08 | Phase 8 | Pending |
| DEID-09 | Phase 5 | Pending |
| DEID-10 | Phase 4 | Pending |
| REC-01 | Phase 4 | Pending |
| REC-02 | Phase 4 | Pending |
| REC-03 | Phase 4 | Pending |
| REC-04 | Phase 4 | Pending |
| REC-05 | Phase 4 | Pending |
| REC-06 | Phase 5 | Pending |
| AUT-01 | Phase 5 | Pending |
| AUT-02 | Phase 5 | Pending |
| AUT-03 | Phase 5 | Pending |
| AUT-04 | Phase 5 | Pending |
| AUT-05 | Phase 5 | Pending |
| AUT-06 | Phase 5 | Pending |
| AUT-07 | Phase 5 | Pending |
| AUT-08 | Phase 5 | Pending |
| AUT-09 | Phase 5 | Pending |
| AUT-10 | Phase 5 | Pending |
| AUT-11 | Phase 8 | Pending |
| VER-01 | Phase 5 | Pending |
| VER-02 | Phase 5 | Pending |
| VER-03 | Phase 5 | Pending |
| VER-04 | Phase 5 | Pending |
| VER-05 | Phase 5 | Pending |
| VER-06 | Phase 5 | Pending |
| VER-07 | Phase 5 | Pending |
| VER-08 | Phase 5 | Pending |
| VER-09 | Phase 5 | Pending |
| VER-10 | Phase 5 | Pending |
| VER-11 | Phase 5 | Pending |
| VER-12 | Phase 5 | Pending |
| VER-13 | Phase 5 | Pending |
| VER-14 | Phase 5 | Pending |
| VER-15 | Phase 5 | Pending |
| COV-01 | Phase 5 | Pending |
| COV-02 | Phase 5 | Pending |
| COV-03 | Phase 5 | Pending |
| BLD-01 | Phase 1 | Pending |
| BLD-02 | Phase 1 | Complete |
| BLD-03 | Phase 1 | Complete |
| BLD-04 | Phase 5 | Pending |
| BLD-05 | Phase 5 | Pending |
| BLD-06 | Phase 5 | Pending |
| BLD-07 | Phase 5 | Pending |
| BLD-08 | Phase 1 | Complete |
| INC-01 | Phase 6 | Pending |
| INC-02 | Phase 6 | Pending |
| INC-03 | Phase 6 | Pending |
| INC-04 | Phase 6 | Pending |
| INC-05 | Phase 6 | Pending |
| INC-06 | Phase 6 | Pending |
| INC-07 | Phase 6 | Pending |
| INC-08 | Phase 6 | Pending |
| INC-09 | Phase 6 | Pending |
| INC-10 | Phase 6 | Pending |
| INC-11 | Phase 6 | Pending |
| OCR-01 | Phase 7 | Pending |
| OCR-02 | Phase 7 | Pending |
| OCR-03 | Phase 7 | Pending |
| OCR-04 | Phase 7 | Pending |
| OCR-05 | Phase 7 | Pending |
| MED-01 | Phase 8 | Pending |
| MED-02 | Phase 8 | Pending |
| MED-03 | Phase 8 | Pending |
| MED-04 | Phase 8 | Pending |
| MED-05 | Phase 8 | Pending |
| MED-06 | Phase 8 | Pending |
| MED-07 | Phase 8 | Pending |
| MED-08 | Phase 8 | Pending |
| WEB-01 | Phase 9 | Pending |
| WEB-02 | Phase 9 | Pending |
| WEB-03 | Phase 9 | Pending |
| PKG-01 | Phase 1 | Pending |
| PKG-02 | Phase 9 | Pending |
| PKG-03 | Phase 1 | Pending |
| PKG-04 | Phase 9 | Pending |
| PKG-05 | Phase 1 | Complete |
| PKG-06 | Phase 1 | Complete |
| PKG-07 | Phase 1 | Complete |
| PKG-08 | Phase 1 | Complete |
| PKG-09 | Phase 1 | Complete |
| PKG-10 | Phase 10 | Pending |
| PKG-11 | Phase 1 | Pending |
| DOC-01 | Phase 10 | Pending |
| DOC-02 | Phase 6 | Pending |
| DOC-03 | Phase 10 | Pending |
| DOC-04 | Phase 1 | Pending |
| DOC-05 | Phase 1 | Pending |
| DOC-06 | Phase 5 | Pending |
| DOC-07 | Phase 10 | Pending |
| TST-01 | Phase 1 | Complete |
| TST-02 | Phase 2 | Pending |
| TST-03 | Phase 5 | Pending |
| TST-04 | Phase 10 | Pending |
| TST-05 | Phase 5 | Pending |
| TST-06 | Phase 10 | Pending |
| TST-07 | Phase 1 | Pending |
| TST-08 | Phase 10 | Pending |

**Coverage:**
- v1 requirements: 154 total
- Mapped to phases: 154
- Unmapped: 0
- Per phase: Phase 1: 27, Phase 2: 24, Phase 3: 11, Phase 4: 14, Phase 5: 39, Phase 6: 12, Phase 7: 5, Phase 8: 10, Phase 9: 5, Phase 10: 7

---
*Requirements defined: 2026-10-17*
*Last updated: 2026-10-18 after Phase 1 plan 01-02: PKG-08 amended for tzdata on Windows (D-20, design §20 A28). Earlier: 2026-10-17 roadmap creation (traceability filled); PKG-11 added (design §20 A15)*
