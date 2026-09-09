#!/usr/bin/env python3
"""How does per-cube CDCL cost scale with cube DEPTH?

A depth-d cube fixes x[e][v] for all e inside a placed set S, |S|=d.  Children
are obtained by inserting one more vertex u into every voter's order; the
insertion tuple must keep every new arc (u,w), w in S, inside the margin rule.
Vertex choice is MRV (fewest valid insertion tuples), matching kinduce16.

Reports, per depth: branching factor, and the CDCL time to refute a sample of
cubes -- so we can see whether sum(children) << parent.
"""
import sys, time, random, itertools, argparse
from cube_sat import paley, build, cube_units
from cubes import enumerate_cubes, cube_string


def margin_ok(cnt, K, exact):
    hi = (K + 1) // 2
    return cnt == hi if exact else cnt >= hi


def children(adj, S, orders, K, exact, u):
    """All insertion tuples for u; returns list of (newS, neworders)."""
    m = len(S)
    good = []
    # per voter, the dissent count contributed at each slot is local; enumerate
    per_voter = []
    for v in range(K):
        per_voter.append(list(range(m + 1)))
    for tup in itertools.product(*per_voter):
        ok = True
        for w in S:
            cnt = 0
            for v in range(K):
                o = orders[v]
                pu = tup[v]
                pw = o.index(w)
                u_before_w = pu <= pw
                # voter agrees with T's arc between u and w?
                if adj[u][w]:
                    cnt += 1 if u_before_w else 0
                else:
                    cnt += 0 if u_before_w else 1
            if not margin_ok(cnt, K, exact):
                ok = False
                break
        if ok:
            no = [orders[v][:tup[v]] + [u] + orders[v][tup[v]:] for v in range(K)]
            good.append((S + [u], no))
    return good


def mrv(adj, S, orders, K, exact, n):
    best = None
    for u in range(n):
        if u in S:
            continue
        ch = children(adj, S, orders, K, exact, u)
        if best is None or len(ch) < len(best[1]):
            best = (u, ch)
        if not ch:
            break
    return best


def cube_of(node, adj, pair, X, K):
    S, orders = node
    units = []
    for v in range(K):
        pos = {u: i for i, u in enumerate(orders[v])}
        for i, j in itertools.combinations(sorted(S), 2):
            e = pair[(i, j)]
            win, los = (i, j) if adj[i][j] else (j, i)
            units.append(X(e, v) if pos[los] < pos[win] else -X(e, v))
    return units


def _child(cls, units, solver, conn):
    import pysat.solvers as S
    import time as _t
    s = getattr(S, solver)(bootstrap_with=cls)
    t = _t.time()
    r = s.solve(assumptions=units)
    conn.send((r, _t.time() - t))
    conn.close()


def solve_child(cls, units, limit, solver):
    """Run one solve in a child process; kill it at `limit` seconds."""
    import multiprocessing as mp
    ctx = mp.get_context('fork')   # macOS defaults to spawn, which re-imports __main__
    pr, pw = ctx.Pipe(False)
    p = ctx.Process(target=_child, args=(cls, units, solver, pw))
    t = time.time()
    p.start()
    p.join(limit)
    if p.is_alive():
        p.terminate(); p.join()
        return None, time.time() - t
    if pr.poll():
        return pr.recv()
    return None, time.time() - t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, required=True)
    ap.add_argument('--margin', default='exact', choices=['majority', 'exact'])
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--base', type=int, nargs='+', default=None)
    ap.add_argument('--cube', type=int, default=0, help='which depth-5 cube to expand')
    ap.add_argument('--max-depth', type=int, default=9)
    ap.add_argument('--sample', type=int, default=4, help='cubes to time per depth')
    ap.add_argument('--per-solve', type=float, default=120.0)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--solver', default='Cadical195')
    a = ap.parse_args()
    random.seed(a.seed)
    exact = a.margin == 'exact'
    adj = paley(a.q)
    B = a.base if a.base else ([0, 1, 2, 3, 5] if a.q == 19 else [0, 1, 2, 5, 11])
    cls, arcs, pair, X, nv = build(adj, a.q, a.k, exact)
    cubes, bm = enumerate_cubes(adj, B, a.k, exact, 'mask')
    c = cubes[a.cube]
    orders = [[B[s] for s in pi] for pi in c]
    node = (list(B), orders)
    print(f"q={a.q} margin={a.margin} base={B} cube#{a.cube} of {len(cubes)}", flush=True)

    frontier = [node]
    depth = len(B)
    while depth <= a.max_depth:
        samp = random.sample(frontier, min(a.sample, len(frontier)))
        ts, unfinished = [], 0
        for nd in samp:
            u = cube_of(nd, adj, pair, X, a.k)
            st, dt = solve_child(cls, u, a.per_solve, a.solver)
            if st is None:
                unfinished += 1
            ts.append(dt)
        ts.sort()
        med = ts[len(ts) // 2]
        est = med * len(frontier)
        print(f"  depth {depth:2d}: cubes_in_subtree={len(frontier):9d}  "
              f"sample={len(samp)} unfinished={unfinished}  "
              f"median={med:7.2f}s max={ts[-1]:7.2f}s  "
              f"subtree_est={est/3600:9.2f} core-h", flush=True)
        if depth == a.max_depth:
            break
        # expand
        nxt = []
        for nd in frontier:
            r = mrv(adj, nd[0], nd[1], a.k, exact, a.q)
            if r is None or not r[1]:
                continue
            nxt.extend(r[1])
        if not nxt:
            print(f"  depth {depth+1}: subtree EMPTY -- cube refuted by placement alone")
            break
        frontier = nxt
        depth += 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
