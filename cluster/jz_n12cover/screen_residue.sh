#!/bin/bash
# Screen ONE residue class of the 903,753,248 order-11 tournaments.
#
# For each host L it settles ALL 2^11 = 2,048 one-vertex extensions at once:
# a 5-voter profile inducing L, inserted at each of the 12^5 slot tuples, gives
# v's arc pattern as the MAJORITY OF FIVE SUFFIXES; OR those into a 2,048-bit
# set and stop when it fills.  A full set proves every order-12 tournament
# extending L is 5-inducible.  Every order-12 tournament is L+v for some L, so
# the sweep over all order-11 classes is a complete case analysis.  Redundancy
# (each order-12 class is reached ~12 times) is HARMLESS -- this is a case
# analysis, not a cover, so nothing needs de-duplicating.
#
# THREE TIERS, and the tier boundaries are a SOUNDNESS mechanism, not tuning:
#   1  margin-1, capped        -- settles ~99% and, since margin-1 SAT implies
#                                 majority SAT, settles BOTH statements at once
#   2  margin-1, uncapped      -- the caps can only DELAY coverage, so a tier-1
#                                 INCOMPLETE means "the cap bit", never a result
#   3  majority                -- for hosts that genuinely fail margin-1 (some
#                                 order-12 tournaments are majority-inducible
#                                 but not margin-1 inducible; margin-1 is known
#                                 to break by n=19)
# ONLY a tier-3 INCOMPLETE with exhausted=1 is a candidate counterexample.
# exhausted=0 means a cap or the time limit stopped the search and NOTHING may
# be concluded -- such a residue is left unmarked so a resubmit retries it.
#
#   usage: screen_residue.sh <res> <mod> <outdir>
set -u
# Caller-supplied paths are relative to the CALLER'S cwd.  Resolve them BEFORE the cd
# below, or a path like "KInduceDFS/<kit>/results" passed from the repo root gets re-read
# relative to this script's own directory and everything lands in a DOUBLED path
# (KInduceDFS/KInduceDFS/...).  That happened on 2026-09-06 and nearly cost a 210 core-h
# run its results: the scheduler said COMPLETED, the aggregator said 0 done.
# Same idiom as jz_reproduce/run.sh, which has always been correct.
# Capture our own directory ABSOLUTELY, before any cd.  The previous idiom was
#     . "$(cd "$(dirname "$0")/.." && pwd)/gt_path.sh"
# evaluated AFTER `cd "$(dirname "$0")"`.  $0 keeps its original relative value, so
# from inside jz_n12cover it tried `cd KInduceDFS/jz_n12cover/..`, which does not
# exist; the subshell produced the EMPTY string and the source path became
# "/gt_path.sh".  Every residue of the 2026-09-07 array then died on `GT: unbound
# variable` -- 0 of 40,000 done.  Absolute-then-cd cannot fail that way.
_KITDIR=$(cd "$(dirname "$0")" && pwd)
_ORIGPWD=$PWD
cd "$_KITDIR"
if [ "${1:-}" = "--check-paths" ]; then RES=0; MOD=1; OUT=$_ORIGPWD; CHECK=1
else RES=$1; MOD=$2; OUT=$3; CHECK=0; fi
case "$OUT" in /*) ;; *) OUT=$_ORIGPWD/$OUT ;; esac
SKIP=${COVER_SKIP:-4096}; PBN=${COVER_PBN:-200}
# T2 and T3 are now PER-INSTANCE decision caps, not per-host coverage budgets:
# an order-12 margin-1 decision measures at 14 ms, so 120 s is four orders of
# magnitude of headroom and anything hitting it is worth looking at by hand.
T2=${TIER2_TIME:-120}; T3=${TIER3_TIME:-600}
KINDUCE=${KINDUCE:-$_KITDIR/../kinduce}

. "$_KITDIR/../gt_path.sh"                          # sets GT; see that file
: "${GT:?gt_path.sh did not set GT -- sourced from $_KITDIR/../gt_path.sh}"

mkdir -p "$OUT/done" "$OUT/candidates" "$OUT/log" "$OUT/unresolved"
# A MARKER IS ONLY TRUSTED IF IT CARRIES generated=.  The vacuous run of
# 2026-09-07 wrote 40,000 markers claiming success having examined nothing, and
# because a unit with a marker is skipped, every resubmit after it was a no-op
# until someone remembered to delete them by hand.  generated= did not exist
# then, and it is written only by a pipeline that actually generated hosts, so it
# is exactly the right discriminator -- and this makes the recovery automatic
# instead of a step in COMMANDS.md that has to be remembered.
if [ -f "$OUT/done/r$RES" ]; then
  if grep -q "generated=" "$OUT/done/r$RES"; then echo "residue $RES already done"; exit 0; fi
  echo "residue $RES: marker predates generated= (vacuous run or old pipeline) -- redoing" >&2
fi

WORK=${JOBSCRATCH:-${SLURM_TMPDIR:-/tmp}}
# --check-paths must not share scratch with a live residue.  It runs as residue 0
# by construction, so on a node where WORK is a shared /tmp it used to compute the
# SAME temp names as a running residue 0 and then delete them from its EXIT trap:
# running the selftest while the sweep was working killed the sweep's host file
# mid-run, and the failure surfaced two tiers later as "awk: can't open file".
# Its own throwaway directory costs nothing and cannot collide.
if [ "$CHECK" = 1 ]; then
  WORK=$(mktemp -d) || exit 1
  trap 'rm -rf "$WORK"' EXIT
  B="$WORK/probe.bits"; B2="$WORK/probe_t2.bits"; B3="$WORK/probe_t3.bits"
else
  B="$WORK/n11_$RES.bits"; B2="$WORK/n11_${RES}_t2.bits"; B3="$WORK/n11_${RES}_t3.bits"
  trap 'rm -f "$B" "$B2" "$B3" "$B.half"' EXIT
fi
t0=$SECONDS

# GENERATOR FAILURE MUST NOT LOOK LIKE AN EMPTY RESIDUE.  This used to be
#     "$GT" 11 "$RES/$MOD" 2>/dev/null > "$B"
# so a missing gentourng had its "command not found" discarded, produced an empty $B,
# was read as a legitimately-empty residue, and got a DONE MARKER claiming success --
# which also stopped any resubmit from retrying it.  2026-09-07: all 40,000 residues
# came back instances=0 and the campaign reported 40000/40000 done, 0 candidates,
# 0 unresolved, having examined ZERO tournaments.  Fail loudly and leave NO marker.
command -v "$GT" >/dev/null 2>&1 || [ -x "$GT" ] || {
  echo "FATAL residue $RES: no gentourng at '$GT'." >&2
  echo "  set GENTOURNG=/path/to/gentourng or NAUTY_DIR, and see COMMANDS.md step 0." >&2
  exit 1; }
if [ "$CHECK" = 1 ]; then
  # Path-only mode for the selftest: everything above has resolved, so report and
  # stop before doing any work.  This exists because selftest.sh and this script
  # used to compute the path to gt_path.sh by DIFFERENT idioms -- the selftest's
  # was correct and this one's was not, so the kit could pass its own test while
  # every production residue died.  The selftest now calls this, in the same
  # invocation shape the batch script uses.
  echo "PATHS OK  kitdir=$_KITDIR  gentourng=$GT  kcover=$(pwd)/kcover"
  [ -x ./kcover ] || { echo "FATAL: no kcover binary; run build.sh" >&2; exit 1; }
  # kinduce decides the leftover masks, so its absence would kill every residue
  # that has any -- i.e. all of them.  Check it by RUNNING it, on a real order-12
  # instance, not by testing the path: a binary built for another architecture
  # exists and is executable and still fails at the first residue.
  [ -x "$KINDUCE" ] || { echo "FATAL: no kinduce at '$KINDUCE'; run build.sh" >&2; exit 1; }
  _t12=$(printf '1%.0s' $(seq 1 66))
  if ! _kout=$(printf '%s\n' "$_t12" | { cat > "$WORK/t12.bits"; "$KINDUCE" --batch "$WORK/t12.bits" --n 12 --k 5 --margin exact --inc --time 30 2>&1; }); then
    echo "FATAL: kinduce failed on the transitive order-12 instance:" >&2
    printf '    %s\n' "$_kout" >&2; rm -f "$WORK/t12.bits"; exit 1
  fi
  rm -f "$WORK/t12.bits"
  # The transitive tournament is 5-inducible at margin 1 by five identical
  # voters, so this is a KNOWN ANSWER: anything but SAT means a broken engine.
  case "$_kout" in
    *"BATCH 0 SAT"*) echo "  kinduce: $KINDUCE, transitive order-12 known-answer SAT" ;;
    *) echo "FATAL: kinduce did not decide the transitive order-12 instance SAT:" >&2
       printf '    %s\n' "$_kout" >&2; exit 1 ;;
  esac
  # labelg is needed for the converse halving, and a MISSING binary is exactly
  # the failure this kit has already shipped twice.  Check it here, where the
  # selftest will see it, rather than at residue 0 on a compute node.
  if [ "${N12_NOHALVE:-0}" = 1 ]; then
    echo "  halving: DISABLED by N12_NOHALVE=1 (labelg not required)"
  elif [ -n "${LABELG:-}" ] && [ -x "$LABELG" ]; then
    echo "  halving: ENABLED, labelg=$LABELG"
    # Run the filter AS A CHILD PROCESS, which is the only way to test that
    # LABELG actually reaches it.  gt_path.sh used to set it as a plain shell
    # variable, so this very check passed while every child died on
    # "LABELG not set".  Checking a variable in our own shell proves nothing
    # about the process that needs it.
    _probe=$("$GT" -q 11 0/400000 2>/dev/null | head -3)
    [ -n "$_probe" ] || { echo "FATAL: gentourng produced no host to test the filter with" >&2; exit 1; }
    if ! _out=$(printf '%s\n' "$_probe" | ./converse_filter.sh 11 2>&1); then
      echo "FATAL: the converse filter fails when run as a child process:" >&2
      printf '    %s\n' "$_out" >&2
      exit 1
    fi
    echo "  filter: runs as a child process and inherits its environment"
  else
    echo "FATAL: converse halving is on but no labelg found. It should sit beside" >&2
    echo "  gentourng at $(dirname "$GT"). Set LABELG=/path/to/labelg, or run with" >&2
    echo "  N12_NOHALVE=1 to sweep every host and forgo the factor of two." >&2
    exit 1
  fi
  exit 0
fi
GTERR="$WORK/gt_$RES.err"
"$GT" 11 "$RES/$MOD" 2>"$GTERR" > "$B"
rc=$?
NGEN=$(wc -l < "$B" | tr -d ' ')
# nauty writes its OWN banner to STDERR unless given -q: ">A <argv>" on entry and
# ">Z K graphs generated in T sec" on exit.  So "the generator wrote to stderr" is
# NOT a failure signal, and the version of this test that treated it as one killed
# every one of the 40,000 residues of job 1888028 in six seconds flat with the
# generator working perfectly -- the third consecutive fatal-at-startup fault in
# this one script, after the empty gt_path.sh source and the python3 dependency.
#
# Use the banner as a POSITIVE check instead: >Z must be there (the generator ran
# to completion) and its count must equal the number of lines we actually received.
# That is strictly STRONGER than the old test -- it catches a truncated write, a
# full filesystem, or a generator killed mid-stream, none of which "no stderr"
# could see -- while a verified ">Z 0" empty class passes, which matters because
# gentourng's res/mod split saturates and high classes are legitimately empty.
# Systematic emptiness, the 2026-09-07 failure, is caught globally instead, by the
# census gate in aggregate.sh: generated summed over residues must equal D_11.
ZK=$(sed -nE 's/^>Z ([0-9]+) graphs generated.*/\1/p' "$GTERR" | tail -1)
GTBAD=$(grep -v '^>[AZ]' "$GTERR" || true)
if [ "$rc" -ne 0 ] || [ -n "$GTBAD" ] || [ -z "$ZK" ] || [ "$ZK" -ne "$NGEN" ]; then
  echo "FATAL residue $RES: gentourng exit=$rc, banner reports '${ZK:-<no >Z line>}' graphs, received $NGEN lines:" >&2
  sed 's/^/    /' "$GTERR" >&2
  rm -f "$GTERR"
  exit 1                      # NO done marker: a resubmit must retry this residue
