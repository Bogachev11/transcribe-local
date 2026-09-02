# transcribe-local

Turn a recording into text on your own machine. Drop in an audio or video file,
get a `.txt` next to it. No account, no upload, no API key: the model runs
locally, so the recording never leaves the computer.

Built on [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Uses an
NVIDIA GPU when it finds one and falls back to the CPU when it does not.

## Install

```bash
git clone https://github.com/Bogachev11/transcribe-local.git
cd transcribe-local
pip install -r requirements.txt
```

Python 3.9 or newer. No ffmpeg to install: decoding comes with the package.

If you have an NVIDIA card and want the fast path:

```bash
pip install -r requirements-gpu.txt
```

The first run downloads the model (about 1.6 GB for the default) and caches it in
your home folder. Every run after that is offline.

## Use

```bash
python transcribe.py meeting.mp3
```

That writes `meeting.txt` beside the input. More of what it takes:

```bash
python transcribe.py interview.m4a lecture.mp4     # several files at once
python transcribe.py ./recordings                  # a whole folder, recursively
python transcribe.py talk.mp3 -f srt -f txt        # subtitles as well as text
python transcribe.py talk.mp3 --timestamps         # every line prefixed with its time
python transcribe.py talk.mp3 -l ru                # skip language detection
python transcribe.py talk.mp3 -m small             # smaller, faster, less accurate
python transcribe.py talk.mp3 -o ~/transcripts     # write somewhere else
```

Video files work the same way. The audio track is pulled out for you.

## Without a terminal

**Windows.** Drag a file onto `transcribe.bat`. The text file appears next to it.

**macOS and Linux.** Double-click `transcribe.command`, then drag the file into
the window that opens and press Enter.

## Through Claude Code

Copy the skill into your Claude Code skills folder:

```bash
cp -r skills/transcribe-audio ~/.claude/skills/
```

Then ask Claude for it in plain language, in any project:

> transcribe audio.mp3

> transcribe this recording and summarise the decisions

Claude runs the same script and reads the result back, so you can go straight to
asking questions about what was said.

## Which model

`large-v3-turbo` is the default: it is the accurate one, and on a modern GPU it
runs roughly 20 to 40 times faster than real time. On a CPU-only laptop expect
somewhere near real time, so a one-hour recording takes about an hour.

| model             | download | notes                                   |
|-------------------|----------|-----------------------------------------|
| `large-v3-turbo`  | ~1.6 GB  | default, best accuracy per second spent |
| `medium`          | ~1.5 GB  | slower than turbo with no gain           |
| `small`           | ~0.5 GB  | sensible choice for a CPU-only machine  |
| `tiny`            | ~75 MB   | for testing that the pipeline works      |

## Output

Plain text comes out as paragraphs, split where the speaker paused for more than
two seconds. `--timestamps` gives one line per segment with its start time
instead. `-f srt` and `-f vtt` produce subtitles, `-f json` gives segments with
start and end times for further processing.

## Licence

MIT.
