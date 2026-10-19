#!/bin/sh
exec "$(cd "$(dirname "$0")/.." && pwd)/unix/build-gpu.sh" "$@"
