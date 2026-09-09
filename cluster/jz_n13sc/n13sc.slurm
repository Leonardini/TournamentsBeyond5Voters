#!/bin/bash
#SBATCH --job-name=n13sc
#SBATCH --account=lia@cpu
#SBATCH --partition=cpu_p1
#SBATCH --qos=qos_cpu-t3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --time=20:00:00
#SBATCH --array=0-499
#SBATCH --output=KInduceDFS/jz_n13sc/slurm/n13sc_%A_%a.out
#SBATCH --error=KInduceDFS/jz_n13sc/slurm/n13sc_%A_%a.out
#
# Self-converse tournaments on 13 vertices, MARGIN 1, k = 5.
#
# THIS IS A HUNT, NOT A CENSUS.  The cheapest open form of the margin-1 question
# is "the smallest tournament that is not margin-1 5-inducible".  The record
# holder is Paley(19); n=13 in general is unswept.  A single UNSAT here drops
# that from 19 to 13 and IS the result -- so hits are printed the moment they
# occur, not aggregated at the end.
#
# Margin 1 first because margin-1 SAT implies majority SAT: anything settled
# here needs no majority run.
#
# WHAT IS ALREADY DONE, LOCALLY, AND MUST NOT BE REDONE (2026-09-05):
#   regular hosts (imbalance 0)        11,237  skipped -- every regular
#                                              tournament on n<=13 is already
#                                              known 5-inducible at BOTH margins
#   imbalance bucket 4, in full       116,765  all SAT
#   imbalance bucket 8, in full       581,515  all SAT
#   every possibly-symmetric host     319,270  all SAT, across all buckets
#   ------------------------------------------
#   settled                         1,028,787  zero UNSAT
# prepare.sh reproduces the same partition, so those files can be skipped.
# Remaining to sweep: about 94.4 million, all of them PROVABLY RIGID.
#
# WHAT A CLEAN RESULT WOULD MEAN.  Colour refinement discretising is a theorem
# that Aut is trivial, so the 319,270 already swept are a genuine SUPERSET of
# every self-converse tournament on 13 vertices with a non-trivial automorphism
# group.  If an obstruction exists here it therefore has TRIVIAL Aut -- unlike
# Paley(19) (|Aut| = 171) and unlike dr19_g2, the only two known.  That is a
# reason to think this sweep comes back empty, and a reason the result is worth
# having anyway: it would say the phenomenon needs symmetry.
#
# COST.  About 10 ms per host on the laptop, so roughly 265 core-h; expect more
# here.  Measure with probe_rate.sh before sizing the array rather than trusting
# that figure -- the n=15 campaign found this cluster >= 4.3x slower than the
# laptop on a different engine.
#
# NO --mem: Jean-Zay rejects it; RAM is proportional to --cpus-per-task.  The
# engine needs a few MB.
#
# NO SYMMETRY BREAK.  Self-converseness is an ANTI-automorphism (u->v iff
# sigma(v)->sigma(u)); it is not in Aut(T) and licenses no vertex break.  And
# --toporb is worthless at margin 1 (0.0007% of nodes) and is the one flag that
# can silently discard profiles -- never pass it here.
#
# Checkpoint granularity is one shard, marked done only on success, so a
# wall-kill costs at most one shard.  Resubmit until aggregate.sh stops rising.
#
# Submit FROM THE REPO ROOT.
set -u
W=${N13_WORK:-${SCRATCH:-/tmp}/n13sc}
OUT=${N13_OUT:-KInduceDFS/jz_n13sc/results}
# OUT is used AFTER the cd into $W below, so make it absolute HERE, while we are
# still in the submit directory -- otherwise every marker lands under $W.
case "$OUT" in /*) ;; *) OUT=$PWD/$OUT ;; esac  # _ORIGPWD-equivalent
PER=${N13_PER:-200000}                  # hosts per shard
A=${SLURM_ARRAY_TASK_COUNT:-1}
T=${SLURM_ARRAY_TASK_ID:-0}
DEADLINE=${N13_DEADLINE:-68400}         # 19 h of a 20 h wall
mkdir -p KInduceDFS/jz_n13sc/slurm "$OUT/done" "$OUT/hits"
cd "$W" || { echo "run prepare.sh first (N13_WORK=$W)"; exit 1; }

# shards are slices of the rigid buckets, most balanced first
ls rigid/imb*.txt 2>/dev/null | sed 's|rigid/imb||; s|\.txt$||' | sort -n \
  | sed 's|^|rigid/imb|; s|$|.txt|' > .order || exit 1
mapfile -t FILES < .order
K=$(cd "$OLDPWD" && pwd)/KInduceDFS

echo "task $T of $A  per=$PER  work=$W  start=$(date)"
t0=$SECONDS; n=0; idx=0
for f in "${FILES[@]}"; do
  total=$(wc -l < "$f" | tr -d ' ')
  for (( lo=1; lo<=total; lo+=PER )); do
    idx=$((idx+1))
    [ $(( (idx-1) % A )) -ne "$T" ] && continue
    tag="$(basename "$f" .txt)_$lo"
    [ -f "$OUT/done/$tag" ] && continue
    if [ $((SECONDS-t0)) -ge "$DEADLINE" ]; then
      echo "deadline reached, stopping cleanly"; exit 0
    fi
    tmp=${JOBSCRATCH:-${SLURM_TMPDIR:-/tmp}}/$tag.bits
    sed -n "${lo},$((lo+PER-1))p" "$f" > "$tmp"
    got=$(wc -l < "$tmp" | tr -d ' ')
    "$K/kinduce" --batch "$tmp" --n 13 --k 5 --margin exact --inc --time 300 \
        > "$tmp.log" 2>&1
    ran=$(grep -c '^BATCH ' "$tmp.log")
    if [ "$ran" -ne "$got" ]; then
      echo "$tag: ran $ran of $got -- NOT a verdict, leaving unmarked" >&2
      rm -f "$tmp" "$tmp.log"; continue
    fi
    U=$(grep -c ' UNSAT ' "$tmp.log"); A2=$(grep -c ' ABORTED ' "$tmp.log")
    if [ "$U" -gt 0 ]; then
      echo "*** UNSAT at n=13 margin 1 in $tag -- a NEW smallest known margin-1 obstruction"
      grep ' UNSAT ' "$tmp.log" | awk '{print $2}' | while read i; do
        sed -n "$((i+1))p" "$tmp"; done | tee "$OUT/hits/$tag.bits"
    fi
    echo "hosts=$got unsat=$U aborted=$A2" > "$OUT/done/$tag"
    n=$((n+1)); rm -f "$tmp" "$tmp.log"
  done
done
echo "task $T finished: $n shards, $(date)"
