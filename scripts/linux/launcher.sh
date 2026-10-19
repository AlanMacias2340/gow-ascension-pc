#!/bin/sh
# Opens the launcher on Linux.
#   scripts/linux/launcher.sh          the window
#   scripts/linux/launcher.sh --play   start the game with the saved settings
here=$(cd "$(dirname "$0")/../.." && pwd)
top=$(cd "$here/.." && pwd)
if [ -x "$top/.venv/bin/python" ]; then py="$top/.venv/bin/python"; else py=python3; fi
exec "$py" "$here/launcher/ascension_launcher.py" "$@"
