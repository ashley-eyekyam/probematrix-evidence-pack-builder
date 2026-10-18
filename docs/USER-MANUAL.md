# ProbeMatrix Evidence Pack Builder: User Manual

This manual is for investigators and safety professionals who want to use the ProbeMatrix
Evidence Pack Builder without any programming knowledge. It explains, one step at a time,
what to type and what you should see. When this manual shows text you should type, it
appears in a grey box. Type it exactly as shown, then press Enter. When it shows what the
screen should say, the words are copied from the plugin itself, so they should match what
you see.

## 1. What this plugin does

The ProbeMatrix Evidence Pack Builder is a plugin for AI apps such as Claude Code. It turns a
folder of incident material (investigation reports, scanned documents, witness statements,
photos, recordings and system exports) into an evidence pack: an Excel workbook that you
import into ProbeMatrix.

This is the first edition of the manual, and it covers what the plugin can do today:

- install the plugin and run its first-time setup;
- set up a case folder for one incident;
- take stock of the files you put in that folder, and keep a plain-language summary of them
  in a file called `INDEX.md`.

The plugin does not yet read the contents of your files or build the workbook. Those stages
arrive in later editions of this manual and the plugin, in this order: converting your files to
text, extracting what they say, writing de-identified evidence items, and building the
workbook itself.

You do not need to know any programming to use the plugin. You talk to the agent in plain
words, and the agent runs the plugin for you. A few steps, such as installing Python, are
done once in a terminal: a window where you type commands. This manual tells you exactly what
to type.

## 2. What stays on your computer

Please read this chapter before you put real incident material into a case folder.

### What happens on your computer

- Setup, the case folder and everything the plugin records about your files stay on your
  computer. Converting your files (in later versions) also runs on your computer.
- The plugin itself does not send your files anywhere. The only time it downloads anything is
  first-time setup, which fetches the plugin's own packages.

### What the AI host sees

The agent you talk to runs inside an AI app, which this manual calls the AI host (for example
Claude Code). To do its work, the agent reads excerpts from your files: a page, a paragraph,
the plugin's summary of a folder. **Every excerpt the agent reads is sent to the AI host's
model provider**, the company that runs the AI model behind the app (for Claude Code, that is
normally Anthropic).

The excerpts come from your original files, so they can include people's names and other
personal details. How the model provider stores and uses what it receives is set by your
agreement with that company, not by this plugin. Check with your organisation that you may use
your AI app with incident material before you start.

### De-identification and file names

De-identification means replacing people's names with role labels, such as "Shift Supervisor
(Control Room)".

De-identification arrives in a later version, together with reading the contents of your
files. From then on it is always on and cannot be switched off, and the evidence pack workbook
uses role labels instead of names.

This version does not replace any names yet. `INDEX.md` and the plugin's own records in the
hidden `.epb` folder list your files by their file and folder names, exactly as you gave them.
If a file is named after a person, that person's name appears in `INDEX.md`.

So, until then:

1. If a file name or folder name contains a person's name (for example a statement named after
   the witness), rename it before you put it in `inputs/`. `INDEX.md` shows every file name as
   it is.
2. Before you share `INDEX.md` or send it to anyone, read it and check that it contains no
   names.
3. Do not share, send or upload the `.epb` folder.

When de-identification arrives, the only list that links real names to role labels will be
kept in the hidden folder `.epb/private/` inside your case folder. Never send, share or upload
that folder.

### Never put a case folder in a sync folder

Never put a case folder inside OneDrive, Dropbox, iCloud Drive or Google Drive, or inside any
other folder that a cloud service copies to the internet. These services upload everything in
the folder, including `.epb/private/` and the list of real names it will hold.

When you set up a case folder, or check the plugin from inside one, the plugin looks for these
services. If the folder appears to be inside one, the agent passes on a warning. For OneDrive
the plugin's warning says:

```text
This folder appears to be inside OneDrive. Sync services upload everything in it, including .epb/private/, where the private name map will be kept.
```

and its advice is:

```text
Move the case folder to a folder that OneDrive does not sync, then continue.
```

For the other services the warning names that service instead. If you see this warning:

