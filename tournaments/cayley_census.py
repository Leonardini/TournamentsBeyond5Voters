#!/usr/bin/env python3
"""Cayley tournaments on 13..23 vertices: how many, and what is their triangle load?

Only ODD orders admit tournaments with a regular automorphism group, so 13, 15, 17, 19, 21, 23.
Groups of odd order n in that range:
    13, 17, 19, 23 prime      -> Z_n only
    15 = 3*5                  -> Z_15 only (3 does not divide 5-1 = 4, so no non-abelian group)
    21 = 3*7                  -> Z_21 and F_21 = Z_7 : Z_3   (3 divides 7-1 = 6)
Each of Z_15, Z_21 and the primes is a CI-group (odd squarefree, Muzychuk / Turner), so
multiplier classes are exactly isomorphism classes for the cyclic ones -- no iso testing needed.
The F_21 side is merged into the Z_21 side by exact isomorphism.
"""
import itertools
import numpy as np
import networkx as nx
from collections import Counter
from networkx.algorithms.isomorphism import DiGraphMatcher


def cyclic_classes(n):
    els = list(range(1, n))
    pairs, used = [], set()
    for g in els:
        if g in used:
            continue
        used |= {g, (-g) % n}
        pairs.append((g, (-g) % n))
    units = [a for a in range(1, n) if np.gcd(a, n) == 1]
    canon = lambda S: min(tuple(sorted((a * g) % n for g in S)) for a in units)
    reps = sorted({canon(frozenset(c)) for c in itertools.product(*pairs)})
    adj = lambda S: np.array([[1 if i != j and (j - i) % n in set(S) else 0
                               for j in range(n)] for i in range(n)])
    return [adj(S) for S in reps]


def f21_classes():
    mul = lambda x, y: ((x[0] + y[0] * pow(2, x[1], 7)) % 7, (x[1] + y[1]) % 3)
    full = [(i, j) for i in range(7) for j in range(3)]
    els = [g for g in full if g != (0, 0)]
    inv = {g: next(h for h in full if mul(g, h) == (0, 0)) for g in full}
    pairs, used = [], set()
    for g in els:
        if g in used:
            continue
        used |= {g, inv[g]}
        pairs.append((g, inv[g]))
    pos = {g: k for k, g in enumerate(full)}
    out = []
    for S in itertools.product(*pairs):
        Ss = set(S)
        A = np.zeros((21, 21), int)
        for a in full:
            for b in full:
                if a != b and mul(inv[a], b) in Ss:
                    A[pos[a], pos[b]] = 1
        out.append(A)
    return out


def tmin(A):
    n = A.shape[0]
    return min(int((A[v] & A[:, u]).sum()) for u in range(n) for v in range(n) if A[u, v])


def dedupe(mats):
    keep = []
    for A in mats:
        GA = nx.DiGraph(A)
        if not any(DiGraphMatcher(nx.DiGraph(B), GA).is_isomorphic() for B in keep):
            keep.append(A)
    return keep


print(f"{'n':>3} {'classes':>8} {'ceiling':>8}  tmin distribution")
tot = 0
for n in (13, 15, 17, 19, 21, 23):
    mats = cyclic_classes(n)
    ncirc = len(mats)
    if n == 21:
        extra = [A for A in f21_classes()]
        mats = dedupe(mats + extra)
    T3 = n * (n * n - 1) // 24
    ceil = 3 * T3 / (n * (n - 1) // 2)
    d = dict(sorted(Counter(tmin(A) for A in mats).items()))
    tot += len(mats)
    note = f"   (circulant {ncirc} + other {len(mats)-ncirc})" if n == 21 else ""
    print(f"{n:>3} {len(mats):>8} {ceil:>8.2f}  {d}{note}")
print(f"\ntotal Cayley tournaments on 13..23 vertices: {tot}")
