# Feature Research

**Domain:** Evidence-pack building for HSE incident investigation. Raw case material goes in; a de-identified, citation-exact `EVIDENCE_PACK_V2` workbook comes out for ProbeMatrix.
**Researched:** 2026-10-17
**Confidence:** MEDIUM overall
- Mapping each feature to the design: HIGH. It was read directly from the approved design, §1–§19.
- Comparable-tool practice: MEDIUM. Web sources were cross-checked where possible, and some vendor material is LOW.

**Ground rule:** the design wins. Features the design already covers are classified below with their design section. Anything outside the design appears only under "Candidates not in design (owner decision)". Those are options for the owner, not scope.

**Comparison domains surveyed:**
1. **E-discovery processing:** the EDRM processing guidelines, Relativity and Everlaw, and court ESI protocols. Covers de-NIST, hashing and deduplication, near-duplicates, family relationships, email threading, exception reports, Bates numbers and control numbers, and privilege and redaction logs.
2. **Investigation evidence practice:** ICAM's PEEPO checklist, TapRooT's "3 Ps and an R", ABS's people, paper, physical and position, and ISO/IEC 27037 for chain of custody and hash verification.
3. **PII redaction:** Microsoft Presidio. It has analyzer recognizers (regex, deny-list, checksum, NER and context), allow-lists, anonymizer operators, pseudonymisation, an image and DICOM redactor, and an evaluation guide.
4. **Citation-grounded LLM extraction:** Google LangExtract (span grounding with exact, lesser, fuzzy or not-found alignment), the Anthropic Citations API (`cited_text` with a character, page or content-block location), and quote-first generation (FRONT, 2024).

---

## Feature Landscape

### Table Stakes (Users Expect These)

These are features an investigator, or anyone who has used e-discovery or forensic tooling, assumes exist. If one is missing, the pack is not defensible.

#### A. Intake and processing (e-discovery "processing" equivalent)

| # | Feature | Comparable practice | Why expected | Complexity | Depends on | Design § |
|---|---------|---------------------|--------------|------------|------------|----------|
| TS-01 | Recursive inventory of the case folder with a SHA-256 fingerprint per file | E-discovery processing ingest; ISO/IEC 27037 hash at acquisition | Without a hash there is no integrity claim and no way to detect a change | LOW | (none) | §7.1 |
| TS-02 | Exact-hash deduplication: same content at two paths gives one source; a known hash at a new path is a rename | E-discovery global dedup by hash | The same file dropped twice must not yield duplicate evidence | LOW | TS-01 | §7.1 |
| TS-03 | Version detection: a known path with new content becomes `S004v2` | Rolling collections, re-collected custodian data | Investigators receive revised statements and reports | MEDIUM | TS-01, TS-02 | §7.1, §12.2 |
| TS-04 | Container expansion with parent/child linkage: archive members and email attachments registered as child sources | E-discovery family relationships (ParentID, BegAttach/EndAttach) | An attachment cut off from its email loses its context and custody | MEDIUM | TS-01 | §7.1, §8.1 (`parent`) |
| TS-05 | System-junk filtering (`.DS_Store`, `Thumbs.db`, `~$*` lock files), listed as ignored | De-NIST, a reduced form suited to case folders rather than whole drive images | Noise must not become "unprocessed" alarms | LOW | TS-01 | §7.1 |
| TS-06 | Exception reporting: every unreadable or unsupported input is listed with a reason and never silently dropped | EDRM exception reporting | Silent loss is a design anti-goal and a defensibility failure | LOW | TS-01, TS-08 | §2 anti-goals, §6.1 "Open issues", §7.2 |
| TS-07 | Text and metadata extraction per modality: PDF, DOCX, PPTX, XLSX/CSV, email headers, HTML, TXT and chat, plus EXIF capture time | E-discovery text and metadata extraction | Nothing downstream works without it | HIGH (breadth) | TS-01 | §7.2 |
| TS-08 | Tool detection, reporting and graceful degradation (`doctor`); a missing tool marks inputs `unprocessed: <tool> missing` | Processing engines report unsupported file types | Local-only tooling varies by machine and host | MEDIUM | (none) | §7.2, §15.2 |
| TS-09 | OCR of scanned pages, with a per-page text-or-scan decision | Every processing platform OCRs image-only documents | Official reports and permits are often scans | HIGH | TS-07, TS-08 | §7.2, §17 step 7 |
| TS-10 | Bounded, chunked processing of very large documents, resumable after interruption | Batch processing in review platforms | Reports run to hundreds of pages; no step may need the whole report in context | HIGH | TS-12 | §2 goal 2, §7.4 (`plan-extract`, `extract-status`) |

#### B. Provenance and citation (Bates-number and attribution equivalent)

