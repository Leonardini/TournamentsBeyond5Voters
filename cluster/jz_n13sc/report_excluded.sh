#!/bin/bash
# Roll up the excluded-class sweep, and refuse to call it complete unless it is.
#
# Separate from sweep_excluded.sh so it can be run at any time on a partial
# result, and so the completeness arithmetic has one home.  The numbers it
# checks against are read from the partition table and from the host files --
# nothing here is written down.
#
#   usage: report_excluded.sh [out_dir]
set -eu
cd "$(dirname "$0")"
OUT=${1:-results_excluded}
W=${N13_WORK:-$HOME/Downloads/n13sc_local}
[ -d "$OUT/done" ] || { echo "FATAL no $OUT/done" >&2; exit 1; }

# Snapshot once: reading a live directory several times can report figures that
# contradict each other, which is how an earlier aggregator came to disagree
# with itself by 1.7% on the same two quantities.
SNAP=$(mktemp); trap 'rm -f "$SNAP"' EXIT
find "$OUT/done" -type f -exec cat {} + > "$SNAP" 2>/dev/null || true

sum_for() {   # sum_for <field> <name-prefix>
  find "$OUT/done" -type f -name "$2*" -exec cat {} + 2>/dev/null |
  awk -v F="$1" '{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]==F)s+=a[2]}}END{print s+0}'
}

for cls in notrigid regular; do
  ni=$(sum_for instances "$cls"); ns=$(sum_for SAT "$cls")
  nu=$(sum_for UNSAT "$cls");    na=$(sum_for ABORTED "$cls")
  nc=$(find "$OUT/done" -type f -name "$cls*" | wc -l | tr -d ' ')
  printf "  %-9s %3d chunks  instances %8d  SAT %8d  UNSAT %d  ABORTED %d\n" \
         "$cls" "$nc" "$ni" "$ns" "$nu" "$na"
done

TI=$(awk '{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]=="instances")s+=a[2]}}END{print s+0}' "$SNAP")
TS=$(awk '{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]=="SAT")s+=a[2]}}END{print s+0}' "$SNAP")
TU=$(awk '{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]=="UNSAT")s+=a[2]}}END{print s+0}' "$SNAP")
TA=$(awk '{for(i=1;i<=NF;i++){split($i,a,"=");if(a[1]=="ABORTED")s+=a[2]}}END{print s+0}' "$SNAP")

# What the two sets SHOULD hold, derived, not recalled.
WSYM=$(cat "$W"/sym/imb*.txt 2>/dev/null | wc -l | tr -d ' ')
# The regular class is optional and off by default, so its host file is often
# absent.  `wc -l < missing` fails BEFORE the pipe under set -e, so the `|| echo 0`
# never runs -- test for the file instead.
if [ -f "$OUT/regular_hosts.txt" ]; then
  WREG=$(wc -l < "$OUT/regular_hosts.txt" | tr -d ' ')
else
  WREG=0
fi
WANT=$((WSYM + WREG))

echo
printf "  total     instances %d of %d expected (%s)\n" "$TI" "$WANT" \
       "$( [ "$TI" -eq "$WANT" ] && echo 'COMPLETE' || echo 'partial' )"
printf "  SAT %d  UNSAT %d  ABORTED %d\n" "$TS" "$TU" "$TA"

fail=0
if [ "$TU" -gt 0 ]; then
  echo "  *** UNSAT PRESENT: a margin-1 obstruction at n=13.  That is a RESULT,"
  echo "      not an error -- it would drop the margin-1 record from 19 to 13."
  echo "      See $OUT/HITS.txt"
  fail=1
fi
if [ "$TA" -gt 0 ]; then
  echo "  ABORTED > 0: those hosts hit the per-instance cap and are NOT verdicts."
  echo "      Re-run them with a larger N13_TIME_CAP before claiming the class."
  fail=1
fi
if [ "$TI" -ne "$WANT" ]; then
  echo "  NOT COMPLETE: $((WANT - TI)) hosts unaccounted for; re-run sweep_excluded.sh"
  fail=1
fi
# SAT + UNSAT + ABORTED must account for every instance, or a verdict class is
# being dropped silently somewhere between the engine and this report.
if [ "$((TS + TU + TA))" -ne "$TI" ]; then
  echo "  FATAL SAT+UNSAT+ABORTED = $((TS+TU+TA)) but instances = $TI"
  fail=1
fi
[ "$fail" -eq 0 ] && echo "  every host in both excluded classes is margin-1 5-inducible, nothing capped"
exit "$fail"
