#!/bin/bash
#SBATCH --job-name=cert
#SBATCH --account=lia@cpu
#SBATCH --partition=cpu_p1
#SBATCH --qos=qos_cpu-t3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --hint=nomultithread
#SBATCH --time=06:00:00
#SBATCH --output=KInduceDFS/jz_reproduce/slurm/cert_%j.out
#SBATCH --error=KInduceDFS/jz_reproduce/slurm/cert_%j.out
#
# Reproduce one instance's certificate END TO END, with the output written to a
# FILE.  Submit from the repo root:
#
#     sbatch --export=ALL,CERT_INSTANCE=p23 KInduceDFS/jz_reproduce/cert.slurm
#
# WHY THIS EXISTS RATHER THAN salloc.  On 2026-09-11/12 three separate p19/p23
# certificate runs produced correct results that were then LOST: two terminals
# were closed and one connection dropped after the computation had finished.  An
# interactive allocation puts the only copy of the answer in a terminal, and the
# answer here is a set of hashes that cost hours to regenerate.  sbatch puts it in
# slurm/cert_<jobid>.out, which survives the session, and the durable cert blocks
# land in $SCRATCH besides.
#
# WHY srun BELOW.  salloc reserves a node but need not move your shell onto it; a
# command typed at an salloc prompt may still execute on the LOGIN node, where
# IDRIS enforces memory and CPU-time limits and kills what exceeds them.  That is
# the most likely reading of the 2026-09-12 failure, in which p23's root stage was
# SIGKILLed at cube 200 of 343,896 while p19 -- twenty-four times smaller -- had
# completed on the login node an hour earlier.  Under sbatch the script already
# runs on the compute node, and srun makes that explicit and bindable.
#
# SIZING.  Four cores is not for parallelism -- every stage here is
# single-threaded -- but for the memory grant, about 4 GB per core on cpu_p1.
# verify_root.py holds the base states as tuples of SHARED permutation objects
# (720 distinct for a 6-vertex base), so p23's 3,414,729 of them are a few hundred
# MB, not tens of GB.  $JOBSCRATCH needs ~4 GB free for the 0.78 GiB coverage CNF
# and its ~2 GiB LRAT proof, which are verified and discarded.
#
# TIME.  p23 measured on the cluster: 2,814 s to enumerate the base states down to
# the 343,896 live ones, then the per-cube regeneration, then a coverage solve that
# takes just under 20 minutes on one laptop core.  Six hours is ample; raise --time
# rather than let it be wall-killed, since nothing here resumes.
set -u
I=${CERT_INSTANCE:?set CERT_INSTANCE, e.g. sbatch --export=ALL,CERT_INSTANCE=p23 ...}
cd "$SLURM_SUBMIT_DIR"
echo "instance=$I  host=$(hostname)  node=${SLURM_JOB_NODELIST:-?}  start=$(date)"
srun KInduceDFS/jz_reproduce/run.sh "$I" all
rc=$?
echo "run.sh exit=$rc  end=$(date)"
# The cert blocks are the artefact worth keeping; say where they landed.
DUR=${JZ_DURABLE:-${SCRATCH:-${WORK:-}}}
[ -n "$DUR" ] && ls -l "$DUR/${I}_cert.portable.txt" "$DUR/${I}_cert.full.txt" 2>/dev/null
exit $rc
