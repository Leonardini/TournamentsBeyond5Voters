#!/usr/bin/env python3
"""Independent dissent-boolean SAT encoding of k-voter inducibility, with cubes.

Written from scratch (not adapted from Paley23Decide/margin1_dissentbool_sat.py)
so that agreement with the DFS is genuine corroboration.

Variables: x[e][v] = 1 iff voter v DISSENTS from arc e of T.
Per arc:  majority -> at most (k-1)/2 dissenters (forbid every ((k+1)/2)-subset)
          exact    -> exactly  (k-1)/2 dissenters (also forbid every
                      ((k+1)/2)-subset of AGREEMENTS)
Per voter per vertex triple: the voter's order is T with its dissent arcs
reversed, and a tournament is transitive iff it has no 3-cycle, so forbid every
reorientation of each triple that is cyclic:
  cyclic triple   -> forbid |D| in {0,3}   (all-agree, all-dissent)
  transitive      -> forbid D={hyp} and D={leg1,leg2}
This is exact, not a filter.

A CUBE is a partial profile on a base set B, supplied as the 5 voters' orders on
B; it fixes x[e][v] for the C(|B|,2) arcs inside B -- i.e. |B|*(|B|-1)/2 * k
units -- which pins each voter's order on B exactly.
"""
import sys, time, itertools, argparse

def paley(q):
    QR = {(x * x) % q for x in range(1, q)}
    return [[1 if (j - i) % q in QR else 0 for j in range(q)] for i in range(q)]

def build(adj, n, K, exact):
    pair = {}
    arcs = []
    for i in range(n):
        for j in range(i + 1, n):
            pair[(i, j)] = pair[(j, i)] = len(arcs)
            arcs.append((i, j) if adj[i][j] else (j, i))   # stored in true direction
    nv = len(arcs) * K
    def X(e, v): return e * K + v + 1
    cls = []
    hi = (K + 1) // 2                      # agreements required
    lo = K - hi                            # dissents allowed
    for e in range(len(arcs)):
        for S in itertools.combinations(range(K), lo + 1):
            cls.append([-X(e, v) for v in S])          # not (lo+1) dissenters
        if exact:
            for S in itertools.combinations(range(K), hi + 1):
                cls.append([X(e, v) for v in S])       # not (hi+1) agreements
    for x, y, z in itertools.combinations(range(n), 3):
        exy, eyz, ezx = pair[(x, y)], pair[(y, z)], pair[(z, x)]
        a, b, c = adj[x][y], adj[y][z], adj[z][x]
        if (a and b and c) or (not a and not b and not c):        # cyclic
            for v in range(K):
                cls.append([X(exy, v), X(eyz, v), X(ezx, v)])      # not all-agree
                cls.append([-X(exy, v), -X(eyz, v), -X(ezx, v)])   # not all-dissent
        else:
            vs = [x, y, z]
            src = [w for w in vs if sum(1 for u in vs if u != w and adj[w][u]) == 2][0]
            snk = [w for w in vs if sum(1 for u in vs if u != w and adj[w][u]) == 0][0]
            mid = [w for w in vs if w not in (src, snk)][0]
            h, l1, l2 = pair[(src, snk)], pair[(src, mid)], pair[(mid, snk)]
            for v in range(K):
                cls.append([-X(h, v), X(l1, v), X(l2, v)])         # not D={hyp}
                cls.append([X(h, v), -X(l1, v), -X(l2, v)])        # not D={legs}
    return cls, arcs, pair, X, nv

def cube_units(orders, B, adj, pair, X, K):
    """orders[v] = voter v's ranking of B (best first). Returns unit literals."""
    units = []
    for v in range(K):
        pos = {u: i for i, u in enumerate(orders[v])}
        for i, j in itertools.combinations(sorted(B), 2):
            e = pair[(i, j)]
            winner = i if adj[i][j] else j
            loser = j if adj[i][j] else i
            dissent = pos[loser] < pos[winner]        # voter ranks the loser higher
            units.append(X(e, v) if dissent else -X(e, v))
    return units

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, required=True)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--margin', default='majority', choices=['majority', 'exact'])
    ap.add_argument('--solver', default='Cadical195')
    ap.add_argument('--cube', default=None, help='5 orders on B, e.g. "0,1,5,6,10;1,0,5,6,10;..."')
    ap.add_argument('--proof', action='store_true')
    ap.add_argument('--time-limit', type=float, default=0)
    a = ap.parse_args()
    adj = paley(a.q)
    cls, arcs, pair, X, nv = build(adj, a.q, a.k, a.margin == 'exact')
    units = []
    if a.cube:
        orders = [[int(t) for t in part.split(',')] for part in a.cube.split(';')]
        B = set(orders[0])
        units = cube_units(orders, B, adj, pair, X, a.k)
    print(f"q={a.q} k={a.k} margin={a.margin} vars={nv} clauses={len(cls)} cube_units={len(units)}",
          file=sys.stderr, flush=True)
    import pysat.solvers as S
    t0 = time.time()
    with getattr(S, a.solver)(bootstrap_with=cls, with_proof=a.proof) as s:
        sat = s.solve(assumptions=units)
        el = time.time() - t0
        st = {}
        try: st = s.accum_stats()
        except NotImplementedError: pass
        pl = 0
        if a.proof and not sat:
            p = s.get_proof(); pl = len(p) if p else 0
        print(f"RESULT {'SAT' if sat else 'UNSAT'} time={el:.2f}s "
              f"conflicts={st.get('conflicts','?')} decisions={st.get('decisions','?')} "
              f"proof_lines={pl}")
