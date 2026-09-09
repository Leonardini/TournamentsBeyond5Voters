#!/bin/bash
# Fetch McKay's self-converse n=13 listing and partition it for the sweep.
#
#   1. drop the REGULAR hosts -- every regular tournament on n<=13 is already
#      known 5-inducible at both margins, so re-running them is pure waste
#   2. split the rest into POSSIBLY-SYMMETRIC and PROVABLY-RIGID by colour
#      refinement.  Discrete refinement => trivial Aut is a THEOREM, so nothing
#      symmetric is ever misfiled into the rigid pile
#   3. bucket by score-sequence imbalance so the sweep runs most-balanced first
#
# ~7 GB unpacked; needs about 20 GB of scratch with the buckets.
set -eu
cd "$(dirname "$0")"
W=${N13_WORK:-${SCRATCH:-/tmp}/n13sc}
mkdir -p "$W"; cd "$W"
[ -f selfcontourn13.txt ] || {
  curl -fL -o selfcontourn13.txt.gz https://users.cecs.anu.edu.au/~bdm/data/selfcontourn13.txt.gz
  gunzip -f selfcontourn13.txt.gz
}
N=$(wc -l < selfcontourn13.txt | tr -d ' ')
echo "  listing: $N lines (expect 95458560)"
[ "$N" = 95458560 ] || { echo "  FAIL: wrong line count -- do not sweep this"; exit 1; }
D="$(cd "$OLDPWD" && pwd)"
mkdir -p buckets sym rigid
# The awk below APPENDS (>>), so a second run would DOUBLE every bucket and silently shift
# every shard's line range -- and the shard tags are the only thing tying a done marker to a
# set of hosts.  Clear first, so re-running is idempotent.
rm -f buckets/imb*.txt sym/imb*.txt rigid/imb*.txt
"$D/order_sym" 13 selfcontourn13.txt | awk '{print $2 >> ("buckets/imb" $1 ".txt")}'
for f in buckets/imb*.txt; do b=$(basename "$f" .txt); "$D/rigid" 13 "$f" "sym/$b.txt" "rigid/$b.txt"; done
echo "  possibly-symmetric: $(cat sym/*.txt | wc -l | tr -d ' ')"
echo "  provably rigid    : $(cat rigid/*.txt | wc -l | tr -d ' ')"
echo "  per-bucket rigid counts (THE cross-check: another machine must match these"
echo "  exactly before a shard tag can be assumed to name the same hosts):"
wc -l rigid/imb*.txt | sed 's/^/    /'
echo "  work dir: $W"
