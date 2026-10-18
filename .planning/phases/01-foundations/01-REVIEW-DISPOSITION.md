---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "A file name that is not valid UTF-8 crashes `scan` with INTERNAL_ERROR (exit 4) and blocks the whole case"
  - id: WR-01
    severity: warning
    disposition: open
    title: "\"Rename the file\" does not remove the name once it has been scanned. After a rename plus edit, the name stays in INDEX.md for good"
  - id: IN-01
    severity: info
    disposition: open
    title: "`_inline` leaves bidi controls, zero-width characters and Markdown link syntax, so names can be disguised in a file users must read and check"
  - id: IN-02
    severity: info
    disposition: open
    title: "`_TEXT_BOMS` ordering comment is meaningless, and the `FF FE` short-circuit also masks CRC-protected MPEG-1 Layer I"
  - id: IN-03
    severity: info
    disposition: open
    title: "The `review-before-sharing` promise \"a later version shows role labels instead\" cannot hold for `state.json` or `sources/`, and the contract and manual disagree about `.epb`"
  - id: IN-04
    severity: info
    disposition: open
    title: "The text-mode subprocess guard is narrower than its docstring claims"
  - id: IN-05
    severity: info
    disposition: open
    title: "The \"full check matches CI\" guards check one substring. Local parity still omits the step that turned CI red"
  - id: IN-06
    severity: info
    disposition: open
    title: "The git-walk test was made to skip, not made hermetic"
open: 8
total: 8
recorded: 2026-10-18T16:07:22.149Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
