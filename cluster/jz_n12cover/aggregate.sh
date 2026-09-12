#!/bin/bash
# Roll up a results directory.  Reports coverage and, crucially, separates
# CANDIDATES (survived all three tiers) from anything still merely capped.
set -eu
# Caller-supplied paths are relative to the CALLER'S cwd.  Resolve them BEFORE the cd
# below, or a path like "KInduceDFS/<kit>/results" passed from the repo root gets re-read
# relative to this script's own directory and everything lands in a DOUBLED path
# (KInduceDFS/KInduceDFS/...).  That happened on 2026-09-06 and nearly cost a 210 core-h
# run its results: the scheduler said COMPLETED, the aggregator said 0 done.
# Same idiom as jz_reproduce/run.sh, which has always been correct.
_ORIGPWD=$PWD
cd "$(dirname "$0")"
OUT=${1:-results}
if [ $# -ge 1 ]; then                     # only an ARGUMENT is caller-relative;
  case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac   # the default stays relative
fi                                        # to this script's own directory.
D="$OUT/done"
# D_11, the number of order-11 tournaments up to isomorphism (A000568).  Written
# down because it is a published census value, and therefore ASSERTED below rather
# than trusted: the campaign's whole claim is that every one of them was reached.
D11=903753248
# S11, the self-converse count at n=11.  It is no longer ASSUMED: the run
# measures it, because kept == (D11 + S11)/2 exactly, so S11 == 2*kept - D11.
# The gate below reports that measurement and compares it against the published
# value, rather than deriving a target from the published value and comparing
# the run to that -- which is what it used to do, and which made a wrong
# constant and a broken halving produce the same message.
#
# The value is right.  Leonid confirmed it on 2026-09-12, against a reading of
# A002785 that put 315,392 here; that reading was wrong.  Our own measurements
# of the neighbouring terms all check out: 176 at n=8 and 2,752 at n=9 counted
# directly by converse_filter.sh, 8,784 at n=10, and 1,492,288 at n=12 being the
# size of the order-12 self-converse family this project swept.
S11_PUB=279968                  # OEIS A002785 at n=11; confirmed by Leonid 2026-09-12
# ONE snapshot of the markers, taken once and reused by every consumer below.
# Two independent reasons, both learned the hard way on 2026-09-09:
#
# 1. `"$D"/*` IS AN ARG_MAX HAZARD, AND IT FIRES AT THE FINISH LINE.  At 40,000
#    markers the glob expands to 3.3 MB of absolute cluster paths, past the ~2 MB
#    ARG_MAX, so awk would fail to exec -- with `2>/dev/null` swallowing the
#    "Argument list too long" and `set -e` ending the script.  The output would be
#    a bare "residues done: 40000" and NOTHING ELSE: byte for byte the signature of
#    the vacuous run this kit exists to guard against, produced at the one moment
#    the census gate finally matters.  It fits today only because 16,314 markers
#    are 1.3 MB.  `find -exec cat {} +` batches and has no such ceiling.
# 2. THE REPORT CONTRADICTED ITSELF against a live sweep.  `ls` for the residue
#    count plus two separate awk passes over $D meant three reads seconds apart.
#    At 41.6% it printed "hosts generated 370,989,264 / instances 171,254,188"
#    above and "375,923,510 generated, 174,180,620 screened" below -- the same two
#    quantities, 1.7% apart, because ~150 residues landed in between.
SNAP=$(mktemp); trap 'rm -f "$SNAP"' EXIT
# Announce the read BEFORE doing it.  On a parallel filesystem this find walks
# tens of thousands of small marker files and takes minutes, during which the
# script used to print nothing whatever -- which reads as a hang and invites
# killing a roll-up that was working fine.
printf "reading %s (tens of thousands of small files; this takes a while) ...\n" "$D"
find "$D" -type f -exec cat {} + > "$SNAP" 2>/dev/null || true
# awk, not `grep -c ... || echo 0`: grep -c PRINTS its zero and then exits 1, so the
# fallback would append a second line and `[ "$n" -eq 0 ]` below would die on "0\n0".
n=$(awk '/^res=/{n++}END{print n+0}' "$SNAP")
echo "residues done: $n"
# With no markers at all the awk below is handed an unmatched glob, fails, and
# `set -e` ends the script -- so the output was a bare "residues done: 0" and
# nothing else, which is indistinguishable at a glance from the vacuous run this
# whole kit is scarred by.  Say which of the two it is instead.
if [ "$n" -eq 0 ]; then
  echo "  Nothing has reported yet.  That is expected while the array is still PD:"
  echo "  a task writes its first marker within seconds of starting, because ~83% of"
  echo "  the res/mod classes at n=11 are empty and an empty one is settled instantly."
  echo "  So: if the job is PENDING, wait.  If tasks have RUN and this is still 0,"
  echo "  read the first lines of KInduceDFS/jz_n12cover/slurm/*.out -- every failure"
  echo "  mode this kit has had announced itself there on the first residue."
  exit 0
fi
awk -F'[= ]' '{for(i=1;i<=NF;i++){if($i=="generated")G+=$(i+1); if($i=="instances")I+=$(i+1);
  if($i=="tier1all")A+=$(i+1); if($i=="leftover")L+=$(i+1);
  if($i=="tier2fixed")B+=$(i+1);
  if($i=="tier3fixed")C+=$(i+1); if($i=="candidates")X+=$(i+1);
  if($i=="secs")S+=$(i+1)}}
  END{printf "hosts generated : %d\n", G;
      printf "instances       : %d  (evaluated, i.e. AFTER the converse halving)\n", I;
      printf "tier1 ALL       : %d hosts fully covered (%.4f%%)\n", A, I?100*A/I:0;
      printf "leftover masks  : %d  (%.2f per host -- each is one order-12 instance)\n", L, I?L/I:0;
      printf "tier2 settled   : %d  (leftovers 5-inducible at margin 1)\n", B;
      printf "tier3 settled   : %d  (not margin-1, but inducible at majority)\n", C;
      printf "CANDIDATES      : %d  <== the only interesting number\n", X;
      printf "core-seconds    : %d  (%.1f core-h)\n", S, S/3600}' "$SNAP"
