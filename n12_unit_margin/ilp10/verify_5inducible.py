#!/usr/bin/env python3
# verify_5inducible.py INMFILE [LIMIT] [K] — confirm each n=10 tournament in INMFILE is K-realizable
# (default K = 5) using an OR-Tools CP-SAT search, and then INDEPENDENTLY re-verify each realization by
# reconstructing the majority tournament from the K voter orders and checking it equals the input.
# CPLEX-free (OR-Tools only). Any line that is not K-realizable would be a non-5-inducible n=10
# tournament — i.e. a proof that N(5) = 10, which the census says does not happen.
#
# INMFILE: one tournament per line, space-separated inm[v] = bitmask of in-neighbours u of v (arc u->v).
#   (The shipped data/n10_A3_counterexamples.tsv is TAB-separated "index<TAB>inm0..inm9"; strip the
#    first column first — see this folder's README.)
import sys
from ortools.sat.python import cp_model

n = 10
INM   = sys.argv[1]
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else None
K     = int(sys.argv[3]) if len(sys.argv) > 3 else 5

def realize(A, k):
    """Return K position-vectors (pos[p][v]) of a valid k-voter profile inducing A, or None."""
    arcs = [(u, v) for u in range(n) for v in range(n) if A[u][v] == 1]
    maj  = (k + 1) // 2
    m = cp_model.CpModel()
    pos = [[m.NewIntVar(0, n - 1, f"p{p}_{v}") for v in range(n)] for p in range(k)]
    for p in range(k):
        m.AddAllDifferent(pos[p])
    bef = {}
    for p in range(k):
        for (u, v) in arcs:
            b = m.NewBoolVar(f"b{p}_{u}_{v}")
            m.Add(pos[p][u] < pos[p][v]).OnlyEnforceIf(b)
            m.Add(pos[p][u] > pos[p][v]).OnlyEnforceIf(b.Not())
            bef[(p, u, v)] = b
    for (u, v) in arcs:                                    # each arc u->v must be forward in >= maj voters
        m.Add(sum(bef[(p, u, v)] for p in range(k)) >= maj)
    s = cp_model.CpSolver(); s.parameters.num_search_workers = 2
    st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return [[s.Value(pos[p][v]) for v in range(n)] for p in range(k)]

def induced_matches(A, orders, k):
    """Independent check: the majority of the k orders induces exactly A."""
    maj = (k + 1) // 2
    for u in range(n):
        for v in range(n):
            if u == v:
                continue
            fwd = sum(1 for p in range(k) if orders[p][u] < orders[p][v])
            if (fwd >= maj) != (A[u][v] == 1):
                return False
    return True

lines = [l for l in open(INM).read().split("\n") if l.strip()]
if LIMIT:
    lines = lines[:LIMIT]

ok = bad = 0
for i, line in enumerate(lines):
    inm = [int(x) for x in line.split()]
    A = [[1 if (inm[v] >> u) & 1 else 0 for v in range(n)] for u in range(n)]
    orders = realize(A, K)
    if orders is not None and induced_matches(A, orders, K):
        ok += 1
    else:
        bad += 1
        print(f"  line {i}: NOT {K}-realizable / verification FAILED  <-- this would be a counterexample (N(5)={n})")

print(f"SUMMARY: {ok}/{len(lines)} tournaments are {K}-realizable (voter profile independently re-verified); {bad} failure(s)")
if bad == 0:
    print(f"OK: every n=10 tournament checked is {K}-inducible (consistent with the census => N(5) > 10).")
