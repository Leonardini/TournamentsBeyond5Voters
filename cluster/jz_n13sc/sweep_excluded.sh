#!/bin/bash
# Sweep the two classes the shard grid deliberately leaves out, and record it.
#
#   NOT PROVABLY RIGID  the hosts colour refinement failed to discretise.  Note
#                       the name: failing to discretise proves nothing about
#                       Aut, it only fails to prove Aut trivial, so this set is
#                       a SUPERSET of the ones with non-trivial Aut.
#   REGULAR             imbalance 0, dropped by order_sym before bucketing.
#                       A subset of the regular order-13 census, which came back
#                       all-SAT at margin 1, so this is a redundant confirmation
#                       -- worth having so the family stands on its own records
#                       instead of pointing at another campaign.
#
# Both were swept when the campaign ran, but only a hard-coded figure in
# aggregate.sh recorded it, and that figure was wrong twice over.  A sweep with
# no log is indistinguishable afterwards from a sweep that never happened.
#
# COST, measured on five buckets before committing rather than assumed: these
# hosts run 50-310 ms each against ~0.11 ms for a typical order-13 tournament,
# because "not provably rigid" selects for exactly the symmetry that makes the
# search hard, and most of the mass sits in the slowest buckets.  About 20
# core-hours in total, so ~2 h on ten cores.
#
# CHUNKED, not one batch per bucket.  Buckets run from 70 to 43,506 hosts, so
# per-bucket tasks would leave one core finishing a 2.9 core-hour bucket while
# nine sat idle.  Fixed-size chunks balance the pool and make each unit small
# enough to bank.  An earlier attempt ran all 319,270 as ONE uncapped batch
# piped through grep: no progress visible, one pathological host could stall it
# unnoticed, and a kill discarded every verdict computed so far.
#
#   usage: N13_WORK=~/Downloads/n13sc_local ./sweep_excluded.sh [out_dir]
#     J=10             workers (machine-wide cap is 10)
#     N13_CHUNK=5000   hosts per task
#     N13_TIME_CAP=300 per-instance abort, in seconds
#
# Re-running skips chunks that already have a summary, so an interrupted sweep
# resumes rather than restarting.  A chunk with no summary is simply redone.
set -eu
cd "$(dirname "$0")"
KIN=${KIN:-../kinduce}
W=${N13_WORK:-$HOME/Downloads/n13sc_local}
OUT=${1:-results_excluded}
J=${J:-10}
CHUNK=${N13_CHUNK:-5000}
PER_CAP=${N13_TIME_CAP:-300}
N=13

[ "$J" -le 10 ] || { echo "FATAL J=$J exceeds the ten-core cap" >&2; exit 1; }
[ -x "$KIN" ] || { echo "FATAL no engine at $KIN (cc -O3 -o kinduce kinduce.c)" >&2; exit 1; }
[ -d "$W/sym" ] || { echo "FATAL no $W/sym -- run prepare.sh first" >&2; exit 1; }
mkdir -p "$OUT/chunks" "$OUT/log" "$OUT/done"

# ---------------------------------------------------------------- host sets
# THE REGULAR CLASS IS OFF BY DEFAULT.  Verdicts already exist for every regular
# tournament on 13 vertices -- n13_regular_result.txt records all 1,495,297 at
# margin 1 with SAT=1495297 UNSAT=0 ABORTED=0 -- and these 11,237 are a subset of
# that, so sweeping them re-derives a clean census at the cost of the slowest
# hosts in the family (imbalance 0 is maximally symmetric).  Set
# N13_SWEEP_REGULAR=1 to include them anyway.
#
# Their COUNT is still wanted, as the independent anchor for the completeness
# identity in aggregate.sh, so the extraction runs either way -- it is the one
# place the imbalance test lives, and a second tool recomputing degrees its own
# way could disagree with the partition the rest of the campaign is built on.
SWEEP_REG=${N13_SWEEP_REGULAR:-0}
REG="$OUT/regular_hosts.txt"
if [ "$SWEEP_REG" = 1 ] && [ ! -s "$REG" ]; then
  # ALWAYS rebuild if the source is newer.  `[ -x ./order_sym ] || cc ...` left a
  # binary from before --only-regular existed in place, so the flag was silently
  # ignored and the extraction emitted all 95.4M irregular hosts -- a 7 GB file
  # that the -s test below would then have accepted as a finished list of 11,237.
  if [ ! -x ./order_sym ] || [ order_sym.c -nt ./order_sym ]; then
    echo "  rebuilding order_sym (source is newer than the binary)"
    cc -O2 -o order_sym order_sym.c
  fi
  [ -f "$W/selfcontourn13.txt" ] || { echo "FATAL no listing at $W/selfcontourn13.txt" >&2; exit 1; }
  echo "  extracting the regular hosts from the listing ..."
  # Write to a temporary and move it into place, so an interrupted extraction
  # leaves NO file rather than a truncated one that looks complete.
  ./order_sym $N "$W/selfcontourn13.txt" --only-regular 2> "$OUT/regular_extract.log" \
    | cut -f2 > "$REG.partial"
  mv "$REG.partial" "$REG"
  sed 's/^/    /' "$OUT/regular_extract.log"
