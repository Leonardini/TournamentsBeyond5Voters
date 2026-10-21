#!/usr/bin/env python3
"""Audit a complete Corollary 2.5 search of a 22-vertex host from the host, its base and the markers.

    usage: quotient_sweep_audit_g.py HOST.bits BASE MARKERS.tar.zst [MARKERS2.tar.zst ...] [--drop N]

The generalisation of quotient_sweep_audit.py (which is specific to Delta_1 - 10 and its anchors)
to the four obstructions of Section 3.2 whose automorphism group has order 5: Delta_1 - 1,
Delta_1 - 2, Delta_11 - 2 and Delta_11 - 5.  These searches used Corollary 2.5 alone, with no
anchoring, over a base given explicitly (BASE, comma-separated 0-based vertices, as the search
was run).  From the host it derives:

  1. Aut(T) by VF2, which must have order 5, and a generator g;
  2. that BASE induces the regular 5-tournament and that g maps it onto itself;
  3. the majority base states of BASE, enumerated exactly as the engine's brec() does, which must
     number 8,031, and that g maps that set onto itself;
  4. one representative per <g>-orbit, the smallest index.

Every representative must then have an exhausted marker in one of the archives.  Two marker
formats occur, and both are written only when the engine printed RESULT UNSAT for that one base
state: the laptop's (`SLICE cleared=1 capped=0` and `RESULT UNSAT ... base_states=8031`) and the
cluster's (`secs=... nodes=...`, which the cluster kit writes only from a RESULT UNSAT line).
Markers for non-representatives are allowed only if they are also UNSAT (the laptop's reverse
sweep and the cluster overlapped).  --drop N removes the N-th representative's marker from every
archive before checking; the gate uses it as the control, which must fail."""
import io, itertools, re, subprocess, sys, tarfile
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

args = sys.argv[1:]
drop = None
if '--drop' in args:
    i = args.index('--drop'); drop = int(args[i + 1]); del args[i:i + 2]
host, base, arcs = args[0], [int(x) for x in args[1].split(',')], args[2:]

s = ''.join(c for c in open(host).read() if c in '01')
n = int(round((1 + (1 + 8 * len(s)) ** .5) / 2))
assert n * (n - 1) // 2 == len(s), 'not a tournament bit string'
A = [[0] * n for _ in range(n)]; k = 0
for i in range(n):
    for j in range(i + 1, n):
        A[i][j], A[j][i] = (1, 0) if s[k] == '1' else (0, 1); k += 1
G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if A[i][j])
auts = [tuple(m[i] for i in range(n)) for m in DiGraphMatcher(G, G).isomorphisms_iter()]
assert len(auts) == 5, f'|Aut| = {len(auts)}, expected 5'
ident = tuple(range(n))
g = next(h for h in auts if h != ident)
B = base
assert len(B) == 5 and all(sum(A[u][v] for v in B) == 2 for u in B), 'BASE is not the regular 5-tournament'
assert sorted(g[v] for v in B) == sorted(B), 'g does not map BASE onto itself'

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

LAPTOP = (re.compile(r'^RESULT UNSAT .*base_states=8031 ', re.M), re.compile(r'^SLICE cleared=1 capped=0', re.M))
CLUSTER = re.compile(r'^secs=([\d.]+)s nodes=\d+', re.M)
mk = {}
for arc in arcs:
    raw = subprocess.run(['zstd', '-dc', arc], capture_output=True, check=True).stdout
    tf = tarfile.open(fileobj=io.BytesIO(raw))
    for m in tf:
        if m.isfile() and '/exhausted/' in m.name:
            st = int(re.sub(r'^.*_', '', m.name.rsplit('/', 1)[1]))
            mk.setdefault(st, []).append(tf.extractfile(m).read().decode())
if drop is not None:
    mk.pop(sorted(reps)[drop], None)


def unsat(t):
    if LAPTOP[0].search(t) and LAPTOP[1].search(t):
        return float(re.search(r' time=([\d.]+)s', t).group(1))
    c = CLUSTER.search(t)
    return float(c.group(1)) if c else None


bad, secs = [], 0.0
for st, ts in mk.items():
    if any(unsat(t) is None for t in ts):
        bad.append(f'{st}: a marker that is not an uncapped UNSAT')
for r in sorted(reps):
    if r not in mk:
        bad.append(f'{r}: no marker'); continue
    secs += min(unsat(t) or 0.0 for t in mk[r])
print(f'Aut order 5; g maps the base {B} (regular) onto itself; 8031 base states, '
      f'{len(reps)} <g>-orbit representatives; {len(mk)} states with markers in {len(arcs)} archive(s)')
if bad:
    print(f'FAIL: {len(bad)} problem(s): ' + '; '.join(bad[:5])); sys.exit(1)
print(f'COMPLETE: all {len(reps)} representatives exhausted, uncapped, '
      f'{secs / 3600:.2f} core-hours (the faster marker where two exist)')
