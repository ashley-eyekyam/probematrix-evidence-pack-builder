# The case folder: workspace contract

This reference describes every file and folder the evidence pack builder knows about in a
case folder, who may change it, and whether it may be shared. Paths are relative to the case
folder. The plugin works in the folder where it is run; it never looks in parent folders.

## Sharing classes

- **user-owned**: the user's own files. The plugin reads them and never changes, moves or
  deletes them.
- **shareable**: de-identified output meant to be read, shared or imported.
- **structural**: settings and bookkeeping that hold no source text. Safe to keep in version
  control.
- **raw-text-confidential**: working files that hold raw source text, which can include
  personal names. Git ignores them and they are never published or copied into samples.
- **private-never-shared**: the private folder. Never shared, committed or copied anywhere.

## Every path

| Path | Class | What it holds |
| --- | --- | --- |
| `inputs/` | user-owned | The evidence files the user puts in, at any depth and of any type. |
| `outputs/` | shareable | Only the evidence-pack workbooks to import into ProbeMatrix. |
| `INDEX.md` | shareable | The case summary, rewritten every run. Only its Imported? boxes may be ticked. |
| `.epb/case.yaml` | structural | Case title, slug, ID prefix, timezone, creation time, plugin version and fixed settings. |
| `.epb/state.json` | structural | Input fingerprints, ID counters, workbooks, items and the status of each chunk. |
| `.epb/sources/` | structural | One record per input (`S001.json` and so on) with its paths, versions and status. |
| `.epb/segments/` | raw-text-confidential | The page- and time-anchored text of each input (later versions). |
| `.epb/media/` | raw-text-confidential | Keyframes, audio and page images used for conversion (later versions). |
| `.epb/ledger/claims.jsonl` | raw-text-confidential | Every claim extracted from the inputs (later versions). |
| `.epb/ledger/conclusions.jsonl` | raw-text-confidential | Conclusions and recommendations held back from the evidence (later versions). |
| `.epb/ledger/chunks.json` | raw-text-confidential | The extraction chunk plan, including section headings; created on the first extraction. |
| `.epb/rosters/` | structural | Role and equipment labels with their aliases; never names (later versions). |
| `.epb/conflicts.yaml` | structural | The register of conflicting accounts (later versions). |
| `.epb/items/` | structural | The authored, de-identified evidence items (later versions). |
| `.epb/coverage.json` | structural | Which claim became which item, or why it was left out (later versions). |
| `.epb/runs/` | raw-text-confidential | One folder per run (`runs/001/`) with its record and report. |
| `.epb/inbox/` | raw-text-confidential | Agent submissions waiting to be checked; never final state. |
| `.epb/tmp/` | raw-text-confidential | The journals that make every change all-or-nothing. |
| `.epb/private/` | private-never-shared | The private folder. Its own ignore file holds `*`, so git ignores everything in it. |
| `.epb/private/name-map.yaml` | private-never-shared | Real names mapped to role labels; the only place names are kept (later versions). |
| `.epb/.gitignore` | structural | Tells git to ignore every folder that holds raw source text. |
| `.epb/.gitattributes` | structural | Holds `* -text`, so git never changes line endings in the state files. |
| `.epb/lock` | structural | The workspace lock, held while a command changes the case folder. |

`init` creates `inputs/`, `outputs/`, `INDEX.md`, `.epb/case.yaml`, `.epb/state.json`, the
`inbox/`, `tmp/`, `runs/` and `private/` folders and the three ignore and attribute files.
Every other path appears when a later version first needs it.

## Rules

- `inputs/` is user-owned and read-only to the plugin. Inputs are never moved, renamed or
  changed, and the agent never edits them either.
- `outputs/` holds only workbooks. Reports, logs and notes go in `.epb/runs/`.
- `INDEX.md` is rewritten by every command that changes the case folder. The only edit a
  person may make is ticking an Imported? box, which has the form `- [ ] Imported: <file>`
  and becomes `- [x] Imported: <file>` once ticked.
- Nothing in `.epb/` is ever edited by hand, by the user or by an agent. Only the epb command
  changes it.
- Git ignores these folders through `.epb/.gitignore`, because they hold raw source text:
  `segments/`, `ledger/`, `inbox/`, `tmp/`, `media/`, `runs/` and `private/`. The structural
  files can be kept in version control. The private folder has its own ignore file as well.
- `.epb/.gitattributes` holds `* -text` so the state files keep their exact bytes.
- If the case folder sits in a cloud sync folder or a git repository, `init` and `doctor`
  warn (`SYNC_FOLDER`, `GIT_PRIVATE_NOT_IGNORED`, `GIT_TRACKS_PRIVATE`).

## IDs

