#!/usr/bin/env python3
"""Paper 2, Appendix H: the automorphism group of each 22-vertex obstruction, by a minimal set of
generators in cycle notation, written in the parent's labels v_1..v_23 (the deleted vertex absent).

All automorphisms by VF2; a generating set of minimum size is found by trying sets of size
0, 1, 2, ... of group elements and closing each under composition until it reaches |Aut|."""
import itertools, os, sys
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher
H = sys.argv[1] if len(sys.argv) > 1 and __name__ == '__main__' else os.path.dirname(os.path.abspath(__file__))  # host-file directory
OBS = [((1, 1), 'd000_mv00'), ((1, 2), 'd000_mv01'), ((1, 10), 'd000_mv09'),
       ((11, 2), 'd010_mv01'), ((11, 5), 'd010_mv04'), ((11, 20), 'd010_mv19'),
       ((6, 5), 'd005_mv04'), ((28, 5), 'd027_mv04'), ((1, 10, (2, 3)), 'd000mv09_r01_02')]


def load(b):
    b = ''.join(c for c in b if c in '01')
    n = int(round((1 + (1 + 8 * len(b)) ** .5) / 2)); A = [[0] * n for _ in range(n)]; k = 0
    for i in range(n):
        for j in range(i + 1, n):
            A[i][j] = int(b[k]); A[j][i] = 1 - A[i][j]; k += 1
    return A


def closure(gens, n):
    ident = tuple(range(n)); G = {ident}; frontier = [ident]
    while frontier:
        new = []
        for g in frontier:
            for h in gens:
                c = tuple(h[g[i]] for i in range(n))
                if c not in G: G.add(c); new.append(c)
        frontier = new
    return G


def cycles(g, lab):
    seen, out = set(), []
    for i in range(len(g)):
        if i in seen or g[i] == i: continue
        c = [i]; seen.add(i); j = g[i]
        while j != i: c.append(j); seen.add(j); j = g[j]
        out.append('(' + ' '.join(str(lab[x]) for x in c) + ')')
    return ''.join(out)


def generators(spec, host):
    """(|Aut|, [generator in cycle notation, parent labels]) for one obstruction."""
    A = load(open(os.path.join(H, host + '.bits')).read()); n = len(A)
    lab = [x for x in range(1, 24) if x != spec[1]]          # obstruction vertex i is parent v_lab[i]
    G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if A[i][j])
    auts = [tuple(m[i] for i in range(n)) for m in DiGraphMatcher(G, G).isomorphisms_iter()]
    ident = tuple(range(n)); rest = [g for g in auts if g != ident]
    gens = []
    for r in range(0, 4):
        # among the generating sets of minimum size, prefer elements of larger order (an 11-cycle
        # translation and a 5-cycle multiplication for Delta_1 - 10, as in Figure 1)
        cands = [c for c in itertools.combinations(rest, r) if len(closure(c, n)) == len(auts)]
        if cands:
            gens = list(max(cands, key=lambda c: sorted((len(closure([g], n)) for g in c), reverse=True)))
            break
    assert len(closure(gens, n)) == len(auts)
    return len(auts), [cycles(g, lab) for g in gens]


if __name__ == '__main__':
    for spec, host in OBS:
        order, gens = generators(spec, host)
        print(f'{host}\t|Aut|={order}\t' + (' ; '.join(gens) if gens else 'trivial'))
