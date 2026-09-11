#!/bin/bash
# ONE base state of the Paley(31)-v majority hunt.
#
# QUESTION: is Paley(31) - v 5-inducible, i.e. is Paley(31) VERTEX-CRITICAL?
# Paley(31) itself is not 5-inducible (settled 2026-09-03: 5253/5253 chunks
# UNSAT, 0 capped, 26.89 core-h).
#
#   SAT   -> Paley(31) IS vertex-critical: a 31-vertex minimal obstruction, and
#            the arc question (is it arc-critical?) then opens.
#   UNSAT -> Paley(31) is not vertex-critical, like Paley(43); the "smooth
#            degradation" picture across q = 19, 23, 27, 31, 43 breaks at 31.
#
# ONE RUN SETTLES ALL 31 DELETIONS.  |Aut(Paley(31))| = 465 = C(31,2) = #arcs
# (nauty), so Aut is regular on arcs and in particular transitive on vertices;
# all one-vertex deletions are isomorphic.
#
# WHY --max-margin 3 IS A MAJORITY VERDICT HERE: by the 3-cycle bound a linear
# order agrees with at most 2 of a 3-cycle's arcs, so over k voters the three
# supports total at most 2k = 10 while majority forces each >= 3; no arc inside
# a 3-cycle can reach support 5.  Measured on THIS host, not assumed: every arc
# of p31_minus1v.bits lies in >= 7 cyclic triangles and 0 arcs lie in none.
#
# MARGIN 1 IS ALREADY REFUTED for this host (m1_family cell p31mv: 2200/2200
# base states, exact coverage, no witness, 2.21 core-h), so majority is the only
# live rung and this sweep is the whole remaining question.
#
# SYMMETRY BREAK --toporb 0 2, ON since 2026-09-09 (Leonid: "let's take the 20%").
# SOUND, verified not assumed: |Aut(Paley(31)-v)| = 15 exactly (nauty) and it has
# exactly two vertex orbits, of size 15 each -- the QR and non-QR cosets of
# Stab(0) -- with new labels 0 and 2 being old labels 1 and 3, one in each.  So
# every profile has an Aut-image in which some voter ranks 0 or 2 first, which is
# what the break assumes.  The engine cannot check this; the caller must, and did.
#
# It does NOT reduce the base-state count (measured: same 8031 with and without),
# it prunes inside each base state.  Mixing regimes is complete -- see README.md.
#
# Resumable and abandonable: a done marker is written ONLY on RESULT UNSAT, so
# the exact index cover of done/ IS the completeness certificate -- a capped or
# killed base state leaves no trace and will be retried.
set -u
cd "$(dirname "$0")/.."
D=p31mv_majority; B=$1
ENG=${ENG:-kinduce}
# NO DEFAULT BASE.  It used to default to {0,1,2,3,10}, the losing arm's base,
# whose space has only 8031 states -- so any index >= 8031 produced an EMPTY
# slice, which the engine correctly reports as an instant "RESULT UNSAT", and
# this script wrote a done marker for it.  A vacuous success that looks exactly
# like a real one; cf. the n12cover run that "settled" 40000 residues of nothing.
: "${BASE:?one.sh needs BASE exported -- drive.sh reads it from p31mv_majority/BASE}"
# The break lives in ONE place, the BREAK file; empty or absent means no break.
BRK=${BRK-$(cat $D/BREAK 2>/dev/null || true)}
[ -f $D/STOP ] && exit 0
# xargs holds no clock, so the deadline lives in a file every worker reads.
[ -f $D/DEADLINE_AT ] && [ "$(date +%s)" -ge "$(cat $D/DEADLINE_AT)" ] && exit 0
[ -f $D/done/$B ] && exit 0
mkdir -p $D/done $D/log
./$ENG --bits $(cat $D/HOST) --n $(cat $D/N) --k 5 --max-margin 3 --order mrv --inc \
    --pool-mb 512 --base $BASE ${BRK:+--toporb $BRK} \
    --bs-from $B --bs-to $((B+1)) > $D/log/b$B.log 2>&1
if grep -q '^RESULT SAT' $D/log/b$B.log; then
  touch $D/STOP; cp $D/log/b$B.log $D/WITNESS_b$B.log
  echo "WITNESS at base state $B  ($(date '+%F %T'))" >> $D/WITNESSES.txt
elif grep -q '^RESULT UNSAT' $D/log/b$B.log; then
  # The slice must have EXISTED.  base_states comes from the engine's own header
  # for this host and base, so an out-of-range index is a hard error, never a
  # marker.  Recorded in the marker too, so a later base change is detectable.
  NB=$(sed -nE 's/^n=[0-9]+ .*base_states=([0-9]+).*/\1/p' $D/log/b$B.log | head -1)
  BM=$(sed -nE 's/^n=[0-9]+ .*base_mask=([0-9]+).*/\1/p' $D/log/b$B.log | head -1)
  if [ -z "$NB" ] || [ "$B" -ge "$NB" ]; then
    echo "FATAL base state $B is outside [0,$NB) for base {$BASE} -- NO marker written" >&2
    exit 1
  fi
  echo "$(grep -o 'time=[0-9.]*s' $D/log/b$B.log | tail -1) mask=$BM brk=${BRK:-none}" > $D/done/$B
  rm -f $D/log/b$B.log
fi
exit 0