| # | Feature | Comparable practice | Why expected | Complexity | Depends on | Design § |
|---|---------|---------------------|--------------|------------|------------|----------|
| TS-11 | Stable, never-reused identifiers. Gaps are left when draft items are removed | Bates and control numbers: unique, sequential, with skips declared | Downstream references must never point at the wrong item | LOW | (none) | §8.3, §12.1 step 5 |
| TS-12 | Page-anchored or time-anchored segments as the unit of citation, storing both the printed page label and the physical page index | Bates page identifiers; Citations API `page_location` and `char_location` | Every quote must be checkable at a precise location | MEDIUM | TS-07 | §7.3 |
| TS-13 | Machine-verified verbatim quotes. Normalisation covers whitespace, hyphenation, quote and dash variants, and ligatures only | LangExtract alignment and the Citations API `cited_text`. Both are weaker: LangExtract accepts fuzzy matches | Invented quotes are the top anti-goal (DEF-01, DEF-02) | HIGH | TS-12 | §8.2, §14 hard gate 1 |
| TS-14 | Generated, not typed, citation strings (`Source` column). Pages come from the anchor segments | Production load files generated from the processing database | Fixes off-by-one page errors (DEF-03) | LOW | TS-12, TS-13 | §8.4, §14 hard gate 2 |
| TS-15 | Section-level location (`Storage Location`) built from a heading tree | Document structure fields in review platforms | A reviewer needs the section as well as the page | MEDIUM | TS-12 | §7.3 (section map), §8.4 |
| TS-16 | Boilerplate detection (running headers, footers, letterheads) excluded from extraction but kept in raw text | Header and footer suppression in processing | Stops repeated noise from becoming claims, while quotes still verify against the raw text | MEDIUM | TS-12 | §7.3 |

#### C. De-identification (Presidio-class)

| # | Feature | Comparable practice | Why expected | Complexity | Depends on | Design § |
|---|---------|---------------------|--------------|------------|------------|----------|
| TS-17 | Layered person detection: a pattern pass (honorifics, "Name:" fields, emails, phones, ID patterns), an agent pass, an optional NER pass and a roster pass | Presidio's analyzer: regex, deny-list, NER and context recognizers | Presidio itself warns that no single detector finds all PII | HIGH | TS-12 | §13.1 |
| TS-18 | Consistent pseudonym per person across the whole case, stable for the life of the case | Presidio pseudonymisation and instance-counter operators | Cross-item analysis needs the same person to carry the same label | MEDIUM | TS-17 | §13.2, §7.6 |
| TS-19 | Allow-list for tokens that are also common words, places or equipment names, with a justification for each entry | Presidio `allow_list` | Prevents over-redaction that corrupts equipment and location facts | LOW | TS-17 | §13.5 |
| TS-20 | Zero-hit residual-name scan as a hard gate over every shareable artefact | Second-pass QC in e-discovery redaction | "One leaked name equals product failure" (Core Value) | MEDIUM | TS-17, TS-18 | §13.5, §14 hard gate 8 |
| TS-21 | Private name map kept outside every shareable path, git-ignored, and refused by the sample publisher | Presidio's reversible encrypt and decrypt keeps the key separate | Re-identification material must never travel with the pack | LOW | TS-18 | §6, §13.5 |
| TS-22 | GPS EXIF stripping and file-name de-identification in shareable output | Metadata scrubbing before production | Location and file names leak identity | LOW | TS-07 | §6.1, §13.4 |

#### D. Evidence register and chain of custody (ICAM / TapRooT / ISO 27037)

| # | Feature | Comparable practice | Why expected | Complexity | Depends on | Design § |
|---|---------|---------------------|--------------|------------|------------|----------|
| TS-23 | Per-item register fields: type, source, collector, collection method, collection date, storage location and hash | ICAM evidence log; the TapRooT and ABS evidence categories | This is what an evidence register is | MEDIUM | TS-14, TS-15 | §8.3, §8.4, §9.1 |
| TS-24 | Chain-of-custody record per item: ingest entry per contributing input, plus custody supplied by the user in sidecars | ISO/IEC 27037 preservation; e-discovery custody logs | Investigators and regulators ask "where did this come from and who handled it?" | MEDIUM | TS-01, TS-30 | §8.4 (Chain of Custody JSON), §7.2 (sidecars) |
| TS-25 | Dates at their stored precision, never padded | Forensic metadata fidelity | Fabricated precision is an anti-goal (DEF-08) | LOW | TS-23 | §8.4, §14 hard gate 11 |
| TS-26 | Perspective recorded on every claim (`asserted_by`) and shown in the Description lead-in | ICAM and TapRooT distinguish people evidence from paper, physical and recording evidence | An analyst must weigh a witness account differently from a system log (DEF-10) | MEDIUM | TS-13 | §10.1, §9.4 |
| TS-27 | Honest integrity flag: `Integrity Verified = No`, because the tool verifies quotes, not physical integrity | Forensic practice of not over-claiming | Over-claiming integrity is a defensibility risk | LOW | (none) | §8.4 |

#### E. Output and import

| # | Feature | Comparable practice | Why expected | Complexity | Depends on | Design § |
|---|---------|---------------------|--------------|------------|------------|----------|
| TS-28 | Importer-exact `EVIDENCE_PACK_V2` writer, with a validator stricter than the importer: exact enums, text cells, no blank Description, valid custody JSON, and the 10-row metadata layout | Load-file specifications in ESI protocols | One blank Description fails the whole file; lax enums import silently wrong | MEDIUM | (none) | §8.4 (incl. importer re-check), §8.5, §14 hard gate 3 |
| TS-29 | Comma-free list elements in fields the importer splits on commas | Load-file delimiter discipline | Fixes comma corruption on import (DEF-14) | LOW | TS-28, TS-18 | §8.4, §14 hard gate 4 |

