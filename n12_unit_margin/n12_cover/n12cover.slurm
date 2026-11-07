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
# Prove N(5) >= 13 by settling every one-vertex extension of every order-11
# tournament.  All 903,753,248 order-11 classes are 5-inducible (paper 1); for
# each, this settles all 2^11 = 2,048 order-12 tournaments extending it.  Every
# order-12 tournament is such an extension, so the sweep is a complete case
# analysis, and the ~12x redundancy is harmless (case analysis, not a cover).
#
# NO --mem.  Jean-Zay REJECTS it: RAM is proportional to --cpus-per-task.  The
# engine uses a few MB (the mask bitset is 256 bytes); 1 core is ample.
#
# SIZING IS NOT SETTLED -- RUN probe_rate.sh ON A COMPUTE NODE FIRST.
# Every local figure was measured while an 11-core job held the laptop, and the
# numbers are inconsistent in exactly the way contention produces (a 100-host
# probe implied 161 ms/instance where a 2,000-host run implied 30).  The
# laptop range is 11-32 ms/instance => 2,800-8,000 core-h; JZ measured >= 4.3x
# slower than this laptop on the n=15 campaign, which would put it at
# 12,000-34,000 core-h.  That factor is a GUESS carried over from a different
# engine at a different n.  Measure it, then set MOD and the array size.
#
# RESIDUE SIZES ARE VERY UNEVEN and MOD SATURATES.  gentourng splits by INPUT
# chunk: at n=11, res=7 yields 8,957 instances and res=1234 yields 164,154, an
# 18x spread -- and mod=40000 and mod=200000 give IDENTICAL counts, so past
# some granularity it stops subdividing and a larger MOD buys nothing but empty
# residues.  Do not size by MOD alone; sample residue sizes first
# (probe_rate.sh prints them).
#
# Checkpoint granularity is ONE RESIDUE, deliberately -- the end-only-save
# pattern has wiped whole campaigns on this project before.  A residue is
# marked done ONLY on success, so a wall-kill or a time-out simply leaves it
# for the next submission.  Resubmit until aggregate.sh reports every residue
# done; that is the intended workflow, not a failure mode.
#
# Submit FROM THE REPO ROOT (this script does not cd).
set -u
MOD=${N12_MOD:-40000}
OUT=${N12_OUT:-KInduceDFS/jz_n12cover/results}
A=${SLURM_ARRAY_TASK_COUNT:-1}
T=${SLURM_ARRAY_TASK_ID:-0}
# The internal deadline exists so a task stops STARTING residues it cannot
# finish, rather than being killed mid-residue and wasting it.  It used to be the
# constant 68400 -- 19 h, typed against the 20 h wall in the header above.  Lower
# --time on the command line and that constant never fires, so every task dies at
# the wall in the middle of a residue; raise --time and it stops early for no
# reason.  Ask the scheduler instead: SLURM_JOB_END_TIME is its own answer, so the
# deadline follows --time automatically and shortening the wall is safe.
if [ -n "${N12_DEADLINE:-}" ]; then
  DEADLINE=$N12_DEADLINE                                   # explicit override wins
elif [ -n "${SLURM_JOB_END_TIME:-}" ]; then
  DEADLINE=$(( SLURM_JOB_END_TIME - $(date +%s) - 3600 ))   # keep an hour in hand
  [ "$DEADLINE" -ge 900 ] || DEADLINE=900
else
  DEADLINE=68400                                           # not under SLURM at all
