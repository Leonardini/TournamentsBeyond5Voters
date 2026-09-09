#!/bin/bash
# ORDERED BY THE IMPLICATION, not by size (Leonid, 2026-09-03 evening).
#   arc SAT  => vertex SAT      (arc-critical => vertex-critical, + arc-transitivity)
#   vertex UNSAT => arc UNSAT   (contrapositive)
# So under an UNSAT prior the VERTEX cell dominates: its refutation hands you the
# arc cell free.  Under a SAT prior the ARC cell dominates.  After UNSAT arc
# results at q=23 and q=27 the prior here is firmly UNSAT, so vertices first.
# Note p27e UNSAT does NOT imply p27mv -- the implication only runs one way --
# so p27mv stays in the queue as a genuinely open cell.
# The implied cells (p31e, p43e) are queued LAST, as independent confirmation
# if time allows, exactly as the q=23 pair cross-checked each other.
set -u
cd "$(dirname "$0")"
{
./sweep.sh p43mv p43_minus1v.bits 42 "0 1 2 3 10"
./sweep.sh p31mv p31_minus1v.bits 30 "0 1 2 3 12"
./sweep.sh p27mv p27_minus1v.bits 26 "0 1 2 6 12"
./sweep.sh p31e  p31_arcrev.bits  31 "0 1 2 4 12"
./sweep.sh p43e  p43_arcrev.bits  43 "0 1 2 4 6"
} 2>&1 | tee -a results.txt
echo OPEN_DONE >> results.txt
