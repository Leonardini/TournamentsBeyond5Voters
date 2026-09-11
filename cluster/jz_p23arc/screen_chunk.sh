#!/bin/bash
# Screen one base state of the blind T^e scan.
#
#   T^e = Paley(23) with the arc (0,1) reversed.  |Aut(T^e)| = 1, so NO symmetry
#   break is available and all 8031 base states are live.  That is precisely why
#   this costs 500 core-h where the broken Paley(23) sweep cost 34.
#
#   SAT   => T^e is 5-inducible => Paley(23) IS arc-critical (Paley(23) itself is
#            not 5-inducible, and Aut(Paley(23)) is regular on arcs, so one
#            reversed arc represents all 253).  Arc-criticality implies
#            vertex-criticality, so that direction closes too.
#   UNSAT => Paley(23) is not arc-critical.
#
# Checkpoint granularity is ONE BASE STATE, deliberately: a marker is written
# only on RESULT UNSAT, so the exact index cover of done/ IS the completeness
# certificate -- a capped or killed state leaves no marker and a resubmit
# retries it.  Never infer completeness from a count.
set -u
# Caller-supplied paths are relative to the CALLER'S cwd.  Resolve them BEFORE the cd
# below, or a path like "KInduceDFS/<kit>/results" passed from the repo root gets re-read
# relative to this script's own directory and everything lands in a DOUBLED path
# (KInduceDFS/KInduceDFS/...).  That happened on 2026-09-06 and nearly cost a 210 core-h
# run its results: the scheduler said COMPLETED, the aggregator said 0 done.
# Same idiom as jz_reproduce/run.sh, which has always been correct.
_ORIGPWD=$PWD
cd "$(dirname "$0")/.."
B=$1                       # base-state index
OUT=${2:-jz_p23arc/results}
case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac
KI=${KI:-./kinduce}

mkdir -p "$OUT/done" "$OUT/log" "$OUT/witness"
[ -f "$OUT/STOP" ] && exit 0          # a witness was already found somewhere
[ -f "$OUT/done/$B" ] && exit 0       # already screened

LOG="$OUT/log/b$B.log"
$KI --bits p23_arcrev.bits --n 23 --k 5 --margin majority --order mrv --inc \
    --pool-mb 512 --base 0 1 2 6 15 --bs-from "$B" --bs-to $((B+1)) > "$LOG" 2>&1

if grep -q '^RESULT SAT' "$LOG"; then
    cp "$LOG" "$OUT/witness/b$B.log"
    echo "$B" >> "$OUT/WITNESSES.txt"
    touch "$OUT/STOP"
    echo "base=$B WITNESS -- Paley(23) IS arc-critical"
    exit 0
elif grep -q '^RESULT UNSAT' "$LOG"; then
    grep -o 'time=[0-9.]*s' "$LOG" | tail -1 > "$OUT/done/$B"
    echo "base=$B unsat $(cat "$OUT/done/$B")"
    rm -f "$LOG"
    exit 0
else
    # capped, killed, or aborted: leave NO marker so a resubmit retries it
    echo "base=$B INCOMPLETE -- left unmarked" >&2
    exit 1
fi
