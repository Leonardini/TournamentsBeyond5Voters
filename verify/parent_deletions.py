#!/usr/bin/env python3
"""Section 3.2: which vertex of which doubly regular parent each 22-vertex obstruction deletes,
and that the three deletions of Delta_1 cover all of its vertex orbits.

    usage: parent_deletions.py DRT_DIR DEL_DIR

For every DEL_DIR/dNNN_mvVV.bits of the obstructions below, rebuild DRT_DIR/dNNN.bits minus 0-based
vertex VV (the rest in order) and require the same bits.  Then compute Aut(d000) = Aut(Delta_1) by
VF2 and require that its vertex orbits are exactly three and that the deleted vertices 0, 1 and 9
lie one in each, so every one-vertex deletion of Delta_1 is isomorphic to one of the three.
Exit 0 only if all of this holds."""
import os, sys
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

OBS = ['d005_mv04', 'd027_mv04', 'd000_mv09', 'd000_mv00', 'd000_mv01', 'd010_mv01', 'd010_mv04', 'd010_mv19']


def adj(p):
    s = ''.join(c for c in open(p).read() if c in '01')
    n = int(round((1 + (1 + 8 * len(s)) ** .5) / 2)); A = [[0] * n for _ in range(n)]; k = 0
    for i in range(n):
        for j in range(i + 1, n):
            A[i][j] = int(s[k]); A[j][i] = 1 - A[i][j]; k += 1
    return A


drt, dele = sys.argv[1], sys.argv[2]
fail = 0
for h in OBS:
    par, v = h.split('_mv'); v = int(v)
    P, H = adj(os.path.join(drt, par + '.bits')), adj(os.path.join(dele, h + '.bits'))
    keep = [u for u in range(len(P)) if u != v]
    same = all(P[keep[i]][keep[j]] == H[i][j] for i in range(len(keep)) for j in range(len(keep)))
    print(f'{h}: {"is" if same else "is NOT"} {par} with 0-based vertex {v} deleted, the rest in order')
    fail |= not same
P = adj(os.path.join(drt, 'd000.bits')); n = len(P)
G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if P[i][j])
auts = [m for m in DiGraphMatcher(G, G).isomorphisms_iter()]
orbs, seen = [], set()
for v in range(n):
    if v not in seen:
        o = {m[v] for m in auts}; seen |= o; orbs.append(o)
hit = [next(i for i, o in enumerate(orbs) if v in o) for v in (0, 1, 9)]
ok = len(orbs) == 3 and sorted(hit) == [0, 1, 2]
print(f'd000 (Delta_1): |Aut| = {len(auts)}, vertex orbits of sizes {sorted(len(o) for o in orbs)}; '
      f'0-based vertices 0, 1, 9 lie in {"three different" if ok else "NOT three different"} orbits'
      + (', so every one-vertex deletion of Delta_1 is isomorphic to d000_mv00, d000_mv01 or d000_mv09' if ok else ''))
fail |= not ok
sys.exit(1 if fail else 0)
