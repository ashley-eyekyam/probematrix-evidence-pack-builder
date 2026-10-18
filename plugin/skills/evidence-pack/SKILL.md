---
name: evidence-pack
description: Start here to build a ProbeMatrix evidence pack (an EVIDENCE_PACK_V2 workbook) from a folder of incident material such as reports, statements, photos, logs and recordings. Use it whenever someone wants to set up the evidence pack builder on this computer, set up a case folder for an incident, put files into the case and take stock of them, or understand what the case's INDEX.md says. It runs the plugin's one-time setup, creates the case folder, registers every input with an ID and explains INDEX.md.
license: MIT
---

# Evidence pack builder

## What this version does

This version of the plugin does four things:

- sets itself up once on this computer (first-time setup);
- sets up a case folder;
- takes stock of the files in the case's `inputs/` folder and gives each one an ID;
- explains the case summary in `INDEX.md`.

Conversion of inputs to text, extraction of facts, de-identification and building the workbook arrive in later versions of this plugin. If the user asks for one of them, say so plainly and do not try to do it by hand.

## Rules

- Before the first command, read the plugin rules in `../../AGENTS.md`, two folders above this skill folder (on Claude Code: `${CLAUDE_SKILL_DIR}/../../AGENTS.md`). In a copy of this skill that has the file `references/plugin-rules.md` (a Codex skills copy), read that file instead. Follow the rules for the whole case.
- Never put personal names on the command line, and that includes the case title.
- Never create, edit, move or delete anything in `.epb/` or `inputs/`. Only the epb command changes `.epb/`, and `inputs/` belongs to the user.
- Never say a ProbeMatrix import worked. Only the user can import a pack and report the result.
- Speak plainly. When you mention an error code, always say what it means.

## Running the CLI

- On Claude Code: `python3 "${CLAUDE_SKILL_DIR}/scripts/epb.py" <command> --json`.
- On other hosts: the `scripts/epb.py` beside this SKILL.md, by its absolute path: `python3 <this skill folder>/scripts/epb.py <command> --json`.
- On Windows, use `py -3` instead of `python3`.
- After first-time setup, use `data.environment.launch` from the doctor or setup envelope as the command prefix. It is a list of two absolute paths, the private Python and `epb.py`: run `<launch[0]> <launch[1]> <command> --json`.
- Always pass `--json` and read the envelope: `ok`, `exit_code`, `data`, `warnings`, `errors` (each with `code`, `message` and `hint`) and `next`. Decide what to do from `exit_code` and `errors[].code`, never from message text.
- Run commands from the case folder, or add `--case <folder>`. The CLI never asks questions. If another command is busy with the case folder, it waits up to 60 seconds; `--wait <seconds>` changes that.

## First-time setup

1. Run `doctor --json`.
2. Exit 0: setup is already done. Keep `data.environment.launch` and go on.
3. Exit 3 with `ENV_NOT_SET_UP` or `CORE_PACKAGE_MISSING`: tell the user that setup downloads the plugin's Python packages once into a private folder on this computer, leaves their other software alone, and can take a few minutes. Then run `doctor --setup --json`.
4. Exit 3 with `PYTHON_TOO_OLD`: the plugin needs Python 3.11 or newer. Pass on the install step from the hint.
5. Show the result as the checklist the command prints, under its three headings: Ready, Optional, not installed, and What to do next. Optional tools are not needed by this version.
6. `VENV_UNAVAILABLE` or `SETUP_FAILED`: show the user the exact command from the hint and ask them to run it in a terminal. Never run sudo or any other elevated command yourself. If your host blocks downloads or writing outside the project, the same terminal command is the way round it.

## Setting up a case folder

1. Ask the user only for the case title. Ask for nothing else before you propose the rest.
2. Propose the other three settings in one line and wait for the user's OK:
   - the slug, made from the folder name (lower case, words joined by hyphens);
   - the ID prefix, the title's initials in capitals (2 to 6 letters or digits, starting with a letter); for example ACM gives evidence IDs EVD-ACM-001 onwards;
   - this computer's timezone, as an IANA name such as Europe/London. If you cannot tell it, ask.

   For example: "I'll set this up as Acme Pump Trip (slug acme-pump-trip, IDs EVD-APT-001 onwards, timezone Asia/Kolkata). OK?"