#### F. Workflow, state and audit

| # | Feature | Comparable practice | Why expected | Complexity | Depends on | Design § |
|---|---------|---------------------|--------------|------------|------------|----------|
| TS-30 | Sidecar notes (`<file>.note.md` or `.note.yaml`) for context a file cannot carry. Sidecars are hashed and cited | Collection forms and custodian interviews | Recordings and photos rarely say who made them or when | LOW | TS-01 | §7.2 |
| TS-31 | Incremental runs that process only new or changed inputs | Rolling productions; incremental processing | Evidence arrives over weeks | HIGH | TS-01–TS-03 | §7, §12.1 |
| TS-32 | Freeze on production: a workbook is locked once it is marked imported | Bates ranges frozen once produced | The importer appends and never deduplicates, so re-import duplicates every item | MEDIUM | TS-31, TS-11 | §4, §12.1 step 5a |
| TS-33 | Human-readable status view: inputs, outputs, what to import where, open issues and run history | Processing summary and exception reports | The owner needs one place to see state | MEDIUM | TS-06, TS-31 | §6.1 |
| TS-34 | Per-run log and gate report | Processing audit logs | An audit trail of what the tool did | LOW | TS-31 | §6 (`runs/<NNN>/`) |
| TS-35 | Crash safety: a lock file, atomic temp-file-then-rename writes, and state written last | Processing job checkpoints | Interrupted runs must not corrupt state | MEDIUM | TS-31 | §12.5 |

### Differentiators (Competitive Advantage)

No comparable tool offers these together. They line up with the Core Value ("traceable and trustworthy"), and each one targets a defect the prototype study documented (DEF-xx, design §3).

| # | Feature | Value proposition | Complexity | Depends on | Design § |
|---|---------|-------------------|------------|------------|----------|
| DF-01 | **Conclusions, lessons and recommendations are never evidence.** Four enforcement layers: section screening, an entry gate at `claims add`, an item gate and a build gate. Held-back claims go to a private ledger. There is no opt-out. | No e-discovery, redaction or extraction tool separates a source's verdicts from its facts. This stops the official answer leaking into evidence (DEF-13). It is the single biggest differentiator. | HIGH | TS-12, TS-13, DF-02 | §11.3, §14 hard gate 7 |
| DF-02 | **Coverage matrix with reasoned omissions and a coverage gate.** Every claim ends as in an item, merged, or omitted with a fixed reason, and anything unaccounted for in observation sections blocks the build. | A withholding log, as in a privilege log, applied to facts rather than documents. It makes curation auditable and catches dropped findings (DEF-12). | HIGH | Claim ledger (§7.4), TS-12 | §11.1, §11.2, §14 hard gate 9 |
| DF-03 | **Conflict detection that never picks a winner.** Time, value, actor and action, sequence and outcome conflicts are detected. Disputed items carry both versions with citations. | Review platforms leave contradictions to humans. Here they are surfaced and kept rather than smoothed over (DEF-04). | HIGH | TS-26, DF-07, event alignment (§7.6) | §10.2, §10.3 |
| DF-04 | **Classify the underlying artefact, not the carrier.** Deterministic type decision rules with tie-breakers and a stored `type_rationale`. | Generic tools type by file format. This types by what the evidence is, which is what HFACS analysis needs (DEF-09). | MEDIUM | Claim `underlying_artefact` (§7.4) | §9.1 |
| DF-05 | **De-identification that stays verifiable.** Bracketed role labels inside quotes verify against the raw source through the private map. The honorific is removed with the name. | Presidio-style masking breaks verbatim verification. This keeps both guarantees (DEF-15). | MEDIUM | TS-13, TS-18, TS-21 | §13.3, §18 |
| DF-06 | **Rich quote conventions:** ellipsis fragments verified in order, cross-page spans citing both pages, `[sic]` (typos are never corrected), typographic quote marks so inch marks never collide with quote delimiters | Beyond the Citations API and LangExtract, which return one contiguous span or a fuzzy alignment. Fixes DEF-02. | MEDIUM | TS-13, TS-12 | §8.2 |
| DF-07 | **Equipment roster** with aliases and source-inconsistency notes. Mismatched IDs are never silently normalised inside a quote. | Entity resolution for equipment as well as people (DEF-18) | MEDIUM | TS-17 pattern infrastructure | §7.6, §13.4 |
| DF-08 | **Description standard plus lints.** A three-part structure; lints for evaluative and speculative phrases, the HFACS blocked list, IDs or row numbers in prose, and length (target 300–900, hard limit 1,800). | Makes each item usable on its own by the analyser, which sees only text. Fixes DEF-05, DEF-06, DEF-07 and DEF-16. | MEDIUM | DF-01, TS-13 | §9.4, §9.2, §14 hard gates 5, 6 and 10 |
| DF-09 | **Correction items** for locked items. A new item supersedes the wrong one, and INDEX tells the owner what to clean up by hand. | Comparable to a corrected production with an overlay, but honest about an append-only importer | MEDIUM | TS-32, TS-03 | §12.4 |
| DF-10 | **Confidence propagation.** Low-confidence OCR or transcript segments flow into the item status and a Description marker. | Review platforms show OCR quality but rarely carry it into the produced record | MEDIUM | TS-09, media intake | §7.2, §14 soft warnings |
| DF-11 | **Visual observation claims.** Only what is visible is described; faces are never described and people are never identified. Items are flagged `visual_unverified` for review. | Lets photos and CCTV become text evidence without inventing anything | MEDIUM | Media intake (§7.2) | §7.5 |
| DF-12 | **Media to anchored text:** audio and video transcription with timestamps, scene-change keyframes and CCTV overlay OCR, all local | E-discovery platforms treat media as near-native files. Here media becomes citable evidence. | HIGH | TS-08, TS-12 | §7.2, §7.3, §17 step 8 |
| DF-13 | **Non-English verbatim quotes** in the original script, plus an English rendering marked `[translation]`. Only the original is verified. | Multilingual sites (for example Hindi and Gujarati) without losing verifiability | MEDIUM | TS-13, TS-09 language packs | §13.3a |
| DF-14 | **Web snapshot, inputs-only and confirmed by the user.** Dated snapshots in `inputs/web/`; no claim from a page the agent did not save. | Makes press and regulator material traceable (DEF-11) | MEDIUM | TS-01, TS-07 | §7.9 |
| DF-15 | **Seeded, reproducible spot-check report.** Five items shown with raw context around each anchor, de-identified. | A human audit in minutes, like QC sampling in review | LOW | TS-13, TS-20 | §14 |
| DF-16 | **Evals on a synthetic incident with planted traps:** verbatim rate, page accuracy, names leaked, conclusions leaked, and an incremental scenario | Measurable trust. Comparable to Presidio's evaluation guide, but scored on the product's own failure modes. | HIGH | Most features | §16 |
| DF-17 | **Same behaviour on three hosts** (Claude Code, Cowork, Codex), with all deterministic work in one CLI using `--json` | Portability that host-specific APIs such as the Citations API cannot give | MEDIUM | TS-08 | §2 goal 9, §15 |
| DF-18 | **Local-only conversion** | Evidence never leaves the machine. Cloud e-discovery and document-AI services cannot claim this. | MEDIUM (tool breadth) | TS-08 | §2 goal 10, §4 |
| DF-19 | **Held-back conclusions ledger**, kept privately for a later fair comparison with the official findings | Supports the downstream "compare ProbeMatrix with the official report" workflow without contaminating evidence | LOW | DF-01 | §11.3 |
| DF-20 | **Optional consolidated workbook** for a fresh incident, produced only on request | Clean re-baseline without breaking the master-plus-deltas contract | LOW | TS-31, TS-28 | §12.3 |

