#!/bin/sh
# Opens the launcher on macOS.
#   scripts/mac/launcher.sh          the window
#   scripts/mac/launcher.sh --play   start the game with the saved settings
here=$(cd "$(dirname "$0")/../.." && pwd)
top=$(cd "$here/.." && pwd)
if [ -x "$top/.venv/bin/python" ]; then py="$top/.venv/bin/python"; else py=python3; fi
exec "$py" "$here/launcher/ascension_launcher.py" "$@"
