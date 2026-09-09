#!/bin/bash
# One base state of the margin-1 blind scan on Paley(23) with an arc reversed.
# Complete per base state (no cap): each either refutes or yields a witness.
set -u
cd "$(dirname "$0")/.."
D=m1_arcrev
B=$1
[ -f $D/STOP ] && exit 0
[ -f $D/done/$B ] && exit 0
mkdir -p $D/done $D/log
# --base is EXACTLY what the auto-selector picks here (mask 918, 2200 base
# states, verified bit-identical: 654513 nodes either way).  Naming it skips
# the most-restrictive-base scan over all C(23,5) = 33,649 subsets, which costs
# ~12 s per PROCESS -- 73% of the cost of a base state whose search is 4.6 s.
./kinduce24 --bits p23_arcrev.bits --n 23 --k 5 --margin exact --order mrv --inc \
    --pool-mb 512 --base 0 1 2 6 15 --bs-from $B --bs-to $((B+1)) > $D/log/b$B.log 2>&1
if grep -q '^RESULT SAT' $D/log/b$B.log; then
  touch $D/STOP
  cp $D/log/b$B.log $D/WITNESS_b$B.log
  echo "WITNESS at base state $B" >> $D/WITNESSES.txt
elif grep -q '^RESULT UNSAT' $D/log/b$B.log; then
  grep -o 'time=[0-9.]*s' $D/log/b$B.log | tail -1 > $D/done/$B
  rm -f $D/log/b$B.log
else
  echo "base state $B produced no RESULT -- not marking done" >&2
fi
