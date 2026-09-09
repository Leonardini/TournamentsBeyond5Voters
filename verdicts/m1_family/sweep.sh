#!/bin/bash
# One margin-1 blind sweep: all 2200 base states of one host, 10 workers, a
# done-marker per base state (so a kill costs at most one), STOP on the first
# witness.  The base is NAMED, not auto-selected: at n>=22 the auto-base scan
# over all C(n,5) subsets costs ~12 s per PROCESS, which is 3x the search
# itself here.  Each named base is exactly what the auto-selector picks.
#   usage: sweep.sh <tag> <bits> <n> "<base>"
set -u
cd "$(dirname "$0")/.."
TAG=$1; HOST=$2; N=$3; BASE=$4
D=m1_family/$TAG
mkdir -p $D/done $D/log
export TAG HOST N BASE D
one() {
  B=$1
  [ -f $D/STOP ] && return 0
  [ -f $D/done/$B ] && return 0
  ./kinduce24 --bits $HOST --n $N --k 5 --margin exact --order mrv --inc \
      --pool-mb 512 --base $BASE --bs-from $B --bs-to $((B+1)) > $D/log/b$B.log 2>&1
  if grep -q '^RESULT SAT' $D/log/b$B.log; then
    touch $D/STOP; cp $D/log/b$B.log $D/WITNESS_b$B.log
  elif grep -q '^RESULT UNSAT' $D/log/b$B.log; then
    grep -o 'time=[0-9.]*s' $D/log/b$B.log | tail -1 > $D/done/$B
    rm -f $D/log/b$B.log
  fi
}
export -f one
seq 0 2199 | xargs -P 10 -I{} bash -c 'one {}'
n=$(ls $D/done | wc -l | tr -d ' ')
if [ -f $D/STOP ]; then echo "$TAG: WITNESS FOUND ($n/2200 refuted before it)"
elif [ "$n" -eq 2200 ]; then echo "$TAG: UNSAT, all 2200 base states refuted"
else echo "$TAG: INCOMPLETE, $n/2200"; fi
