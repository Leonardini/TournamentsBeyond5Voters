#!/bin/bash
#SBATCH --job-name=n12audit
#SBATCH --account=lia@cpu
#SBATCH --partition=cpu_p1
#SBATCH --qos=qos_cpu-t3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --time=04:00:00
#SBATCH --array=0-199
#SBATCH --output=KInduceDFS/jz_n12cover/slurm/audit_%A_%a.out
#SBATCH --error=KInduceDFS/jz_n12cover/slurm/audit_%A_%a.out
#
# Find out where the census lost its hosts.  Generation and the converse halving
# only -- no screening, no solving.  See halving_audit.sh for the argument; in
# short, the completed census kept 443,771,294 of 903,753,248 order-11 classes,
# and the keep rule cannot go below 451,876,624, so hosts vanished.
#
# Submit from the repo root, then roll it up:
#     ...batch KInduceDFS/jz_n12cover/halving_audit.slurm
#     KInduceDFS/jz_n12cover/halving_audit_rollup.sh KInduceDFS/jz_n12cover/results
#
# MOD MUST MATCH THE CENSUS -- 40,000, the value the markers were written with.
# A different MOD partitions the classes differently, so the audit's residue r
# would not be the census's residue r and nothing could be compared residue by
# residue.  Do not override N12_MOD here for any reason.
#
# COST.  Two labelg canonical forms and one gentourng line per host: a few
# core-hours for the whole census against the 9,905 the screening took.  One core
# per task, no --mem (Jean Zay rejects it; RAM follows --cpus-per-task).
set -u
cd "$SLURM_SUBMIT_DIR"
OUT=${N12_OUT:-KInduceDFS/jz_n12cover/results}
MOD=${N12_MOD:-40000}
T=${SLURM_ARRAY_TASK_ID:-0}
A=${SLURM_ARRAY_TASK_COUNT:-1}
echo "audit task $T of $A, mod=$MOD, host=$(hostname), start=$(date)"
n=0; fail=0
for ((RES=T; RES<MOD; RES+=A)); do
  if KInduceDFS/jz_n12cover/halving_audit.sh "$RES" "$MOD" "$OUT" > /dev/null; then n=$((n+1))
  else echo "residue $RES FAILED to audit"; fail=$((fail+1)); fi
done
echo "audit task $T finished: $n residues, $fail failed, $(date)"
