#!/usr/bin/env bash
# =====================================================================================
# reproduce_paley43.sh — end-to-end reproduction of the proof that Paley(43) is NOT
# the majority (Kemeny median) of 5 voters, i.e. Paley(43) is not 5-realizable.
#
# PROOF SKELETON (see PALEY43_NONREALIZABLE.md for the math):
#   1. MAS(Paley43) = 543               [dp43 join, certified on completion]
#   2. Sum fwd >= 3C=2709, each <=543  =>  the top TWO voters have fwd >= 542 (delta<=1).
#   3. Co-backing lemma: in any 5-realization each cyclic triangle has <=1 double-backer
#      => the 5 voters' double-back (DB) sets are pairwise disjoint. In particular the two
#      delta<=1 voters are two delta<=1 orders with DISJOINT DB-sets.
#   4. razor_screen proves NO two delta<=1 orders have disjoint DB-sets  => contradiction.
#
# STAGES (each guarded; re-run is idempotent / resumable):
#   0  build C/R tools
#   1  self-tests + validation gauntlet (dp43 q7/11 selftest; q19/23/31 MAS certified)
#   2  build the q=43 delta<=2 shell layer tables  [EXPENSIVE: ~hours, ~48 GB disk]
#   3  join(542) -> enum(542) -> canon_reps  => delta<=1 orbit reps (census check == 1,841,303)
#   4  razor_screen on d0 (sanity: 0 seeds) and on delta<=1 (the proof)
#
# Resource envelope: <=8 threads, peak RAM ~5 GB, peak disk ~50 GB (layer tables).
# Stage 2 runs for hours; dp43 prints a per-layer heartbeat on stderr every 30 s so you can see
# how far into a layer it is. Set PROGRESS=0 to silence it.
# Usage:  ./reproduce_paley43.sh [from_stage]     (default 0; e.g. `./reproduce_paley43.sh 3`)
# =====================================================================================
set -euo pipefail
cd "$(dirname "$0")"
THREADS=${THREADS:-8}
DIR=dp43run43
FROM=${1:-0}
say(){ printf '\n\033[1;36m== %s\033[0m\n' "$*"; }
die(){ printf '\033[1;31mFAIL: %s\033[0m\n' "$*" >&2; exit 1; }

# ---- stage 0: build ----
if [ "$FROM" -le 0 ]; then
  say "STAGE 0  build tools"
  cc -O3 -march=native -pthread -o dp43        dp43.c
  cc -O3 -march=native -pthread -o canon_reps  canon_reps.c
  cc -O3 -march=native -pthread -o razor_screen razor_screen.c
  echo "built dp43, canon_reps, razor_screen"
fi

# ---- stage 1: self-tests + gauntlet ----
if [ "$FROM" -le 1 ]; then
  say "STAGE 1  self-tests + validation gauntlet"
  ./dp43 selftest 7  /tmp/st7  || die "selftest q=7"
  ./dp43 selftest 11 /tmp/st11 || die "selftest q=11"
  # Gauntlet (full pool reproduction + certified MAS) for q=19/23/31 is documented in
  # DP43_PLAN.md; run `./dp43 all 19 <tau> dir` etc. to reproduce those pools byte-identically.
  echo "self-tests passed (q=7, q=11 canon/Burnside/brute-force/prune)"
fi

# ---- stage 2: q=43 layer tables (EXPENSIVE) ----
if [ "$FROM" -le 2 ]; then
  say "STAGE 2  q=43 delta<=2 shell layer tables  [EXPENSIVE ~hours, ~48 GB]"
  if [ -f "$DIR/manifest.txt" ] && grep -q '^L 22 ' "$DIR/manifest.txt"; then
    echo "layer tables already present in $DIR (L00..L22) — skipping rebuild"
  else
    mkdir -p "$DIR"
    THREADS=$THREADS ./dp43 layers 43 541 "$DIR" || die "layers"
  fi
fi

# ---- stage 3: delta<=1 orbit reps + census check ----
if [ "$FROM" -le 3 ]; then
  say "STAGE 3  join(542) -> enum(542) -> canon_reps  (delta<=1 orbit reps)"
  THREADS=$THREADS ./dp43 join 43 542 "$DIR"  || die "join 542"
  THREADS=$THREADS ./dp43 enum 43 542 "$DIR"  || die "enum 542"
  ./canon_reps "$DIR/pool_raw.txt" delta1_reps.txt | tee /tmp/canon.out
  n=$(awk '{print $1}' <<<"$(wc -l < delta1_reps.txt)")
  [ "$n" -eq 1841303 ] || die "delta<=1 orbit count $n != census 1,841,303 (enumeration incomplete!)"
  echo "delta<=1 reps complete + census-verified: 1,841,303 orbits"
fi

# ---- stage 4: the screen ----
if [ "$FROM" -le 4 ]; then
  say "STAGE 4a  razor_screen sanity on delta=0 (must report TRUE_DISJOINT=0)"
  # d0 reps: canonicalize the tau=543 enum, or reuse committed d0_reps.txt
  [ -f d0_reps.txt ] || die "d0_reps.txt missing (delta=0 orbit reps)"
  MCAP=300000 ./razor_screen d0_reps.txt 1 24 0 $THREADS | tee /tmp/d0.out
  grep -q 'TRUE_DISJOINT=0' /tmp/d0.out || die "d0 sanity: found a disjoint pair (unexpected)"

  say "STAGE 4b  razor_screen on delta<=1  (THE PROOF)"
  MCAP=50000000 ./razor_screen delta1_reps.txt 1 24 0 $THREADS | tee /tmp/proof.out
  if grep -q 'TRUE_DISJOINT=0' /tmp/proof.out; then
    printf '\n\033[1;32m========================================================================\n'
    printf 'PROVED: no two delta<=1 orders of Paley(43) have disjoint double-back sets.\n'
    printf 'By co-backing + fwd-counting, Paley(43) is NOT 5-realizable  =>  N(5) <= 43.\n'
    printf '========================================================================\033[0m\n'
  else
    printf '\n\033[1;33mSEEDS FOUND: see razor_disjoint_hits.txt (Paley(43) may be 5-realizable).\033[0m\n'
  fi
fi
