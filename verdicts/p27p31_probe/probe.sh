#!/bin/bash
# A ONE-HOUR, ONE-CORE witness hunt for Paley(27)-v and Paley(31)-v at MAJORITY.
#
# WHY: the criticality ladder is measured at q=19 (margin-1 arc-critical), q=23
# (majority arc-critical) and q=43 (not even majority vertex-critical), and 27
# and 31 are the unmeasured middle.  Leonid's conjecture is that they are
# majority-VERTEX-critical but not arc-critical, i.e. that P-v is 5-inducible.
# A SAT is a certificate and terminates early, so the conjecture's own direction
# is the cheap one to test -- which is what this probe exploits.
#
# WHY --max-margin 3 IS majority here: 3-cycle bound, and both hosts were
# checked (min 6 and 7 cyclic triangles per arc, 0 arcs in none).  Margin-1 is
# ALREADY refuted for both (m1_family cells p27mv, p31mv), so majority is the
# only live rung.
#
# NO SYMMETRY BREAK, deliberately.  Stab(0) has order (q-1)/2 and a --toporb
# break would be worth ~20% at this margin, but an unsound one loses witnesses,
# and a FALSE NEGATIVE is precisely the failure this probe cannot afford.
#
# RESOURCE DISCIPLINE: one process at a time, never two; the whole thing wrapped
# in `timeout 3600` by the caller; breadth over depth (a per-base-state cap, many
# random base states) because a satisfiable base state normally yields a witness
# quickly under MRV, so shallow-and-wide beats deep-and-narrow for a hunt.
set -u
cd "$(dirname "$0")/.."
D=p27p31_probe
PER_HOST=${PER_HOST:-1740}      # seconds per host, serialised
CAP=${CAP:-150}                 # per-base-state cap
mkdir -p $D/logs

hunt() { # host n base...
  local f=$1 n=$2; shift 2
  local base="$*" tag=${f%%_*}
  local hdr nb t0 tried capped
  hdr=$(./kinduce --bits $f --n $n --k 5 --max-margin 3 --order mrv --inc --pool-mb 512 \
          --base $base --bs-from 0 --bs-to 0 2>&1 | grep -m1 "^n=$n")
  nb=$(echo "$hdr" | sed -nE 's/.*base_states=([0-9]+).*/\1/p')
  [ -n "$nb" ] && [ "$nb" -gt 0 ] || { echo "FATAL $tag: no base_states from the engine" >&2; return 1; }
  echo "=== $tag  host=$f n=$n base={$base} base_states=$nb  budget=${PER_HOST}s cap=${CAP}s ==="
  # uniform random base states, so "k tried, none satisfiable" is a real sample
  python3 -c "
import random; random.seed(hash('$tag') % 2**32)
xs=list(range($nb)); random.shuffle(xs); print('\n'.join(map(str,xs[:400])))" > $D/logs/${tag}_order.txt
  t0=$(date +%s); tried=0; capped=0
  while read -r b; do
    [ $(( $(date +%s) - t0 )) -ge $PER_HOST ] && break
    timeout $CAP ./kinduce --bits $f --n $n --k 5 --max-margin 3 --order mrv --inc \
        --pool-mb 512 --base $base --bs-from $b --bs-to $((b+1)) > $D/logs/${tag}_b$b.log 2>&1
    tried=$((tried+1))
    if grep -q '^RESULT SAT' $D/logs/${tag}_b$b.log; then
      echo "*** WITNESS: $tag base state $b -- $tag IS 5-inducible at majority ***"
      cp $D/logs/${tag}_b$b.log $D/WITNESS_${tag}_b$b.log; return 0
    fi
    if grep -q '^RESULT UNSAT' $D/logs/${tag}_b$b.log; then
      printf '%s\t%s\t%s\tUNSAT\n' "$tag" "$b" "$(grep -o 'time=[0-9.]*s' $D/logs/${tag}_b$b.log | tail -1)" >> $D/results.tsv
      rm -f $D/logs/${tag}_b$b.log
    else
      capped=$((capped+1))
      printf '%s\t%s\tcap=%ss\tCAPPED\n' "$tag" "$b" "$CAP" >> $D/results.tsv
      # keep the log: a capped state is where a deeper look would go
      mv $D/logs/${tag}_b$b.log $D/logs/${tag}_capped_b$b.log
    fi
  done < $D/logs/${tag}_order.txt
  echo "    $tag: $tried base states of $nb tried ($(echo "scale=3; 100*$tried/$nb" | bc)%), "\
"$capped capped at ${CAP}s, NO WITNESS -- not a verdict, a sample"
}

: > $D/results.tsv
hunt p27_minus1v.bits 26 0 1 2 6 12
hunt p31_minus1v.bits 30 0 1 2 3 12
echo "=== probe done $(date '+%F %T') ==="
