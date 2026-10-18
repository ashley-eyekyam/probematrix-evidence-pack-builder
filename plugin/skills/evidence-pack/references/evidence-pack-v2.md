# The EVIDENCE_PACK_V2 workbook format

This reference describes the workbook format exactly as the ProbeMatrix importer reads it.
The plugin's format module (`scripts/epb/formats/probematrix_v2.py`) holds the same strings,
and its validator (`scripts/epb/formats/validate.py`) checks every workbook before it is
handed over. The validator is stricter than the importer wherever the importer is lax.

Checked against the ProbeMatrix importer on 2026-10-17. The importer sources read for that
check, as references only (no ProbeMatrix code is copied): `server/services/evidenceExportService.ts`,
the import route in `server/routes.ts`, `shared/schema.ts` and the analyser prompt in
`server/services/analysis.ts`. Re-check this file whenever the format module changes.

## The file

- An `.xlsx` workbook with exactly three sheets, in this order: `Pack Metadata`,
  `Evidence Pack`, `Attachments Manifest`.
- The format marker is `EVIDENCE_PACK_V2`, in cell B1 of `Pack Metadata`.
- Every cell is a text cell. Dates, hashes, IDs and anything that looks like a number are
  written as text, or the importer would read a date as a spreadsheet serial number. No cell
  is ever a formula, including text that starts with `=`.
- A cell holds at most 32767 characters. A cell of exactly 32767 characters is treated as
  probably cut short (spreadsheet libraries truncate longer text silently), so the validator
  rejects it.

## Pack Metadata

Exactly ten rows. Column A holds the label, column B the value. The importer reads by
position, so no extra rows are ever added.

| Row | Column A | Column B |
| --- | --- | --- |
| 1 | Evidence Pack Format | `EVIDENCE_PACK_V2` |
| 2 | Incident Number | the case number |
| 3 | Incident Title | the case title |
| 4 | Export Date | the build time, ISO 8601 |
| 5 | Total Evidence Items | the number of item rows in this file, as text |
| 6 | Total Attachments | always `0` |
| 7 | (blank) | (blank) |
| 8 | IMPORTANT: Do not modify the structure of this file. | |
| 9 | Modifying column headers or the metadata sheet may cause import errors. | |
| 10 | Note: Attachments are listed in the Attachments Manifest sheet for reference only. | |

## Evidence Pack

Row 1 holds the 30 headers in this order; each following row is one evidence item. Widths are
in SheetJS character units (wch); a ProbeMatrix export stores each on disk as the width plus
0.83203125, and the plugin does the same so a pack stays comparable with ProbeMatrix's own
exports. "List" marks a column the importer splits on commas.

| # | Header | Width | Notes |
| --- | --- | --- | --- |
| 1 | `Evidence ID` | 12 | Required header. The value is replaced on import. |
| 2 | `Type` | 18 | Required. One of the Type values below. |
| 3 | `Description` | 60 | Required, never blank. |
| 4 | `Priority` | 10 | Required. One of the Priority values below. |
| 5 | `Analysis Status` | 15 | Required. One of the Analysis Status values below. |
| 6 | `Tags` | 25 | List. |
| 7 | `Linked Individuals` | 25 | List of role labels. |
| 8 | `Linked Equipment` | 25 | List of equipment labels. |
| 9 | `Source` | 20 | |
| 10 | `Collection Date` | 15 | `YYYY`, `YYYY-MM` or `YYYY-MM-DD`, or blank. Never padded. |
| 11 | `Collection Method` | 20 | |
| 12 | `Collector` | 15 | |
| 13 | `Storage Location` | 20 | |
| 14 | `Evidence Tag` | 15 | Kept on import; the stable reference between items. |
| 15 | `Hash/Checksum` | 20 | |
| 16 | `Related Evidence` | 25 | List of Evidence Tags; stored as plain text, never resolved. |
| 17 | `Chain of Custody (JSON)` | 40 | A JSON array; see below. |
| 18 | `Integrity Verified` | 15 | `Yes` or `No`. |
| 19 | `Collection Conditions` | 25 | Imported as the collection location. |
| 20 | `Preservation Method` | 20 | Imported as the environmental requirements. |
| 21 | `Access Restrictions` | 25 | Dropped on import. |
| 22 | `Regulatory Requirements` | 25 | List. |
| 23 | `Retention Category` | 15 | One of the Retention Category values below, or blank. |
| 24 | `Retention Until` | 15 | Imported as the disposal date. |
| 25 | `QA Status` | 15 | One of the QA Status values below, or blank. Imported as the lifecycle status. |
| 26 | `QA Reviewed By` | 20 | Dropped on import. |
| 27 | `QA Reviewed At` | 22 | Dropped on import. |
| 28 | `Verification Notes` | 30 | Dropped on import. |
| 29 | `Created At` | 22 | Not read on import; written for people. |
| 30 | `Updated At` | 22 | Not read on import; written for people. |

### List columns

`Tags`, `Linked Individuals`, `Linked Equipment`, `Related Evidence` and
`Regulatory Requirements` are split by the importer at every comma, and each piece is trimmed.
So entries are joined with exactly `, ` (a comma and one space), and an entry never contains a
comma. A semicolon does not separate entries: the importer keeps it inside one entry.

### Allowed values

The validator accepts only these exact, lower-case values (`Yes` and `No` excepted).

- Type: `witness_statement`, `photograph`, `document`, `log_record`, `recording`,
  `physical_item`, `lab_report`, `other`.
