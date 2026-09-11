#!/bin/bash
# Base competition for the Paley(31)-v majority sweep.  Standing instruction:
# vary the base among the top five 5-vertex classes and rank on
# base_states x MEASURED s/base, never on base count -- with the pool SATURATED,
# since a partial-load probe under-prices a saturated run by ~1.35x.
#
# On P43-2v this competition picked class 12 over class 76 and saved 19%, and
# round 1 with 2-5 samples per arm was off by 4x, so take enough samples.
# A SAT here is not a probe artifact -- it ANSWERS the question, so it stops.
set -u
cd "$(dirname "$0")/.."
D=p31mv_majority; OUT=$D/pricing
HOST=$(cat $D/HOST); N=$(cat $D/N)
NS=${NS:-16}; CAP=${CAP:-420}; J=${J:-10}; BUDGET=${BUDGET:-660}
mkdir -p $OUT

arm_base() { case $1 in A) echo 0 1 2 3 12;; B) echo 0 1 2 3 4;; C) echo 0 1 2 3 16;; D) echo 0 1 2 3 6;; esac; }
declare -A NB
for a in A B C D; do
  NB[$a]=$(./kinduce --bits $HOST --n $N --k 5 --max-margin 3 --order mrv --inc --pool-mb 512 \
            --base $(arm_base $a) --bs-from 0 --bs-to 0 2>&1 |
           sed -nE "s/^n=$N.*base_states=([0-9]+).*/\1/p" | head -1)
  echo "arm $a  base={$(arm_base $a)}  base_states=${NB[$a]}"
done

python3 - <<PY > $OUT/queue.txt
import random
random.seed(31009)
nb = {"A":${NB[A]}, "B":${NB[B]}, "C":${NB[C]}, "D":${NB[D]}}
picks = {a: random.sample(range(n), $NS) for a, n in nb.items()}
for i in range($NS):
    for a in ("A","B","C","D"): print(a, picks[a][i])
PY

: > $OUT/results.tsv
START=$(date +%s)
while read -r arm idx; do
  [ -f $OUT/STOP ] && break
  [ $(( $(date +%s) - START )) -ge $BUDGET ] && { echo "BUDGET SPENT after $(( $(date +%s) - START ))s"; break; }
  while [ "$(ps -Ao command | grep '[.]/kinduce ' | grep -vc timeout)" -ge $J ]; do sleep 1; done
  (
    base=$(arm_base $arm); t0=$(date +%s); v=CAPPED
    timeout $CAP ./kinduce --bits $HOST --n $N --k 5 --max-margin 3 --order mrv --inc \
        --pool-mb 512 --base $base --bs-from $idx --bs-to $((idx+1)) > $OUT/${arm}_$idx.log 2>&1
    t1=$(date +%s)
    grep -q '^RESULT SAT'   $OUT/${arm}_$idx.log && v=SAT
    grep -q '^RESULT UNSAT' $OUT/${arm}_$idx.log && v=UNSAT
    printf '%s\t%s\t%s\t%s\n' "$arm" "$idx" "$((t1-t0))" "$v" >> $OUT/results.tsv
    if [ "$v" = SAT ]; then touch $OUT/STOP; cp $OUT/${arm}_$idx.log $D/WITNESS_compete_${arm}_$idx.log
      echo "*** WITNESS during the competition: arm $arm base state $idx -- Paley(31) IS VERTEX-CRITICAL ***"
    else rm -f $OUT/${arm}_$idx.log; fi
  ) &
done < $OUT/queue.txt
wait
echo "elapsed $(( $(date +%s) - START ))s, $(wc -l < $OUT/results.tsv) probes"
