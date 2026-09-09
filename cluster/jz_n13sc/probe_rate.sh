#!/bin/bash
# Measure the real per-host rate here before sizing the array.
# Do not size from the laptop's ~10 ms/host: the n=15 campaign measured this
# cluster at >= 4.3x slower on a different engine, and that factor is a guess.
set -eu
cd "$(dirname "$0")"
W=${N13_WORK:-${SCRATCH:-/tmp}/n13sc}; N=${1:-20000}
f=$(ls "$W"/rigid/imb*.txt | head -1)
t=${JOBSCRATCH:-${SLURM_TMPDIR:-/tmp}}/n13probe.bits
# a mid-stream slice, not the head: the listing is not in random order
sed -n "500001,$((500000+N))p" "$f" > "$t" || sed -n "1,${N}p" "$f" > "$t"
g=$(wc -l < "$t" | tr -d ' ')
s=$(date +%s)
../kinduce --batch "$t" --n 13 --k 5 --margin exact --inc --time 300 > "$t.log" 2>&1
e=$(date +%s)
awk -v g="$g" -v d="$((e-s))" 'BEGIN{
  ms = g ? 1000.0*d/g : 0
  printf "  %d hosts in %d s = %.2f ms/host\n", g, d, ms
  printf "  PROJECTED for the remaining ~94.4M: %.0f core-h\n", 94400000*ms/1000/3600
}'
grep -c ' UNSAT ' "$t.log" | awk '{print "  UNSAT in the probe:",$1}'
# The projection is only trustworthy if every host actually FINISHED: --time is a
# PER-INSTANCE cap, so any ABORTED host contributes the full cap and inflates the
# rate, while a killed allocation loses the measurement entirely.  Print the
# engine's own summary (instances=, ABORTED=) before discarding the log.
grep -h "^BATCH_SUMMARY" "$t.log" 2>/dev/null | sed 's/^/  /' || echo "  (no BATCH_SUMMARY -- run did not complete)"
rm -f "$t" "$t.log"
