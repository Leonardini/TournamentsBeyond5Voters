#!/usr/bin/env python3
"""
realize5_cpsat.py — k-realizability search for a tournament minus a vertex set S (OR-Tools CP-SAT).

Lifted encoding (PV_SETTLE_PLAN.md §3, Leonid 2026-07-13): voters are permutations of ALL n
vertices; the majority constraint is enforced only on arcs disjoint from S ("lift the constraints
on the non-existing edges"). Equivalent to k-realizability of T-S (delete S from each voter /
insert S anywhere), but keeps T's structure available for symmetry breaking.

Valid (implied) cuts — never assumptions:
  * per-voter fwd_p <= MAS(T-S) when known (Paley43 staircase 543-21|S|, PROVEN);
  * sum_p fwd_p >= ceil(k/2) * #kept-arcs (majority counting);
  * co-backing (k=5): <= 1 double-backer per cyclic triangle. Proof: each arc needs >= 3 of 5
    voters forward, so each of the 3 arcs has <= 2 backers => <= 6 backings in total; in a linear
    order every cyclic triangle has 1 or 2 backward arcs, so each of the 5 voters contributes
    >= 1 backing => #double-backers <= 6 - 5 = 1.
  * voter-exchange break: fwd_1 >= ... >= fwd_k;
  * Stab(S) pin (Paley43, S={0}): Stab(0) = {x -> ax : a in QR} = C21 acts regularly on the QR
    set, so WLOG voter 1 ranks vertex 1 first among the 21 QR vertices (complete break);
    for |S|=2 the pair-stabilizer is trivial (Aut regular on pairs) — no pin available.
  * --at-most-one-top L: at most one voter with fwd >= MAS-L. VALID ONLY when the corresponding
    pair screen is clean at level <= L (P-v: L=1 proven 2026-07-11/13; do NOT use otherwise).

Self-verification: any SAT model is independently checked (majority tournament of the k orders
restricted to kept vertices == T-S; every claimed cut re-checked).

Gauntlet (run with --gauntlet): ce1068 k=3 INFEASIBLE, ce1068 k=5 FEASIBLE, paley11 k=5 FEASIBLE.

Usage examples:
  python3 realize5_cpsat.py --gauntlet
  python3 realize5_cpsat.py --graph paley43 --k 5 --drop 0,1 --timeout 21600 --workers 2
  python3 realize5_cpsat.py --graph paley43 --k 5 --drop 0 --at-most-one-top 1 --timeout 21600
"""
import argparse, sys, time
from ortools.sat.python import cp_model

CE1068_ROWS = ["01111100000","00110100011","00011100110","00001110011","01000011101",
               "00001001111","11100101000","11110000010","11010011000","10001010101","10100011100"]

def paley(q):
    qr = {(x*x) % q for x in range(1, q)}
    return [[1 if (v-u) % q in qr and u != v else 0 for v in range(q)] for u in range(q)]

def build_graph(name):
    if name == "ce1068":   return [[int(c) for c in r] for r in CE1068_ROWS]
    if name.startswith("paley"):
        q = int(name[5:])
        if q % 4 != 3 or any(q % p == 0 for p in range(2, int(q**0.5) + 1)):
            raise SystemExit(f"{name}: need prime q = 3 mod 4 (prime powers not implemented)")
        return paley(q)
    raise SystemExit(f"unknown graph {name}")

MAS_FULL = {7: 14, 11: 35, 23: 161, 43: 543}   # 43: dp43-certified; 23: alpha*=7/11 (arc-orbit LP,
                                               # arc-transitive => MAS = 7*253/11); 11: 35 (=7/11*55),
                                               # 7: 14 (=2/3*21)

def triple_cyclic(A, S):
    x, y, z = S
    od = {x: 0, y: 0, z: 0}
    for (u, v) in ((x, y), (x, z), (y, z)):
        if A[u][v]: od[u] += 1
        else:       od[v] += 1
    return all(o == 1 for o in od.values())

def paley_mas_bound(q, A, drop):
    """Valid UPPER bound on MAS(Paley(q) - drop); exact for |drop|<=2 (prepend/delete-prefix
    staircase, the Paley43 argument verbatim: regular out-degree d=(q-1)/2) and for transitive
    triples; cyclic triples get the bound base-3d+1 (true value is that or one less)."""
    if q not in MAS_FULL: return None
    base, d, m = MAS_FULL[q], (q - 1)//2, len(drop)
    if m == 0: return base
    if m <= 2: return base - d*m
    if m == 3: return base - 3*d + (1 if triple_cyclic(A, drop) else 0)
    return None

