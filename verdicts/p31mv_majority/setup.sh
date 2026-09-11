#!/bin/bash
# Build order.txt for the chosen base of the Paley(31)-v sweep.  The base-state
# down: it is read out of the engine's own header for this host and this base,
# so the queue and the search cannot disagree about the size of the space.
set -eu
cd "$(dirname "$0")/.."
D=p31mv_majority
ENG=${ENG:-kinduce}; BASE=${BASE:-0 1 2 3 6}
HDR=$(./$ENG --bits $(cat $D/HOST) --n $(cat $D/N) --k 5 --max-margin 3 --order mrv --inc \
        --pool-mb 512 --base $BASE --bs-from 0 --bs-to 0 2>&1 | grep -m1 '^n=')
NB=$(echo "$HDR" | sed -nE 's/.*base_states=([0-9]+).*/\1/p')
BM=$(echo "$HDR" | sed -nE 's/.*base_mask=([0-9]+).*/\1/p')
[ -n "$NB" ] && [ "$NB" -gt 0 ] || { echo "FATAL: could not read base_states from the engine header" >&2; exit 1; }
echo "engine reports base=$BASE base_mask=$BM base_states=$NB"
python3 - "$NB" <<'PY' > $D/order.txt
import random, sys
nb = int(sys.argv[1]); xs = list(range(nb)); random.seed(4302); random.shuffle(xs)
print("\n".join(map(str, xs)))
PY
L=$(wc -l < $D/order.txt | tr -d ' ')
[ "$L" -eq "$NB" ] || { echo "FATAL: order.txt has $L lines, engine says $NB" >&2; exit 1; }
sort -n $D/order.txt | cmp -s - <(seq 0 $((NB-1))) || { echo "FATAL: order.txt is not a permutation of [0,$NB)" >&2; exit 1; }
printf '%s\n' "$BASE" > $D/BASE
printf '%s\n' "$NB"   > $D/NBASE
echo "order.txt: $L indices, verified a permutation of [0,$NB).  BASE and NBASE recorded."
