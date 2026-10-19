#!/bin/sh
# Run the Linux build. The disc is the extracted folder at work/disc
# (PS3_GAME/USRDIR must exist). The ELF is ascension/input/EBOOT.ELF.
set -e
here=$(cd "$(dirname "$0")/../.." && pwd)
work=${ASCENSION_WORK:-$here/../work}
mkdir -p "$work/disc" "$work/hdd0"
work=$(cd "$work" && pwd)
if [ ! -d "$work/disc/PS3_GAME" ]; then
    echo "The disc is not at $work/disc (extract the ISO there)" >&2
    exit 1
fi
exe="$here/build/linux/AscensionRecomp"
[ -x "$exe" ] || { echo "no $exe (scripts/linux/build.sh)" >&2; exit 1; }
cd "$work"
PS3_VFS_ROOT="$work/disc" PS3_HDD0_ROOT="$work/hdd0" \
    "$exe" "$here/input/EBOOT.ELF" > "$work/run.log" 2>&1 &
pid=$!
echo "AscensionRecomp running (pid $pid); log: $work/run.log"
wait $pid
