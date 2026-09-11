#!/bin/sh
# Node-for-node regression of the consolidated engine against the historical
# version that ORIGINALLY produced each published result.
#
# WHY THIS EXISTS.  `kinduce.c` is a consolidation; not one published number was
# produced by it.  Every result names its original version in REPRODUCE.md, and
# until this ran, "the two agree" was an assertion.  Verdicts would replicate
# under any correct implementation -- that is the paper's claim -- but node
# counts are the sharper test, because they pin the tie-breaking, the variable
# order and the domain refinement, any of which can differ silently between two
# programs that reach the same verdict.
#
#   usage: regression.sh [--fast]
#
# Each case runs the PUBLISHED command line of REPRODUCE.md with its base-state
# range narrowed, under both binaries, and requires the WHOLE RESULT line to
# agree apart from `time=`, plus the SLICE line's `capped=`.  That is every
# counter the engine keeps: nodes, sols, base_states, dom_calls, dom_nodes,
# mrv_fails, top0_fails, bound_fails, fas_fails and refine_tuples.  Narrowing
# the range is sound because base states are independent -- the same fact every
# distributed run in this repository rests on.
#
# Ranges are chosen so each case does real work in seconds; where a break kills
# every state in the cheap window, the comparison is still substantive, because
# `dom_nodes` and `top0_fails` then carry it.  --fast keeps only the cases that
# finish in about a second, for use inside a gate.
#
# Single-threaded and sequential: safe beside a campaign holding the core budget.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
# The hosts sit beside the engine in the working repository and under
# tournaments/ in the reproduction package.  Resolve rather than assume: the
# first version of this script ran fine in the working tree and failed in the
# package with "clang: error: no input files", which names neither the missing
# host nor the missing source.
SRC=$HERE
[ -f "$SRC/kinduce.c" ] || SRC="$HERE/.."
BITS=$HERE
[ -f "$BITS/p27_paley.bits" ] || BITS="$SRC/tournaments"
[ -f "$BITS/p27_paley.bits" ] || BITS="$SRC/../tournaments"
if [ ! -f "$SRC/kinduce.c" ]; then
  echo "FATAL cannot find kinduce.c from $HERE" >&2; exit 1
fi
if [ ! -f "$BITS/p27_paley.bits" ]; then
  echo "FATAL cannot find the .bits hosts from $HERE (tried $HERE, $SRC/tournaments)" >&2
  exit 1
fi
FAST=0
[ "${1:-}" = "--fast" ] && FAST=1
CC=${CC:-cc}
BIN=$(mktemp -d) || exit 1
trap 'rm -rf "$BIN"' EXIT

build() {                                  # build <name> <source>
  $CC -O2 -o "$BIN/$1" "$2" 2>"$BIN/$1.err" && return 0
  # Several historical versions predate a warning-free build.  -w is not a
  # correctness compromise; a version that still fails is REPORTED, not skipped
  # silently, because a quietly absent case reads exactly like a passing one.
  $CC -O2 -w -o "$BIN/$1" "$2" 2>"$BIN/$1.err"
}

fields() {                                 # the comparable part of a run's output
  awk '/^RESULT/{ s=""; for(i=1;i<=NF;i++) if($i !~ /^time=/) s = s $i " "; print s }
       /^SLICE/ { for(i=1;i<=NF;i++) if($i ~ /^capped=/) print $i }
       /^BATCH_SUMMARY/{ s=""; for(i=1;i<=NF;i++) if($i !~ /^wall=/) s = s $i " "; print s }' "$1"
}

pass=0; fail=0; skip=0

case_run() {                               # case_run <cost> <label> <version> <args...>
  cost=$1; label=$2; ver=$3; shift 3
  [ "$FAST" = 1 ] && [ "$cost" != cheap ] && return
  src="$SRC/versions/$ver.c"
  if [ ! -f "$src" ]; then
    printf '  SKIP  %-40s %s.c is not in versions/\n' "$label" "$ver"
    skip=$((skip+1)); return
  fi
  if ! build "$ver" "$src"; then
    printf '  SKIP  %-40s %s.c does not build here\n' "$label" "$ver"
    sed 's/^/          /' "$BIN/$ver.err" | head -3
    skip=$((skip+1)); return
  fi
  ( cd "$BITS" && "$BIN/cons"  "$@" ) > "$BIN/a.out" 2>&1
  ( cd "$BITS" && "$BIN/$ver" "$@" ) > "$BIN/b.out" 2>&1
  fa=$(fields "$BIN/a.out"); fb=$(fields "$BIN/b.out")
  if [ -z "$(printf '%s' "$fa" | tr -d ' \n')" ]; then
    printf '  SKIP  %-40s the consolidated engine produced no RESULT line\n' "$label"
    sed 's/^/          /' "$BIN/a.out" | tail -3
    skip=$((skip+1)); return
  fi
  if [ "$fa" = "$fb" ]; then
    printf '  ok    %-40s %s\n' "$label" "$ver"
    # echo, not printf '%s': the field block ends without a newline, and gluing
    # the next case's heading onto the last counter line made the log unreadable
    # and ungreppable.
    echo "$fa" | sed 's/^/          /'
    pass=$((pass+1))
  else
    printf '  FAIL  %-40s %s\n' "$label" "$ver"
    printf '          consolidated: %s\n' "$(printf '%s' "$fa" | tr '\n' '|')"
    printf '          %-12s  %s\n' "$ver:" "$(printf '%s' "$fb" | tr '\n' '|')"
    fail=$((fail+1))
  fi
}

