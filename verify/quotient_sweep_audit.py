#!/usr/bin/env python3
"""Audit the complete search of Delta_1 - 10 (Section 3.2) from the host and the markers alone.

    usage: quotient_sweep_audit.py HOST.bits MARKERS.tar.zst [--drop N]

The search did not visit all 8,031 base states.  It kept one per orbit of an order-5
subgroup H of Aut(T) (Corollary 2.5) and anchored on the two vertices H fixes (Corollary
2.3).  So a tiling of [0, 8031) is the wrong test, and this script derives the right one
from the host:

  1. Aut(T) by VF2; it must have order 55 and two vertex orbits X and Y (X is the orbit
     of vertex 0).
  2. g = the first automorphism of order 5 fixing vertex 0 (H = <g>); it fixes exactly one
     vertex x0 of X and one y0 of Y, the anchoring representatives (--toporb x0 y0).
  3. B = the out-neighbours of x0 inside X, which must induce the regular 5-tournament,
     and g must map B onto itself.
  4. The majority base states of B, enumerated exactly as the engine's brec() does
     (orders of the base positions in lexicographic order, K = 5 orders as a
     non-decreasing index multiset, every base arc carried by at least 3), must number
     8,031, and g must map that set onto itself.
  5. One representative per H-orbit, the smallest index.  Every representative must have
     a marker reading `RESULT UNSAT ... base_states=8031` and `SLICE cleared=1 capped=0`,
     and there must be no marker for a non-representative.

It prints the base, the anchors and the summed core-hours.  --drop N removes the N-th
marker before checking; the gate uses it as the control, which must fail.  The markers
hold only the engine's RESULT and SLICE lines, so the base and anchors the search was run
with are recorded in the archive's xsweep.sh, not in each marker."""
import io, itertools, re, subprocess, sys, tarfile
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

args = sys.argv[1:]
drop = None
if '--drop' in args:
    i = args.index('--drop'); drop = int(args[i + 1]); del args[i:i + 2]
host, arc = args

s = ''.join(c for c in open(host).read() if c in '01')
n = int(round((1 + (1 + 8 * len(s)) ** .5) / 2))
assert n * (n - 1) // 2 == len(s), 'not a tournament bit string'
A = [[0] * n for _ in range(n)]; k = 0
for i in range(n):
    for j in range(i + 1, n):
        A[i][j], A[j][i] = (1, 0) if s[k] == '1' else (0, 1); k += 1
G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if A[i][j])
auts = [tuple(m[i] for i in range(n)) for m in DiGraphMatcher(G, G).isomorphisms_iter()]
assert len(auts) == 55, f'|Aut| = {len(auts)}, expected 55'
X = sorted({h[0] for h in auts})
assert len(X) == n // 2, 'vertex 0 does not have an orbit of half the vertices'
ident = tuple(range(n))


def order(h):
    q, k = h, 1
    while q != ident:
        q, k = tuple(h[x] for x in q), k + 1
    return k


g = next(h for h in auts if order(h) == 5 and h[0] == 0)
fixed = [v for v in range(n) if g[v] == v]
x0 = next(v for v in fixed if v in X); y0 = next(v for v in fixed if v not in X)
assert len(fixed) == 2, fixed
B = [v for v in X if A[x0][v]]
assert len(B) == 5 and all(sum(A[u][v] for v in B) == 2 for u in B), 'B is not the regular 5-tournament'
assert sorted(g[v] for v in B) == B, 'g does not map B onto itself'

b, K = 5, 5
pairs = [(i, j) for i in range(b) for j in range(i + 1, b)]
perms = []
for idx in itertools.permutations(range(b)):
    pos = {v: r for r, v in enumerate(idx)}
    perms.append((idx, sum(1 << e for e, (i, j) in enumerate(pairs) if pos[i] < pos[j])))
target = [1 if A[B[i]][B[j]] else 0 for i, j in pairs]
states = []


def rec(t, lo, cnt, chosen):
    if t == K:
        states.append(tuple(chosen)); return
    rem = K - t - 1
    for p in range(lo, len(perms)):
        m = perms[p][1]; c2 = cnt[:]; ok = True
        for e in range(len(pairs)):
            c2[e] += (m >> e) & 1
            sup = c2[e] if target[e] else (t + 1 - c2[e])
            if sup + rem < 3:
                ok = False; break
        if ok:
            rec(t + 1, p, c2, chosen + [p])


rec(0, 0, [0] * len(pairs), [])
assert len(states) == 8031, len(states)
index = {st: i for i, st in enumerate(states)}
pidx = {perms[p][0]: p for p in range(len(perms))}
gpos = [B.index(g[B[i]]) for i in range(b)]


def gmap(st):
    return tuple(sorted(pidx[tuple(gpos[x] for x in perms[p][0])] for p in st))


reps, seen = set(), set()
for st in states:
    if st in seen:
        continue
    orb = {st}; q = gmap(st)
    while q not in orb:
        orb.add(q); q = gmap(q)
    assert all(o in index for o in orb), 'g does not map the base states onto themselves'
    seen |= orb; reps.add(min(index[o] for o in orb))

raw = subprocess.run(['zstd', '-dc', arc], capture_output=True, check=True).stdout
mk, tf = {}, tarfile.open(fileobj=io.BytesIO(raw))
for m in tf:
    if m.isfile() and '/exhausted/' in m.name:
        mk[int(m.name.rsplit('/', 1)[1])] = tf.extractfile(m).read().decode()
if drop is not None:
    del mk[sorted(mk)[drop]]
bad, secs = [], 0.0
for r in sorted(reps):
    t = mk.get(r)
    if t is None:
        bad.append(f'{r}: no marker'); continue
    if not (re.search(r'^RESULT UNSAT .*base_states=8031 ', t, re.M) and
            re.search(r'^SLICE cleared=1 capped=0', t, re.M)):
        bad.append(f'{r}: not an uncapped UNSAT'); continue
    secs += float(re.search(r' time=([\d.]+)s', t).group(1))
extra = sorted(set(mk) - reps)
if extra:
    bad.append(f'{len(extra)} marker(s) for non-representatives, e.g. {extra[:3]}')
print(f'Aut order 55, g of order 5 fixes x0={x0}, y0={y0}; base {B} (regular); '
      f'8031 base states, {len(reps)} H-orbit representatives')
if bad:
    print(f'FAIL: {len(bad)} problem(s): ' + '; '.join(bad[:5])); sys.exit(1)
print(f'COMPLETE: all {len(reps)} representatives exhausted, uncapped, '
      f'{secs / 3600:.2f} core-hours')