fi
if [ "$SWEEP_REG" = 1 ]; then
  NREG=$(wc -l < "$REG" | tr -d ' ')
  echo "  regular hosts (imbalance 0): $NREG  -- INCLUDED in this sweep"
else
  NREG=0
  echo "  regular hosts (imbalance 0): NOT swept, verdicts already exist"
  echo "    n13_regular_result.txt: all 1,495,297 regular order-13 tournaments,"
  echo "    margin 1, SAT=1495297 UNSAT=0 ABORTED=0; these 11,237 are a subset."
  echo "    Their count is anchored independently by selfconverse_regular_count.py,"
  echo "    which reaches 11,237 from gentourng rather than from this listing."
fi

# ------------------------------------------------------------------ chunks
# Built once and kept, so a resumed run addresses exactly the same units.
if [ ! -f "$OUT/chunks/.built" ]; then
  echo "  building chunks of $CHUNK ..."
  for f in "$W"/sym/imb*.txt; do
    b=$(basename "$f" .txt)
    split -l "$CHUNK" -a 4 -d "$f" "$OUT/chunks/notrigid_${b}_"
  done
  if [ "$SWEEP_REG" = 1 ]; then
    split -l "$CHUNK" -a 4 -d "$REG" "$OUT/chunks/regular_imb0_"
  fi
  touch "$OUT/chunks/.built"
fi
NC=$(ls "$OUT/chunks" | grep -c '^\(notrigid\|regular\)' || true)
NH=$(cat "$OUT"/chunks/notrigid_* "$OUT"/chunks/regular_* 2>/dev/null | wc -l | tr -d ' ')
echo "  $NC chunks covering $NH hosts, $J workers, per-instance cap ${PER_CAP}s"

# The chunks must account for every host in both sets, or the sweep is of
# something smaller than it claims.  Checked before any compute.
WANT=$(cat "$W"/sym/imb*.txt | wc -l | tr -d ' ')
if [ "$SWEEP_REG" = 1 ]; then WANT=$(( WANT + NREG )); fi
[ "$NH" -eq "$WANT" ] || { echo "FATAL chunks hold $NH hosts, the two sets hold $WANT" >&2; exit 1; }

# -------------------------------------------------------------------- work
cat > "$OUT/.one.sh" <<'EOS'
#!/bin/bash
set -u
c=$1; OUT=$2; KIN=$3; CAP=$4; N=$5
tag=$(basename "$c")
[ -s "$OUT/done/$tag" ] && exit 0
"$KIN" --batch "$c" --n "$N" --k 5 --margin exact --order mrv --inc --time "$CAP" \
    > "$OUT/log/$tag.log" 2>&1
# A marker is written ONLY on a real summary line, so the set of markers is the
# completeness record: a killed or crashed chunk leaves nothing behind and is
# retried on the next run.
if grep -q '^BATCH_SUMMARY' "$OUT/log/$tag.log"; then
  grep '^BATCH_SUMMARY' "$OUT/log/$tag.log" > "$OUT/done/$tag"
  if grep -qE 'UNSAT=[1-9]' "$OUT/done/$tag"; then
    cp "$OUT/log/$tag.log" "$OUT/HIT_$tag.log"
    echo "$tag" >> "$OUT/HITS.txt"
  fi
  rm -f "$OUT/log/$tag.log"
fi
exit 0
EOS
chmod +x "$OUT/.one.sh"

ls "$OUT/chunks" | grep '^\(notrigid\|regular\)' | while read -r t; do
  [ -s "$OUT/done/$t" ] || echo "$OUT/chunks/$t"
done > "$OUT/.queue"
QN=$(wc -l < "$OUT/.queue" | tr -d ' ')
echo "  queue: $QN chunks outstanding of $NC"
if [ "$QN" -gt 0 ]; then
  xargs -P "$J" -n 1 -I{} "$OUT/.one.sh" {} "$OUT" "$KIN" "$PER_CAP" "$N" < "$OUT/.queue"
fi

# ------------------------------------------------------------------ report
echo
echo "=== roll-up ==="
"$(dirname "$0")/report_excluded.sh" "$OUT"