3. After the OK, run `init --title "<title>" --slug <slug> --prefix <PREFIX> --timezone <Area/City> --json`. Always pass `--timezone`: on Windows the timezone often cannot be detected, and init then stops with `TIMEZONE_REQUIRED`.
4. Pass on any warning in plain words:
   - `SYNC_FOLDER`: the case folder is inside a cloud sync service, so private working files may be copied to the cloud. Suggest a folder outside it.
   - `GIT_PRIVATE_NOT_IGNORED` or `GIT_TRACKS_PRIVATE`: the folder is in a git repository that would pick up, or already tracks, private working files. Pass on the hint.
   - `GIT_UNAVAILABLE`: git is not installed, so those checks were skipped.
5. `WORKSPACE_EXISTS` means the folder is already set up with different settings: tell the user and change nothing. `ALREADY_SET_UP` means there was nothing to do.
6. The folder now holds `inputs/`, `outputs/`, `INDEX.md` and the plugin's working folder `.epb/`.

## Taking stock of the inputs

1. Ask the user to put their files in `inputs/`, at any depth and of any type. A note about one file can sit beside it, named exactly `<file>.note.md` or `<file>.note.yaml` (for example `cam3.mp4.note.md`).
2. Run `scan --json`.
3. Report what `data` lists, in plain words:
   - `new`: new inputs, each with its ID (`S001`, `S002` and so on);
   - `new_versions`: a known file whose content changed, shown with its version (for example `S004v2`);
   - `renamed` and `moved`: the same content now at another path;
   - `duplicates`: the same content at more than one path; it stays one input;
   - `restored`: an input that came back;
   - `removed`: an input no longer in `inputs/`; its record is kept;
   - `ignored`: links, special files, system leftovers such as `.DS_Store`, and files or folders whose names are not valid text (reason `bad-name`), none of which are registered.
4. Pass on `MIME_MISMATCH` (a file's content does not match its extension; the content wins), `SIDECAR_ORPHAN` (a note with no matching file, usually a misspelt name), `INPUT_REMOVED` and `BAD_NAME_IGNORED` in plain words. `BAD_NAME_IGNORED` means a file or folder whose name is not valid text was skipped (for example one from an old ZIP file): name it as the warning shows it and ask the user to rename it, then scan again.
5. `changed: false` means nothing has changed since the last scan.
6. `INDEX.md` and the plugin's records show file and folder names exactly as they are, because this version does not replace names yet. If a name in `data` looks like a person's name, tell the user, naming the input by its ID (for example S003) rather than repeating the name, and suggest they rename the file themselves before they share `INDEX.md`. You never rename, move or edit anything in `inputs/`.

## Reading INDEX.md

`INDEX.md` is rewritten by every command that changes the case folder. The user may only tick its Imported? boxes. It has six sections:

1. Case: the title, slug, ID prefix, timezone, plugin version and last run.
2. What to import where: the workbooks in `outputs/` and the order to import them. Each has a line `- [ ] Imported: <file>` for the user to tick after importing it.
3. Inputs: one row per input with its ID, path, type, size, short fingerprint and status. The paths are the file names exactly as they are.
4. Outputs: which inputs went into each workbook.
5. Open issues: removed inputs, content that does not match its extension, notes with no matching file, and skipped links, special files or names that are not valid text.
6. Run history: one line per run of `init` or `scan`.

"none yet" means nothing of that kind exists yet, which is normal for a new case. "waiting for conversion" means the input is registered and will be converted by a later version of this plugin. "removed from folder" means the file has gone from `inputs/` but its record is kept.

## Exit codes

- 0: done. Still read `warnings` and pass them on.
- 1: the content was checked and rejected. This belongs to later stages.
- 2: the command was wrong or run in the wrong folder (`USAGE`, `BAD_ARGUMENT`, `NOT_A_WORKSPACE`, `TIMEZONE_REQUIRED`). Fix the command and run it again.
- 3: something the plugin needs is missing or out of date. Run first-time setup.
- 4: stop. Tell the user the error code and its message, and do not edit evidence or the `.epb` folder. `STATE_INVALID` means the case folder's state is damaged: pass on the restore hint and do not try to repair it. `LOCK_TIMEOUT` means another command is still busy with the case folder; try again when it finishes. `WORKSPACE_TOO_NEW` means a newer version of the plugin wrote this case folder; update the plugin.

The full description of the case folder is in `references/workspace-contract.md`, and the workbook format is in `references/evidence-pack-v2.md`.
