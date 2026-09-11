#!/bin/bash
# HUNT at MARGIN <= 3 (was majority).  More constrained, so cheaper, and a
# witness implies majority anyway.  Serves both conjectures: a witness proves
# Paley(43) vertex-critical; an M=3 refutation plus an M=5 witness would prove
# the margin hierarchy strict, which is the open half of the paper conjecture.  A witness
# proves Leonid's conjecture that Paley(43) is VERTEX-CRITICAL, Paley(43) being
# already refuted.  Shuffled order, stop-on-first-witness, done-marker per base
# state so it is resumable and abandonable at any point.
#   complete refutation would cost 8031 x 96.3 s = 215 core-h = 21.5 h on 10
#   cores -- so this is worth running ONLY as a hunt, on the SAT prior.
# --base is named: at n=42 the auto-selector would scan all C(42,5) = 850,668
# subsets once per process.
set -u
cd "$(dirname "$0")/.."
D=p43mv_majority; B=$1
[ -f $D/STOP ] && exit 0
[ -f $D/done/$B ] && exit 0
mkdir -p $D/done $D/log
./kinduce24 --bits p43_minus1v.bits --n 42 --k 5 --max-margin 3 --order mrv --inc \
    --pool-mb 512 --base 0 1 2 3 10 --toporb 0 1 --bs-from $B --bs-to $((B+1)) > $D/log/b$B.log 2>&1
if grep -q '^RESULT SAT' $D/log/b$B.log; then
  touch $D/STOP; cp $D/log/b$B.log $D/WITNESS_b$B.log
  echo "WITNESS at base state $B" >> $D/WITNESSES.txt
elif grep -q '^RESULT UNSAT' $D/log/b$B.log; then
  grep -o 'time=[0-9.]*s' $D/log/b$B.log | tail -1 > $D/done/$B; rm -f $D/log/b$B.log
fi
