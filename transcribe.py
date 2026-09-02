#!/usr/bin/env python3
"""Local speech-to-text: point it at audio or video, get a text file beside it.

Nothing is uploaded. faster-whisper runs the model on this machine, on an NVIDIA
GPU when one is usable and on the CPU otherwise.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

MEDIA_SUFFIXES = {
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".flac", ".wma",
    ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".mpg", ".mpeg", ".ts",
}

# A pause this long reads as a new paragraph in the plain-text output.
PARAGRAPH_GAP_SECONDS = 2.0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="transcribe",
        description="Transcribe audio or video to text, locally.",
    )
    parser.add_argument("inputs", nargs="+", metavar="FILE",
                        help="audio/video files, or folders to scan for them")
    parser.add_argument("-m", "--model", default="large-v3-turbo",
                        help="whisper model (default: large-v3-turbo; "
                             "use 'small' on a weak machine)")
    parser.add_argument("-l", "--language", default=None,
                        help="language code such as ru or en (default: detect)")
    parser.add_argument("-f", "--format", dest="formats", action="append",
                        choices=["txt", "srt", "vtt", "json"],
                        help="output format, repeatable (default: txt)")
    parser.add_argument("-o", "--output-dir", default=None, type=Path,
                        help="where to write results (default: beside each input file)")
    parser.add_argument("-d", "--device", default="auto", choices=["auto", "cuda", "cpu"],
                        help="where to run (default: auto)")
    parser.add_argument("--timestamps", action="store_true",
                        help="prefix every line of the txt output with its start time")
    parser.add_argument("--no-vad", action="store_true",
                        help="disable voice-activity filtering (keeps silence and noise)")
    args = parser.parse_args(argv)
    args.formats = list(dict.fromkeys(args.formats or ["txt"]))
    return args


def collect_inputs(raw_paths):
    """Expand folders into the media files inside them; keep explicit files as given."""
    files = []
    for raw in raw_paths:
        path = Path(raw).expanduser()
        if path.is_dir():
            files.extend(sorted(
                child for child in path.rglob("*")
                if child.is_file() and child.suffix.lower() in MEDIA_SUFFIXES
            ))
        elif path.is_file():
            files.append(path)
        else:
            print("skipped, not found: " + str(path), file=sys.stderr)
    return files


def load_model(name, device):
    """Return (model, device_used). 'auto' tries the GPU first, then falls back."""
    from faster_whisper import WhisperModel

    attempts = []
    if device in ("auto", "cuda"):
        attempts.append(("cuda", "float16"))
    if device in ("auto", "cpu"):
        attempts.append(("cpu", "int8"))

    last_error = None
    for dev, compute_type in attempts:
        try:
            print("loading {} on {} ({})...".format(name, dev, compute_type),
                  file=sys.stderr, flush=True)
            return WhisperModel(name, device=dev, compute_type=compute_type), dev
        except Exception as exc:  # noqa: BLE001 - any GPU problem means we try the CPU
            last_error = exc
            if dev == "cuda" and device == "auto":
                print("GPU unavailable ({}), using the CPU instead.".format(
                    exc.__class__.__name__), file=sys.stderr)
    raise SystemExit("could not load the model: {}".format(last_error))


def stamp(seconds, sep=","):
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    millis = int((seconds - int(seconds)) * 1000)
    return "{:02d}:{:02d}:{:02d}{}{:03d}".format(hours, minutes, secs, sep, millis)


def write_txt(segments, path, timestamps):
    lines, buffer, prev_end = [], [], 0.0
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        if timestamps:
            lines.append("[{}] {}".format(stamp(seg.start, ".")[:-4], text))
            continue
        if buffer and seg.start - prev_end > PARAGRAPH_GAP_SECONDS:
            lines.append(" ".join(buffer))
            buffer = []
        buffer.append(text)
        prev_end = seg.end
    if buffer:
        lines.append(" ".join(buffer))
    separator = "\n" if timestamps else "\n\n"
    path.write_text(separator.join(lines).strip() + "\n", encoding="utf-8")


def write_srt(segments, path):
    blocks = []
    index = 1
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        blocks.append("{}\n{} --> {}\n{}\n".format(
            index, stamp(seg.start), stamp(seg.end), text))
        index += 1
    path.write_text("\n".join(blocks), encoding="utf-8")


def write_vtt(segments, path):
    blocks = ["WEBVTT\n"]
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        blocks.append("{} --> {}\n{}\n".format(
            stamp(seg.start, "."), stamp(seg.end, "."), text))
    path.write_text("\n".join(blocks), encoding="utf-8")


def write_json(segments, path, language, duration):
    import json

    payload = {
        "language": language,
        "duration": round(duration, 2),
        "segments": [
            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segments if s.text.strip()
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def transcribe_one(model, source, args):
    started = time.monotonic()
    segments, info = model.transcribe(
        str(source),
        language=args.language,
        beam_size=5,
        vad_filter=not args.no_vad,
    )
    print("{}: {} ({:.0%} sure), {:.1f} min".format(
        source.name, info.language, info.language_probability, info.duration / 60),
        file=sys.stderr, flush=True)

    collected = []
    for seg in segments:
        collected.append(seg)
        if info.duration:
            done = min(seg.end, info.duration) / info.duration
            print("\r  {:.0%}".format(done), end="", file=sys.stderr, flush=True)
    print("\r  100%", file=sys.stderr, flush=True)

    out_dir = args.output_dir or source.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in args.formats:
        target = out_dir / "{}.{}".format(source.stem, fmt)
        if fmt == "txt":
            write_txt(collected, target, args.timestamps)
        elif fmt == "srt":
            write_srt(collected, target)
        elif fmt == "vtt":
            write_vtt(collected, target)
        elif fmt == "json":
            write_json(collected, target, info.language, info.duration)
        written.append(target)

    elapsed = time.monotonic() - started
    speed = info.duration / elapsed if elapsed else 0
    print("  done in {:.0f}s ({:.0f}x realtime) -> {}".format(
        elapsed, speed, ", ".join(str(w) for w in written)), file=sys.stderr, flush=True)
    return written


def main(argv=None):
    args = parse_args(argv)
    sources = collect_inputs(args.inputs)
    if not sources:
        raise SystemExit("nothing to transcribe")

    model, _ = load_model(args.model, args.device)

    failures = 0
    for source in sources:
        try:
            transcribe_one(model, source, args)
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
            failures += 1
            print("{}: failed ({})".format(source.name, exc), file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
