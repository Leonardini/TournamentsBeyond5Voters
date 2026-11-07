#!/bin/bash
# Materialise the order-11 listing as EVENLY SIZED shards.
#
# Generation is 2.01 us/instance = 0.8 core-h for all 903,753,248, against
# thousands of core-h for evaluation, so it is free.  Doing it once buys:
#   * EVEN work units -- we slice the FILE, not gentourng's tree.  gentourng
#     splits by input chunk and its residues are wildly uneven (res=7 -> 8,957
#     instances, res=1234 -> 164,154, an 18x spread) and stop subdividing past
#     some MOD, so sizing an array job off it is guesswork.
#   * retries that do not regenerate -- a tier-3 time-out currently re-runs
#     gentourng over the whole residue for nothing.
#   * no nauty needed on the compute nodes.
# Cost: ~51 GB raw (56 bytes x 903,753,248), ~12-15 GB gzipped.
#
# SKIP THIS ENTIRELY if a previous campaign already left the listing on disk
# (see HANDOFF.md: there may be one under jz_11).  Point N12_LIST at it instead,
# but verify the format first -- one 55-character upper-triangular bit string
# per line, and 903,753,248 lines.  A different bit order would silently
# evaluate the wrong tournaments.
#
#   usage: generate.sh <outdir> [lines_per_shard] [gen_mod]
set -eu
# Caller-supplied paths are relative to the CALLER'S cwd.  Resolve them BEFORE the cd
# below, or a path like "KInduceDFS/<kit>/results" passed from the repo root gets re-read
# relative to this script's own directory and everything lands in a DOUBLED path
# (KInduceDFS/KInduceDFS/...).  That happened on 2026-09-06 and nearly cost a 210 core-h
# run its results: the scheduler said COMPLETED, the aggregator said 0 done.
# Same idiom as jz_reproduce/run.sh, which has always been correct.
_ORIGPWD=$PWD
cd "$(dirname "$0")"
OUT=${1:?usage: generate.sh <outdir> [lines_per_shard] [gen_mod]}
case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac
PER=${2:-45000}
GMOD=${3:-2000}
if [ -n "${GENTOURNG:-}" ]; then GT="$GENTOURNG"
elif command -v gentourng >/dev/null 2>&1; then GT="$(command -v gentourng)"
else GT="$(cd ../.. && pwd)/nauty/gentourng"; fi
mkdir -p "$OUT"
echo "generating into $OUT, $PER lines per shard, gentourng split $GMOD"
for ((R=0; R<GMOD; R++)); do
  "$GT" 11 "$R/$GMOD" 2>/dev/null
done | split -l "$PER" -d -a 6 - "$OUT/sh_"
N=$(ls "$OUT"/sh_* | wc -l | tr -d ' ')
TOT=$(cat "$OUT"/sh_* | wc -l | tr -d ' ')
echo "$N shards, $TOT instances" | tee "$OUT/MANIFEST"
[ "$TOT" = 903753248 ] || echo "WARNING: expected 903,753,248 instances, got $TOT" >&2
