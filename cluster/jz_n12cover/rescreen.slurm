#!/bin/bash
#SBATCH --job-name=n12rescreen
#SBATCH --account=lia@cpu
#SBATCH --partition=cpu_p1
#SBATCH --qos=qos_cpu-t3
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --hint=nomultithread
#SBATCH --time=10:00:00
#SBATCH --array=0-99
#SBATCH --output=KInduceDFS/jz_n12cover/slurm/rescreen_%A_%a.out
#SBATCH --error=KInduceDFS/jz_n12cover/slurm/rescreen_%A_%a.out
#
# Re-screen the residues the census lost, and ONLY those.
#
# WHAT HAPPENED.  converse_filter.sh puts its temporaries wherever mktemp -d
# lands -- $TMPDIR, else /tmp, a small node-local filesystem shared by every array
# task on the node rather than the scratch this job was given.  It filled.  The
# campaign logs carry 2,874 "No space left on device" errors; 52 residues had
# their host list truncated on the way into the filter and 46 received nothing at
# all, so 15,690,562 order-11 classes were generated and then never screened.
# Nothing noticed, because the filter counted what it had RECEIVED and every
# number downstream agreed with every other.
#
# Fixed in screen_residue.sh (which now exports TMPDIR into the job scratch and
# asserts the filter's counts against its own), so a rerun cannot repeat it.
#
#   sbatch KInduceDFS/jz_n12cover/rescreen.slurm
#
# The residue list comes from filter_log_check.sh (free, from the logs) or from
# halving_audit_rollup.sh (a few core-hours, from a re-derivation).  Point
# N12_LIST at whichever; they should name the same residues, and if they do not,
# read the audit's before re-screening anything.
#
# ONE RESIDUE PER TASK.  The lost residues are the BIG ones -- the filesystem
# filled where the writes were largest -- up to 305,159 hosts against a 22,594
# mean, so budget hours, not minutes, and do not batch several into one task.
set -u
cd "$SLURM_SUBMIT_DIR"
OUT=${N12_OUT:-KInduceDFS/jz_n12cover/results}
LIST=${N12_LIST:-$OUT/rescreen_from_logs.txt}
MOD=${N12_MOD:-40000}
T=${SLURM_ARRAY_TASK_ID:-0}
A=${SLURM_ARRAY_TASK_COUNT:-1}
[ -s "$LIST" ] || { echo "FATAL: no residue list at $LIST"; exit 1; }
N=$(wc -l < "$LIST" | tr -d ' ')
# A GUARD, because this script DELETES MARKERS.  A list naming a large fraction of
# the census is not a repair, it is a mistake -- a wrong path, a truncated file, or
# a rollup that failed open -- and it would throw away thousands of core-hours of
# finished work.  10% of the residues is far beyond any plausible repair.
LIM=$(( MOD / 10 ))
[ "$N" -le "$LIM" ] || { echo "FATAL: $LIST names $N residues, more than the $LIM this will act on."; exit 1; }
echo "rescreen task $T of $A: $N residues listed in $LIST, host=$(hostname), start=$(date)"

# Markers are MOVED, not deleted: a marker is the only record that a residue ran,
# and if this rerun turns out to be the mistaken one we want the old counts back.
mkdir -p "$OUT/done_superseded"
n=0; fail=0
i=0
while read -r RES; do
  case "$RES" in ''|*[!0-9]*) continue ;; esac
  i=$((i+1))
  [ $(( (i-1) % A )) -eq "$T" ] || continue
  if [ -f "$OUT/done/r$RES" ]; then
    echo "residue $RES: superseding marker $(cat "$OUT/done/r$RES")"
    mv "$OUT/done/r$RES" "$OUT/done_superseded/r$RES"
  fi
  if KInduceDFS/jz_n12cover/screen_residue.sh "$RES" "$MOD" "$OUT"; then n=$((n+1))
  else echo "residue $RES FAILED again -- left unmarked"; fail=$((fail+1)); fi
done < "$LIST"
echo "rescreen task $T finished: $n residues redone, $fail failed, $(date)"
