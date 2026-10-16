#!/bin/sh
# Run the macOS build in a window, from the layout README.md describes:
#
#   ascension/  this repository, built into build/
#   work/       disc/ (the ISO, mounted here), hdd0/ (saves), run.log
#
# The disc image is mounted read-only at work/disc when it is not already.
# Point ASCENSION_ISO at it the first time:
#
#   ASCENSION_ISO="/Volumes/Externo/isos/.../God of War - Ascension (...).iso" tools/run_mac.sh
#
# Extra environment switches pass through, e.g. PS3RECOMP_METAL_HEADLESS=1 or
# PS3RECOMP_METAL_FRAME_DUMP="$PWD/../work/frames/f%u.ppm" (every 120th frame).
set -e
here=$(cd "$(dirname "$0")/.." && pwd)
work=${ASCENSION_WORK:-$here/../work}
mkdir -p "$work/disc" "$work/hdd0"
work=$(cd "$work" && pwd)

if [ ! -d "$work/disc/PS3_GAME" ]; then
    if [ -z "$ASCENSION_ISO" ]; then
        echo "The disc is not mounted at $work/disc: set ASCENSION_ISO to the .iso" >&2
        exit 1
    fi
    hdiutil attach -readonly -nobrowse -mountpoint "$work/disc" "$ASCENSION_ISO" >/dev/null
fi

cd "$work"
PS3_VFS_ROOT="$work/disc" PS3_HDD0_ROOT="$work/hdd0" \
    "$here/build/AscensionRecomp" "$here/input/EBOOT.ELF" > "$work/run.log" 2>&1 &
pid=$!
echo "AscensionRecomp running (pid $pid); log: $work/run.log"
wait $pid
