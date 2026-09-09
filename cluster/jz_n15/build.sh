#!/bin/bash
# Build both binaries on Jean-Zay.  Run on a COMPUTE node or the login node --
# these are seconds-long compiles, not compute.
set -e
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)

echo "== kinduce20 (the screening engine) =="
# The 25 historical engines were archived to ../versions/ on 2026-09-04.  This
# kit deliberately still builds kinduce20: the selftest verdicts below were
# established with it, and the consolidated ../kinduce.c has not yet been
# regression-tested in --batch mode.  Migrate only after that passes.
gcc -O2 -w -o ../kinduce20 ../versions/kinduce20.c
../kinduce20 2>&1 | head -1 || true

echo "== nauty gentourng (the instance generator) =="
# Nauty is present on JZ.  If it is not on PATH, set GENTOURNG (or NAUTY_DIR)
# and this step is a no-op; only then does it fall back to fetching a copy.
# nauty is NOT in the repo (upstream tarball).  Fetch and build it once.
# locate gentourng: explicit override, then a loaded module on PATH, then a
# local build.  Nauty already exists on JZ, so the PATH/override paths are the
# normal ones and nothing is fetched.
if [ -n "${GENTOURNG:-}" ]; then GT="$GENTOURNG"
elif [ -n "${NAUTY_DIR:-}" ] && [ -x "${NAUTY_DIR}/gentourng" ]; then GT="${NAUTY_DIR}/gentourng"
elif command -v gentourng >/dev/null 2>&1; then GT="$(command -v gentourng)"
else GT="$ROOT/nauty/gentourng"; fi
if [ ! -x "$GT" ]; then
  mkdir -p "$ROOT/nauty" && cd "$ROOT/nauty"
  if [ ! -f nauty2_8_6.tar.gz ]; then
    curl -fLO https://pallini.di.uniroma1.it/nauty2_8_6.tar.gz
  fi
  tar xzf nauty2_8_6.tar.gz --strip-components=1
  ./configure >/dev/null && make gentourng >/dev/null
fi
"$GT" -help 2>&1 | head -3
echo
echo "build OK.  Now run:  ./selftest.sh   (MANDATORY before submitting)"
