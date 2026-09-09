#!/bin/bash
# Roll up the n=13 self-converse sweep.  The only line that matters is HITS.
#
# Takes one or more results directories and reports their UNION, deduplicated by
# shard tag.  That matters because this sweep ran on TWO machines: 407 shards on
# Jean Zay and the last 81 on the laptop, and the family is closed only if the
# union covers the whole rigid universe.  Reporting the union in one place is the
# only way to see that, which is why the markers of both halves are tracked in
# git -- one line each, and they are the evidence.
set -eu
_ORIGPWD=$PWD
cd "$(dirname "$0")"
[ $# -ge 1 ] || set -- results            # default: this kit's own results dir
# A directory may be given relative to the CALLER's cwd (the usual case, since
# N13_OUT is caller-relative) or relative to this kit.  Try the caller first, then
# here, and name both if neither has a done/ -- resolving only one way is what
# made a 210 core-h run read as "0 done" from a doubled path on 2026-09-06.
DIRS=()
for a in "$@"; do
  case "$a" in
    /*) d=$a ;;
    *)  if   [ -d "$_ORIGPWD/$a/done" ]; then d=$_ORIGPWD/$a
        elif [ -d "$a/done" ];           then d=$PWD/$a
        else echo "FATAL: no done/ under either $_ORIGPWD/$a or $PWD/$a" >&2; exit 1
        fi ;;
  esac
  [ -d "$d/done" ] || { echo "FATAL: no done/ under $d" >&2; exit 1; }
  DIRS+=("$d")
done
echo "reading $# results director$([ $# -eq 1 ] && echo y || echo ies):"
for d in "${DIRS[@]}"; do echo "  $d ($(ls "$d/done" | wc -l | tr -d ' ') markers)"; done

TMP=$(mktemp -d) || exit 1
trap 'rm -rf "$TMP"' EXIT
for d in "${DIRS[@]}"; do
  for f in "$d"/done/*; do [ -f "$f" ] || continue
    printf '%s\t%s\n' "$(basename "$f")" "$f"
  done
done > "$TMP/all"

# Dedupe by tag, and FAIL if the same shard tag carries different counts in two
# directories: that would mean the two halves disagree about what a tag covers,
# and summing them would be meaningless.
read -r SHARDS HOSTS ABORTED < <(awk -F'\t' '
  { tag = $1; path = $2; line = ""
    while ((getline l < path) > 0) line = line l; close(path)
    if (tag in seen) {
      if (seen[tag] != line) {
        printf("FATAL: shard %s differs between copies:\n  [%s]\n  [%s]\n",
               tag, seen[tag], line) > "/dev/stderr"; bad = 1 }
      next }
    seen[tag] = line
    delete v; n = split(line, a, /[ =]+/)
    for (i = 1; i < n; i += 2) v[a[i]] = a[i+1]
    S++; H += v["hosts"]; U += v["unsat"]; A += v["aborted"] }
  END { if (bad) exit 1; print S+0, H+0, A+0; print U+0 > "/dev/stderr" }
  ' "$TMP/all" 2> "$TMP/unsat")
UNSAT=$(cat "$TMP/unsat")
printf "  shards done   : %d\n"   "$SHARDS"
printf "  hosts swept   : %d\n"   "$HOSTS"
printf "  ABORTED       : %d  (capped at 300 s -- NOT verdicts, re-run these)\n" "$ABORTED"
printf "  HITS (UNSAT)  : %d  <== the only interesting number\n" "$UNSAT"
# 1,026,306, NOT the naive 1,028,787.  COMMANDS.md records that two buckets were
# swept in full, so their 534 and 1,947 possibly-symmetric members are already
# inside those bucket counts and must not be added again -- the naive sum
# double-counts by exactly 2,481.  This line printed the wrong one, which is the
# worst place for it: a reported number is the version that gets quoted.
echo "  already settled separately, not in the above: 1,026,306"
echo "    (this is a SUPERSET of every self-converse 13-tournament with"
echo "     non-trivial Aut, so an obstruction surviving the sweep below would"
echo "     necessarily have trivial Aut -- see COMMANDS.md)"
# COMPLETENESS IDENTITY, asserted rather than described.  The self-converse
# 13-tournaments partition into three parts, and if they do not sum to the total
# then something has been dropped and no clean sweep means the family is closed.
# This is the check that turns "we think we covered everything" into a hard error.
#
# Line 11 already cd'd into this script's own directory, so the counts file is
# simply state/jz_counts.tsv from here.  It USED to say "$(dirname "$0")/state/...",
# which is resolved AFTER that cd and so doubled the path -- exactly the fault the
# comment above warns about, in the same file.  On JZ (`bash KInduceDFS/jz_n13sc/
# aggregate.sh` from the repo root) it died with FileNotFoundError AFTER printing
# the verdict lines, so the sweep numbers were right and only this assertion was
# lost.  Running it from inside this directory is the one shape that cannot catch it.
CNT=state/jz_counts.tsv
[ -f "$CNT" ] || { echo "FATAL: no $CNT in $PWD -- cannot check completeness" >&2; exit 1; }
python3 - "$CNT" "$HOSTS" "$SHARDS" "${N13_PER:-200000}" <<'PYEOF'
import sys
TOTAL   = 95_458_560   # self-converse tournaments on 13 vertices
REGULAR = 11_237       # imbalance 0: EXCLUDED, every regular tournament on n <= 13
                       # is already known 5-inducible at both margins
SYM     = 319_270      # possibly-symmetric across all buckets, swept locally.
                       # Colour refinement discretising is a THEOREM that Aut is
                       # trivial, so this is a superset of every self-converse
                       # 13-tournament with non-trivial Aut.
counts, hosts, shards, per = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
buckets = [(int(l.split()[0]), int(l.split()[1])) for l in open(counts) if l.strip()]
rigid = sum(c for _, c in buckets)
print(f"  completeness: {REGULAR:,} regular (excluded) + {SYM:,} symmetric (swept)"
      f" + {rigid:,} rigid = {REGULAR+SYM+rigid:,}")
assert REGULAR + SYM + rigid == TOTAL, \
    f"FATAL: parts sum to {REGULAR+SYM+rigid:,}, not the {TOTAL:,} self-converse " \
    f"13-tournaments -- something is uncovered and no sweep can close the family"
print(f"  matches the {TOTAL:,} total EXACTLY -- no gap, no overlap")
# the two buckets swept in full must reconcile with their rigid counts
r = dict(buckets)
for b, full, sym in ((4, 116_765, 534), (8, 581_515, 1_947)):
    got = r[b] + sym
    assert got == full, f"FATAL: bucket {b} rigid+{sym} = {got}, not the {full} swept in full"
print("  buckets 4 and 8 reconcile with their in-full sweeps")
# Is the sweep FINISHED?  The grid is recomputed from the bucket counts and the
# shard size -- never typed -- so this line stays right if either changes.
grid = sum(-(-c // per) for _, c in buckets)
print(f"  shard grid at PER={per:,}: {grid} shards covering {rigid:,} rigid hosts")
if hosts == rigid and shards == grid:
    print(f"  ==> COVERED IN FULL: {shards}/{grid} shards, every rigid host swept.")
    print("      With HITS 0 above, every self-converse tournament on 13 vertices is")
    print("      margin-1 5-inducible, so the family is CLOSED and the smallest known")
    print("      margin-1 obstruction stays at n=19.")
elif hosts > rigid or shards > grid:
    raise SystemExit(f"FATAL: swept {hosts:,} hosts in {shards} shards, MORE than the "
                     f"{rigid:,} in {grid} -- shards must be double-counted")
else:
    print(f"  ==> INCOMPLETE: {shards} of {grid} shards, {hosts:,} of {rigid:,} hosts; "
          f"{grid-shards} shards / {rigid-hosts:,} hosts still to sweep")
    print("      (pass BOTH results directories to see the union -- the sweep ran on"
          " two machines)")
PYEOF
for d in "${DIRS[@]}"; do
  n=$(ls "$d/hits" 2>/dev/null | wc -l | tr -d ' ')
  [ "$n" != 0 ] && { echo; echo "  *** $n shard(s) produced a hit -- inspect $d/hits/"
    echo "  *** each line is an order-13 tournament with NO margin-1 five-voter profile"; }
done
exit 0