### Anti-Features (Deliberately NOT Built)

The design's non-goals and anti-goals (§2), plus patterns from comparable tools that the design explicitly rejects.

#### From design §2 (non-goals)

| Anti-feature | Why requested | Why problematic | Alternative | Design § |
|--------------|---------------|-----------------|-------------|----------|
| HFACS classification, root-cause analysis or recommendations | "Do the whole investigation" | That is ProbeMatrix's paid job. Pre-classification biases the analyser (DEF-06). | Blocked-term lint and an operational tag vocabulary | §2, §9.2, §14 hard gate 6 |
| Automatic import or an API client for ProbeMatrix | Convenience | Adds coupling. The user stays in control of what is imported. | The user uploads; INDEX says what to import where | §2 |
| Other output formats (DOCX reports, JSON for other tools) | Reuse elsewhere | Scope creep; `outputs/` must hold only packs | A `formats/` seam kept for a future V3 | §2, §8.5 |
| A GUI | Approachability | Duplicates the agent and the CLI; three hosts to support | Agent + CLI + `INDEX.md` | §2 |
| Cloud OCR, transcription or document-AI | Better accuracy | Evidence would leave the machine | Local tools reported by `doctor` | §2, §4 |
| Speaker diarisation on by default | Who-spoke-when | The model needs a licence acceptance | Optional `pyannote`; speakers attributed from self-identification or a sidecar | §7.2 |
| A fixed item-count target ("40–80 items") | Predictability | Pushes towards either cataloguing or skimming | Coverage gate plus density warnings | §11.2 |

#### From design §2 (anti-goals: never acceptable, whatever the reason)