fi
mkdir -p KInduceDFS/jz_n12cover/slurm "$OUT"
t0_epoch=$(date +%s)
echo "task $T of $A  MOD=$MOD  out=$OUT  host=$(hostname)  start=$(date)"
n=0; fail=0; t0=$SECONDS
# "Cannot plausibly finish" has to be measured, not assumed.  A residue is a few
# HOURS on this cluster while an empty class is a second, so a fixed margin is
# either far too small (the task starts a residue with an hour left and is killed
# mid-way, wasting it) or far too large.  Seed the estimate from what residues
# have actually cost in this results directory -- the markers carry secs= -- and
# keep updating it as this task finishes its own.  A campaign that has run before
# therefore prices itself, and shortening --time becomes safe rather than a trap.
# The gate below used to key off the MAXIMUM residue cost ever recorded, times
# 1.2.  That is monotone and global, so ONE pathological residue permanently
# raised the bar for every task in every later submission: with a ~42,500 s
# residue on record, tasks refused to start anything with less than ~14 h left
# and idled two thirds of a 20 h wall.  Measured on the 2026-09-09 run: 20,022
# residues done across 1000 tasks, 5.84 h of work per task against a 19 h
# budget, i.e. of order 14,000 core-hours idle against 5,838 useful -- and it
# ratchets, since MAXRES only ever grows.
#
# Two changes.  Key off a high PERCENTILE rather than the max, so one outlier
# cannot set policy; and CAP the reservation at a fraction of the budget, so the
# gate can never idle most of an allocation whatever the data says.
#
# The trade this gets right: an unfinished residue costs only its own wasted
# time.  No marker is written unless it completed, so a resubmit retries it and
# nothing is corrupted.  Reserving 14 h to avoid losing 4 is the wrong way round.
#
# find -exec, not "$OUT"/done/* : at 20,000+ markers on a long Lustre path the
# glob approaches ARG_MAX, and if it blew, awk would fail, MAXRES would fall
# back to 0 and the gate would vanish silently.
PCTL=${N12_PCTL:-90}
P_RES=$(find "$OUT/done" -type f -exec cat {} + 2>/dev/null |
        tr ' ' '\n' | grep '^secs=' | cut -d= -f2 | sort -n |
        awk -v p="$PCTL" '{a[n++]=$1} END{if(n==0){print 0; exit}
                           i=int((p/100)*(n-1)+0.5); print a[i]+0}')
MAXRES=${P_RES:-0}
echo "p${PCTL} residue cost on record: ${MAXRES}s (was keyed off the maximum, which one outlier could set)"
for ((RES=T; RES<MOD; RES+=A)); do
  # Time left, from the scheduler where it knows and from the deadline otherwise.
  if [ -n "${SLURM_JOB_END_TIME:-}" ]; then REMAIN=$(( SLURM_JOB_END_TIME - $(date +%s) ))
  else                                      REMAIN=$(( DEADLINE - (SECONDS - t0) )); fi
  NEED=$(( MAXRES * 12 / 10 ))               # 20% over the p90
  [ "$NEED" -ge 900 ] || NEED=900            # and never less than a quarter hour
  # Never reserve more than this share of the budget: beyond it the task spends
  # more time refusing work than a lost residue could ever cost.
  BUDGET=${SLURM_JOB_END_TIME:+$(( SLURM_JOB_END_TIME - t0_epoch ))}
  BUDGET=${BUDGET:-$DEADLINE}
  CAP=$(( BUDGET * ${N12_RESERVE_PCT:-30} / 100 ))
  [ "$NEED" -le "$CAP" ] || { echo "reservation ${NEED}s capped to ${CAP}s (${N12_RESERVE_PCT:-30}% of budget)"; NEED=$CAP; }
  if [ "$REMAIN" -lt "$NEED" ]; then
    echo "${REMAIN}s left, ${NEED}s needed for a residue: stopping cleanly with $((MOD-RES)) residues left for the next submission"
    break
  fi
  _r0=$SECONDS
  if KInduceDFS/jz_n12cover/screen_residue.sh "$RES" "$MOD" "$OUT"; then
    n=$((n+1))
    _d=$((SECONDS-_r0))
    [ "$_d" -gt "$MAXRES" ] && MAXRES=$_d    # the estimate only ever grows
  else
    echo "residue $RES incomplete -- left unmarked so a resubmit retries it"
    fail=$((fail+1))
  fi
done
echo "task $T finished: $n residues done, $fail left for retry, $(date)"
