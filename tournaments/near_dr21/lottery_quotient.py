"""Complete unit-margin lottery on the order-5 gluings via Lemma 2.4 (his call, 2026-10-17).

For each open host: an order-5 automorphism g (the gluing's sigma x tau, fixing the apex),
base B = one 5-cycle of g inside X (every circulant 5-tournament is the regular one, so
B induces RT5), the UNIT-margin base states of B enumerated exactly as kinduce's brec()
(lexicographic next_permutation order of the --base positions, non-decreasing index
multisets of K orders, every base arc carried by exactly 3 of 5), one representative
per <g>-orbit.  No anchoring is used, so Lemma 2.4 needs no compatibility condition.
Searching every representative to exhaustion with no witness proves the host is not
5-inducible at unit margin.  Representatives are shuffled per host and queued block-major.

Writes lottery21q/hosts/<h>.{bits,base} and lottery21q/queue.txt ("host state").
Asserts: |Aut| divisible by 5, B is g-invariant and regular, 2,200 states, g maps the
state set onto itself."""
import itertools, pathlib, random
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

import sys
HERE = pathlib.Path(__file__).parent
# generalised 2026-10-17 19:35:  lottery_quotient.py [HOSTS_TSV OUTDIR MARGIN ONLY_FILE]
#   MARGIN exact (unit, 2,200 states on RT5) or majority (8,031); ONLY_FILE lists host names to queue.
HOSTS_TSV = sys.argv[1] if len(sys.argv) > 1 else 'O5_HOSTS21.tsv'
OUT = HERE / (sys.argv[2] if len(sys.argv) > 2 else 'lottery21q')
MARGIN = sys.argv[3] if len(sys.argv) > 3 else 'exact'
ONLY = set(open(HERE / sys.argv[4]).read().split()) if len(sys.argv) > 4 else None
EXPECT = {'exact': 2200, 'majority': 8031}[MARGIN]
(OUT / 'hosts').mkdir(parents=True, exist_ok=True); (OUT / 'found').mkdir(exist_ok=True)
found_before = {p.name for p in (HERE / 'lottery21' / 'found').iterdir()} if len(sys.argv) <= 1 else set()
rows = [l.rstrip('\n').split('\t') for l in open(HERE / HOSTS_TSV) if not l.startswith('#')]
K, b = 5, 5
pairs = [(i, j) for i in range(b) for j in range(i + 1, b)]
perms = []
for idx in itertools.permutations(range(b)):
    pos = {v: r for r, v in enumerate(idx)}
    perms.append((idx, sum(1 << e for e, (i, j) in enumerate(pairs) if pos[i] < pos[j])))
pidx = {p[0]: k for k, p in enumerate(perms)}

def unit_states(target):
    states = []
    def rec(t, lo, cnt, chosen):
        if t == K: states.append(tuple(chosen)); return
        rem = K - t - 1
        for p in range(lo, len(perms)):
            m = perms[p][1]; c2 = cnt[:]; ok = True
            for e in range(len(pairs)):
                c2[e] += (m >> e) & 1
                sup = c2[e] if target[e] else (t + 1 - c2[e])
                if (MARGIN == 'exact' and sup > 3) or sup + rem < 3: ok = False; break   # exact: exactly 3; majority: >= 3
            if ok: rec(t + 1, p, c2, chosen + [p])
    rec(0, 0, [0] * len(pairs), [])
    return states

queue = {}
for name, n, _, _, bits, *_ in rows:
    if name in found_before or (ONLY is not None and name not in ONLY): continue
    n = int(n); A = [[0] * n for _ in range(n)]; k = 0
    for i in range(n):
        for j in range(i + 1, n): A[i][j], A[j][i] = (1, 0) if bits[k] == '1' else (0, 1); k += 1
    G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if A[i][j])
    auts = [tuple(m[i] for i in range(n)) for m in DiGraphMatcher(G, G).isomorphisms_iter()]
    assert len(auts) % 5 == 0, (name, len(auts))
    ident = tuple(range(n))
    def order(h):
        q, c = h, 1
        while q != ident: q, c = tuple(h[x] for x in q), c + 1
        return c
    g = next(h for h in auts if order(h) == 5)
    x0 = next(v for v in range(n) if g[v] != v)                   # any vertex g moves: its 5-cycle is the base
    B = [x0]
    while g[B[-1]] != x0: B.append(g[B[-1]])
    B = sorted(B)
    assert len(B) == 5 and sorted(g[v] for v in B) == B
    assert all(sum(A[u][w] for w in B) == 2 for u in B), "base not regular"
    target = [A[B[i]][B[j]] for i, j in pairs]
    st = unit_states(target); assert len(st) == EXPECT, (name, len(st))
    index = {s: i for i, s in enumerate(st)}
    gpos = [B.index(g[B[i]]) for i in range(b)]
    def gmap(s): return tuple(sorted(pidx[tuple(gpos[x] for x in perms[p][0])] for p in s))
    reps, seen = [], set()
    for s in st:
        if s in seen: continue
        orb = {s}; q = gmap(s)
        while q not in orb: assert q in index; orb.add(q); q = gmap(q)
        seen |= orb; reps.append(min(index[o] for o in orb))
    random.Random(name).shuffle(reps); queue[name] = reps
    (OUT / 'hosts' / f'{name}.bits').write_text(bits + '\n'); (OUT / 'hosts' / f'{name}.base').write_text(' '.join(map(str, B)) + '\n')
    print(f"{name}: |Aut|={len(auts)} base {B} {EXPECT} states -> {len(reps)} orbit reps", flush=True)
D = max(len(r) for r in queue.values())
with open(OUT / 'queue.txt', 'w') as f:
    for r in range(D):
        for name, reps in queue.items():
            if r < len(reps): f.write(f"{name} {reps[r]}\n")
print(len(queue), 'hosts,', sum(len(r) for r in queue.values()), 'states queued')
