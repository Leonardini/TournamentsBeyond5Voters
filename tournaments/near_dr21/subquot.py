"""Sub-base quotient (Lemma 2.4 applied to a SUBSET of the base), his idea of 2026-10-18 09:30.

A fixed-point-free automorphism g of order 3 maps no 5-set onto itself, but it maps each of its
3-cycles C (a directed triangle) onto itself.  Lemma 2.4 with base C: if T is k-inducible, some
witness extends a chosen representative of each <g>-orbit of C's base states.  That witness also
extends SOME base state of any 5-set B containing C, and its restriction to C is the chosen
representative.  So it suffices to search the B-states whose restriction to C is a chosen
representative -- about a third of them, still 5-vertex states (parallel, SAT-certifiable).

    python3 subquot.py HOST.bits MARGIN [--base v1 .. v5] [--out FILE]

MARGIN is exact (unit) or majority.  The base must contain a <g>-orbit; with no --base, the
lexicographically first regular 5-set containing one is used.  B-states are enumerated in kinduce's
own order (lottery_quotient.py's replica, checked against base_states_gen), so the printed indices
feed --bs-from/--bs-to directly.  ASSERTED: g is an automorphism of order 3 with no fixed point,
B is regular and contains C, the B-state count is the library's, the restrictions of the B-states
are EXACTLY the independently enumerated C-states, and g permutes the C-states in orbits of 3.
--check-witness LOG (a kinduce witness log for this host and base) additionally asserts that the
logged state index is the witness's own B-state, and that some g^j(witness) lands in the filter."""
import argparse, itertools, sys
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

K = 5

def load(path):
    s = ''.join(c for c in open(path).read() if c in '01')
    n = round((1 + (1 + 8 * len(s)) ** 0.5) / 2); A = [[0] * n for _ in range(n)]; k = 0
    for i in range(n):
        for j in range(i + 1, n): A[i][j], A[j][i] = (1, 0) if s[k] == '1' else (0, 1); k += 1
    return A

