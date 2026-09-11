#!/bin/bash
# Build the consolidated engine for the blind T^e scan.  Seconds-long compile.
set -e
cd "$(dirname "$0")/.."
echo "== kinduce (consolidated engine) =="
gcc -O2 -w -o kinduce kinduce.c
./kinduce 2>&1 | head -1 || true      # prints its usage line; that is expected
echo
echo "build OK.  Now run:  ./jz_p23arc/selftest.sh   (MANDATORY before submitting)"