1. Close the AI app.
2. Move the whole case folder to a folder that is not synced, for example a folder called
   `evidence-cases` directly inside your home folder.
3. Open the AI app again in the folder's new place and carry on.

Moving a case folder is safe: the plugin does not depend on where the folder is.

### Never put `.epb/private/` into git

If you use git, a tool that keeps the history of a folder and can copy it to a server, never
let it record `.epb/private/`. The plugin adds the files that tell git to leave that folder
out, and it warns you if a case folder sits inside a git repository that would record it. If
you do not use git, you can skip this paragraph.

## 3. Install Python

The plugin needs Python 3.11 or newer. Python is a free program that many tools use. You
install it once.

### Linux

These steps have been tested on Ubuntu.

1. Open a terminal: press Ctrl+Alt+T.
2. Type this command and press Enter:

   ```text
   python3 --version
   ```

3. Look at the answer. If it says `Python 3.11` or a higher number, for example
   `Python 3.12.3`, Python is installed. Go to step 4 anyway: it adds a part that setup needs.
4. Type this command and press Enter:

   ```text
   sudo apt install python3 python3-venv
   ```

5. Type your computer password when asked and press Enter. Nothing appears on the screen while
   you type the password; that is normal.
6. If the terminal asks `Do you want to continue? [Y/n]`, type `Y` and press Enter.
7. Wait until the terminal shows its prompt again, then type `python3 --version` once more.
   It should now say `Python 3.11` or higher.

Older Ubuntu releases, such as Ubuntu 22.04, come with Python 3.10, which is too old. On those,
type `sudo apt install python3.11 python3.11-venv` in step 4 instead. Setup finds Python 3.11
on its own. This route for older Ubuntu releases has not been tried with the plugin yet.

### Windows

*This section is not yet tested on this system.* The steps follow Python's official installer,
but nobody has yet tried them with this plugin on a Windows computer.

1. Open https://www.python.org/downloads/ in your web browser.
2. Click the yellow button that says "Download Python" followed by a version number.
3. Open the file you downloaded.
4. If the first screen shows a box labelled "Add python.exe to PATH", tick it.
5. Click "Install Now" and wait until the installer says it has finished. Then click "Close".
6. Open a terminal: press the Windows key, type `Terminal`, and press Enter. (On older
   versions of Windows, type `PowerShell` instead.)
7. Type this command and press Enter:

   ```text
   py -3 --version
   ```

8. It should say `Python 3.11` or a higher number. If it says the command is not recognised,
   restart your computer and try step 7 again.

### macOS

*This section is not yet tested on this system.* The steps follow Python's official installer,
but nobody has yet tried them with this plugin on a Mac.

1. Open https://www.python.org/downloads/ in your web browser.
2. Click the yellow button that says "Download Python" followed by a version number.
3. Open the file you downloaded and follow the installer: click "Continue" on each screen,
   then "Install", and type your Mac password when asked.
4. When the installer says it has finished, click "Close".
5. Open Terminal: press Cmd+Space, type `Terminal`, and press Return.
6. Type this command and press Return:

   ```text
   python3 --version
   ```

7. It should say `Python 3.11` or a higher number. If a window offers to install "command line
   developer tools" instead, click "Cancel", close Terminal, open it again and repeat step 6.

## 4. Add the plugin to Claude Code

You need Claude Code installed and signed in. If you do not have it yet, install it first by
following Anthropic's instructions for Claude Code.

1. Open a terminal (see chapter 3 for how to open one on your computer).
2. Type this command and press Enter to start Claude Code:

   ```text
   claude
   ```

3. In Claude Code, type this command and press Enter:

   ```text
   /plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder
   ```

   Claude Code confirms that it has added the marketplace `probematrix-evidence-pack-builder`.
   A marketplace is a list of plugins you can install.
4. Type this command and press Enter:

   ```text
   /plugin install probematrix-evidence-pack-builder@probematrix-evidence-pack-builder
   ```

   Claude Code confirms that the plugin is installed.
5. If Claude Code asks you to restart it, type `/exit` and press Enter, then type `claude` and
   press Enter again.

The plugin is now installed. Go on to chapter 5 to run its first-time setup.

### Using OpenAI Codex instead

