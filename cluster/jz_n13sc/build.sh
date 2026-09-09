#!/bin/bash
# Build the classification helpers.  The engine itself is ../kinduce.
set -eu
cd "$(dirname "$0")"
CC=${CC:-cc}
for f in rigid order_sym tri freearc; do $CC -O3 -o $f $f.c && echo "  built $f"; done
[ -x ../kinduce ] || (cd .. && $CC -O3 -w -o kinduce kinduce.c && echo "  built ../kinduce")