| Anti-feature | Why problematic | Prevention | Design § |
|--------------|-----------------|------------|----------|
| Any quote not verbatim in a saved input | Destroys trust in the whole pack (DEF-01, DEF-02) | Verify on write and again at build | §8.2, §14 hard gate 1 |
| Any personal name in shareable output | Privacy failure | Zero-hit scan gate | §13.5 |
| The official answer leaking into evidence | Contaminates the independent analysis (DEF-13) | Four-layer enforcement | §11.3 |
| HFACS pre-classification in Descriptions or Tags | Biases the analyser (DEF-06) | Blocked-term lint | §9.2, §14 |
| Duplicates in ProbeMatrix from re-import | The importer appends and never deduplicates | Locking, deltas and correction items | §12 |
| Silent loss of inputs, findings or contradictions | Indefensible gaps (DEF-12) | Exception listing, coverage gate, conflict register | §6.1, §10, §11 |
| Fabricated date precision | False facts (DEF-08) | Stored precision | §8.4 |

#### Comparable-tool patterns the design explicitly rejects

| Anti-feature | Where it is common | Why problematic here | Design's alternative | Design § |
|--------------|-------------------|----------------------|----------------------|----------|
| Accepting fuzzy or approximate quote alignment | LangExtract `fuzzy` and `lesser` statuses; LLM "near-match" verifiers | A fuzzy match is a paraphrase inside quotation marks (DEF-02) | Fixed normalisation set only; anything else is rejected | §8.2 |
| Silently correcting source typos inside quotes | LLM extraction "cleanup" | Changes the evidence | `[sic]` | §8.2 |
| Generic placeholder masking (`<PERSON>`, `[REDACTED]`, ad-hoc initials) | Presidio's default replace operator; manual redaction | Loses who-is-who across items; the prototype left inconsistent placeholders (DEF-15) | Stable comma-free role labels | §13.2, §13.3 |
| De-identifying at conversion time | Redaction pipelines that scrub on ingest | Makes verbatim verification against the original impossible | Raw text kept in confidential working files; de-identified at render | §6, §18 |
| An opt-out switch for de-identification or for the conclusions rule | "Power user" settings | One misconfiguration would ship names or verdicts | Always on, no setting | §4, §11.3 |
| The agent deciding which conflicting version is true | LLM summarisation tends to reconcile | Smooths over disputes (DEF-04) | Both versions shown; dismissal only for false positives | §10.2 |
| Meta-items describing the source document itself | Evidence logs that list "the report" as an item | Not evidence (DEF-17) | Source details go in metadata and INDEX | §8.4 |
| IDs or row numbers in prose cross-references | Hand-written cross-references | IDs are regenerated on import (DEF-07) | `Related Evidence` holds Evidence Tags | §8.4, §14 hard gate 5 |
| Rewriting a workbook that is already imported | "Regenerate everything" pipelines | Duplicates on import; references break | Correction items in the next delta | §12.1, §12.4 |
| Paraphrasing web sources from memory or from failed fetches | LLM web answers | Unverifiable (DEF-11) | Saved snapshot or nothing | §7.9 |
| Describing faces or guessing intent from images | Vision-model captioning | Identifies people; speculation | Visible-only observations | §7.5, §13.4 |
| Copying prototype code or prose | Speed | Brings back invented example prose (DEF-01) | Clean-room build; synthetic fixtures only | §4, §16 |

---

## Feature Dependencies

```
TS-01 Fingerprint
  ├─> TS-02 Dedup/rename ─> TS-03 Versions ─> DF-09 Corrections
  ├─> TS-04 Families (archives, email attachments)
  ├─> TS-06 Exception listing ─> TS-33 INDEX.md
  └─> TS-07 Conversion ─(TS-08 doctor gates it)─> TS-09 OCR / DF-12 Media
          └─> TS-12 Anchored segments + section map
                 ├─> TS-13 Quote verifier ─────────────────────┐
                 │      ├─> DF-06 Ellipsis / cross-page / [sic]  │
                 │      ├─> DF-05 Bracketed role labels verify ──┤ (needs TS-18, TS-21)
                 │      └─> TS-14 Generated citations            │
                 └─> TS-10 Chunk plan ─> Claim ledger (§7.4)     │
                         ├─> DF-01 Conclusions entry gate ───────┤
                         ├─> TS-26 asserted_by ─> DF-03 Conflicts│
                         ├─> DF-07 Equipment roster ─> DF-03     │
                         └─> TS-17 De-id detection ─> TS-18 Role │labels ─> TS-20 Zero-hit scan
                                                                 v
                                        Items (§8.3): DF-04 typing, DF-08 Description + lints
                                                                 v
                                        DF-02 Coverage gate + all hard gates (§14)
                                                                 v
                                        TS-28 Importer-exact writer (+TS-29 comma gate)
                                                                 v
                                        TS-31 Incremental ─> TS-32 Lock on import ─> DF-09 Corrections
```

### Dependency Notes

