#!/bin/bash
# Arc-criticality of dr19_g2, the second doubly regular tournament on 19 vertices.
#
# One orbit representative per arc orbit (57 of them, each of size 3 since
# |Aut(dr19_g2)| = 3): reverse it and ask whether the result becomes margin-1
# 5-inducible.  A YES on an orbit means that arc is critical; if every orbit says
# YES the host is arc-critical, which is the property Paley(19) has.
#
# This lives in the repo rather than in a session scratchpad ON PURPOSE: the
# first pass of this sweep was driven by an inline loop that no file recorded, so
# nothing but the log survived the session.
#
# RESUMABLE: a flip already carrying a verdict in the log is skipped, so a
# re-run only costs the undecided ones.  ABORTED is not a verdict and IS retried.
set -u
cd "$(dirname "$0")"
LOG=sweep.log
CORES=${DR19_CORES:-9}                  # never more than 10 on this laptop
CAP=${DR19_CAP:-1800}                   # per flip; the measured mean is ~160 s
touch "$LOG"

pending=()
for f in g2_f*.bits; do
  tag=${f%.bits}
  # A real verdict is SAT or UNSAT.  Anything else (ABORTED, nothing) is retried.
  if grep -qE "^  $tag +(SAT|UNSAT) " "$LOG"; then continue; fi
  pending+=("$tag")
done
total=$(ls g2_f*.bits | wc -l | tr -d ' ')
echo "[$(date +%H:%M)] $total orbits, $((total - ${#pending[@]})) already decided, ${#pending[@]} to run on $CORES cores, cap ${CAP}s" | tee -a "$LOG"
[ ${#pending[@]} -eq 0 ] && { echo "nothing to do"; exit 0; }

one() {
  tag=$1; cap=$2
  t0=$SECONDS
  out=$(timeout "$cap" ../kinduce --bits "$tag.bits" --n 19 --k 5 --margin exact --inc 2>&1)
  rc=$?
  el=$((SECONDS - t0))
  if [ $rc -eq 124 ]; then
    printf "  %-9s ABORTED (%ss cap)\n" "$tag" "$cap"
  elif echo "$out" | grep -q WITNESS; then
    printf "  %-9s SAT %ss\n" "$tag" "$el"
  elif echo "$out" | grep -qi "no witness\|UNSAT"; then
    printf "  %-9s UNSAT %ss  <== A NEW n=19 MARGIN-1 OBSTRUCTION\n" "$tag" "$el"
    echo "$out" > "$tag.unsat.log"
  else
    printf "  %-9s UNCLEAR rc=%s %ss (see %s.raw.log)\n" "$tag" "$rc" "$el" "$tag"
    echo "$out" > "$tag.raw.log"
  fi
}
export -f one
printf '%s\n' "${pending[@]}" | xargs -P "$CORES" -I{} bash -c 'one "$@"' _ {} "$CAP" | tee -a "$LOG"

echo "[$(date +%H:%M)] SWEEP DONE" | tee -a "$LOG"
awk '/^  g2_f/{v=$2; c[v]++} END{printf "  tally: "; for (k in c) printf "%s=%d ", k, c[k]; print ""}' "$LOG" | tee -a "$LOG"
