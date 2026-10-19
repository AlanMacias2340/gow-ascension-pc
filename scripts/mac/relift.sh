#!/bin/sh
# macOS entry for the shared lifter. See scripts/unix/relift.sh.
exec "$(cd "$(dirname "$0")/.." && pwd)/unix/relift.sh" "$@"
