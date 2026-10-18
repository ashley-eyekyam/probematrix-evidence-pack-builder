# ProbeMatrix Evidence Pack Builder: User Manual

This manual is for investigators and safety professionals who want to use the ProbeMatrix
Evidence Pack Builder without any programming knowledge. It explains, one step at a time,
what to type and what you should see. When this manual shows text you should type, it
appears in a grey box. Type it exactly as shown, then press Enter. When it shows what the
screen should say, the words are copied from the plugin itself, so they should match what
you see.

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
