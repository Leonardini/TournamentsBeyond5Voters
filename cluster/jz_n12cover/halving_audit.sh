#!/bin/bash
# Re-run ONLY the generation and the converse halving for one residue, and record
# what it sees.  No tiers, no solving: this is a post-mortem on where the hosts
# went, not a re-screening.
#
# WHY.  On 2026-09-12 the completed census reported 903,753,248 order-11 classes
# generated and 443,771,294 hosts kept.  Kept must be at least D11/2 = 451,876,624
# -- one host of every converse pair survives the rule "keep iff canon(T) <=
# canon(conv(T))", because the two decisions on a pair read the same two canonical
# forms in opposite order.  Being 8,105,330 below that floor means hosts VANISHED,
# and neither worker checked for it: the filter read its input and wrote its
# output through paths nothing reconciled against the generator's count.
#
# This re-derives the two numbers per residue so they can be compared against the
# markers.  A residue whose audited kept count EXCEEDS its marker's instances= is
# a residue that lost hosts, and it names exactly what has to be re-screened.
#
# It also counts the self-converse hosts, which is the only unknown in the global
# identity kept == (D11 + S11)/2.  Summed over the residues it MEASURES S11, so
# the census gate can stop trusting a written-down constant.
#
# COST.  Generation plus two labelg canonical forms per host, and nothing else:
# about 6 us per host, so the whole census is a few core-hours against the 9,905
# the screening took.
#
#   usage: halving_audit.sh <res> <mod> <outdir>
set -u
_KITDIR=$(cd "$(dirname "$0")" && pwd)
_ORIGPWD=$PWD
cd "$_KITDIR"
RES=$1; MOD=$2; OUT=$3
case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac
. "$_KITDIR/../gt_path.sh"
: "${GT:?gt_path.sh did not set GT}"
: "${LABELG:?no labelg -- the audit is ABOUT the halving, so it cannot be skipped}"
mkdir -p "$OUT/audit"
[ -f "$OUT/audit/r$RES" ] && { echo "residue $RES already audited"; exit 0; }

# Audit temporaries go in the JOB scratch, deliberately: $TMPDIR is the prime
# suspect for the loss this script exists to find, so do not depend on it.
WORK=${JOBSCRATCH:-${SLURM_TMPDIR:-/tmp}}
B="$WORK/audit_$RES.bits"; CFC="$WORK/audit_$RES.counts"; ERR="$WORK/audit_$RES.err"
trap 'rm -f "$B" "$CFC" "$ERR"' EXIT
export TMPDIR="$WORK"

"$GT" 11 "$RES/$MOD" 2>"$ERR" > "$B" || {
  echo "FATAL residue $RES: gentourng exit $?" >&2; sed 's/^/    /' "$ERR" >&2; exit 1; }
NGEN=$(wc -l < "$B" | tr -d ' ')
ZK=$(sed -nE 's/^>Z ([0-9]+) graphs generated.*/\1/p' "$ERR" | tail -1)
[ -n "$ZK" ] && [ "$ZK" -eq "$NGEN" ] || {
  echo "FATAL residue $RES: banner says '${ZK:-<none>}' graphs, received $NGEN" >&2; exit 1; }

if [ "$NGEN" -eq 0 ]; then
  echo "res=$RES generated=0 kept=0 self=0" > "$OUT/audit/r$RES"; cat "$OUT/audit/r$RES"; exit 0
fi
CF_COUNTS="$CFC" ./converse_filter.sh 11 < "$B" > /dev/null 2>"$ERR" || {
  echo "FATAL residue $RES: converse filter failed" >&2; sed 's/^/    /' "$ERR" >&2; exit 1; }
NIN=$(sed -nE 's/.*in=([0-9]+).*/\1/p' "$CFC")
NKEPT=$(sed -nE 's/.*kept=([0-9]+).*/\1/p' "$CFC")
NSELF=$(sed -nE 's/.*self=([0-9]+).*/\1/p' "$CFC")
[ "$NIN" = "$NGEN" ] || {
  echo "FATAL residue $RES: generated $NGEN but the filter received $NIN -- IT IS STILL LOSING HOSTS" >&2
  exit 1; }
echo "res=$RES generated=$NGEN kept=$NKEPT self=$NSELF" > "$OUT/audit/r$RES"
cat "$OUT/audit/r$RES"