C=$(cat "$OUT/candidates"/*.txt 2>/dev/null | grep -c '^UNCOVERED' || true)
echo "candidate uncovered-mask lines: ${C:-0}"
[ "${C:-0}" != 0 ] && echo "  ==> INSPECT $OUT/candidates -- each names an order-12 tournament with no 5-voter realization"

# ---- the census gate, and the global check on the converse halving -------
# THIS SECTION USED TO BE UNREACHABLE: an `exit 0` sat immediately above it, so
# the one cross-check that can catch a vacuous or partial run never ran.  And the
# markers it reads did not carry `generated=` either, so even reached it would
# have found nothing and silently printed nothing.  Both are fixed; a check that
# cannot fail is worse than no check, because it reads as reassurance.
#
# The halving can ONLY be checked globally: a single residue is not closed under
# the converse map, so its keep rate is meaningless (see screen_residue.sh).
# Across all residues, "keep iff canon(T) <= canon(conv(T))" keeps exactly one of
# each converse pair plus every self-converse host, so
#     instances == (D11 + S11)/2,  S11 = the self-converse count at n=11.
# S11 IS published: OEIS A002785(11) = 279,968, so the target is EXACT rather
# than a bracket.  This was a factor bracketed in [1.98, 2.001] until 2026-09-09,
# on the belief that S11 was unpublished; a keep rule correct on all but a handful
# of converse pairs sits at 1.999 and would have passed that bracket.  Corroborated
# three ways before being trusted: our own exhaustive n=10 count found 8,784
# self-converse among all 9,733,056 (= A002785(10)); A002785(12) = 1,492,288 is the
# size of the order-12 self-converse family we swept; and D11 + S11 is even, as it
# must be, since D11 counts converse pairs with the self-converse ones as fixed
# points.  Both this file and Appendix D of the paper must state the same target,
# so it is derived here from D11 and S11 rather than written down.
LOGS=${N12_LOGS:-slurm}      # overridable so the recovery path below is testable
G=$(awk -F'[= ]' '{for(i=1;i<=NF;i++)if($i=="generated")G+=$(i+1)}END{print G+0}' "$SNAP")
I=$(awk -F'[= ]' '{for(i=1;i<=NF;i++)if($i=="instances")I+=$(i+1)}END{print I+0}' "$SNAP")
if [ "${G:-0}" -eq 0 ] && [ "${I:-0}" -gt 0 ]; then
  # Markers written before generated= existed.  Recover it from the slurm logs,
  # one line per residue, counting ONLY residues that actually have a marker --
  # a residue that printed its counts and then died must not be counted as done.
  awk -F'[= ]' '/^res=/{print $2}' "$SNAP" > "$OUT/.tags" || true
  G=$(awk 'NR==FNR{ok[$0]=1;next}
           /^res=[0-9]+ generated=[0-9]+ screened=[0-9]+$/{
             split($1,a,"="); split($2,b,"="); if (a[2] in ok) g[a[2]]=b[2]}
           END{s=0; for(k in g) s+=g[k]; print s+0}' "$OUT/.tags" "$LOGS"/*.out 2>/dev/null || echo 0)
  rm -f "$OUT/.tags"
  [ "${G:-0}" -gt 0 ] && echo "  (generated= recovered from slurm/*.out: these markers predate the field)"
fi
# The self-converse hosts are COUNTED by the filter and carried in the markers as
# self=, so S11 has a second, independent measurement.  Older markers predate the
# field; only use the sum when every one of them carries it.
SELF=$(awk -F'[= ]' '{for(i=1;i<=NF;i++)if($i=="self")S+=$(i+1)}END{print S+0}' "$SNAP")
NSELF=$(grep -c ' self=' "$SNAP" || true)
if [ "${G:-0}" -gt 0 ] && [ "${I:-0}" -gt 0 ]; then
  awk -v g="$G" -v i="$I" -v d11="$D11" -v spub="$S11_PUB" \
      -v self="$SELF" -v nself="${NSELF:-0}" -v n="$n" 'BEGIN{
    printf "converse halving: %d generated, %d screened, factor %.4f\n", g, i, g/i
    if (g > d11) {
      printf "FATAL: generated %d EXCEEDS the %d order-11 classes -- residues overlap\n", g, d11
      exit 1 }
    if (g < d11) {
      # 4 dp, not 2: at 40,000 markers minus one residue this printed
      # "(100.00%), 33248 to go" -- a rounded 100% next to a nonzero shortfall.
      printf "  INCOMPLETE: %d of %d classes generated (%.4f%%), %d to go\n", g, d11, 100*g/d11, d11-g
      print  "  (the factor is meaningless until every residue is done: residues are"
      print  "   not closed under the converse map)"
      exit 0 }
    printf "  ALL %d order-11 classes generated -- census gate PASSED\n", d11
    # THE FLOOR, AND IT NEEDS NO PUBLISHED CONSTANT.  "Keep iff canon(T) <=
    # canon(conv(T))" decides a pair (T, conv T) by comparing the SAME two
    # canonical forms in opposite order, so exactly one host of every pair
    # survives -- two if it is self-converse, none never.  Hence kept >= D11/2
    # for any correct run whatsoever, and kept == (D11 + S11)/2 identifies S11.
    # A count below the floor cannot be a wrong S11 and cannot be a wrong keep
    # rule: it means hosts were LOST between the generator and the marker, i.e.
    # order-11 classes that nothing ever screened.  That is a hole in the case
    # analysis, so it is fatal.  (2026-09-12: the completed census reported
    # 443,771,294, which is 8,105,330 below the floor.)
    floor = d11 / 2
    if (i < floor) {
      printf "FATAL: kept %d, which is %d BELOW the floor D11/2 = %d\n", i, floor-i, floor
      print  "  No keep rule can do this: one host of every converse pair always survives."
      print  "  Hosts went MISSING, so that many order-11 classes were never screened and"
      print  "  the case analysis has a hole.  Run filter_log_check.sh, then halving_audit.sh."
      exit 1 }
    s_implied = 2*i - d11
    printf "  the run MEASURES S11 = 2*kept - D11 = %d self-converse order-11 tournaments\n", s_implied
    if (nself == n) {
      printf "  the filters COUNTED %d self-converse hosts directly\n", self
      if (self != s_implied) {
        printf "FATAL: the two measurements of S11 disagree, %d counted vs %d implied\n", self, s_implied
        print  "  They are independent, so one of the halving and the counting is wrong."
        exit 1 }
    } else
      printf "  (only %d of %d markers carry self=, so the direct count is not usable)\n", nself, n
    if (s_implied != spub) {
      printf "FATAL: S11 measures %d but A002785 at n=11 is %d\n", s_implied, spub
      printf "  off by %d.  The published value is confirmed, so it is the HALVING that\n", s_implied-spub
      print  "  is wrong -- or hosts went missing, which the floor above would have caught\n" \
             "  only if enough of them had.  Do NOT edit the constant to match the run."
      exit 1 }
    printf "  halving EXACT: kept %d = (D11 + S11)/2, D11 from A000568, S11 as measured\n", i }'
fi
exit 0
