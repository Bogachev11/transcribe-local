#!/bin/sh
# Double-click this file, then drag a recording into the window and press Enter.
cd "$(dirname "$0")" || exit 1

if [ "$#" -eq 0 ]; then
  printf 'Drag an audio or video file into this window and press Enter: '
  IFS= read -r dropped
  # Finder escapes spaces when it drops a path into a terminal; undo that.
  dropped=$(printf '%s' "$dropped" | sed 's/\\ / /g' | sed "s/^'//; s/'$//")
  [ -n "$dropped" ] || exit 1
  set -- "$dropped"
fi

if command -v python3 >/dev/null 2>&1; then
  python3 transcribe.py "$@"
else
  python transcribe.py "$@"
fi
