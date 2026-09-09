#!/usr/bin/env python3
"""The FULL vertex-transitive family on 21 vertices, deduped by EXACT isomorphism.

Cayley tournaments over both groups of order 21 (Z_21, F_21 = Z_7 : Z_3): a connection set picks
one element of each inverse pair.  Spectrum is used only to BUCKET candidates; every collision is
then settled by an exact VF2 isomorphism test, because cospectral non-isomorphic tournaments exist
and merging on spectrum alone silently undercounts.

Filter under test (Leonid's, 2026-09-05): min over arcs of #{3-cycles through that arc} >= 5.
The mean is 3*(#3-cycles)/#arcs = 5.5 at n=21, so this selects the evenly-loaded end.
"""
import itertools, sys, numpy as np, networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

def z21():
    els = list(range(1, 21)); pairs, used = [], set()
    for g in els:
        if g in used: continue
        used |= {g, (-g) % 21}; pairs.append((g, (-g) % 21))
    def adj(S):
        A = np.zeros((21, 21), int)
        for i in range(21):
            for j in range(21):
                if i != j and (j - i) % 21 in S: A[i, j] = 1
        return A
    return pairs, adj

def f21():
    mul = lambda x, y: ((x[0] + y[0] * pow(2, x[1], 7)) % 7, (x[1] + y[1]) % 3)
    full = [(i, j) for i in range(7) for j in range(3)]
    els = [g for g in full if g != (0, 0)]
    inv = {g: next(h for h in full if mul(g, h) == (0, 0)) for g in full}
    pairs, used = [], set()
    for g in els:
        if g in used: continue
        used |= {g, inv[g]}; pairs.append((g, inv[g]))
    pos = {g: k for k, g in enumerate(full)}
    def adj(S):
        A = np.zeros((21, 21), int)
        for a in full:
            for b in full:
                if a != b and mul(inv[a], b) in S: A[pos[a], pos[b]] = 1
        return A
    return pairs, adj

def spectrum(A):
    ev = sorted(np.linalg.eigvals(A.astype(float)), key=lambda z: (round(z.real,6), round(z.imag,6)))
    return tuple((round(z.real, 4), round(abs(z.imag), 4)) for z in ev)

def tri_per_arc(A):
    n = A.shape[0]
    return [int(sum(1 for w in range(n) if A[v, w] and A[w, u]))
            for u in range(n) for v in range(n) if A[u, v]]

cands = []
for name, (pairs, adj) in (("Z21", z21()), ("F21", f21())):
    for S in itertools.product(*pairs):
        A = adj(frozenset(S))
        assert (A + A.T == 1 - np.eye(21, dtype=int)).all() and A.sum(1).min() == A.sum(1).max() == 10
        cands.append((name, frozenset(S), A))
print(f"{len(cands)} Cayley tournaments generated (1024 per group)")

buckets = {}
for name, S, A in cands:
    buckets.setdefault(spectrum(A), []).append((name, S, A))
reps = []
for sp, group in buckets.items():
    keep = []
    for name, S, A in group:
        G = nx.DiGraph(A)
        if not any(DiGraphMatcher(nx.DiGraph(B), G).is_isomorphic() for _, _, B in keep):
            keep.append((name, S, A))
    reps.extend(keep)
ncos = sum(1 for sp, g in buckets.items() if len({id(x) for x in g}) and len(g) > 1)
print(f"{len(buckets)} distinct spectra -> {len(reps)} isomorphism classes after exact VF2 tests")
print(f"  (spectrum alone would have said {len(buckets)}; the difference is cospectral non-isomorphs)")

ncyc = 21 * (21 * 21 - 1) // 24
sel = [(n, S, A) for n, S, A in reps if min(tri_per_arc(A)) >= 5]
print(f"\nmean 3-cycles per arc = {3*ncyc}/{21*20//2} = {3*ncyc/(21*20//2)}")
print(f"classes with EVERY arc in >= 5 cyclic triangles: {len(sel)}")
for n, S, A in sel:
    t = tri_per_arc(A); print(f"    {n}  min={min(t)} max={max(t)}  S={sorted(S)}")
np.save("vt21_all_reps.npy", np.array([A for _, _, A in reps]))
np.save("vt21_sel_reps.npy", np.array([A for _, _, A in sel]))
print(f"\nsaved {len(reps)} representatives -> vt21_all_reps.npy")
