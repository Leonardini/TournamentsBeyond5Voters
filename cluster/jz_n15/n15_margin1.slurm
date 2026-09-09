#!/bin/bash
#SBATCH --job-name=n15reg
#SBATCH --account=lia@cpu
#SBATCH --partition=cpu_p1
#SBATCH --qos=qos_cpu-t3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --time=20:00:00
#SBATCH --array=0-599
#SBATCH --output=KInduceDFS/jz_n15/slurm/n15_%A_%a.out
#SBATCH --error=KInduceDFS/jz_n15/slurm/n15_%A_%a.out
#
# Screen ALL 18,400,989,629 regular tournaments on 15 vertices (OEIS A096368(7)), margin-1
# 5-inducibility.  Every UNSAT is a non-5-inducible regular n=15 tournament.
#
# NO --mem.  Jean-Zay REJECTS it: RAM is strictly proportional to
# --cpus-per-task (~4-4.8 GB/core).  This engine uses ~2 MB, so 1 core is
# ample.  Do not add a memory flag.
#
# SHARD SIZE IS THE CRITICAL PARAMETER, not a free choice.  kinduce20 pays a
# ~17.6 s one-time setup per PROCESS (building the per-mask base-state cache)
# and only ~101 us per instance after that.  Cost per residue is therefore
#     17.6 s  +  instances x 130 us     (130 = 101 search + 29 generation)
# so shrinking residues multiplies the setup term (re-derived 2026-09-03 on the
# corrected 18,400,989,629 total, laptop rate):
#     MOD = 100000 -> 1,154 core-h   (489 h of pure repeated setup)
#     MOD =   6000 ->   694 core-h   ( 29 h of setup, 4%)   <-- chosen
#     MOD =   1000 ->   670 core-h   (  5 h, but 30 min checkpoint granularity)
# MOD=6000 gives ~3.1M instances on AVERAGE (NOT 2.0M -- the 12,007,554,066
# total this was sized from is wrong, see HANDOFF.md).  gentourng splits by
# INPUT chunk and makes NO promise about output-class sizes; 20 sampled
# residues ran 2.16M..5.02M and an order-of-magnitude spread is possible, so
# ~7 min per residue ON THE LAPTOP: setup amortised to 4%, and a wall-kill
# costs at most one residue.  --time is 20 h, not 6: the fattest residue is
# 653 s locally and JZ measured >= 4.3x slower, so 10 residues per task can
# approach 8 h.  Trade-off: a longer request queues longer on JZ; the
# alternative is --array=0-1199 (5 residues each) at --time=10:00:00.
#
# Checkpoint granularity is ONE RESIDUE, deliberately -- the end-only-save
# pattern has wiped whole campaigns on this project before.
#
# Submit FROM THE REPO ROOT (this script does not cd).
#
# The --output directory above MUST already exist: SLURM opens that file
# before this body runs, so the mkdir below cannot help it.  It is kept in
# git via KInduceDFS/jz_n15/slurm/.gitkeep -- do not delete that.
set -u
MOD=${N15_MOD:-6000}
OUT=${N15_OUT:-KInduceDFS/jz_n15/results_margin1}
MARGIN=${N15_MARGIN:-exact}
A=${SLURM_ARRAY_TASK_COUNT:-1}
T=${SLURM_ARRAY_TASK_ID:-0}
mkdir -p KInduceDFS/jz_n15/slurm "$OUT"
echo "task $T of $A  MOD=$MOD  margin=$MARGIN  out=$OUT  host=$(hostname)  start=$(date)"
n=0; fail=0
for ((RES=T; RES<MOD; RES+=A)); do
  if KInduceDFS/jz_n15/screen_residue.sh "$RES" "$MOD" "$OUT" "$MARGIN"; then
    n=$((n+1))
  else
    echo "residue $RES FAILED -- left unmarked so a resubmit retries it"
    fail=$((fail+1))
  fi
done
echo "task $T finished: $n residues done, $fail failed, $(date)"
