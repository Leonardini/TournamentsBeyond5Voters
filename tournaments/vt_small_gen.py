#!/usr/bin/env python3
"""Write the vertex-transitive tournaments on 15, 17 and 19 vertices.

McKay lists NO non-circulant vertex-transitive tournaments below order 21, and orders 17, 19 are
prime (so VT => circulant by Cauchy anyway); order 15 is covered by the catalogue's silence.
Counts are asserted against McKay's: 13 -> 6, 15 -> 16, 17 -> 16, 19 -> 30.  Order 13 is
generated only as a KNOWN-ANSWER CHECK -- the regular ladder already settled n <= 13.

Paley(19) is written too, as a positive control: it is margin-1 UNSAT, so it must NOT come back
SAT.  Everything else here is untested.
"""
import itertools
import os
import numpy as np

MCKAY = {13: 6, 15: 16, 17: 16, 19: 30}


def classes(n):
    els = list(range(1, n))
    pairs, used = [], set()
    for g in els:
        if g in used:
            continue
        used |= {g, (-g) % n}
        pairs.append((g, (-g) % n))
    units = [a for a in range(1, n) if np.gcd(a, n) == 1]
    canon = lambda S: min(tuple(sorted((a * g) % n for g in S)) for a in units)
    return sorted({canon(frozenset(c)) for c in itertools.product(*pairs)})


def adj(n, S):
    S = set(S)
    return np.array([[1 if i != j and (j - i) % n in S else 0
                      for j in range(n)] for i in range(n)])


def tmin(A):
    n = A.shape[0]
    return min(int((A[v] & A[:, u]).sum()) for u in range(n) for v in range(n) if A[u, v])


def bits(A):
    n = A.shape[0]
    return "".join(str(int(A[i, j])) for i in range(n) for j in range(i + 1, n))


for n, want in MCKAY.items():
    got = len(classes(n))
    assert got == want, f"n={n}: enumerated {got}, McKay says {want}"
print("counts agree with McKay for n = 13, 15, 17, 19")

total = 0
for n in (15, 17, 19):
    d = f"vt{n}"
    os.makedirs(d, exist_ok=True)
    QR = {(x * x) % n for x in range(1, n)} if n % 4 == 3 else None
    reps = classes(n)
    rows = sorted(((tmin(adj(n, S)), S) for S in reps), key=lambda r: -r[0])
    man = []
    for k, (t, S) in enumerate(rows):
        is_paley = QR is not None and set(S) == QR
        name = f"paley{n}" if is_paley else f"c{k:03d}"
        A = adj(n, S)
        assert (A + A.T == 1 - np.eye(n, dtype=int)).all()
        assert A.sum(1).min() == A.sum(1).max() == (n - 1) // 2
        open(os.path.join(d, name + ".bits"), "w").write(bits(A) + "\n")
        man.append((name, t, sorted(S)))
        total += 0 if is_paley else 1
    with open(os.path.join(d, "manifest.tsv"), "w") as f:
        f.write("name\ttmin\tconnection_set\n")
        for name, t, S in man:
            f.write(f"{name}\t{t}\t{','.join(map(str, S))}\n")
    ceil = 3 * (n * (n * n - 1) // 24) / (n * (n - 1) // 2)
    from collections import Counter
    print(f"n={n}: {len(rows)} classes -> {d}/  ceiling {ceil:.2f}  "
          f"tmin {dict(sorted(Counter(t for t, _ in rows).items()))}")
print(f"\nuntested total (Paley(19) excluded as a control): {total}")
