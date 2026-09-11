#!/bin/bash
# Progress and completeness for the blind T^e scan.  Safe to run mid-job.
set -u
# Caller-supplied paths are relative to the CALLER'S cwd.  Resolve them BEFORE the cd
# below, or a path like "KInduceDFS/<kit>/results" passed from the repo root gets re-read
# relative to this script's own directory and everything lands in a DOUBLED path
# (KInduceDFS/KInduceDFS/...).  That happened on 2026-09-06 and nearly cost a 210 core-h
# run its results: the scheduler said COMPLETED, the aggregator said 0 done.
# Same idiom as jz_reproduce/run.sh, which has always been correct.
_ORIGPWD=$PWD
cd "$(dirname "$0")/.."
OUT=${1:-jz_p23arc/results}
if [ $# -ge 1 ]; then                     # only an ARGUMENT is caller-relative;
  case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac   # the default stays relative
fi                                        # to this script's own directory.
N=8031
done_n=$(ls "$OUT/done" 2>/dev/null | wc -l | tr -d ' ')
echo "base states screened : $done_n / $N"
if [ -f "$OUT/WITNESSES.txt" ]; then
  echo "*** WITNESS FOUND at base state(s): $(tr '\n' ' ' < "$OUT/WITNESSES.txt")"
  echo "*** Paley(23) IS arc-critical.  Verify with verify_witness_bits.py before believing it."
else
  echo "witnesses            : none"
fi
if [ "$done_n" -gt 0 ]; then
  cat "$OUT"/done/* 2>/dev/null | sed 's/time=//;s/s$//' | \
    awk -v n="$N" '{s+=$1; c++} END {
      if (c) printf "core-hours spent     : %.1f\nmean per base state  : %.1f s\nprojected total      : %.0f core-h\n",
                     s/3600, s/c, s/c*n/3600 }'
fi
# completeness: the INDEX COVER, not the count -- gaps and duplicates can cancel
# Exact set difference on the INDEX COVER.  `comm` was wrong here: it collates
# LEXICALLY ("10" < "2") while both inputs were built numerically, so it emitted
# "not in sorted order" and its counts could not be trusted in either direction.
# awk compares the sets themselves, so ordering is irrelevant.
miss=$(ls "$OUT/done" 2>/dev/null | awk -v n="$N" '{got[$1]=1}
  END{c=0; for(i=0;i<n;i++) if(!(i in got)) c++; print c}')
extra=$(ls "$OUT/done" 2>/dev/null | awk -v n="$N" '{if($1+0<0||$1+0>=n||$1!=($1+0)"") c++}
  END{print c+0}')
echo "missing indices      : $miss"
echo "unexpected indices   : $extra"
if [ "$miss" = 0 ] && [ "$extra" = 0 ] && [ ! -f "$OUT/WITNESSES.txt" ]; then
  echo
  echo "COMPLETE AND EXACT: all 8031 base states refuted, no gaps, no witness."
  echo "=> Paley(23) is NOT arc-critical."
fi
