#!/bin/bash
# Evaluate ONE shard of the order-11 listing.  Reads a pre-generated file instead
# of calling gentourng, so work units are even and a retry does not regenerate.
# The decision pipeline is NOT duplicated here: both workers source tiers.sh, so
# "identical logic to screen_residue.sh" is now true by construction rather than
# by a comment that nothing checked.
#
#   usage: eval_shard.sh <shardfile> <outdir>
set -u
# Caller-supplied paths are relative to the CALLER'S cwd.  Resolve them BEFORE the cd
# below, or a path like "KInduceDFS/<kit>/results" passed from the repo root gets re-read
# relative to this script's own directory and everything lands in a DOUBLED path
# (KInduceDFS/KInduceDFS/...).  That happened on 2026-09-06 and nearly cost a 210 core-h
# run its results: the scheduler said COMPLETED, the aggregator said 0 done.
# Same idiom as jz_reproduce/run.sh, which has always been correct.
_KITDIR=$(cd "$(dirname "$0")" && pwd)
_ORIGPWD=$PWD
cd "$_KITDIR"
SHARD=$1; OUT=$2
case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac
ID=$(basename "$SHARD")
SKIP=${COVER_SKIP:-4096}; PBN=${COVER_PBN:-200}
T2=${TIER2_TIME:-120}; T3=${TIER3_TIME:-600}   # PER-INSTANCE caps; see tiers.sh
KINDUCE=${KINDUCE:-$_KITDIR/../kinduce}
mkdir -p "$OUT/done" "$OUT/candidates" "$OUT/unresolved"
# A MARKER IS ONLY TRUSTED IF IT CARRIES generated=.  The vacuous run of
# 2026-09-07 wrote 40,000 markers claiming success having examined nothing, and
# because a unit with a marker is skipped, every resubmit after it was a no-op
# until someone remembered to delete them by hand.  generated= did not exist
# then, and it is written only by a pipeline that actually generated hosts, so it
# is exactly the right discriminator -- and this makes the recovery automatic
# instead of a step in COMMANDS.md that has to be remembered.
if [ -f "$OUT/done/$ID" ]; then
  if grep -q "generated=" "$OUT/done/$ID"; then echo "$ID already done"; exit 0; fi
  echo "$ID: marker predates generated= (vacuous run or old pipeline) -- redoing" >&2
fi

WORK=${JOBSCRATCH:-${SLURM_TMPDIR:-/tmp}}
# AND THE FILTER'S TEMPORARIES GO THERE TOO.  converse_filter.sh calls mktemp -d,
# which obeys $TMPDIR and otherwise lands in /tmp -- a small node-local filesystem
# shared by every array task on the node, NOT the scratch sized for this job.  On
# 2026-09-12 that filesystem filled: 2,874 "No space left on device" errors across
# the campaign, 52 residues truncated and 46 that received nothing at all, and
# 15,690,562 order-11 classes never reached the filter, let alone the screening.
# The assertions below turn that into a hard failure; this line stops it happening.
export TMPDIR="$WORK"
trap 'rm -f "$WORK/${ID}_screened" "$WORK"/*_$ID.log "$WORK"/unc_$ID "$WORK"/ext_$ID.bits "$WORK"/ext3_$ID.bits "$WORK"/key_$ID "$WORK"/u2_$ID "$WORK"/c3_$ID' EXIT
t0=$SECONDS
NGEN=$(wc -l < "$SHARD" | tr -d ' ')

# THE CONVERSE HALVING APPLIES HERE TOO, and was missing: this worker handed its
# shard straight to the pipeline and so screened both members of every converse
# pair, twice the necessary work.  A shard is not closed under the converse map,
# but the rule "keep iff canon(T) <= canon(conv(T))" depends only on the
# isomorphism class, and the shards partition every class, so exactly one of each
# pair survives across the campaign -- the same argument as for residues, and the
# same reason the keep rate of a single shard means nothing on its own.
# generate.sh writes the FULL census (verify_listing.sh checks the line count is
# D_11 exactly), so generated= summed over shards is D_11 and the census gate in
# aggregate.sh reads the same way for both workers.
HOSTS="$WORK/${ID}_screened"
if [ "${N12_NOHALVE:-0}" = 1 ]; then
  cp "$SHARD" "$HOSTS"
else
  CFC="$WORK/${ID}.cfcounts"
  CF_COUNTS="$CFC" ./converse_filter.sh 11 stats < "$SHARD" > "$HOSTS" || {
    echo "FATAL $ID: converse filter failed -- not marking done" >&2; exit 1; }
fi
NINST=$(wc -l < "$HOSTS" | tr -d ' ')
[ "$NINST" -le "$NGEN" ] || { echo "FATAL $ID: filter kept $NINST of $NGEN -- a filter cannot add" >&2; exit 1; }
# The same two assertions screen_residue.sh makes, for the same reason: the filter
# reads its input and writes its output through an unchecked $TMPDIR, and the
# 2026-09-12 census came back BELOW the D11/2 floor, which only vanished hosts can
# explain.  See screen_residue.sh for the argument.  Shards do not go through
# gentourng, so $NGEN here is the shard's own line count.
NSELF=0
if [ "${N12_NOHALVE:-0}" != 1 ]; then
  NIN=$(sed -nE 's/.*in=([0-9]+).*/\1/p'   "$CFC"); NKEPT=$(sed -nE 's/.*kept=([0-9]+).*/\1/p' "$CFC")
  NSELF=$(sed -nE 's/.*self=([0-9]+).*/\1/p' "$CFC"); rm -f "$CFC"
  [ -n "$NIN" ] && [ -n "$NKEPT" ] && [ -n "$NSELF" ] || {
    echo "FATAL $ID: the converse filter reported no counts" >&2; exit 1; }
  [ "$NIN" -eq "$NGEN" ] || {
    echo "FATAL $ID: shard has $NGEN hosts but the filter received only $NIN -- truncated \$TMPDIR" >&2; exit 1; }
  [ "$NINST" -eq "$NKEPT" ] || {
    echo "FATAL $ID: the filter kept $NKEPT hosts but wrote $NINST -- truncated \$JOBSCRATCH" >&2; exit 1; }
fi
echo "shard=$ID generated=$NGEN screened=$NINST"
[ "$NINST" -eq 0 ] && { echo "shard=$ID generated=$NGEN instances=0 self=0 tier1all=0 leftover=0 tier2fixed=0 tier3fixed=0 candidates=0 secs=0" > "$OUT/done/$ID"; exit 0; }

. "$_KITDIR/tiers.sh"          # the pipeline itself, shared with screen_residue.sh
run_tiers "$HOSTS" "$ID"

if [ "$UNRES" -gt 0 ]; then
  echo "$ID UNRESOLVED=$UNRES (budget, not a result) -- left unmarked for retry" >&2
  exit 1
fi
echo "shard=$ID generated=$NGEN instances=$NINST self=$NSELF tier1all=$A1 leftover=$NLEFT tier2fixed=$FIX2 tier3fixed=$FIX3 candidates=$CAND secs=$((SECONDS-t0))" > "$OUT/done/$ID"
cat "$OUT/done/$ID"
