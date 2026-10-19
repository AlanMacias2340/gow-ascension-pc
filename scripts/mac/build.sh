#!/bin/sh
# Configure (the first time) and build into build/mac (macOS; build.ps1 is the
# Windows one). Log in build/logs/build[-<name>].log; prints the time, the first
# error lines and the last line.
#
#   scripts/mac/build.sh            # build
#   scripts/mac/build.sh <name>     # same, log named build-<name>.log
#   RPCS3=1 scripts/mac/build.sh    # also link RPCS3's RSX (scripts/mac/build-gpu.sh first)
#
# Needs: brew install cmake ninja sdl2 glslang spirv-cross ffmpeg
# A build from scratch takes 20-40 minutes and wants 16 GB of memory; JOBS=<n>
# caps the parallel compiles (default: the CPU count, at most 6, as each lifted
# PPU unit takes 1-2 GB).
set -e
here=$(cd "$(dirname "$0")/../.." && pwd)
build="$here/build/mac"
logs="$here/build/logs"
mkdir -p "$logs"
log="$logs/build${1:+-$1}.log"

missing=""
for tool in cmake ninja; do command -v $tool >/dev/null 2>&1 || missing="$missing $tool"; done
for pkg in sdl2 glslang spirv-cross ffmpeg; do
    [ -d "$(brew --prefix 2>/dev/null)/opt/$pkg" ] || missing="$missing $pkg"
done
if [ -n "$missing" ]; then
    echo "missing:$missing  (brew install$missing)" >&2
    exit 1
fi

rpcs3=""
if [ "${RPCS3:-}" = 1 ]; then
    rpcs3="-DASCENSION_RPCS3_RSX=ON"
    gpu="$here/../work/gpu-build/libps3rsx.a"
    if [ ! -f "$gpu" ]; then
        echo "RPCS3=1 needs $gpu: run scripts/mac/build-gpu.sh first" >&2
        exit 1
    fi
fi
if [ ! -f "$build/build.ninja" ] || [ -n "$rpcs3" ]; then
    cmake -S "$here" -B "$build" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo \
        -DPS3RECOMP_FFMPEG_RUNTIME=ON -DPS3RECOMP_FFMPEG_INCLUDE_DIR="$(brew --prefix)/include" \
        $rpcs3 \
        > "$logs/configure.log" 2>&1 || { tail -n 20 "$logs/configure.log"; exit 1; }
fi

jobs=${JOBS:-$(sysctl -n hw.ncpu 2>/dev/null || nproc)}
[ -z "$JOBS" ] && [ "$jobs" -gt 6 ] && jobs=6
start=$(date +%s)
set +e
ninja -C "$build" -j "$jobs" > "$log" 2>&1
code=$?
set -e
secs=$(( $(date +%s) - start ))
if [ $code -eq 0 ]; then state=OK; else state=FAILED; fi
printf 'build %s in %d:%02d  (log: %s)\n' "$state" $((secs / 60)) $((secs % 60)) "$log"
grep -E "error:|FAILED:|fatal error|Undefined symbols" "$log" | head -n 15 | sed 's/^/  /'
echo "last line: $(tail -n 1 "$log")"
exit $code