fi
rm -f "$GTERR"

# ---- halve the hosts: keep one of each converse pair ---------------------
# A tournament and its converse have the same majority dimension, and extensions
# match up exactly: conv(T + out-set S) = conv(T) + out-set complement(S).  So
# screening one host of each pair still settles every order-12 tournament, and
# self-converse hosts (canon(T) == canon(conv(T))) are kept because they pair with
# nothing.  converse_filter.py --selftest verifies both the counts and that
# correspondence exhaustively.  Costs ~5.6 us per host against the ~32 ms of
# screening it halves.
if [ "${N12_NOHALVE:-0}" = 1 ]; then
  echo "residue $RES: converse halving DISABLED by N12_NOHALVE=1"
else
  BH="$B.half"
  # converse_filter.sh, NOT the .py: nothing in the compute-node path may need an
  # interpreter.  python3 is not in the default PATH on a Jean Zay compute node
  # and this script loads no module, so the .py version killed every residue
  # while the selftest -- which runs on the login node -- passed.
  if ! ./converse_filter.sh 11 stats < "$B" > "$BH" 2>"$WORK/cf_$RES.err"; then
    echo "FATAL residue $RES: converse filter failed:" >&2
    sed 's/^/    /' "$WORK/cf_$RES.err" >&2
    rm -f "$BH" "$WORK/cf_$RES.err"
    exit 1                    # NO done marker.  Never silently skip the halving:
  fi                          # a bypass must be an explicit N12_NOHALVE=1.
  sed 's/^/    /' "$WORK/cf_$RES.err" >&2; rm -f "$WORK/cf_$RES.err"
  NH=$(wc -l < "$BH" | tr -d ' ')
  # A RESIDUE IS NOT CLOSED UNDER THE CONVERSE MAP, so the per-residue keep rate is
  # NOT 1/2 and must not be checked against it.  gentourng splits by generation-tree
  # prefix, which correlates with canonical order, so a host's converse usually
  # lands in a DIFFERENT residue: measured, residue 0/4000 at n=11 keeps 1,242 of
  # 7,624, a factor of 6.1.  The rule "keep iff canon(T) <= canon(conv(T))" depends
  # only on the isomorphism class, so across the residues -- which partition every
  # class -- exactly one of each pair survives and the GLOBAL factor is still
  # (N+S)/2.  An earlier version of this guard demanded NH >= NGEN/2 and would have
  # aborted essentially every residue.  The global check lives in aggregate.sh,
  # which is the only place it can be made.
  [ "$NH" -le "$NGEN" ] || { echo "FATAL residue $RES: filter kept $NH of $NGEN -- a filter cannot add" >&2; exit 1; }
  [ "$NGEN" -eq 0 ] || [ "$NH" -gt 0 ] || echo "residue $RES: filter kept NOTHING of $NGEN -- possible but extraordinary, check aggregate.sh totals" >&2
  mv "$BH" "$B"
