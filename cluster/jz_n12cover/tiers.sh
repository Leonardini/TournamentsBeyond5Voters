#!/bin/bash
# ONE copy of the decision pipeline, sourced by both workers.
#
# WHY THIS FILE EXISTS.  screen_residue.sh (generates its hosts with gentourng)
# and eval_shard.sh (reads a pre-generated shard) differ only in WHERE their
# hosts come from.  They must not differ in HOW those hosts are decided, but each
# carried its own copy of the tiers under a comment reading "identical logic to"
# the other, with nothing checking the claim.  When the pipeline was redesigned on
# 2026-09-08, one of the two would have been left running the version that
# provably cannot terminate on a structured residue.  So: state it once, and have
# both read it.
#
#   run_tiers <hostfile> <tag>
#
# Reads   : OUT WORK SKIP PBN T2 T3 KINDUCE, and ./kcover in the current directory
# Sets    : A1 NLEFT FIX2 FIX3 CAND UNRES
# Writes  : $OUT/candidates/<tag>.txt on a hit, $OUT/unresolved/<tag>.t{2,3}.log
#           when an instance runs out of budget
# Returns : 0 normally.  The CALLER decides what to do about UNRES > 0 -- both
#           callers leave the unit unmarked so a resubmit retries it.

EXTEND='
# prev MUST start at -1, not unset.  An unset awk variable is both "" and 0, and
# comparing it against the strnum $2 is a NUMERIC comparison, so "0" != prev is
# FALSE for the very first host: index 0 never got its bits parsed and its
# extensions came out 11 characters long instead of 66.  Selftest T8 caught it.
BEGIN { prev = -1 }
NR==FNR { h[FNR-1] = $0; next }                 # host index in COVER lines is 0-based
/^UNCOVERED/ {
  idx = $2; mask = $3; sub(/^mask=/, "", mask); mask += 0
  if (!(idx in h)) { printf("FATAL: no host at index %d\n", idx) > "/dev/stderr"; exit 1 }
  if (idx != prev) {                            # UNCOVERED lines come grouped by
    delete up; k = 0                            # host, so parse each host once
    for (a = 0; a < n; a++) for (b = a + 1; b < n; b++) up[a "," b] = substr(h[idx], ++k, 1)
    if (k != n * (n - 1) / 2) { print "FATAL: host bit count" > "/dev/stderr"; exit 1 }
    prev = idx
  }
  for (a = 0; a < n; a++) up[a "," n] = (int(mask / 2 ^ a) % 2 == 1) ? "0" : "1"
  s = ""
  for (a = 0; a <= n; a++) for (b = a + 1; b <= n; b++) s = s up[a "," b]
  print s
  print idx, mask > key
}'

