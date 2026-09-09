#!/usr/bin/env python3
"""Per-node coverage certificates for a depth-d cube tree.

*** WORK IN PROGRESS -- BROKEN, NEVER VALIDATED, DO NOT TRUST. ***
Raises KeyError in node_cube_local (the parent order is indexed over S
but looked up over S+u).  Committed only for the design in this
docstring; the level-1 certificate in cover_check.py IS validated.

Level 1 (cover_check.py): the depth-|B| cubes cover, modulo the voter-lex lemma.
Level 2 (here): for every internal node N of the cube tree, its children cover N.

    F_{S+u} & C_N & AND_j not-C_j   is UNSAT

with S = N's placed set and u the vertex N branches on.  This certifies that the
insertion-tuple enumeration missed nothing -- so the DFS is only a SPLITTER and
its pruning never has to be trusted.  Note NO symmetry break appears below the
base: the voter-lex break is used only to choose base representatives, and Aut
pruning is deliberately not applied below the base so that nothing but the
margin rule and transitivity is in play here.
"""
import sys, os, time, subprocess, argparse, itertools
from cube_sat import paley, build
from cubes import enumerate_cubes
from deepen import mrv, cube_of

DRAT = "/Users/lchindelevitch/Downloads/DownloadedSoftware/drat-trim"


def sub_build(adj, S, K, exact):
    """Encoding of T|S on its own variables, plus the index maps."""
    sub = [[adj[u][w] for w in S] for u in S]
    return build(sub, len(S), K, exact)


def node_cube_local(orders, S, sub, pairS, XS, K):
    """N's (or a child's) cube expressed on the T|S variable set."""
    loc = {v: i for i, v in enumerate(S)}
    units = []
    for v in range(K):
        pos = {u: i for i, u in enumerate(orders[v])}
        for i, j in itertools.combinations(range(len(S)), 2):
            e = pairS[(i, j)]
            a, b = S[i], S[j]
            win, los = (a, b) if sub[loc[a]][loc[b]] else (b, a)
            units.append(XS(e, v) if pos[los] < pos[win] else -XS(e, v))
    return units


def check(adj, S, orders, children, K, exact, keep, tag, verify):
    """One node-expansion coverage check.  Returns (ok, nvars, nclauses, secs)."""
    Su = sorted(set(S) | {children[0][0][-1]})
    sub = [[adj[u][w] for w in Su] for u in Su]
    clsS, arcsS, pairS, XS, nvS = build(sub, len(Su), K, exact)
    parent = node_cube_local(orders, Su, sub, pairS, XS, K)
    # the parent pins only the arcs INSIDE S; drop literals touching the new vertex
    inS = set(S)
    pin = []
    loc = {v: i for i, v in enumerate(Su)}
    for e, (i, j) in enumerate(arcsS):
        if Su[i] in inS and Su[j] in inS:
            for v in range(K):
                pin.append([l for l in parent if abs(l) == XS(e, v)][0])
    negs = []
    for (cS, corders) in children:
        u = node_cube_local(corders, Su, sub, pairS, XS, K)
        negs.append([-l for l in u])
    cls = clsS + [[l] for l in pin] + negs
    t = time.time()
    import pysat.solvers as S_
    s = S_.Glucose42(bootstrap_with=cls, with_proof=True)
    sat = s.solve()
    pr = s.get_proof() or []
    s.delete()
    dt = time.time() - t
    if sat:
        return (False, nvS, len(cls), dt, 'SAT -- CHILDREN DO NOT COVER')
    if not verify:
        return (True, nvS, len(cls), dt, 'UNSAT (unchecked)')
    cnf, drt = f"{keep}/{tag}.cnf", f"{keep}/{tag}.drat"
    with open(cnf, 'w') as f:
        f.write(f"p cnf {nvS} {len(cls)}\n")
        for c in cls:
            f.write(' '.join(map(str, c)) + " 0\n")
    open(drt, 'w').write('\n'.join(pr) + '\n')
    p = subprocess.run([f"{DRAT}/drat-trim", cnf, drt], capture_output=True, text=True)
    ok = 's VERIFIED' in p.stdout
    os.remove(cnf); os.remove(drt)          # check-and-discard
    return (ok, nvS, len(cls), dt, 'VERIFIED' if ok else 'DRAT FAILED')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, default=19)
    ap.add_argument('--margin', default='exact', choices=['majority', 'exact'])
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--base', type=int, nargs='+', default=None)
    ap.add_argument('--cube', type=int, default=0)
    ap.add_argument('--depth', type=int, default=7)
    ap.add_argument('--keep', default='/tmp/coverdeep')
    ap.add_argument('--no-verify', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.keep, exist_ok=True)
    exact = a.margin == 'exact'
    adj = paley(a.q)
    B = a.base if a.base else ([0, 1, 2, 3, 5] if a.q == 19 else [0, 1, 2, 5, 11])
    cubes, bm = enumerate_cubes(adj, B, a.k, exact, 'mask')
    node = (list(B), [[B[s] for s in pi] for pi in cubes[a.cube]])
    print(f"q={a.q} margin={a.margin} base={B} cube#{a.cube} -> depth {a.depth}",
          flush=True)
    frontier = [node]
    nchecks = nfail = 0
    tsum = 0.0
    for d in range(len(B), a.depth):
        nxt = []
        for ni, nd in enumerate(frontier):
            r = mrv(adj, nd[0], nd[1], a.k, exact, a.q)
            if r is None or not r[1]:
                continue          # dead node: no children to cover, nothing to certify
            ok, nv, nc, dt, msg = check(adj, nd[0], nd[1], r[1], a.k, exact,
                                        a.keep, f"d{d}_{ni}", not a.no_verify)
            nchecks += 1; tsum += dt
            if not ok:
                nfail += 1
                print(f"  *** depth {d} node {ni}: {msg}", flush=True)
            nxt.extend(r[1])
        print(f"  depth {d}->{d+1}: {len(frontier):6d} nodes, "
              f"{len(nxt):6d} children, {nchecks} coverage checks so far, "
              f"{nfail} failures, {tsum:.1f}s", flush=True)
        if not nxt:
            break
        frontier = nxt
    print(f"RESULT coverage_checks={nchecks} failures={nfail} "
          f"leaves={len(frontier)} time={tsum:.1f}s "
          f"{'ALL VERIFIED' if nfail == 0 else 'FAILURES PRESENT'}")
    return 1 if nfail else 0


if __name__ == '__main__':
    sys.exit(main())