*This section is not yet tested on this system.* The plugin is built to work in Codex too,
but nobody has yet tried these steps with it.

In a terminal, type this command and press Enter:

```text
codex plugin marketplace add ashley-eyekyam/probematrix-evidence-pack-builder
```

If that does not work, download the plugin's repository from GitHub, open a terminal inside
the downloaded folder, and type `python3 tools/install-codex.py` (on Windows,
`py -3 tools/install-codex.py`). It copies the plugin's skills into the folder Codex reads them
from.

## 5. First-time setup

The plugin needs a few extra building blocks, called packages, before it can work. First-time
setup downloads these packages once and keeps them in a private folder on your computer. The
plugin never mixes them with anything else installed on your computer.

- Setup needs an internet connection.
- Setup usually takes a few minutes. Let it finish.
- You only need to do it once for each version of the plugin. When the plugin is updated, the
  agent runs setup again for the new version.

### Start first-time setup

1. Open Claude Code in any folder, for example the empty folder you will use for your first
   case.
2. Type this message to the agent:

   ```text
   Run first-time setup for the evidence pack plugin
   ```

3. The agent checks your computer first. If setup has not been run yet, it tells you that
   setup will download the plugin's packages once into a private folder, and then starts it.
   If Claude Code asks for permission to run a command, allow it.
4. Wait until the agent shows you a short checklist like the one below.

Some AI apps do not let the agent download anything. If that happens, the agent shows you a
command that starts with `python3` and ends with `doctor --setup`. In that case:

1. Open a terminal (on Ubuntu, press Ctrl+Alt+T).
2. Copy the exact command the agent showed you, paste it into the terminal and press Enter.
3. Wait until the terminal shows the checklist below, then go back to the agent.

### What you should see after setup

The checklist always has three headings, in this order. Here is what it looks like on a Linux
computer that has 7-Zip and git installed but none of the other optional tools:

<!-- golden:setup -->
```text
Ready
- Python 3.12 — ready
- Private environment — created (~/.local/share/probematrix-epb/envs/0.1.0)
- Core packages — installed (14 of 14)
- 7-Zip — ready: .7z archives (support arrives in a later version of this plugin)
- git — ready: a warning when a case folder sits inside a git repository

Optional, not installed
- ffmpeg — would enable audio and video recordings (support arrives in a later version of this plugin). Install: sudo apt install ffmpeg
- Tesseract OCR — would enable scanned pages and images of text (support arrives in a later version of this plugin). Install: sudo apt install tesseract-ocr
- LibreOffice — would enable ODT, RTF and older Office files (support arrives in a later version of this plugin). Install: sudo apt install libreoffice
- pandoc — would enable an extra converter for word-processor files (support arrives in a later version of this plugin). Install: sudo apt install pandoc
- email extra — would enable Outlook .msg emails (support arrives in a later version of this plugin). Licence: GPL-3.0. Install: ask the agent to install the email extra.
- media extra — would enable local transcription of audio and video (support arrives in a later version of this plugin). Licence: MIT; pulls GPL-licensed codec binaries. Install: ask the agent to install the media extra.
- docs extra — would enable layout-aware conversion of complex PDFs (support arrives in a later version of this plugin). Licence: MIT; large download. Install: ask the agent to install the docs extra.

What to do next
- Set up a case folder: ask the agent to set up an evidence pack case folder here.
```
<!-- /golden:setup -->

Your list may be a little different: it shows your own Python version and the tools that are
on your computer. The version number at the end of the private environment folder is the
version of the plugin you installed.

What the three headings mean:

- **Ready** lists what is installed and working. After setup it should always include Python,
  the private environment and the core packages. "created" means setup has just built the
  private environment; if you run setup again it says "ready" instead.
- **Optional, not installed** lists extra tools that would let the plugin handle more kinds of
  files, with the command that installs each one on your kind of computer. They are optional:
  the plugin works without them, and you can add any of them later. Many say "support arrives
  in a later version of this plugin", which means this version does not use them yet.
- **What to do next** tells you the next step. After a successful setup it tells you to set up
  a case folder, which chapter 6 explains.

### Check your setup at any time

