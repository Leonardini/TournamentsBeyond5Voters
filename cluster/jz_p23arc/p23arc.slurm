#!/bin/bash
#SBATCH --job-name=p23arc
#SBATCH --account=lia@cpu
#SBATCH --partition=cpu_p1
#SBATCH --qos=qos_cpu-t3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --time=20:00:00
#SBATCH --array=0-267
#SBATCH --output=KInduceDFS/jz_p23arc/slurm/p23arc_%A_%a.out
#SBATCH --error=KInduceDFS/jz_p23arc/slurm/p23arc_%A_%a.out
#
# Blind T^e scan: is Paley(23) arc-critical?
#
#   8031 base states, no symmetry break (|Aut(T^e)| = 1), 224.1 s per base state
#   measured at matched load => ~500 core-h.
#
#   268 tasks x ~30 base states each.  At the measured rate that is ~1.9 h per
#   task on laptop-equivalent hardware; --time=20:00:00 leaves ample room even
#   if JZ runs several times slower.  Confirm the rate with COMMANDS.md step 3
#   BEFORE submitting -- the n=15 kit was once killed at its wall for exactly
#   this reason.
#
#   Base states are assigned STRIDED, not in blocks: task T takes
#   T, T+268, T+536, ...  A block assignment would concentrate any systematic
#   cost gradient in a few tasks; strided spreads it, so every task finishes in
#   about the same time and partial progress is even across the whole index
#   range.
set -u
cd "$SLURM_SUBMIT_DIR"
mkdir -p KInduceDFS/jz_p23arc/slurm

T=${SLURM_ARRAY_TASK_ID:-0}
A=268
N=8031
OUT=KInduceDFS/jz_p23arc/results

for ((B=T; B<N; B+=A)); do
  [ -f "$OUT/STOP" ] && { echo "STOP present -- a witness was found; exiting"; break; }
  KInduceDFS/jz_p23arc/screen_chunk.sh "$B" "$OUT" || \
      echo "base $B FAILED or was capped -- left unmarked so a resubmit retries it"
done
echo "task $T done"