- Inputs are numbered `S001`, `S002` and so on, with at least three digits; after `S999`
  comes `S1000`. A number is never reused.
- A changed input keeps its number and gets a new version, shown as `S004v2`, `S004v3` and
  so on. Version 1 is shown without a suffix.
- Runs are numbered `001`, `002` and so on, in `.epb/runs/<NNN>/`. Only `init`, `scan` and an
  upgrade start a run.
- Evidence IDs look like `EVD-<PREFIX>-001`, from the case's ID prefix (later versions).

## Scan rules

`scan` reads `inputs/` and nothing else. It fingerprints every regular file by content
(SHA-256) and compares the result with what the case folder already knows.

- Content decides identity. A file whose content is already known is the same input, wherever
  it now sits.
- A renamed or moved file keeps its ID. The same content at several paths is a duplicate: one
  input with several paths.
- When a known path now holds content that matches another input, content wins: the path
  joins that other input, and the old input keeps only the paths that still hold its own
  content.
- Changed content at a known path becomes a new version of that input (for example `S004v2`).
  Content that matches no input becomes a new input with the next ID.
- Only an input's current version is matched. Restoring an older version of a file counts as
  new content, so it becomes a new version or a new input, never a step back.
- A file that disappears is marked removed from the folder. Its record and its last known
  paths are kept, and anything already built from it stays. Records are never deleted.
- A note about one file sits beside it, named exactly `<file>.note.md` or `<file>.note.yaml`
  (for example `cam3.mp4.note.md` describes `cam3.mp4`). The note is registered as an input
  of its own and paired with its file by exact name. A note with no matching file is reported
  as `SIDECAR_ORPHAN`. A file named only `.note.md` is an ordinary input.
- These are listed as ignored and never registered: links and junctions (never followed),
  special files such as pipes and devices, and system leftovers matching `.DS_Store`,
  `Thumbs.db`, `desktop.ini`, `~$*`, `._*`, `.~lock.*#` or `*.tmp`.
- When the content and the extension disagree, the content decides the file type and the
  mismatch is reported (`MIME_MISMATCH`).
- Two files whose names differ only in how their accented letters are encoded cannot both be
  kept; scan stops with `BAD_ARGUMENT`, changes nothing and names the file, so the user can
  rename one.
- A new input is waiting for conversion until a later version of the plugin converts it.

## Records and state

- Every source record has `parents`, a list of the carriers it came from (an email or an
  archive), one entry per carrier. It is empty for a file the user put in `inputs/` directly.
  An identical attachment delivered by two emails is one input with two parents.
- Chunk data is split in two. `.epb/state.json` holds only each chunk's status, with no raw
  text, so it stays safe to keep in version control. `.epb/ledger/chunks.json` holds the
  chunk plan with its section headings, which are raw text, so it is git-ignored.
- Every stored file carries `schema_version`. A case folder written by an older plugin is
  upgraded automatically by the next command that changes it: copies of `state.json`,
  `case.yaml` and the source records go to `.epb/runs/<NNN>/pre-upgrade/`, the upgrade runs
  as one all-or-nothing change, and a `WORKSPACE_UPGRADED` warning says where the copy is.
  Commands that only look never upgrade; they warn `UPGRADE_PENDING`.
- Adding an optional field to a stored file needs no upgrade. Only a change that older
  records cannot satisfy gets an upgrade step.

## The lock and the journals

- A command that changes the case folder holds `.epb/lock` for its whole run. A second such
  command waits up to 60 seconds (`--wait` changes that), then stops with `LOCK_TIMEOUT`. The
  lock is released automatically when the command ends, even if it crashes. Its content (the
  process, command and start time of the holder) is rewritten by every such command.
- Commands that only look, such as `status`, take no lock.
- Every change is staged in a journal under `.epb/tmp/` and applied all at once, with
  `state.json` written last. If a command is interrupted, the next command that changes the
  case folder finishes the change first and warns `RECOVERED`.

## Exit code 4 and the case folder

Exit code 4 means the case folder or the plugin is in a state the command cannot use. Stop,
tell the user the code and the message, and do not edit anything in `.epb/` or `inputs/`.

- `STATE_INVALID`: `.epb/state.json` or `.epb/case.yaml` is damaged or was edited by hand,
  or a source record cannot be read. Restore the `.epb` folder from a backup or from version
  control. Never repair it by hand.
- `RECORD_INVALID`: a stored record can be read but fails its schema. Treat it like
  `STATE_INVALID`.
- `WORKSPACE_TOO_NEW`: a newer version of the plugin wrote this case folder. Update the
  plugin; never downgrade the folder.
- `LOCK_TIMEOUT`: another command held the case folder for too long. Wait for it to finish,
  then try again.