- **TS-28 (writer and validator) has no upstream dependency.** It can be built and tested first against the format spec. The design's build order puts it in step 1 (§17).
- **TS-13 (quote verifier) requires TS-12 (segments with `norm_text` and a character map).** Cross-page quotes need adjacent segments that share a normalised stream. DF-05 also requires the private name map (TS-21), so the verifier cannot be finished until reconcile exists. Plan an interface seam: the verifier in phase 2, with bracket-label support added in phase 4.
- **DF-01 must exist before any evidence claim is persisted.** The entry gate is at `claims add` (§11.3 layer 2). Building extraction first and the gate later would let held-back material into the ledger. Ship the claim-kind schema and the held-back ledger in the same phase as `claims add` (§17 step 3).
- **DF-02 (coverage) depends on section tagging from segmentation** (observation and finding sections) and on the held-back section screening. Both originate in TS-12.
- **DF-03 (conflicts) depends on TS-26, DF-07 and event alignment.** Without rosters, actor and value conflicts cannot be keyed.
- **TS-20 (zero-hit scan) depends on the roster pass (TS-17 layer 4).** The scan list is generated from the name map. Detection recall bounds scan recall: Presidio's own documentation warns that no detector finds everything. That is why the design layers four passes.
- **TS-31 and TS-32 depend on stable IDs (TS-11) and fingerprints (TS-01).** DF-09 depends on TS-32, because corrections apply only to locked items.
- **DF-10 and DF-12 depend on TS-08.** On Cowork the capability profile is unverified (§18), so text intake is the guaranteed baseline.
- **Conflict to watch:** DF-05 (bracketed labels) against TS-13 (strict verbatim). They are reconciled only through the private map. Any change to label rendering must be re-tested against the verifier.

---

## MVP Definition

This follows the design's build order (§17). The design defines v0.1.0 as all ten steps (kickoff §11), so "MVP" here means the end-to-end milestone inside v0.1.0, not a reduced release.

### Launch With (end-to-end milestone, §17 steps 1–5)

- [ ] TS-28, TS-29: importer-exact writer and validator. Without them nothing can be imported.
- [ ] TS-01–TS-08, TS-10, TS-12, TS-15, TS-16: text-document intake with anchored segments
- [ ] TS-13, TS-14, DF-06: quote verifier. Core Value #1.
- [ ] DF-01: conclusions entry gate at `claims add`. Core Value #3.
- [ ] TS-17–TS-22, DF-05: rosters, de-identification and the zero-hit scan. Core Value #2.
- [ ] DF-03, DF-07, TS-26: conflicts and perspective
- [ ] DF-04, DF-08, TS-23–TS-25, TS-27: items, typing and Descriptions
- [ ] DF-02, DF-15, all 12 hard gates: coverage and verification
- [ ] TS-33, TS-34: INDEX and run report

### Add next inside v0.1.0 (§17 steps 6–10)

- [ ] TS-31, TS-32, TS-35, DF-09: incremental runs and corrections. This milestone is the incremental eval.
- [ ] TS-09, DF-10, DF-13: OCR, confidence propagation and multi-language support
- [ ] DF-11, DF-12, TS-30: media and sidecars
- [ ] DF-14: web snapshot (optional skill)
- [ ] DF-16, DF-17, DF-20: evals, hosts, consolidated build, CI and release

### Future consideration

- [ ] Anything under "Candidates not in design" below, if the owner accepts it.

---

## Feature Prioritization Matrix

| Feature group | User value | Implementation cost | Priority |
|---------------|------------|---------------------|----------|
| Quote verifier (TS-13, DF-06, DF-05) | HIGH | HIGH | P1 |
| Conclusions rule (DF-01) | HIGH | HIGH | P1 |
| De-identification and zero-hit scan (TS-17–TS-22) | HIGH | HIGH | P1 |
| Importer-exact writer (TS-28, TS-29) | HIGH | MEDIUM | P1 |
| Text intake and segments (TS-01–TS-08, TS-12) | HIGH | HIGH | P1 |
| Coverage gate (DF-02) | HIGH | MEDIUM | P1 |
| Conflicts and perspective (DF-03, TS-26) | HIGH | HIGH | P1 |
| Item typing and Description lints (DF-04, DF-08) | HIGH | MEDIUM | P1 |
| Incremental runs, locks and corrections (TS-31, TS-32, DF-09) | HIGH | HIGH | P1 (v0.1.0 milestone) |
| OCR and confidence (TS-09, DF-10) | HIGH | MEDIUM | P1 (v0.1.0) |
| Media (DF-11, DF-12) | MEDIUM | HIGH | P1 (v0.1.0), degrades gracefully |
| Multi-language (DF-13) | MEDIUM | MEDIUM | P1 (v0.1.0) |
| Web snapshot (DF-14) | MEDIUM | MEDIUM | P2 (optional skill) |
| Consolidated build (DF-20) | LOW | LOW | P2 |
| Spot-check report (DF-15) | MEDIUM | LOW | P1 |

---

## Competitor Feature Analysis

