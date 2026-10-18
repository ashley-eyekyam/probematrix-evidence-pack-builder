# Rules for agents using the ProbeMatrix Evidence Pack Builder

These rules apply whenever you help a user build an evidence pack with this plugin, on any
host. Read them before the first command and follow them for the whole case. When a skill
and these rules seem to disagree, follow the stricter of the two and tell the user.

## Just culture

- Describe what happened and what was observed. Never decide who is to blame.
- Write about actions, conditions and systems, not about a person's character or attitude.
- Keep a neutral tone. Words such as "careless", "negligent" or "failed to" pass judgement;
  leave them out unless they sit inside a verbatim quote.

## Roles only

- People appear only as role labels, for example "Shift Supervisor (Control Room)" or
  "Contractor Technician A (Pump House)". Never write a personal name into anything the user
  may share.
- Keep each role label the same for the whole case, and keep labels free of commas.
- Never guess a seniority, department or employer that the inputs do not state.

## Inputs only

- Every fact must come from a saved input in the case's `inputs/` folder.
- Never add facts from your own memory or from the web. If a web page matters, ask the user
  to save a snapshot into `inputs/` first, then work from that copy.
- When an input is missing or unreadable, say so plainly instead of filling the gap.

## Facts only

- Record observations, records, measurements and statements: what was seen, measured, found
  in a document or said by a witness.
- Give no causal verdicts. Deciding why something happened is the investigation team's job
  in ProbeMatrix, not yours.
- Keep times and dates at the precision the input gives. Never pad a year to a full date.

## Verbatim quotes

- A quote is the exact text of the source, character for character, including its spelling,
  numbers and punctuation.
- Mark an error that is in the source with [sic]. Never correct it silently.
- Put quotes in typographic quotation marks (“ ”). A quote you cannot find in the cited part
  of the source must not be used.

## Evidence-bank entry rule

- Conclusions, lessons and recommendations are never evidence, whoever wrote them: an
  official report, an internal review, an audit, a regulator or the press.
- That covers root causes and other causal findings, opinions on adequacy or blame, lessons
  learned, recommendations, remedial or corrective measures, action plans and improvement
  lists.
- What the source directly observed is still evidence, and so is a plain timeline of what
  happened when, provided it carries no judgement about cause.
- When one sentence mixes a fact with a verdict, split it: keep the fact and hold the
  verdict back.
- When in doubt, hold it back.

## Working with the epb command

- Run first-time setup with `doctor --setup`. Always call commands with `--json`, read the
  envelope, and branch on `exit_code` and `errors[].code`, never on message text.
- Exit code 2 means the command itself was wrong: fix the arguments and run it again. Exit
  code 3 means something the plugin needs is missing or out of date: run `doctor --setup`
  and follow what it says.
- Exit code 4 means an internal or environment problem: stop, report the error code to the
  user, and never edit evidence or the .epb folder in response.
- Never hand-edit `.epb/state.json` or any other file under `.epb/`; only the `epb` command
  changes them. Never put personal names on the command line; pass them in a file or on
  standard input when a command asks for them.
- Only the user can import a pack into ProbeMatrix. Never claim that a ProbeMatrix import
  worked; ask the user to report the result.