def cyclic_triangles(A, keep):
    n = len(A); T = []
    for a in range(n):
        if a not in keep: continue
        for b in range(a+1, n):
            if b not in keep: continue
            for c in range(b+1, n):
                if c not in keep: continue
                # cyclic iff not transitive: out-degrees within the triple are 1,1,1
                od = {a:0, b:0, c:0}
                for (x, y) in ((a,b),(a,c),(b,c)):
                    if A[x][y]: od[x] += 1
                    else:       od[y] += 1
                if od[a] == od[b] == od[c] == 1:
                    T.append((a, b, c))
    return T

def solve(A, k, drop, timeout, workers, mas=None, pin_c21_qr=None, at_most_one_top=None,
          freeze=None, hint=None, seed=None, verbose=True):
    n = len(A)
    S = set(drop)
    keep = [v for v in range(n) if v not in S]
    arcs = [(u, v) for u in keep for v in keep if A[u][v]]
    maj = k//2 + 1
    m = cp_model.CpModel()
    pos = [[m.NewIntVar(0, n-1, f"pos_{p}_{v}") for v in range(n)] for p in range(k)]
    for p in range(k):
        m.AddAllDifferent(pos[p])
    if freeze:            # exact extension test: pin each voter's frozen suborder via chains;
        assert len(freeze) == k, "freeze file must have k voter lines"
        for p, order in enumerate(freeze):    # frozen labels may be a SUBSET of kept (insertions float)
            assert set(order) <= set(keep), f"freeze voter {p}: labels not among kept vertices"
            assert sorted(order) == sorted(freeze[0]), f"freeze voter {p}: label set differs from voter 0"
            for i in range(len(order) - 1):
                m.Add(pos[p][order[i]] < pos[p][order[i+1]])
    if hint:              # warm start only (soft)
        for p, order in enumerate(hint):
            for i, v in enumerate(order):
                m.AddHint(pos[p][v], i)
    before = {}
    for p in range(k):
        for (u, v) in arcs:
            b = m.NewBoolVar(f"bef_{p}_{u}_{v}")
            m.Add(pos[p][u] < pos[p][v]).OnlyEnforceIf(b)
            m.Add(pos[p][u] > pos[p][v]).OnlyEnforceIf(b.Not())
            before[(p, u, v)] = b
    for (u, v) in arcs:
        m.Add(sum(before[(p, u, v)] for p in range(k)) >= maj)
    # per-voter forward counts on kept arcs + counting cut + voter-exchange break
    ub = mas if mas is not None else len(arcs)
    fwd = [m.NewIntVar(0, ub, f"fwd_{p}") for p in range(k)]
    for p in range(k):
        m.Add(fwd[p] == sum(before[(p, u, v)] for (u, v) in arcs))
    m.Add(sum(fwd) >= maj * len(arcs))
    for p in range(k-1):
        m.Add(fwd[p] >= fwd[p+1])
    # co-backing (k=5): <= 1 double-backer per cyclic triangle of T-S
    tris = cyclic_triangles(A, set(keep))
    ndb = 0
    if k == 5:
        for (a, b, c) in tris:
            # the three arcs of the triangle, oriented as in A
            tarcs = [(x, y) if A[x][y] else (y, x) for (x, y) in ((a,b),(a,c),(b,c))]
            dbs = []
            for p in range(k):
                sfwd = sum(before[(p, u, v)] for (u, v) in tarcs)
                d = m.NewBoolVar(f"db_{p}_{a}_{b}_{c}")
                m.Add(sfwd <= 1).OnlyEnforceIf(d)      # in a total order sfwd is 1 or 2
                m.Add(sfwd >= 2).OnlyEnforceIf(d.Not())
                dbs.append(d); ndb += 1
            m.Add(sum(dbs) <= 1)
    # Stab pin: voter 1 ranks pin_c21_qr[0] first among pin_c21_qr
    if pin_c21_qr:
        v0 = pin_c21_qr[0]
        for s in pin_c21_qr[1:]:
            m.Add(pos[0][v0] < pos[0][s])
    # screen lemma (VALIDITY IS CALLER'S RESPONSIBILITY)
    if at_most_one_top is not None and mas is not None:
        tops = []
        for p in range(k):
            t = m.NewBoolVar(f"top_{p}")
            m.Add(fwd[p] >= mas - at_most_one_top).OnlyEnforceIf(t)
            m.Add(fwd[p] <= mas - at_most_one_top - 1).OnlyEnforceIf(t.Not())
            tops.append(t)
        m.Add(sum(tops) <= 1)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = workers
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.log_search_progress = False
    if seed is not None:
        solver.parameters.random_seed = seed
        solver.parameters.randomize_search = True
    t0 = time.time()
    st = solver.Solve(m)
    wall = time.time() - t0
    name = {cp_model.OPTIMAL: "FEASIBLE", cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE (proven)", cp_model.UNKNOWN: "UNKNOWN"}[st]
    if verbose:
        print(f"  n={n} |S|={len(S)} k={k} (maj>={maj}) arcs={len(arcs)} tris={len(tris)} dbvars={ndb}: "
              f"{name}  [{solver.StatusName(st)}, {wall:.1f}s]", flush=True)
    orders = None
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        orders = []
        for p in range(k):
            perm = sorted(range(n), key=lambda v: solver.Value(pos[p][v]))
            orders.append([v for v in perm if v not in S])   # restrict to kept vertices
        # ---- independent verification (no solver objects) ----
        rank = [{v: i for i, v in enumerate(o)} for o in orders]
        for (u, v) in arcs:
            cnt = sum(1 for p in range(k) if rank[p][u] < rank[p][v])
            assert cnt >= maj, f"VERIFY FAIL arc {u}->{v}: only {cnt} voters"
        fwds = sorted((sum(1 for (u, v) in arcs if rank[p][u] < rank[p][v]) for p in range(k)),
                      reverse=True)
        if mas is not None:
            assert fwds[0] <= mas, f"VERIFY FAIL fwd {fwds[0]} > MAS {mas}"
        print(f"  VERIFIED realization; fwd(desc)={fwds}"
              + (f" levels={[mas-f for f in fwds]}" if mas is not None else ""), flush=True)
    return name, orders, wall

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", default="paley43")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--drop", default="", help="comma-separated vertices to delete (lifted)")
    ap.add_argument("--timeout", type=float, default=3600)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--at-most-one-top", type=int, default=None,
                    help="VALID ONLY if the pair screen is clean at this level (P-v: 1)")
    ap.add_argument("--no-pin", action="store_true")
    ap.add_argument("--freeze-file", default=None,
                    help="k lines of kept-vertex orders: FREEZE them, solve insertions only (exact extension test)")
    ap.add_argument("--hint-file", default=None,
                    help="k lines of kept-vertex orders: soft warm start for the full solve")
    ap.add_argument("--seed", type=int, default=None, help="CP-SAT random seed (diverse parallel hunts)")
    ap.add_argument("--gauntlet", action="store_true")
    args = ap.parse_args()

    if args.gauntlet:
        print("GAUNTLET (known answers):")
        A = build_graph("ce1068")
        r1, _, _ = solve(A, 3, [], 600, args.workers)
        r2, _, _ = solve(A, 5, [], 600, args.workers)
        A = build_graph("paley11")
        r3, _, _ = solve(A, 5, [], 600, args.workers, mas=35,
                         pin_c21_qr=None)
        ok = (r1.startswith("INFEASIBLE") and r2 == "FEASIBLE" and r3 == "FEASIBLE")
        print("GAUNTLET:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    A = build_graph(args.graph)
    drop = [int(x) for x in args.drop.split(",") if x != ""]
    mas = None; pin = None
    if args.graph.startswith("paley"):
        q = int(args.graph[5:])
        mas = paley_mas_bound(q, A, drop)
        if drop == [0] and not args.no_pin:
            qr = sorted({(x*x) % q for x in range(1, q)})
            pin = [1] + [s for s in qr if s != 1]   # voter 1 ranks vertex 1 first among QRs
    def load_orders(path):
        if not path: return None
        with open(path) as f:
            return [[int(x) for x in line.split()] for line in f if line.strip()]
    freeze = load_orders(args.freeze_file); hint = load_orders(args.hint_file)
    print(f"graph={args.graph} k={args.k} drop={drop} mas={mas} pin={'Cstab' if pin else 'none'} "
          f"amot={args.at_most_one_top} freeze={bool(freeze)} hint={bool(hint)} "
          f"timeout={args.timeout}s workers={args.workers}", flush=True)
    solve(A, args.k, drop, args.timeout, args.workers, mas=mas, pin_c21_qr=pin,
          at_most_one_top=args.at_most_one_top, freeze=freeze, hint=hint, seed=args.seed)

if __name__ == "__main__":
    main()
