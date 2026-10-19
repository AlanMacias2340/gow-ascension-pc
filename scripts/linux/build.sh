#!/bin/sh
# Configure (the first time) and build into build/linux.
#   scripts/linux/build.sh            # build
#   scripts/linux/build.sh <name>     # log named build-<name>.log
#   CONFIGURE=1 scripts/linux/build.sh  # run CMake again (after changing .env)
#
# Settings from .env (scripts/unix/env.sh); RPCS3_RSX=1 there links RPCS3's RSX
# (scripts/linux/build-gpu.sh first).
#
# Needs cmake, ninja, and the SDL2, glslang, spirv-cross and FFmpeg dev packages.
# A build from scratch takes 20-40 minutes and wants 16 GB of memory.
set -e
here=$(cd "$(dirname "$0")/../.." && pwd)
. "$here/scripts/unix/env.sh"
build="$here/build/linux"
logs="$here/build/logs"
mkdir -p "$logs"
log="$logs/build${1:+-$1}.log"

missing=""
for tool in cmake ninja pkg-config; do command -v $tool >/dev/null 2>&1 || missing="$missing $tool"; done
if [ -n "$missing" ]; then
    echo "missing:$missing" >&2
    exit 1
fi

rpcs3="-DASCENSION_RPCS3_RSX=OFF"
if [ "$RPCS3_RSX" = 1 ]; then
    rpcs3="-DASCENSION_RPCS3_RSX=ON -DASCENSION_RPCS3_BUILD=$GPU_BUILD_DIR"
    if [ ! -f "$GPU_BUILD_DIR/libps3rsx.a" ]; then
        echo "RPCS3_RSX=1 needs $GPU_BUILD_DIR/libps3rsx.a: run scripts/linux/build-gpu.sh first" >&2
        exit 1
    fi
fi

if [ ! -f "$build/build.ninja" ] || [ "${CONFIGURE:-}" = 1 ]; then
    cmake -S "$here" -B "$build" -G Ninja -DCMAKE_BUILD_TYPE="$BUILD_TYPE" -DPS3RECOMP_DIR="$PS3KIT_DIR" \
        -DPS3RECOMP_FFMPEG_RUNTIME=ON ${FFMPEG_INCLUDE_DIR:+-DPS3RECOMP_FFMPEG_INCLUDE_DIR=$FFMPEG_INCLUDE_DIR} $rpcs3 \
        > "$logs/configure.log" 2>&1 || { tail -n 20 "$logs/configure.log"; exit 1; }
fi

jobs=${JOBS:-$(nproc 2>/dev/null || echo 4)}
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
