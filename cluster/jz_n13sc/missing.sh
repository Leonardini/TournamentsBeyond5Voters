#!/bin/bash
# WHICH SHARDS ARE STILL UNSWEPT.  Run this ON THE CLUSTER, from the repo root.
#
# A done marker is named "<bucket>_<startline>", so it names EXACTLY the host range it
# covers, and the unswept set is just the complement of the marker set against the shard
# grid.  Nothing has to be remembered between runs.
#
# It also prints the per-bucket rigid line counts, which are THE cross-check before any
# other machine can act on this list: a shard tag only names the same 200,000 hosts if
# that machine's partition has identical bucket sizes.  Compare them, do not assume them.
set -u
W=${N13_WORK:-${SCRATCH:-/tmp}/n13sc}
OUT=${N13_OUT:-$PWD/KInduceDFS/jz_n13sc/results}
case "$OUT" in /*) ;; *) OUT=$PWD/$OUT ;; esac
PER=${N13_PER:-200000}
cd "$W" || { echo "no work dir $W -- set N13_WORK"; exit 1; }

echo "### per-bucket rigid counts (cross-check these against the other machine)"
wc -l rigid/imb*.txt

ls rigid/imb*.txt | sed 's|rigid/imb||; s|\.txt$||' | sort -n \
  | sed 's|^|rigid/imb|; s|$|.txt|' > .order
MISS=$W/missing_shards.txt; : > "$MISS"; TOT=0
# NOTE the `< .order` redirection rather than a pipe: a pipe puts the loop in a subshell
# and TOT would come back 0, which would make the identity check below pass vacuously.
while read -r f; do
  b=$(basename "$f" .txt); total=$(wc -l < "$f" | tr -d ' ')
  for lo in $(seq 1 "$PER" "$total"); do
    TOT=$((TOT+1))
    [ -f "$OUT/done/${b}_$lo" ] || echo "${b}_$lo" >> "$MISS"
  done
done < .order

DONE=$(ls "$OUT/done" 2>/dev/null | wc -l | tr -d ' ')
NMISS=$(wc -l < "$MISS" | tr -d ' ')
echo "### shards: total=$TOT done=$DONE missing=$NMISS"
if [ $((DONE + NMISS)) -ne "$TOT" ]; then
  echo "### IDENTITY FAILS: done+missing != total -- there are markers that match no shard"
  echo "### (stale PER, or a partition that changed under the markers).  DO NOT act on this list."
  exit 1
fi
echo "### identity OK: done + missing == total"
echo "### hosts still unswept: $(awk -v p="$PER" 'END{print NR*p" (upper bound; last shard of each bucket is short)"}' "$MISS")"
echo "### list written to $MISS"
cat "$MISS"
