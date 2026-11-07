#!/bin/bash
#SBATCH --job-name=n12cov
#SBATCH --account=lia@cpu
#SBATCH --partition=cpu_p1
#SBATCH --qos=qos_cpu-t3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --time=20:00:00
#SBATCH --array=0-999
#SBATCH --output=KInduceDFS/jz_n12cover/slurm/n12cov_%A_%a.out
#SBATCH --error=KInduceDFS/jz_n12cover/slurm/n12cov_%A_%a.out
#
# SHARDED variant: evaluates a PRE-GENERATED order-11 listing.  Preferred over
# n12cover.slurm, which calls gentourng inline.
#
# Why separate generation from evaluation: generation is 2.01 us/instance, i.e.
# 0.8 core-h for all 903,753,248, against thousands of core-h for evaluation --
# so it is free, and doing it once buys EVEN WORK UNITS (we slice the file, not
# gentourng's tree, whose residues run 8,957..164,154 and stop subdividing past
# some MOD) and retries that do not regenerate.
#
# N12_LIST must point at a directory of shards named sh_* .  If a previous
# campaign already left the listing on disk (there may be one under jz_11), use
# it -- but run verify_listing.sh on it FIRST.  A listing of the right size but
# the wrong convention, or a partial run, would evaluate the wrong tournaments
# and come back clean for the wrong reason.
#
# NO --mem.  Jean-Zay REJECTS it: RAM is proportional to --cpus-per-task.
#
# Checkpoint granularity is ONE SHARD.  A shard is marked done only on success,
# so a wall-kill or a budget time-out simply leaves it for the next submission.
# Resubmit until aggregate.sh stops rising; that is the workflow, not a failure.
#
# Submit FROM THE REPO ROOT (this script does not cd).
set -u
LIST=${N12_LIST:?set N12_LIST to the directory of sh_* shards}
OUT=${N12_OUT:-KInduceDFS/jz_n12cover/results}
A=${SLURM_ARRAY_TASK_COUNT:-1}
T=${SLURM_ARRAY_TASK_ID:-0}
DEADLINE=${N12_DEADLINE:-68400}          # 19 h of a 20 h wall: stop STARTING work
mkdir -p KInduceDFS/jz_n12cover/slurm "$OUT"
mapfile -t SHARDS < <(ls "$LIST"/sh_* 2>/dev/null | sort)
NS=${#SHARDS[@]}
[ "$NS" -eq 0 ] && { echo "no shards under $LIST" >&2; exit 1; }
echo "task $T of $A  shards=$NS  list=$LIST  out=$OUT  host=$(hostname)  start=$(date)"
n=0; fail=0; t0=$SECONDS
for ((I=T; I<NS; I+=A)); do
  if [ $((SECONDS-t0)) -ge "$DEADLINE" ]; then
    echo "deadline reached, stopping cleanly; remaining shards go to the next submission"
    break
  fi
  if KInduceDFS/jz_n12cover/eval_shard.sh "${SHARDS[$I]}" "$OUT"; then
    n=$((n+1))
  else
    echo "shard ${SHARDS[$I]} incomplete -- left unmarked so a resubmit retries it"
    fail=$((fail+1))
  fi
done
echo "task $T finished: $n shards done, $fail left for retry, $(date)"
