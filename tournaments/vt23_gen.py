#!/usr/bin/env python3
"""Write the 94 vertex-transitive tournaments on 23 vertices as .bits, tagged by tmin,
with Paley(23) identified and held out."""
import itertools
import os
import numpy as np

n = 23
els = list(range(1, n))
pairs, used = [], set()
for g in els:
    if g in used:
        continue
    used |= {g, (-g) % n}
    pairs.append((g, (-g) % n))
units = [a for a in range(1, n) if np.gcd(a, n) == 1]
QR = frozenset((x * x) % n for x in range(1, n))


def canon(S):
    return min(tuple(sorted((a * g) % n for g in S)) for a in units)


def adj(S):
    return np.array([[1 if i != j and (j - i) % n in S else 0
                      for j in range(n)] for i in range(n)])


def tmin(A):
    return min(int((A[v] & A[:, u]).sum()) for u in range(n) for v in range(n) if A[u, v])


def bits(A):
    return "".join(str(int(A[i, j])) for i in range(n) for j in range(i + 1, n))


reps = sorted({canon(frozenset(c)) for c in itertools.product(*pairs)})
assert len(reps) == 94, f"expected McKay's 94, got {len(reps)}"
paley_canon = canon(QR)

out = "vt23"
os.makedirs(out, exist_ok=True)
rows = []
for S in reps:
    A = adj(set(S))
    rows.append((tmin(A), S, A))
rows.sort(key=lambda r: -r[0])          # hardest-looking first
npal = 0
manifest = []
for k, (t, S, A) in enumerate(rows):
    is_p = (tuple(S) == paley_canon)
    npal += is_p
    name = "paley23" if is_p else f"v{k:03d}"
    assert len(bits(A)) == n * (n - 1) // 2 == 253
    open(os.path.join(out, name + ".bits"), "w").write(bits(A) + "\n")
    manifest.append((name, t, sorted(S)))
assert npal == 1, "Paley(23) must appear exactly once"
with open(os.path.join(out, "manifest.tsv"), "w") as f:
    f.write("name\ttmin\tconnection_set\n")
    for name, t, S in manifest:
        f.write(f"{name}\t{t}\t{','.join(map(str, S))}\n")
print(f"wrote {len(rows)} tournaments to {out}/ (Paley(23) held out as paley23.bits)")
from collections import Counter
print("tmin distribution:", dict(sorted(Counter(t for t, _, _ in rows).items())))
print("to sweep:", len(rows) - 1)
