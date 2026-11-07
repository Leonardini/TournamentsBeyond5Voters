#!/bin/bash
# Build the cover engine.  No dependencies beyond a C compiler.
set -eu
cd "$(dirname "$0")"
CC=${CC:-cc}
$CC -O3 -w -o kcover kcover.c
echo "built $(pwd)/kcover"
# The leftover masks are decided one instance at a time by the placement engine,
# so this kit needs ../kinduce as well as its own kcover.  Same line as the other
# kits use, so there is one way to build it and not two.
[ -x ../kinduce ] || (cd .. && $CC -O3 -w -o kinduce kinduce.c && echo "  built ../kinduce")
[ -x ../kinduce ] || { echo "FATAL: no ../kinduce after build" >&2; exit 1; }
echo "have $(cd .. && pwd)/kinduce"
./kcover --n 7 --k 3 2>/dev/null | head -1 || true