def states(A, B, margin):
    """kinduce's base-state order for base B (as given): perm p = order of base SLOTS top to bottom,
    lexicographic in itertools order; a state is a non-decreasing K-tuple of perm indices."""
    b = len(B); pairs = [(i, j) for i in range(b) for j in range(i + 1, b)]
    perms = []
    for idx in itertools.permutations(range(b)):
        pos = {v: r for r, v in enumerate(idx)}
        perms.append((idx, [pos[i] < pos[j] for i, j in pairs]))
    target = [A[B[i]][B[j]] for i, j in pairs]; need = K // 2 + 1
    out = []
    def rec(t, lo, cnt, chosen):
        if t == K: out.append(tuple(chosen)); return
        rem = K - t - 1
        for p in range(lo, len(perms)):
            c2 = cnt[:]; ok = True
            for e in range(len(pairs)):
                c2[e] += perms[p][1][e]
                sup = c2[e] if target[e] else (t + 1 - c2[e])
                if (margin == 'exact' and sup > need) or sup + rem < need: ok = False; break
            if ok: rec(t + 1, p, c2, chosen + [p])
    rec(0, 0, [0] * len(pairs), [])
    return out, [p[0] for p in perms]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bits'); ap.add_argument('margin', choices=['exact', 'majority'])
    ap.add_argument('--base', type=int, nargs=5); ap.add_argument('--out')
    ap.add_argument('--check-witness')
    a = ap.parse_args()
    A = load(a.bits); n = len(A)
    G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if A[i][j])
    ident = list(range(n))
    def comp(h, g): return [h[g[x]] for x in range(n)]
    g = None
    for m in DiGraphMatcher(G, G).isomorphisms_iter():
        h = [m[i] for i in range(n)]
        if h != ident and comp(h, comp(h, h)) == ident and all(h[v] != v for v in range(n)): g = h; break
    assert g, "no fixed-point-free automorphism of order 3"
    orbits = sorted({tuple(sorted({v, g[v], g[g[v]]})) for v in range(n)})
    assert all(len(o) == 3 for o in orbits) and len(orbits) == n // 3
    def regular(S): return all(sum(A[u][w] for w in S) == 2 for u in S)
    if a.base:
        B = sorted(a.base)
    else:
        B = next(sorted(S) for S in itertools.combinations(range(n), 5)
                 if regular(S) and any(set(o) <= set(S) for o in orbits))
    assert regular(B), "base is not the regular 5-tournament"
    C = next((o for o in orbits if set(o) <= set(B)), None)
    assert C, f"base {B} contains no <g>-orbit"
    EXPECT = {'exact': 2200, 'majority': 8031}[a.margin]
    st, perms = states(A, B, a.margin); assert len(st) == EXPECT, len(st)
    def restrict(state):
        return tuple(sorted(tuple(B[x] for x in perms[p] if B[x] in C) for p in state))
    # C-states enumerated independently: K-multisets of orders of C, each arc at the margin
    corders = list(itertools.permutations(C)); need = K // 2 + 1
    cstates = set()
    for ms in itertools.combinations_with_replacement(range(6), K):
        ok = True
        for u, w in itertools.permutations(C, 2):
            if not A[u][w]: continue
            sup = sum(corders[i].index(u) < corders[i].index(w) for i in ms)
            if sup < need or (a.margin == 'exact' and sup != need): ok = False
        if ok: cstates.add(tuple(sorted(corders[i] for i in ms)))
    restr = [restrict(s) for s in st]
    assert set(restr) == cstates, "restrictions of the B-states are not exactly the C-states"
    def gC(cs): return tuple(sorted(tuple(g[v] for v in o) for o in cs))
    # Lemma 2.4 allows ANY representative per orbit: take the one with the FEWEST B-states above it.
    from collections import Counter
    above = Counter(restr)
    reps = set()
    for cs in sorted(cstates):
        orb = {cs, gC(cs), gC(gC(cs))}; assert len(orb) == 3, "a C-state is fixed by g"
        reps.add(min(sorted(orb), key=lambda o: above[o]))
    assert len(reps) == len(cstates) // 3
    keep = [i for i, r in enumerate(restr) if r in reps]
    print(f"{a.bits}: margin={a.margin} base {B} triangle {list(C)}: {len(cstates)} C-states in "
          f"{len(reps)} orbits; keep {len(keep)} of {len(st)} B-states ({100*len(keep)/len(st):.1f}%)", file=sys.stderr)
    if a.check_witness:
        W = [list(map(int, l.split(':')[1].split())) for l in open(a.check_witness) if l.strip().startswith('voter ')]
        assert len(W) == K
        idx = {s: i for i, s in enumerate(st)}; pid = {p: t for t, p in enumerate(perms)}
        def bstate(prof):
            return tuple(sorted(pid[tuple(B.index(v) for v in o if v in B)] for o in prof))
        Wj = [W, [[g[v] for v in o] for o in W], [[g[g[v]] for v in o] for o in W]]
        hits = [idx[bstate(P)] in set(keep) for P in Wj]
        lo = [l for l in open(a.check_witness) if 'base_state_slice=' in l]
        hdr = [l for l in open(a.check_witness) if ' base=' in l]
        logged_base = sorted(map(int, hdr[0].split(' base=')[1].split()[0].split(','))) if hdr else None
        if lo and logged_base == B:
            s0 = int(lo[0].split('[')[1].split(',')[0])
            print(f"  witness: logged state {s0}, recomputed {idx[bstate(W)]}", file=sys.stderr)
            assert s0 == idx[bstate(W)], "state order differs from kinduce's"
        print(f"  witness images g^0,g^1,g^2 in the filter: {hits}", file=sys.stderr)
        assert any(hits), "no image of a genuine witness survives the filter -- UNSOUND"
    if a.out:
        open(a.out, 'w').write(f"# {a.margin} base {' '.join(map(str, B))} triangle {' '.join(map(str, C))} "
                               f"g {' '.join(map(str, g))}\n" + ''.join(f"{i}\n" for i in keep))

main()