You can ask the agent to check the plugin at any time, for example after installing one of the
optional tools. Type:

```text
Check the evidence pack plugin setup
```

The agent shows the same three headings. On the same computer as above, after setup, it says:

<!-- golden:doctor -->
```text
Ready
- Python 3.12 — ready
- Private environment — ready (~/.local/share/probematrix-epb/envs/0.1.0)
- Core packages — ready (14 of 14 installed)
- 7-Zip — ready: .7z archives (support arrives in a later version of this plugin)
- git — ready: a warning when a case folder sits inside a git repository

Optional, not installed
- ffmpeg — would enable audio and video recordings (support arrives in a later version of this plugin). Install: sudo apt install ffmpeg
- Tesseract OCR — would enable scanned pages and images of text (support arrives in a later version of this plugin). Install: sudo apt install tesseract-ocr
- LibreOffice — would enable ODT, RTF and older Office files (support arrives in a later version of this plugin). Install: sudo apt install libreoffice
- pandoc — would enable an extra converter for word-processor files (support arrives in a later version of this plugin). Install: sudo apt install pandoc
- email extra — would enable Outlook .msg emails (support arrives in a later version of this plugin). Licence: GPL-3.0. Install: ask the agent to install the email extra.
- media extra — would enable local transcription of audio and video (support arrives in a later version of this plugin). Licence: MIT; pulls GPL-licensed codec binaries. Install: ask the agent to install the media extra.
- docs extra — would enable layout-aware conversion of complex PDFs (support arrives in a later version of this plugin). Licence: MIT; large download. Install: ask the agent to install the docs extra.

What to do next
- Set up a case folder: ask the agent to set up an evidence pack case folder here.
```
<!-- /golden:doctor -->

If **What to do next** asks you to run first-time setup, setup has not been run for this
version of the plugin yet: go back to "Start first-time setup" above.

## 6. Your first case folder

A case folder holds everything for one incident. You put the incident material in it, and the
plugin keeps its records and, in later versions, the evidence pack beside it. The examples
below use a made-up incident called "Acme Pump Trip".

### Make the folder and start the agent there

1. Open a terminal.
2. Make an empty folder for the case. On Linux or macOS type this command and press Enter:

   ```text
   mkdir -p ~/evidence-cases/acme-pump-trip
   ```

   On Windows (not yet tested on this system), type
   `mkdir $HOME\evidence-cases\acme-pump-trip` instead. Remember chapter 2:
   the folder must not be inside OneDrive, Dropbox, iCloud Drive or Google Drive.
3. Go into the folder. On Linux or macOS type `cd ~/evidence-cases/acme-pump-trip` and press
   Enter (on Windows, `cd $HOME\evidence-cases\acme-pump-trip`).
4. Start Claude Code there: type `claude` and press Enter.

### Set up the case folder

1. Type this message to the agent:

   ```text
   Set up an evidence pack case folder here
   ```

   If first-time setup has not been run yet, the agent runs it first (chapter 5).
2. The agent asks you for the case title, and only for that. Type a short title that describes
   the incident, for example `Acme Pump Trip`. Do not put a person's name in the title.
3. The agent proposes the other settings in one line and waits for your answer, for example:

   ```text
   I'll set this up as Acme Pump Trip (slug acme-pump-trip, IDs EVD-APT-001 onwards, timezone Asia/Kolkata). OK?
   ```

   - The **slug** is the short name used in file names. It comes from the folder name.
   - The **ID prefix** (here `APT`) appears in every evidence ID. It comes from the title's
     initials.
   - The **timezone** is used for dates and times. It comes from your computer. On Windows the
     plugin cannot always read it by itself, so check it with particular care.
4. Check the three settings carefully: they cannot be changed once the case folder is set up.
   If they are right, type `OK`. If not, say what to change, for example
   `Use the prefix PMP instead`.
5. The agent sets up the folder. It now holds a folder called `inputs`, a folder called
   `outputs`, a file called `INDEX.md` and a hidden folder called `.epb`, which is the plugin's
   own working area. Never change anything inside `.epb`.
6. If the agent passes on a warning about a sync service or git, follow chapter 2.

### Put your files in `inputs/`