echo "consolidated kinduce.c vs the version that produced each published result"
echo "compared: every counter on the RESULT line except time=, plus capped="
[ "$FAST" = 1 ] && echo "(--fast: only the cases that finish in about a second)"
echo

build cons "$SRC/kinduce.c" || {
  echo "FATAL kinduce.c does not build"; sed 's/^/  /' "$BIN/cons.err" | head; exit 1; }

case_run cheap "P23 anchor A, N(5) <= 23"        kinduce16 \
  --paley 23 --k 5 --margin majority --order mrv --inc --pool-mb 512 \
  --base 0 1 2 5 11 --top0rr 2 5 --bs-from 0 --bs-to 200
case_run cheap "P23 anchor B, a different break"  kinduce22 \
  --paley 23 --k 5 --margin majority --order mrv --inc --pool-mb 512 \
  --base 0 1 2 6 7 --toppair 1 2 6 2 --bs-from 0 --bs-to 200
case_run cheap "P27 not 5-inducible"              kinduce22 \
  --bits p27_paley.bits --n 27 --k 5 --margin majority --order mrv --inc \
  --pool-mb 512 --base 0 1 2 3 14 --toppair 0 14 2 1 --bs-from 0 --bs-to 4
case_run cheap "P31 not 5-inducible"              kinduce22 \
  --paley 31 --k 5 --margin majority --order mrv --inc --pool-mb 512 \
  --base 0 1 2 3 6 --toppair 2 3 0 3 --bs-from 2000 --bs-to 2003
case_run dear  "P43 - v, not vertex-critical"     kinduce24 \
  --bits p43_minus1v.bits --n 42 --k 5 --max-margin 3 --order mrv --inc \
  --pool-mb 512 --base 0 1 2 3 10 --toporb 0 1 --bs-from 0 --bs-to 1
case_run dear  "P31 - v, not vertex-critical"     kinduce24 \
  --bits p31_minus1v.bits --n 30 --k 5 --max-margin 3 --order mrv --inc \
  --pool-mb 512 --base 0 1 2 3 12 --toporb 0 2 --bs-from 0 --bs-to 1
case_run dear  "P19 unit margin, certified half"  kinduce24 \
  --paley 19 --k 5 --max-margin 1 --order mrv --inc --base 0 1 2 3 5 \
  --bs-from 0 --bs-to 10
case_run dear  "dr19_g2 unit margin"              kinduce24 \
  --bits dr19_g2.bits --n 19 --k 5 --max-margin 1 --order mrv --inc \
  --bs-from 0 --bs-to 10
case_run dear  "margin-1 family, P23 - v cell"    kinduce24 \
  --bits p23_minus1v.bits --n 22 --k 5 --margin exact --order mrv --inc \
  --pool-mb 512 --base 0 1 2 3 5 --bs-from 0 --bs-to 20
# The one POSITIVE case: every other comparison above is a refutation, so a bug
# that lost witnesses would agree with itself.  This is the slice that actually
# produced the published Paley(23) - v witness.
case_run dear  "P23 - v IS 5-inducible (witness)"  kinduce21 \
  --bits p23_minus1v.bits --n 22 --k 5 --margin majority --order mrv --inc \
  --pool-mb 512 --toporb 0 4 --bs-from 6560 --bs-to 6564

# Batch mode has its own summary line and its own code path.  The chunk is
# regenerated rather than shipped: `gentourng -d7 -D7 15` is deterministic, so
# the same 40 regular 15-vertex tournaments come back anywhere.
SW=${SOFTWARE_DIR:-$HOME/Downloads/DownloadedSoftware}
GT=${GENTOURNG:-$SW/nauty2_8_6/gentourng}
[ -x "$GT" ] || GT=$(command -v gentourng 2>/dev/null || true)
if [ -n "$GT" ] && [ -x "$GT" ]; then
  "$GT" -d7 -D7 15 2>/dev/null | head -40 > "$BIN/n15.d6"
  case_run cheap "regular n=15, batch mode"       kinduce20 \
    --batch "$BIN/n15.d6" --n 15 --k 5 --margin exact --order mrv --inc
else
  printf '  SKIP  %-40s gentourng not found for the batch chunk\n' "regular n=15, batch mode"
  skip=$((skip+1))
fi

echo
printf 'passed %d   failed %d   skipped %d\n' "$pass" "$fail" "$skip"
[ "$fail" -eq 0 ] || exit 1
exit 0