| Capability | E-discovery (Relativity, Everlaw, EDRM) | Presidio | ICAM / TapRooT practice | LLM grounding (LangExtract, Citations API) | Our approach (design) |
|---|---|---|---|---|---|
| Ingest and hashing | Hash on ingest; de-NIST; global dedup | n/a | Manual evidence log | n/a | SHA-256, dedup, renames, versions (§7.1) |
| Families | ParentID and attachment ranges; families kept together | n/a | n/a | n/a | `parent` on child sources (§7.1, §8.1) |
| Near-duplicates and threading | Near-dedup; email threading | n/a | n/a | n/a | **Not in design** (see candidates) |
| Exceptions | Exception report | n/a | n/a | n/a | `unprocessed: <reason>` in INDEX (§6.1) |
| Location identifier | Bates number per page | n/a | Evidence reference number | Char, page or block location | Segment ID, printed page label, generated `Source` (§7.3, §8.4) |
| Quote fidelity | Native document review | n/a | Investigator transcription | Single span or fuzzy alignment | Strict verbatim, ellipsis, cross-page, `[sic]` (§8.2) |
| PII handling | Manual and assisted redaction, redaction reports | Analyzer + anonymizer; allow and deny lists; "no guarantee" caveat | Names usually kept internally | n/a | Four-layer detection, role labels, zero-hit gate (§13) |
| Withholding log | Privilege and redaction logs | n/a | n/a | n/a | Coverage omission reasons for claims (§11.1); conclusions ledger (§11.3) |
| Custody | Audit logs, custodian fields | n/a | Chain-of-custody forms | n/a | Custody JSON per item plus sidecars (§8.4) |
| Fact versus verdict | None | None | Done by the investigator | None | Four-layer conclusions rule (§11.3) |
| Contradictions | Reviewer judgement | n/a | Investigator judgement | n/a | Detected, both versions kept (§10) |
| Incremental output | Rolling productions, frozen Bates ranges | n/a | n/a | n/a | Master plus deltas, lock on import, corrections (§12) |

---

## Candidates not in design (owner decision)

These are **not scope**. Each comes from a comparable tool or practice. The researcher's lean is advisory only.

| # | Candidate | Comparable practice | One-line rationale | Complexity | Interacts with | Researcher lean |
|---|-----------|---------------------|--------------------|------------|----------------|-----------------|
| C-01 | **Near-duplicate detection across inputs**, for example the same report as DOCX and PDF, or a scan plus its text copy | E-discovery near-dedup | Exact-hash dedup (§7.1) misses format twins, which would yield duplicate claims and false "conflicts". Today only the `duplicate` omission reason (§11.1) catches them, after extraction. | MEDIUM | §7.1, §10.2, §11.1 | Consider. It saves extraction effort on real case folders. |
| C-02 | **Email threading and quoted-reply suppression** | E-discovery email threading | Reply chains repeat earlier messages verbatim. Without threading, the same text is extracted once per message, and citations may point at a later copy rather than the original. | MEDIUM | §7.1 email, §7.4 | Consider for email-heavy cases. |
| C-03 | **Multiple parents for one child source**: an identical attachment carried by two emails | E-discovery family rules for duplicates within families | §7.1 merges identical content into one source, but §8.1 has a single `parent` field. This is a small model gap that affects the custody JSON. | LOW | §7.1, §8.1, §8.4 custody | Recommend clarifying. It looks like a design ambiguity rather than new scope. |
| C-04 | **Withheld-input register**: the user marks an input "do not use" (for example legally privileged advice) with a reason | Privilege log | Today the only way to exclude an input is to delete it, which leaves a misleading "removed from folder" status. | MEDIUM | §6 inputs read-only, §6.1, §12 | Owner decision. Depends on how privilege is handled in their investigations. |
| C-05 | **De-identification replacement summary** in the run report: counts per role label and per field, no names | Redaction log or report (Relativity Redact Reports) | Gives a reviewer evidence that de-identification ran, not just that the scan found zero names. | LOW | §13.5, §14 run report | Consider. It is cheap. |
| C-06 | **Over-redaction metric** in evals: equipment or place tokens wrongly replaced by role labels | Presidio's PII evaluation guide (precision as well as recall) | §16 scores names leaked (recall) but not false replacements, which corrupt equipment facts. | LOW | §13.5 allow-list, §16 | Consider. The synthetic fixture can plant surname-like place names. |
| C-07 | **Presidio as the optional third-net detector** instead of raw spaCy | Presidio analyzer | Adds context-aware recognizers and checksum IDs for free. Adds a dependency footprint; licence to be verified as permissive. | MEDIUM | §13.1 layer 3, §18 dependencies | Neutral. The design's four passes already cover the pattern classes. |
| C-08 | **Re-hash inputs at build** to confirm they are unchanged since `scan` in the same run | ISO/IEC 27037 verify-after-acquisition | Closes a small time-of-check to time-of-use window, where a file is edited while a long run is in progress. | LOW | §7.1, §12.5, §14 gate 1 | Consider. It is cheap. |
| C-09 | **Cross-input term search** (`epb search <term>`) over segments | Search-term reports and persistent highlighting (Relativity, Everlaw) | Helps the agent and the user confirm an omission or find aliases. §15.2 has `segments show` but no search. | LOW | §15.2, §13 (raw text includes names, so output must be de-identified or kept private) | Consider, with the de-identification caveat. |
| C-10 | **Evidence-category inventory in INDEX**: item counts by artefact facet (people, paper, physical, recording) | TapRooT "3 Ps and an R"; ICAM PEEPO | Shows gaps such as "no recordings yet" at a glance. It must stay a neutral inventory: suggesting what to collect drifts towards performing the investigation, a §2 non-goal. | LOW | §6.1 fixed section list, §9.2 artefact tags | Owner decision; scope risk. |
| C-11 | **Chronology table** in the run report: event claims sorted by `event_time` with precision | Investigation timelines | Useful for checking conflicts. It risks implying causal sequence and is not an `outputs/` format. | MEDIUM | §2 non-goals, §10 | Lean against, or keep it private to `.epb/runs/` only. |
| C-12 | **Using the Anthropic Citations API or LangExtract** for extraction grounding | LLM grounding tools | Host-specific (no equivalent on Codex), and both allow fuzzy or contiguous-only spans. The design's deterministic verifier is stricter and host-neutral. | MEDIUM | §2 goal 9, §8.2 | Decline. Quote-first prompting (extract the span, then write the claim) can still guide the extraction instructions without a dependency. |
| C-13 | **Image and video redaction** (face blur, burned-in name removal) | Presidio image and DICOM redactor; video redaction tools | The outputs carry no attachments (`Total Attachments = 0`, §8.4 point 13), so no image is ever shared. | HIGH | §8.4 | Decline. Not needed under the current output contract. |
| C-14 | **Bates-style stamping of input pages** | E-discovery production | Inputs are read-only (§6). Printed and physical page labels already serve as stable locators. | MEDIUM | §6, §7.3 | Decline. It conflicts with the workspace contract. |
| C-15 | **Full hash manifest file** (for example `hashes.sha256`) for third-party integrity checking | Forensic acquisition reports | Full hashes are already in the Hash/Checksum column and short hashes in INDEX. A manifest cannot go in `outputs/`, which holds `.xlsx` only. | LOW | §6 outputs rule | Lean against, or put it in `.epb/runs/` only. |
| C-16 | **Per-user access audit log** | E-discovery and DEMS access logs | Single-user local tool. The run logs cover what the tool did. | MEDIUM | §6 | Decline for v0.1.0. |

