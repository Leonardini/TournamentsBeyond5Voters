#!/usr/bin/env python3
"""How many vertex-transitive tournaments are there on 21 and 23 vertices?

A VT tournament is regular, so n must be odd.  We enumerate CAYLEY tournaments over each group
of order n: pick one element from each inverse pair {g, g^-1} as the connection set S, giving
2^((n-1)/2) sets per group, then count isomorphism classes.

n = 23 is PRIME, so any transitive group on 23 points has order divisible by 23 (Cauchy), hence
contains a 23-cycle: every VT tournament on 23 vertices IS a circulant.  Circulants of prime
order are CI (Turner), so isomorphism is exactly multiplier equivalence and the count is an
orbit count -- exact, no iso testing needed.

n = 21 = 3*7 has two groups, Z_21 and F_21 = Z_7 : Z_3.  Used here as a KNOWN-ANSWER CHECK
against the seven hosts already on file.
"""
import itertools, sys
from collections import defaultdict

def orbits_under(sets, maps):
    seen, reps = set(), []
    for S in sets:
        if S in seen: continue
        orb = {frozenset(m[g] for g in S) for m in maps}
        seen |= orb; reps.append(S)
    return reps

def cyclic(n):
    """Z_n: elements 0..n-1, multiplier maps x -> a*x for a in units."""
    els = list(range(1, n))
    pairs = []
    used = set()
    for g in els:
        if g in used: continue
        used |= {g, (-g) % n}; pairs.append((g, (-g) % n))
    units = [a for a in range(1, n) if __import__('math').gcd(a, n) == 1]
    maps = [{g: (a * g) % n for g in els} for a in units]
    return els, pairs, maps

def frob21():
    """F_21 = <a,b | a^7, b^3, b a b^-1 = a^2>, elements (i,j) = a^i b^j."""
    n7, n3 = 7, 3
    els = [(i, j) for i in range(n7) for j in range(n3) if (i, j) != (0, 0)]
    def mul(x, y):
        i1, j1 = x; i2, j2 = y
        return ((i1 + i2 * pow(2, j1, 7)) % 7, (j1 + j2) % 3)
    def inv(x):
        for y in [(i, j) for i in range(7) for j in range(3)]:
            if mul(x, y) == (0, 0): return y
    pairs, used = [], set()
    for g in els:
        if g in used: continue
        used |= {g, inv(g)}; pairs.append((g, inv(g)))
    # automorphisms of F_21: order 42 group; build by brute force over generator images
    auts = []
    a_cands = [g for g in els if all(_pow(g, k, mul) != (0, 0) for k in (1,)) and _ord(g, mul) == 7]
    b_cands = [g for g in els if _ord(g, mul) == 3]
    for A in a_cands:
        for B in b_cands:
            if mul(mul(B, A), inv(B)) != _pow(A, 2, mul): continue
            m = {}
            for i in range(7):
                for j in range(3):
                    if (i, j) == (0, 0): continue
                    m[(i, j)] = mul(_pow(A, i, mul), _pow(B, j, mul))
            auts.append(m)
    return els, pairs, auts

def _pow(g, k, mul):
    r = (0, 0)
    for _ in range(k): r = mul(r, g)
    return r
def _ord(g, mul):
    r, k = g, 1
    while r != (0, 0): r = mul(r, g); k += 1
    return k

for name, (els, pairs, maps) in [("Z_21", cyclic(21)), ("F_21", frob21()), ("Z_23", cyclic(23))]:
    sets = [frozenset(c) for c in itertools.product(*pairs)]
    reps = orbits_under(sets, maps)
    print(f"{name:>5}: {len(pairs)} inverse pairs -> {len(sets)} connection sets, "
          f"|Aut(G)|={len(maps)} -> {len(reps)} classes up to group-automorphism")

# --- soundness check: are the Z_21 classes really pairwise NON-isomorphic tournaments? ---
# Spectrum of the adjacency matrix is an exact isomorphism invariant, so DISTINCT spectra
# prove distinct tournaments (one-way, which is the direction we need for a lower bound).
import numpy as np
def cay_adj(n, S):
    A = np.zeros((n, n), int)
    for i in range(n):
        for j in range(n):
            if i != j and (j - i) % n in S: A[i, j] = 1
    return A
els, pairs, maps = cyclic(21)
reps21 = orbits_under([frozenset(c) for c in itertools.product(*pairs)], maps)
spec = {}
for S in reps21:
    ev = np.round(np.sort_complex(np.linalg.eigvals(cay_adj(21, S))), 6)
    spec.setdefault(tuple(np.round(ev.real,4)) + tuple(np.round(ev.imag,4)), []).append(S)
print(f"\nZ_21: {len(reps21)} multiplier classes -> {len(spec)} DISTINCT spectra "
      f"=> at least {len(spec)} pairwise non-isomorphic VT tournaments on 21 vertices")
els, pairs, maps = cyclic(23)
reps23 = orbits_under([frozenset(c) for c in itertools.product(*pairs)], maps)
spec23 = {}
for S in reps23:
    ev = np.round(np.sort_complex(np.linalg.eigvals(cay_adj(23, S))), 6)
    spec23.setdefault(tuple(np.round(ev.real,4)) + tuple(np.round(ev.imag,4)), []).append(S)
print(f"Z_23: {len(reps23)} multiplier classes -> {len(spec23)} DISTINCT spectra "
      f"=> at least {len(spec23)} pairwise non-isomorphic VT tournaments on 23 vertices")
