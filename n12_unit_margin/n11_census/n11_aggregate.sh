#!/bin/bash
# Aggregate the n=11 five-inducibility census (MOD slices from n11_worker.sh).
# Completeness guards (lessons from the ILP10/AlphaSweep campaigns): every
# worker must be present and complete (missing ones are NAMED), the slice
# totals must sum to D_11 = 903,753,248 exactly, and the three stage tallies
# must be mutually consistent for every slice.
#
# Usage: n11_aggregate.sh RESULTSDIR MOD
set -uo pipefail
DIR=$1; MOD=$2
D11=903753248

missing=""
for r in $(seq 0 $((MOD-1))); do
  [ -f "$DIR/w_${r}.done" ] || missing="$missing $r"
done
if [ -n "$missing" ]; then
  echo "INCOMPLETE — missing workers:$missing"
  exit 1
fi

python3 - "$DIR" "$MOD" <<'EOF'
import re, sys, glob
d, mod = sys.argv[1], int(sys.argv[2])
D11 = 903753248
tot = m1 = r3 = n3 = 0
sat = unsat = ver = res = 0
for r in range(mod):
    t1 = open(f"{d}/w_{r}.tally1").read()
    g = re.search(r"total (\d+), margin1-SAT (\d+), REALIZABLE-NOT-MARGIN1 (\d+), non-realizable (\d+)", t1)
    assert g, f"worker {r}: bad tally1"
    a, b, c, e = map(int, g.groups())
    assert a == b + c + e, f"worker {r}: tally1 inconsistent"
    tot += a; m1 += b; r3 += c; n3 += e
    t2 = open(f"{d}/w_{r}.tally2").read()
    g = re.search(r"total (\d+): margin1-k5-SAT (\d+), UNSAT (\d+)", t2)
    assert g, f"worker {r}: bad tally2"
    ct, cs, cu = map(int, g.groups())
    assert ct == e, f"worker {r}: cert total {ct} != non-realizable {e}"
    sat += cs; unsat += cu
    t3 = open(f"{d}/w_{r}.tally3").read()
    g = re.search(r"verified (\d+) margin-1-k5 witnesses .*; (\d+) UNSAT", t3)
    assert g, f"worker {r}: bad tally3"
    vv, vu = map(int, g.groups())
    assert vv == cs and vu == cu, f"worker {r}: verifier/cert mismatch"
    ver += vv
    nres = sum(1 for _ in open(f"{d}/w_{r}.residual"))
    assert nres == cu, f"worker {r}: residual file {nres} != UNSAT {cu}"
    res += nres
print(f"slices: {mod}, all present and internally consistent")
print(f"total tournaments:            {tot:>12,}")
print(f"  margin-1 3-inducible:       {m1:>12,}")
print(f"  3-inducible, not margin-1:  {r3:>12,}")
print(f"  not 3-inducible:            {n3:>12,}")
print(f"    margin-1 5-inducible:     {sat:>12,}  (all witnesses verified: {ver:,})")
print(f"    residual (need ILP):      {res:>12,}")
if tot != D11:
    print(f"FAIL: total != D_11 = {D11:,}")
    sys.exit(1)
print("COMPLETENESS CHECK PASSED: total == D_11 == 903,753,248")
if res == 0:
    print("=> every 11-vertex tournament is 5-inducible: N(5) >= 12  [PROVEN, no ILP needed]")
else:
    print(f"=> {res:,} tournaments remain for the 5-inducibility ILP stage (cat w_*.residual)")
EOF