run_tiers() {
  local HOSTS=$1 TAG=$2
  # ---- tier 1: margin-1 coverage, capped ----------------------------------
  # Settles the great majority of hosts outright: a host whose 2,048 extension
  # masks are all covered needs nothing further, because a covering profile IS a
  # five-voter realisation of that order-12 tournament.
  L1="$WORK/t1_$TAG.log"
  ./kcover --batch "$HOSTS" --n 11 --k 5 --inc --cover --cover-skip "$SKIP" \
           --per-base-nodes "$PBN" --margin exact --cover-dump > "$L1" 2>&1
  grep -q '^COVER' "$L1" || { echo "unit=$TAG TIER1 PRODUCED NO OUTPUT -- not marking done" >&2; exit 1; }
  A1=$(grep -c 'ALL ' "$L1")

  # ---- what the leftovers are, and why the unit of work changes here ------
  # MEASURED 2026-09-08, and this is why tiers 2 and 3 are no longer coverage runs.
  # Tier 1 settles 95% of hosts on an ordinary residue but 0% on residue 0, whose
  # first host is the TRANSITIVE tournament: with all five voters using the
  # transitive order the only reachable masks are the 12 suffixes, so every other
  # mask needs profiles that disagree about the host while still inducing it.
  # Giving such a host MORE coverage time does not help -- three of them ran the
  # old uncapped tier 2 for 174 s each and came back with 1764-2000 of 2048 masks
  # and nothing decided -- and since a residue with an undecided host is left
  # unmarked, residue 0 could never be marked done however often the array was
  # resubmitted.
  #
  # But each uncovered mask is just ONE order-12 tournament, and deciding one
  # directly is 14 ms.  The 284 leftovers of that transitive host all came back
  # 5-inducible in 4 seconds total.  So from here the unit of work is an INSTANCE,
  # not a host: build each leftover as an order-12 tournament and decide it.
  grep '^UNCOVERED' "$L1" > "$WORK/unc_$TAG" || true
  NLEFT=$(wc -l < "$WORK/unc_$TAG" | tr -d ' ')
  FIX2=0; FIX3=0; CAND=0; UNRES=0

  # Extension builder, in awk because nothing on the compute path may need an
  # interpreter (python3 is absent from Jean Zay compute nodes and killed this kit
  # once already).  Conventions taken from kcover.c, not assumed:
  #   * a .bits line is the upper triangle row-major over pairs (a,b), a<b, and
  #     '1' means a->b                                     (loader, kcover.c:927)
  #   * a cover mask has bit u set iff the NEW vertex beats u  (cov_rec + the
  #     printer, kcover.c:401-419 and 1070-1078)
  # so the new pairs (a, n) carry '1' iff a -> v, i.e. iff mask bit a is 0.
  if [ "$NLEFT" -gt 0 ]; then
    EXT="$WORK/ext_$TAG.bits"
    awk -v n=11 -v key="$WORK/key_$TAG" "$EXTEND" "$HOSTS" "$WORK/unc_$TAG" > "$EXT" || {
      echo "FATAL unit $TAG: extension builder failed" >&2; exit 1; }
    NE=$(wc -l < "$EXT" | tr -d ' ')
    [ "$NE" -eq "$NLEFT" ] || { echo "FATAL unit $TAG: built $NE extensions for $NLEFT leftovers" >&2; exit 1; }

    # ---- tier 2: each leftover as its own order-12 instance, margin 1 ------
    L2="$WORK/t2_$TAG.log"
    "$KINDUCE" --batch "$EXT" --n 12 --k 5 --margin exact --inc --time "$T2" > "$L2" 2>&1
    grep -q '^BATCH_SUMMARY' "$L2" || { echo "unit=$TAG TIER2 GAVE NO SUMMARY -- not marking done" >&2; exit 1; }
    RAN2=$(grep -c '^BATCH ' "$L2")
    [ "$RAN2" -eq "$NE" ] || { echo "FATAL unit $TAG: tier 2 ran $RAN2 of $NE instances" >&2; exit 1; }
    FIX2=$(awk '/^BATCH /&&$3=="SAT"{c++}   END{print c+0}' "$L2")
    AB2=$(awk  '/^BATCH /&&$3=="ABORTED"{c++} END{print c+0}' "$L2")
    awk '/^BATCH /&&$3=="UNSAT"{print $2}' "$L2" > "$WORK/u2_$TAG"
    N2=$(wc -l < "$WORK/u2_$TAG" | tr -d ' ')
    UNRES=$((UNRES + AB2))

    if [ "$N2" -gt 0 ]; then
      # ---- tier 3: the same instances at majority -------------------------
      # Margin-1 UNSAT is NOT a counterexample: some order-12 tournaments are
      # majority-inducible and not margin-1 inducible, and margin 1 is known to
      # break by n = 19.  Only a majority UNSAT counts.
      EXT3="$WORK/ext3_$TAG.bits"
      awk 'NR==FNR{w[$1+1];next}(FNR in w)' "$WORK/u2_$TAG" "$EXT" > "$EXT3"
      L3="$WORK/t3_$TAG.log"
      "$KINDUCE" --batch "$EXT3" --n 12 --k 5 --margin majority --inc --time "$T3" > "$L3" 2>&1
      grep -q '^BATCH_SUMMARY' "$L3" || { echo "unit=$TAG TIER3 GAVE NO SUMMARY -- not marking done" >&2; exit 1; }
      RAN3=$(grep -c '^BATCH ' "$L3")
      [ "$RAN3" -eq "$N2" ] || { echo "FATAL unit $TAG: tier 3 ran $RAN3 of $N2 instances" >&2; exit 1; }
      FIX3=$(awk '/^BATCH /&&$3=="SAT"{c++}     END{print c+0}' "$L3")
      AB3=$(awk  '/^BATCH /&&$3=="ABORTED"{c++} END{print c+0}' "$L3")
      CAND=$(awk '/^BATCH /&&$3=="UNSAT"{c++}   END{print c+0}' "$L3")
      UNRES=$((UNRES + AB3))
      if [ "$CAND" -gt 0 ]; then
        # An order-12 tournament with no five-voter profile at all: N(5) = 12.
        # The UNCOVERED token is what aggregate.sh counts, so keep it.
        awk '/^BATCH /&&$3=="UNSAT"{print $2}' "$L3" > "$WORK/c3_$TAG"
        { echo "# unit $TAG: order-12 tournaments with NO 5-voter profile at majority"
          echo "# verify by hand before believing:  ../kinduce --bits <one line> --n 12 --k 5 --margin majority --inc"
          awk 'NR==FNR{w[$1+1];next}(FNR in w){print "UNCOVERED", $0}' "$WORK/c3_$TAG" "$EXT3"
        } > "$OUT/candidates/$TAG.txt"
        echo "*** unit $TAG: $CAND CANDIDATE(S) -- see $OUT/candidates/r$RES.txt" >&2
      fi
      if [ "$AB3" -gt 0 ]; then cp "$L3" "$OUT/unresolved/$TAG.t3.log"; fi
    fi
    if [ "$AB2" -gt 0 ]; then cp "$L2" "$OUT/unresolved/$TAG.t2.log"; fi
  fi
  # An explicit status: the last command above was a test that is FALSE on a
  # clean run, so without this the function returned 1 exactly when nothing had
  # gone wrong -- fatal for any caller running with `set -e`, which is how
  # probe_rate.sh found it.  UNRES is what the caller must look at, not $?.
  return 0
}
