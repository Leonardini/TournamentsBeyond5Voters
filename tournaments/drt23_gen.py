#!/usr/bin/env python3
"""Parse McKay's 37 doubly-regular tournaments on 23 vertices, verify them, and hold out the
circulant one (Paley(23)).

The bit ordering in the file is not documented here, so BOTH plausible upper-triangle orderings
are tried and the one that yields a regular tournament for every line is adopted -- if neither
does, that is a hard failure rather than a silent mis-read.  Each tournament is then checked to
be doubly regular (constant cyclic-triangle load, which at n=23 must equal the ceiling 6).
"""
import itertools
import os
import numpy as np
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

n = 23
SRC = "drt23/drtourn23.txt"
lines = [ln.strip() for ln in open(SRC) if ln.strip()]
print(f"{len(lines)} lines, each {len(set(map(len, lines)))} distinct length(s): "
      f"{sorted(set(map(len, lines)))}")


def build(b, rowmajor=True):
    A = np.zeros((n, n), int)
    k = 0
    if rowmajor:
        for i in range(n):
            for j in range(i + 1, n):
                A[i, j] = int(b[k]); A[j, i] = 1 - A[i, j]; k += 1
    else:
        for j in range(n):
            for i in range(j):
                A[i, j] = int(b[k]); A[j, i] = 1 - A[i, j]; k += 1
    return A


def is_regular_tournament(A):
    return ((A + A.T == 1 - np.eye(n, dtype=int)).all()
            and A.sum(1).min() == A.sum(1).max() == (n - 1) // 2)


order = None
for rm in (True, False):
    if all(is_regular_tournament(build(b, rm)) for b in lines):
        order = rm
        break
assert order is not None, "neither upper-triangle ordering yields regular tournaments"
print(f"bit ordering: {'row-major' if order else 'column-major'} upper triangle")

mats = [build(b, order) for b in lines]


def tri(A):
    t = [int((A[v] & A[:, u]).sum()) for u in range(n) for v in range(n) if A[u, v]]
    return min(t), max(t)


ceiling = 3 * (n * (n * n - 1) // 24) / (n * (n - 1) // 2)
for k, A in enumerate(mats):
    lo, hi = tri(A)
    assert lo == hi == ceiling, f"line {k} is not doubly regular: tmin={lo} max={hi}"
print(f"all {len(mats)} verified DOUBLY REGULAR: every arc in exactly {int(ceiling)} "
      f"cyclic triangles (= the n=23 ceiling)")

# pairwise non-isomorphic?
uniq = []
for A in mats:
    G = nx.DiGraph(A)
    if not any(DiGraphMatcher(nx.DiGraph(B), G).is_isomorphic() for B in uniq):
        uniq.append(A)
print(f"pairwise non-isomorphic: {len(uniq)} of {len(mats)}")

QR = {(x * x) % n for x in range(1, n)}
P = np.array([[1 if i != j and (j - i) % n in QR else 0 for j in range(n)] for i in range(n)])
pal = [k for k, A in enumerate(mats)
       if DiGraphMatcher(nx.DiGraph(A), nx.DiGraph(P)).is_isomorphic()]
print(f"isomorphic to Paley(23): line(s) {pal}  (expected exactly one -- the circulant DRT)")

out = "drt23"
os.makedirs(out, exist_ok=True)


def bits(A):
    return "".join(str(int(A[i, j])) for i in range(n) for j in range(i + 1, n))


w = 0
for k, A in enumerate(mats):
    if k in pal:
        continue
    open(os.path.join(out, f"d{k:03d}.bits"), "w").write(bits(A) + "\n")
    w += 1
print(f"wrote {w} non-circulant DRTs to {out}/  (Paley(23) held out)")
