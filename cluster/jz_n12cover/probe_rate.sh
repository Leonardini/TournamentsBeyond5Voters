#!/bin/bash
# Measure the ACTUAL per-instance rate on THIS machine before sizing anything.
#   usage: probe_rate.sh [n_instances]
# Every laptop figure in HANDOFF.md was taken while an 11-core job held the
# machine, so it is inflated and inconsistent (a 100-host probe implied 161
# ms/instance where a 2,000-host run implied 30).  Never size a campaign from a
# number measured under load, and never from a short probe -- both under-price.
set -eu
# Capture our own directory ABSOLUTELY, before any cd.  The previous idiom was
#     . "$(cd "$(dirname "$0")/.." && pwd)/gt_path.sh"
# evaluated AFTER `cd "$(dirname "$0")"`.  $0 keeps its original relative value, so
# from inside jz_n12cover it tried `cd KInduceDFS/jz_n12cover/..`, which does not
# exist; the subshell produced the EMPTY string and the source path became
# "/gt_path.sh".  Every residue of the 2026-09-07 array then died on `GT: unbound
# variable` -- 0 of 40,000 done.  Absolute-then-cd cannot fail that way.
_KITDIR=$(cd "$(dirname "$0")" && pwd)
cd "$_KITDIR"
N=${1:-4000}
[ -x ./kcover ] || ./build.sh
. "$_KITDIR/../gt_path.sh"                          # sets GT; see that file
: "${GT:?gt_path.sh did not set GT}"
[ -x "$GT" ] || { echo "gentourng not found at '$GT'; set GENTOURNG or NAUTY_DIR" >&2; exit 1; }

WORK=$(mktemp -d) || exit 1
trap 'rm -rf "$WORK"' EXIT
OUT="$WORK/out"; mkdir -p "$OUT/done" "$OUT/candidates" "$OUT/unresolved"
SKIP=${COVER_SKIP:-4096}; PBN=${COVER_PBN:-200}
T2=${TIER2_TIME:-120}; T3=${TIER3_TIME:-600}
KINDUCE=${KINDUCE:-$_KITDIR/../kinduce}
[ -x "$KINDUCE" ] || ./build.sh

# THE WHOLE PIPELINE, not just tier 1.  This script used to time the tier-1
# coverage run alone and project that over all 903,753,248 classes, which was
# wrong twice over: the converse halving means only about half of them are ever
# evaluated, and the masks tier 1 leaves uncovered are decided afterwards, one
# order-12 instance at a time.  Timing a third of the work and dividing by the
# wrong denominator can miss in either direction, so time what production runs.
#
# A mid-stream residue, not the head of the listing: the first classes are the
# near-transitive ones and behave nothing like typical (residue 0 costs 251 ms
# per host against residue 5000's 50 ms).
B0="$WORK/gen.bits"
"$GT" -q 11 "7919/2000000" 2>/dev/null | head -"$N" > "$B0"
NGEN=$(wc -l < "$B0" | tr -d ' ')
B="$WORK/hosts.bits"
if [ "${N12_NOHALVE:-0}" = 1 ]; then cp "$B0" "$B"
else ./converse_filter.sh 11 < "$B0" > "$B" || exit 1; fi
GOT=$(wc -l < "$B" | tr -d ' ')
[ "$GOT" -gt 0 ] || { echo "probe_rate: no hosts generated" >&2; exit 1; }

. "$_KITDIR/tiers.sh"
t0=$(date +%s.%N)
run_tiers "$B" "probe"
t1=$(date +%s.%N)

# D_11 = 903,753,248 (A000568).  Only about half are evaluated, one host of each
# converse pair, so the denominator for a rate measured on SCREENED hosts is
# D_11/2 -- and this projection is deliberately printed both ways, because the
# figure that gets quoted should not depend on remembering which one it was.
awk -v g="$GOT" -v ng="$NGEN" -v a="$A1" -v l="$NLEFT" -v f2="$FIX2" -v f3="$FIX3" \
    -v c="$CAND" -v u="$UNRES" -v t0="$t0" -v t1="$t1" 'BEGIN{
  d11 = 903753248; el = t1 - t0; ms = 1000*el/g
  printf "generated=%d  screened=%d (factor %.2f)  wall=%.1fs\n", ng, g, ng/g, el
  printf "tier1 ALL=%d (%.1f%%)  leftover masks=%d (%.2f per host)  settled: margin1=%d majority=%d\n",
         a, 100*a/g, l, l/g, f2, f3
  if (u > 0) printf "  WARNING: %d instance(s) hit their time cap -- the rate is a floor, not the cost\n", u
  if (c > 0) printf "  *** %d CANDIDATE(S) in the probe -- inspect before anything else\n", c
  printf "%.2f ms per screened host\n", ms
  printf "PROJECTED, this machine: %.0f core-h for the %d screened hosts (half of D_11 = %d)\n",
         (d11/2)*ms/1000/3600, d11/2, d11
  printf "  the cluster measured 2.6-3.3x slower than the laptop on this project, so multiply\n"
  printf "  by that if this probe is running on a login node rather than a compute node\n"
}'