1. Before you copy a file in, check its name. If a file name or folder name contains a
   person's name, rename it first, for example to `witness-statement-1.pdf`. `INDEX.md` shows
   file names exactly as they are, and renaming is up to you.
2. Copy the incident files into the `inputs` folder. Any type of file is fine, and you can use
   sub-folders. The plugin never changes, moves or renames anything in `inputs/`.
3. If you want to add a note about a file, for example where it came from, make a text file
   next to it with the same name followed by `.note.md`. For example, a note about
   `inputs/control-room-log.pdf` is called `inputs/control-room-log.pdf.note.md`.

### Take stock of the inputs

1. Type this message to the agent:

   ```text
   Take stock of the inputs
   ```

2. The agent tells you what it found. Each new file gets an ID: `S001`, `S002` and so on. When
   you later add or change files and ask again, it tells you what changed, for example that
   `S001v2` is a new version of a file that changed since the last time.

### Read `INDEX.md`

`INDEX.md` is a plain-text summary of the case folder. The plugin rewrites it every time it
runs, so do not edit it. Open it with any text editor, or ask the agent:

```text
What does INDEX.md say?
```

It has six sections, always in this order:

- **1. Case**: the title, slug, ID prefix, timezone, plugin version, the last run and the
  current version of the evidence pack.
- **2. What to import where**: the workbooks to import into ProbeMatrix, in order, once the
  plugin can build them.
- **3. Inputs**: one row for each file in `inputs/`, with its ID, its file name and folder,
  type, size and status.
- **4. Outputs**: each workbook and the inputs that contributed to it.
- **5. Open issues**: anything that needs your attention, for example a note whose file is
  missing or a file the plugin had to skip.
- **6. Run history**: one line for each time the plugin changed the case folder.

Before you share `INDEX.md`, check that no file name in it contains a person's name (see
chapter 2).

Two phrases appear often in this edition:

- "none yet" means there is nothing of that kind yet. For example, **2. What to import where**
  says "none yet" until the plugin can build a workbook.
- "waiting for conversion (coming in a later version)" means the plugin has registered the file
  and will convert it to text in a later version.

## 7. Where the private environment lives

First-time setup keeps the plugin's packages in a private folder on your computer, called the
private environment. There is one such folder for each user of the computer, and every AI app
on the computer uses the same one. Your case folders are never kept there, so removing it never
touches your evidence.

Inside that folder, a folder called `envs` holds one folder for each version of the plugin,
named after the version number, for example `envs/0.1.0`. When you update the plugin, setup
builds a new folder for the new version and leaves the old one where it is. A detailed check
of the plugin lists any old versions it finds.

You can delete the folder of an old version by hand to free space, as described below for your
computer. If you delete the folder of the version you use by mistake, nothing is lost: ask the
agent to run first-time setup again and it rebuilds it.

### Linux

The private environment is in `~/.local/share/probematrix-epb/`. The `~` means your home
folder, and the dot at the start of `.local` means the folder is hidden.

1. Close Claude Code.
2. Open the Files app and go to your home folder.
3. Press Ctrl+H to show hidden folders.
4. Open `.local`, then `share`, then `probematrix-epb`, then `envs`.
5. Right-click the folder of the old version, for example `0.1.0`, and choose "Move to Trash".

### Windows

*This section is not yet tested on this system.*

The private environment is in `%LOCALAPPDATA%\probematrix-epb\`, which is usually
`C:\Users\<your user name>\AppData\Local\probematrix-epb\`.

1. Close the AI app.
2. Press the Windows key and R together. A small window called "Run" opens.
3. Type `%LOCALAPPDATA%\probematrix-epb\envs` and press Enter. File Explorer opens the `envs`
   folder.
4. Right-click the folder of the old version, for example `0.1.0`, and choose "Delete".

### macOS

*This section is not yet tested on this system.*

The private environment is in `~/Library/Application Support/probematrix-epb/`. The `~` means
your home folder.

1. Close the AI app.
2. Open Finder and press Cmd+Shift+G. A box called "Go to Folder" opens.
3. Type `~/Library/Application Support/probematrix-epb/envs` and press Return.
4. Drag the folder of the old version, for example `0.1.0`, to the Trash.
