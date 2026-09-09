#!/bin/bash
# Screen ONE residue class of the regular n=15 tournaments.
#   usage: screen_residue.sh <res> <mod> <outdir> [margin]
# Writes, per residue, and ONLY on success (so a wall-kill never leaves a
# residue looking done):
#   $outdir/done/r<res>       marker with the counts   <- resume key
#   $outdir/unsat/r<res>.bits the non-inducible instances, if any  <- the prize
#   $outdir/log/r<res>.log    engine summary
set -u
# Caller-supplied paths are relative to the CALLER'S cwd.  Resolve them BEFORE the cd
# below, or a path like "KInduceDFS/<kit>/results" passed from the repo root gets re-read
# relative to this script's own directory and everything lands in a DOUBLED path
# (KInduceDFS/KInduceDFS/...).  That happened on 2026-09-06 and nearly cost a 210 core-h
# run its results: the scheduler said COMPLETED, the aggregator said 0 done.
# Same idiom as jz_reproduce/run.sh, which has always been correct.
_ORIGPWD=$PWD
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
# locate gentourng: explicit override, then a loaded module on PATH, then a
# local build.  Nauty already exists on JZ, so the PATH/override paths are the
# normal ones and nothing is fetched.
if [ -n "${GENTOURNG:-}" ]; then GT="$GENTOURNG"
elif [ -n "${NAUTY_DIR:-}" ] && [ -x "${NAUTY_DIR}/gentourng" ]; then GT="${NAUTY_DIR}/gentourng"
elif command -v gentourng >/dev/null 2>&1; then GT="$(command -v gentourng)"
else GT="$ROOT/nauty/gentourng"; fi
RES=$1; MOD=$2; OUT=$3; MARGIN=${4:-exact}
case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac
mkdir -p "$OUT/done" "$OUT/unsat" "$OUT/log"
[ -f "$OUT/done/r$RES" ] && { echo "residue $RES already done, skipping"; exit 0; }

WORK=${JOBSCRATCH:-${SLURM_TMPDIR:-/tmp}}
B="$WORK/reg15_$RES.bits"
trap 'rm -f "$B"' EXIT

t0=$SECONDS
$GT -d7 -D7 15 "$RES/$MOD" 2>/dev/null > "$B"
NINST=$(wc -l < "$B" | tr -d ' ')
[ "$NINST" -eq 0 ] && { echo "res=$RES instances=0" > "$OUT/done/r$RES"; exit 0; }

../kinduce20 --batch "$B" --n 15 --k 5 --margin "$MARGIN" --order mrv --inc \
    > "$OUT/log/r$RES.log" 2>&1
SUM=$(grep BATCH_SUMMARY "$OUT/log/r$RES.log")
[ -z "$SUM" ] && { echo "res=$RES ENGINE PRODUCED NO SUMMARY -- not marking done" >&2; exit 1; }

NU=$(echo "$SUM" | sed -n 's/.*UNSAT=\([0-9]*\).*/\1/p')
NA=$(echo "$SUM" | sed -n 's/.*ABORTED=\([0-9]*\).*/\1/p')
# recover the actual bit strings of any UNSAT instance (BATCH lines are 0-indexed)
if [ "${NU:-0}" -gt 0 ]; then
  grep -E '^BATCH [0-9]+ UNSAT' "$OUT/log/r$RES.log" | awk '{print $2+1}' \
    | while read -r L; do sed -n "${L}p" "$B"; done > "$OUT/unsat/r$RES.bits"
fi
# keep per-residue logs only when interesting; they are otherwise pure bulk
if [ "${NU:-0}" -eq 0 ] && [ "${NA:-0}" -eq 0 ]; then rm -f "$OUT/log/r$RES.log"; fi

echo "res=$RES instances=$NINST unsat=${NU:-0} aborted=${NA:-0} secs=$((SECONDS-t0))" \
     > "$OUT/done/r$RES"
cat "$OUT/done/r$RES"
