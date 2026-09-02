---
name: transcribe-audio
description: Transcribe an audio or video recording to text locally, with no upload and no API key. Use whenever the user points at a recording and wants the words out of it - a meeting, an interview, a voice message, a lecture, a podcast, a video - or asks to summarise, search or quote something that only exists as audio. Triggers on "transcribe", "what was said in", "get the text from this recording", and on any message that attaches or names an audio or video file.
---

# Transcribe audio locally

Runs Whisper on this machine through `transcribe.py`. The recording is never
uploaded anywhere.

## Steps

1. **Find the script.** It lives beside this skill in the `transcribe-local`
   checkout. If the path is unknown, look for `transcribe.py` in the user's
   projects, or ask where they cloned it.

2. **Check the dependency once.** `python -c "import faster_whisper"`. If that
   fails, run `pip install -r requirements.txt` from the checkout and say that
   the first run also downloads about 1.6 GB of model.

3. **Run it.** Write the output next to the recording unless the user asked
   otherwise:

   ```bash
   python transcribe.py "<path to the recording>"
   ```

   Useful flags: `-l ru` to skip language detection, `-m small` on a machine
   without a GPU, `-f srt` for subtitles, `--timestamps` when the user needs to
   cite moments, `-o <dir>` to redirect the output.

4. **Expect it to take a while.** A long recording on a CPU can run for as long
   as the recording itself. Start it in the background and tell the user the
   estimate rather than blocking on it. Progress goes to stderr as a percentage.

5. **Read the result and answer the actual question.** The `.txt` is a means,
   not the goal. If the user asked what was decided, read the transcript and
   answer that. Hand over the file path as well, so they keep it.

## Notes

- Video files are accepted directly; the audio track is extracted for you.
- A folder can be passed instead of a file to transcribe everything in it.
- Whisper punctuates and capitalises but does not label speakers. If the user
  needs who-said-what, say so plainly rather than guessing from the text.
- Quiet or overlapping speech produces confident-looking mistakes. When quoting
  a transcript for anything that matters, tell the user it is machine output.