fi
NINST=$(wc -l < "$B" | tr -d ' ')
echo "res=$RES generated=$NGEN screened=$NINST"
# An empty res/mod slice is ROUTINE, not extraordinary: gentourng splits by
# generation-tree prefix and the split SATURATES, so once MOD exceeds the number of
# nodes at the level it splits on, the surplus classes are empty and the census
# concentrates in the rest.  Job 1888028 showed class=35000/40000 through
# class=39000/40000 all reporting ">Z 0 graphs" at n=11.  The union over residues
# is still every class, so this is a real outcome: record it done, with generated=
# so the census gate can see it, and say so in the log.  Do NOT compute a
# "mean residue size" and reason from it -- the distribution is nowhere near
# uniform (residue 0 of 4000 holds 7,624 hosts against a mean of 225,938).
[ "$NINST" -eq 0 ] && { echo "residue $RES: gentourng succeeded but produced NO instances" >&2;
  echo "res=$RES generated=$NGEN instances=0 tier1all=0 tier2fixed=0 tier3fixed=0 candidates=0 secs=0" > "$OUT/done/r$RES"; exit 0; }

. "$_KITDIR/tiers.sh"          # the pipeline itself, shared with eval_shard.sh
run_tiers "$B" "r$RES"

# An ABORTED instance is a budget running out, NOT a result.  Leave the residue
# unmarked so a resubmit (with larger TIER2_TIME/TIER3_TIME) retries it.
if [ "$UNRES" -gt 0 ]; then
  echo "res=$RES UNRESOLVED=$UNRES instances hit their time cap -- left unmarked for retry" >&2
  exit 1
fi
echo "res=$RES generated=$NGEN instances=$NINST tier1all=$A1 leftover=$NLEFT tier2fixed=$FIX2 tier3fixed=$FIX3 candidates=$CAND secs=$((SECONDS-t0))" > "$OUT/done/r$RES"
cat "$OUT/done/r$RES"
rm -f "$WORK/inc1_$RES" "$WORK/inc2_$RES" "$WORK/t1_$RES.log" "$WORK/t2_$RES.log" "$WORK/t3_$RES.log"
