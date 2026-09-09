#!/bin/bash
# Progress and result summary.  Safe to run at any time, including mid-job.
#   usage: aggregate.sh [resultsdir]
set -u
# Caller-supplied paths are relative to the CALLER'S cwd.  Resolve them BEFORE the cd
# below, or a path like "KInduceDFS/<kit>/results" passed from the repo root gets re-read
# relative to this script's own directory and everything lands in a DOUBLED path
# (KInduceDFS/KInduceDFS/...).  That happened on 2026-09-06 and nearly cost a 210 core-h
# run its results: the scheduler said COMPLETED, the aggregator said 0 done.
# Same idiom as jz_reproduce/run.sh, which has always been correct.
_ORIGPWD=$PWD
cd "$(dirname "$0")"
OUT=${1:-results_margin1}
if [ $# -ge 1 ]; then                     # only an ARGUMENT is caller-relative;
  case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac   # the default stays relative
fi                                        # to this script's own directory.
MOD=${N15_MOD:-6000}
[ -d "$OUT/done" ] || { echo "no results yet at $OUT"; exit 0; }
# Say something BEFORE the slow part.  Every figure below comes out of awk's END
# block, so the old version printed nothing at all until it had read every
# marker -- on a parallel filesystem with thousands of small files that is
# minutes of total silence, indistinguishable from a hang.  Announce the count
# first, then the roll-up.
printf "reading %s ...\n" "$OUT/done"
# Count MARKERS, not files.  done/ carries a tracked .gitkeep, so a file count
# came to 6,001 against MOD=6000 -- which sailed past the equality test below
# and reported "-1 residues outstanding" on a run that was in fact complete and
# exact.  The count now comes from the same read as the sums (awk counts the
# records it parses), so there is no second listing to disagree with the first
# and nothing that is not a marker can inflate it.
printf "summing markers ...\n"
# STREAM the markers instead of passing them as arguments.  `"$OUT"/done/r*`
# put one argument per residue on the command line, which at 6,000 long paths
# risks E2BIG, and -- if the glob matched nothing, whether through nullglob or a
# marker naming change -- left awk with no file at all, so it read stdin and
# blocked forever with no output.  find | awk cannot do either.
find "$OUT/done" -type f -exec cat {} + 2>/dev/null |
awk -v mod="$MOD" '
  /instances=/{d++}                      # one marker per record, and only markers
  {for(i=1;i<=NF;i++){split($i,a,"=");v[a[1]]+=a[2]}}
  END{
    printf "residues done    %d / %s (%.1f%%)\n", d+0, mod, mod?100*d/mod:0
    printf "instances        %d\n", v["instances"]
    printf "UNSAT            %d\n", v["unsat"]
    printf "ABORTED          %d\n", v["aborted"]
    printf "core-seconds     %d (%.1f core-h)\n", v["secs"], v["secs"]/3600
    if (d>0) printf "projected total  %.0f core-h\n", (v["secs"]/d)*mod/3600
    if (d==mod)     printf "COMPLETE         all %s residues\n", mod
    else if (d<mod) printf "INCOMPLETE       %d residues outstanding\n", mod-d
    else            printf "OVER-COUNT       %d markers for %s residues -- investigate\n", d, mod
  }'
echo "expected total   18,400,989,629 instances (OEIS A096368(7)); mean 3,066,832 per residue"
NU=$(cat "$OUT"/unsat/*.bits 2>/dev/null | wc -l | tr -d ' ')
if [ "${NU:-0}" -gt 0 ]; then
  echo
  echo "*** $NU NON-5-INDUCIBLE REGULAR n=15 TOURNAMENT(S) FOUND ***"
  echo "    send $OUT/unsat/*.bits back for independent verification"
else
  echo "UNSAT instances  none so far"
fi
A=$(ls "$OUT/log" 2>/dev/null | wc -l | tr -d ' ')
if [ "${A:-0}" -gt 0 ]; then
  echo "note: $A residue log(s) retained (those had unsat or aborted instances)"
fi
