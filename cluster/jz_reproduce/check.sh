#!/bin/bash
# CHEAP TIER for every instance -- a thin loop over run.sh, which is the single
# driver.  Add a campaign by dropping a file in instances/; nothing here changes.
#
#   check.sh            all instances
#   check.sh p19        just one
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
INSTANCES=${*:-$(cd "$HERE/instances" && ls *.conf | sed 's/\.conf$//')}
fail=0

echo "=== toolchain (coverage needs these; the root stage needs NO solver) ==="
for t in "$HOME/Downloads/DownloadedSoftware/cadical/build/cadical" \
         "$HOME/Downloads/DownloadedSoftware/lrat-trim/lrat-trim"; do
  [ -x "$t" ] && echo "  found $t" || echo "  MISSING $t -- see COMMANDS.md"
done

echo
echo "=== known answers (published censuses, independent of our runs) ==="
# Check3Majority/ lives at the REPO ROOT, which is $HERE/../.. -- not $HERE/.., which is
# KInduceDFS.  This ran from the wrong directory and 2>/dev/null hid the resulting
# "No such file or directory", so the check reported a bare "?" and FAILed for a reason
# that had nothing to do with the toolchain.  Keep stderr on the failure path.
N8LOG=$(cd "$HERE/../.." && KInduceDFS/kinduce --batch Check3Majority/margin1_sat/allt_n8.txt \
     --n 8 --k 3 --inc 2>&1)
N8=$(printf '%s' "$N8LOG" | sed -n 's/.*UNSAT=\([0-9]*\).*/\1/p')
echo "  n=8 k=3 UNSAT: ${N8:-?} (expect 96)"
[ "${N8:-}" = 96 ] || { echo "  FAIL"; printf '%s\n' "$N8LOG" | tail -3 | sed 's/^/    /'; fail=1; }

for I in $INSTANCES; do
  "$HERE/run.sh" "$I" root     || fail=1
  "$HERE/run.sh" "$I" coverage || fail=1
  "$HERE/run.sh" "$I" cert     || fail=1
done
printf "\n%s\n" "$([ $fail = 0 ] && echo 'CHEAP TIER PASS' || echo 'CHEAP TIER FAIL')"
exit $fail
