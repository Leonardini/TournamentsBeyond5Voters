#!/usr/bin/env python3
"""The 2 doubly-regular tournaments on 15 vertices: verify, and check whether either is already
covered by the 16 circulant (= all vertex-transitive) classes on 15 vertices.

n=15 is the ONE gap in "all VTs and DRTs up to 23 vertices": the regular ladder settled n <= 13,
so orders 3/7/11 are covered; 19 and 23 are in hand.  A DRT on 15 need not be vertex-transitive,
so it need not appear in vt15/ -- that is exactly what this checks rather than assumes.
"""
import glob
import os
import numpy as np
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

n = 15
lines = [ln.strip() for ln in open("drt15/drtourn15.txt") if ln.strip()]
assert all(len(b) == n * (n - 1) // 2 for b in lines), "not C(15,2) bits per line"


def build(b):
    A = np.zeros((n, n), int)
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            A[i, j] = int(b[k]); A[j, i] = 1 - A[i, j]; k += 1
    return A


def tri(A):
    t = [int((A[v] & A[:, u]).sum()) for u in range(n) for v in range(n) if A[u, v]]
    return min(t), max(t)


def bits(A):
    return "".join(str(int(A[i, j])) for i in range(n) for j in range(i + 1, n))


mats = [build(b) for b in lines]
ceiling = 3 * (n * (n * n - 1) // 24) / (n * (n - 1) // 2)
for k, A in enumerate(mats):
    assert (A + A.T == 1 - np.eye(n, dtype=int)).all(), f"line {k} not a tournament"
    assert A.sum(1).min() == A.sum(1).max() == (n - 1) // 2, f"line {k} not regular"
    lo, hi = tri(A)
    assert lo == hi == ceiling, f"line {k} not doubly regular: {lo}..{hi} vs ceiling {ceiling}"
print(f"{len(mats)} tournaments verified DOUBLY REGULAR "
      f"(every arc in exactly {int(ceiling)} cyclic triangles = the n=15 ceiling)")

assert not DiGraphMatcher(nx.DiGraph(mats[0]), nx.DiGraph(mats[1])).is_isomorphic(), \
    "McKay lists 2, but they are isomorphic"
print("the two are pairwise non-isomorphic, as catalogued")

vt = []
for f in sorted(glob.glob("vt15/*.bits")):
    b = open(f).read().strip()
    vt.append((os.path.basename(f), build(b)))
print(f"comparing against the {len(vt)} vertex-transitive classes on 15 vertices")

os.makedirs("drt15", exist_ok=True)
new = 0
for k, A in enumerate(mats):
    G = nx.DiGraph(A)
    hit = [nm for nm, B in vt if DiGraphMatcher(nx.DiGraph(B), G).is_isomorphic()]
    if hit:
        print(f"  DRT {k}: ALREADY COVERED -- isomorphic to vt15/{hit[0]}")
    else:
        open(f"drt15/e{k:03d}.bits", "w").write(bits(A) + "\n")
        new += 1
        print(f"  DRT {k}: NOT vertex-transitive -- written as drt15/e{k:03d}.bits")
print(f"\n{new} genuinely new tournament(s) to sweep at n=15")