- Priority: `critical`, `high`, `medium`, `low`.
- Analysis Status: `analyzed`, `pending`, `requires_followup`.
- QA Status: `collected`, `preserved`, `under_review`, `verified`, `disputed`, `released`,
  `destroyed`, `sealed`.
- Retention Category: `regulatory`, `legal`, `internal`, `permanent`.
- Integrity Verified: `Yes`, `No`.

### Chain of Custody (JSON)

A JSON array of entry objects; `[]` when there is no custody record. Each entry has four
required text keys, `timestamp` (an ISO 8601 date-time), `transferred_from`, `transferred_to`
and `received_by`, and these optional keys:

- `reason`, `location` and `notes`: text;
- `verification_confirmed`: true or false;
- `condition_on_receipt`: one of `intact`, `sealed`, `damaged`, `opened`, `unknown`;
- `action_type`: one of `transfer`, `inspection`, `duplication`, `return`, `sealed`,
  `unsealed`.

No other key is allowed.

## Attachments Manifest

The plugin writes this sheet with its header row only, matching Total Attachments `0`. The
importer ignores it. Headers and widths, in order: `Evidence ID` 12, `Attachment ID` 12,
`File Name` 40, `File Type` 12, `File Size (bytes)` 15, `MIME Type` 25,
`File Hash (SHA-256)` 70, `Uploaded By` 15, `Uploaded At` 22, `Integrity Status` 15,
`Last Verified At` 22.

## What the importer does

- It imports into the incident named in the upload and appends every row. Nothing is checked
  for duplicates, so importing the same file twice duplicates every item. A workbook is never
  imported twice.
- It replaces each Evidence ID with a fresh ID of its own. Only the Evidence Tag survives, so
  items refer to each other by tag, never by Evidence ID or row number.
- An Evidence Tag that collides with an existing tag, or with another row in the file, gets
  `-IMP1`, `-IMP2` and so on added, with a warning.
- It matches headers by name, not position, and reads only cell B1 of the metadata sheet.
- It rejects the whole file when the metadata sheet is missing or empty, the marker is wrong
  (`EVIDENCE_PACK_V1` is accepted with a warning), the Evidence Pack sheet is missing, a
  required header is missing, or any row has a blank Description.
- It skips a row with a blank Type without saying so. The validator rejects such a row.
- It normalises three columns instead of rejecting them: Type is lower-cased with spaces
  turned into `_`, Priority is lower-cased, and Analysis Status is lower-cased with spaces
  turned into `_`. Unknown values silently become `other`, `medium` or `pending` with a
  warning. QA Status and Retention Category are stored exactly as written, with no
  normalisation. The validator therefore demands the exact values in every enum column.
- Malformed Chain of Custody JSON only raises a warning there, and its shape is not checked.
  The validator checks both.
- `Integrity Verified` equal to `Yes` stamps the import time as the verification time.
- The analysis sees each item as its ID with type and priority, the Description cut at 2,000
  characters, Tags, Linked Individuals and Linked Equipment.

## Validator finding codes

Every finding has a code, the sheet, the cell and a plain message. Validation never stops at
the first finding.

| Code | Meaning |
| --- | --- |
| `SHEETS_INVALID` | The file is not a readable workbook, or its sheets are not exactly the three above in order. |
| `FORMAT_MARKER` | Pack Metadata B1 is not exactly `EVIDENCE_PACK_V2`. |
| `METADATA_LAYOUT` | A Pack Metadata label or note is not exactly as above, or a cell outside the layout holds a value. |
| `METADATA_TOTAL_MISMATCH` | Total Evidence Items does not equal the number of item rows. |
| `METADATA_ATTACHMENTS` | Total Attachments is not `0`. |
| `HEADERS_INVALID` | The Evidence Pack header row is not exactly the 30 headers in order, or a value sits in a column with no header. |
| `ATTACHMENTS_INVALID` | The Attachments Manifest header row is wrong, or the sheet has rows below it. |
| `REQUIRED_BLANK` | Evidence ID, Type or Description is blank. |
| `ENUM_INVALID` | A value is not exactly one of the allowed values for its column. |
| `DATE_PRECISION` | Collection Date is not `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. |
| `CUSTODY_JSON` | Chain of Custody is blank, not valid JSON, or not an array of objects. |
| `CUSTODY_ENTRY` | A custody entry is missing a required key, has a wrong type or value, or has an unknown key. |
| `LIST_SEPARATOR` | A list cell does not separate its entries with exactly `, `. |
| `LIST_SEMICOLON` | A list cell contains a semicolon. |
| `LIST_EMPTY_FRAGMENT` | A list cell has an empty entry. |
| `LIST_FRAGMENT_UNBALANCED` | A list entry has unbalanced brackets, a sign that a comma split one label in two. |
| `LIST_DUPLICATE` | A list cell repeats an entry. |
| `LIST_CELL_WHITESPACE` | A list cell starts or ends with whitespace. |
| `CELL_NOT_TEXT` | A cell is stored as a number, date or other non-text type. |
| `CELL_FORMULA` | A cell is a formula. |
| `CELL_TOO_LONG` | A cell has more than 32767 characters. |
| `CELL_PROBABLY_TRUNCATED` | A cell has exactly 32767 characters, so its text was probably cut short. |
| `CELL_BAD_CHAR` | A cell contains a character a workbook cannot hold (U+FFFE, U+FFFF or a lone surrogate). |