---

## Sources

- Approved design: `docs/design/2026-10-17-evidence-pack-builder-design.md` §1–§19, read in full. HIGH.
- `.planning/PROJECT.md`. HIGH.
- EDRM Guidelines for E-Discovery Processing: https://edrm.net/wp-content/uploads/dlm_uploads/2022/02/EDRM-Guidelines-for-E-Discovery-Processing-v3CC4.pdf. MEDIUM. The steps were confirmed from its table of contents; exception-report contents were not fetched.
- De-NIST versus dedup: https://www.everlaw.com/blog/ediscovery-best-practices/what-is-denisting-in-ediscovery and https://judicature.duke.edu/wp-content/uploads/sites/3/2022/08/EDRM_Fall2018.pdf. MEDIUM.
- Near-dedup and threading: https://nextpoint.com/?p=4723. LOW (vendor).
- Families, Bates and control numbers (court ESI protocols): https://www.njcourts.gov/sites/default/files/mcl/orders-decisions/pelvic-mesh-gynecare/general/orderesiprotocol.pdf, https://www.justice.gov/atr/public/electronic_discovery/243194d.htm and https://www.wvsd.uscourts.gov/sites/wvsd/files/mdl-orders/2325-PTO_15.pdf. MEDIUM.
- Privilege and redaction logs: https://edrm.net/wp-content/uploads/2023/09/EDRM-PrivilegeLogProtocol-final.pdf and https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-november/crafting-effective-privilege-logs-legal-success. MEDIUM.
- Relativity Redact Reports: https://help.relativity.com/RelativityOne/Content/Relativity/Relativity_Redact/Redact_Reports.htm. MEDIUM.
- Presidio (docs moved): https://presidio.dataprivacystack.org/. Fetched directly; source of the "no guarantee that Presidio will find all sensitive information" caveat. MEDIUM.
- ICAM PEEPO templates: https://policies.une.edu.au/document/view-current.php?id=454 and https://www.adelaide.edu.au/hr/ua/media/327/ICAM-invesigation-report-template.pdf. LOW to MEDIUM (institutional templates; no single authoritative ICAM evidence-log schema was found).
- TapRooT "3 Ps and an R": https://wolterskluwer.com/en/expert-insights/4-types-of-evidence-during-a-root-cause-analysis-investigation. ABS "position" variant: https://www.abs-group.com/content/documents/resources/rca-resources/qp1103basics.pdf. MEDIUM.
- ISO/IEC 27037 (secondary descriptions only; the standard is paywalled): https://www.elliptic.co/corpus/gen-2702/iso-iec-jtc-1-sc-27/iso-iec-27037-digital-evidence.html. LOW.
- LangExtract alignment statuses (community port docs): https://lang-extract.hexdocs.pm/alignment.html. LOW to MEDIUM. Google's Python repo was not fetched.
- Anthropic Citations (cookbook): https://platform.claude.com/cookbook/misc-using-citations. MEDIUM.
- Quote-first grounding (FRONT): https://export.arxiv.org/pdf/2408.04568. MEDIUM.

---
*Feature research for: HSE evidence-pack building (ProbeMatrix Evidence Pack Builder)*
*Researched: 2026-10-17*
