#!/bin/bash
# JZ fallback for the n=11 five-inducibility census (only needed if the local
# run cannot finish or a large ILP residual appears; the pipeline is the same).
# Each array task = one gentourng res/mod slice, generated ON THE NODE — no
# tournament file is ever materialized or transferred.
#
# Adjust ACCOUNT/partition to the usual settings (cf. Cluster.R conventions);
# then: sbatch --array=0-63 n11_census.slurm
# Afterwards: bash n11_aggregate.sh $WORK/n11_census 64
#SBATCH --job-name=n11census
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --time=03:00:00
#SBATCH --output=n11_%a.out
#SBATCH --error=n11_%a.err

MOD=64
RES=${SLURM_ARRAY_TASK_ID}
KIT=${KIT:-$WORK/n11_kit}          # contains n11_worker.sh, bin/, gentourng
OUT=${OUTDIR:-$WORK/n11_census}
mkdir -p "$OUT"
bash "$KIT/n11_worker.sh" "$RES" "$MOD" "$OUT" "$KIT/bin" "$KIT/gentourng"
