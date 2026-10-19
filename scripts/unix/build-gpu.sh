#!/bin/sh
# Build RPCS3's RSX (ps3recomp/gpu) into work/gpu-build.
# macOS: MoltenVK (brew install molten-vk vulkan-loader vulkan-headers).
# Linux: the Vulkan SDK or distro vulkan packages, and libgl.
# Then rebuild the game with RPCS3=1 scripts/mac/build.sh (or scripts/linux/build.sh).
set -e
here=$(cd "$(dirname "$0")/../.." && pwd)   # ascension/
top=$(cd "$here/.." && pwd)
kit=ps3kit; [ -d "$top/$kit" ] || kit=ps3recomp   # the toolkit beside this repo
gpu="$top/$kit/gpu"
build="$top/work/gpu-build"
logs="$here/build/logs"
mkdir -p "$logs"
log="$logs/gpu-build.log"

if [ "$(uname)" = Darwin ]; then
    prefix=$(brew --prefix 2>/dev/null || true)
    [ -n "$prefix" ] || { echo "brew not found" >&2; exit 1; }
    for pkg in molten-vk vulkan-loader vulkan-headers; do
        [ -d "$prefix/opt/$pkg" ] || { echo "missing $pkg (brew install molten-vk vulkan-loader vulkan-headers)" >&2; exit 1; }
    done
    prefix_arg="-DCMAKE_PREFIX_PATH=$prefix"
else
    prefix_arg=""
fi

echo "configuring ps3rsx -> $build"
cmake -S "$gpu" -B "$build" -G Ninja -DCMAKE_BUILD_TYPE=Release $prefix_arg \
    > "$logs/gpu-configure.log" 2>&1 || { tail -n 30 "$logs/gpu-configure.log"; exit 1; }

jobs=${JOBS:-$(sysctl -n hw.ncpu 2>/dev/null || nproc)}
[ -z "$JOBS" ] && [ "$jobs" -gt 6 ] && jobs=6
start=$(date +%s)
set +e
ninja -C "$build" -j "$jobs" > "$log" 2>&1
code=$?
set -e
secs=$(( $(date +%s) - start ))
if [ $code -eq 0 ]; then state=OK; else state=FAILED; fi
printf 'gpu build %s in %d:%02d  (log: %s)\n' "$state" $((secs / 60)) $((secs % 60)) "$log"
grep -E "error:|FAILED:|fatal error" "$log" | head -n 20 | sed 's/^/  /'
echo "last line: $(tail -n 1 "$log")"
exit $code
