#!/usr/bin/env python3
"""One global registry for every tournament we sweep, with a unique id per ISOMORPHISM CLASS.

Two families can contain the same tournament -- a doubly-regular tournament may also be
vertex-transitive -- and running it twice wastes cores and, worse, makes a verdict table look
like it has more independent evidence than it does.  So:

  * scan every .bits file in every sweep directory
  * bucket by cheap exact invariants (n, tmin, spectrum, sorted triangle-per-arc multiset)
  * settle every collision inside a bucket by an exact VF2 isomorphism test
  * assign one id per class and report every file that is a DUPLICATE of an earlier one

Ids are `t{n}_{k:03d}`, k assigned in a deterministic order (tmin, spectrum, smallest bit string
held for that class), so re-running this reproduces the same names.
"""
import glob
import os
import numpy as np
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

R = os.path.dirname(os.path.abspath(__file__))
DIRS = ["drt_small", "vt15", "vt17", "vt19", "drt19", "vt21_rest", "vt21_hosts", "vt23", "drt15", "drt23",
        "vt23_hard"]


def load(p):
    b = "".join(open(p).read().split())
    n = int(round((1 + (1 + 8 * len(b)) ** .5) / 2))
    if n * (n - 1) // 2 != len(b):
        return None, None
    A = np.zeros((n, n), int)
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            A[i, j] = int(b[k]); A[j, i] = 1 - A[i, j]; k += 1
    return n, A


def tri_multiset(A):
    n = A.shape[0]
    return tuple(sorted(int((A[v] & A[:, u]).sum())
                        for u in range(n) for v in range(n) if A[u, v]))


def spec(A):
    ev = sorted(np.linalg.eigvals(A.astype(float)),
                key=lambda z: (round(z.real, 6), round(z.imag, 6)))
    return tuple((round(z.real, 4), round(abs(z.imag), 4)) for z in ev)


items = []
for d in DIRS:
    for p in sorted(glob.glob(os.path.join(R, d, "*.bits"))):
        n, A = load(p)
        if A is None:
            print(f"SKIP (not C(n,2) bits): {p}")
            continue
        items.append((d, os.path.basename(p)[:-5], n, A))
print(f"scanned {len(items)} .bits files across {len(DIRS)} directories")

buckets = {}
for d, name, n, A in items:
    tm = tri_multiset(A)
    buckets.setdefault((n, tm[0], spec(A), tm), []).append((d, name, A))

classes = []          # (n, key, [(dir,name)...], A)
for key, group in buckets.items():
    reps = []
    for d, name, A in group:
        G = nx.DiGraph(A)
        hit = None
        for r in reps:
            if DiGraphMatcher(nx.DiGraph(r[2]), G).is_isomorphic():
                hit = r
                break
        if hit:
            hit[1].append((d, name))
        else:
            reps.append([key, [(d, name)], A])
    classes.extend(reps)

classes.sort(key=lambda c: (c[0][0], c[0][1], c[0][2],
                            min("".join(str(int(c[2][i, j])) for i in range(c[2].shape[0])
                                        for j in range(i + 1, c[2].shape[0])) for _ in (0,))))
by_n = {}
for c in classes:
    by_n.setdefault(c[0][0], []).append(c)

dupes = 0
with open(os.path.join(R, "registry.tsv"), "w") as f:
    f.write("id\tn\ttmin\tmembers\n")
    for n in sorted(by_n):
        for k, c in enumerate(by_n[n]):
            tid = f"t{n}_{k:03d}"
            mem = ",".join(f"{d}/{nm}" for d, nm in c[1])
            f.write(f"{tid}\t{n}\t{c[0][1]}\t{mem}\n")
            if len(c[1]) > 1:
                dupes += 1
                print(f"DUPLICATE class {tid} (n={n}, tmin={c[0][1]}): {mem}")

print(f"\n{len(classes)} distinct isomorphism classes across all directories")
for n in sorted(by_n):
    print(f"   n={n}: {len(by_n[n])} classes")
print(f"duplicate classes spanning more than one file: {dupes}")
print("registry written to registry.tsv")
