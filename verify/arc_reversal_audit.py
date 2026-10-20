#!/usr/bin/env python3
"""Section 3.3: reversing a non-rung arc from Y to X in Delta_1 - 10 leaves an obstruction.

    usage: arc_reversal_audit.py HOST.bits U V BASE MARKERS.tar.zst [--drop N]

HOST is Delta_1 - 10; U V (0-based) name the arc to reverse; BASE is the comma-separated base
the search used, in the same vertex names.  The script checks, from these alone:

  1. Aut(Delta_1 - 10) has order 55 with two vertex orbits; X is the orbit of vertex 0, Y the
     other.  The arc between U and V points from Y to X, and its Aut-orbit has 55 arcs, all
     from Y to X -- so it is not a rung (the rungs form an orbit of 11).
  2. The reversed tournament T' has no non-trivial automorphism, so no symmetry reduction
     applies and its search must cover every base state.
  3. BASE induces the regular tournament on five vertices in T', and its majority base
     states, enumerated exactly as the engine's brec() does, number 8,031.
  4. The markers are exactly one per base state 0..8030, each an exhausted state.  These
     markers were written by the cluster kit's run_block.sh (or its one-state rerun) only
     after the engine's log read `RESULT UNSAT` and `SLICE cleared=1 capped=0`; they keep
     the RESULT line's counters (secs, nodes, ...), not the line itself.

--drop N removes the N-th marker first; the gate uses it as the control, which must fail."""
import io, itertools, re, subprocess, sys, tarfile
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

args = sys.argv[1:]
drop = None
if '--drop' in args:
    i = args.index('--drop'); drop = int(args[i + 1]); del args[i:i + 2]
host, u, v, base, arc = args[0], int(args[1]), int(args[2]), [int(x) for x in args[3].split(',')], args[4]

s = ''.join(c for c in open(host).read() if c in '01')
n = int(round((1 + (1 + 8 * len(s)) ** .5) / 2))
assert n * (n - 1) // 2 == len(s), 'not a tournament bit string'
A = [[0] * n for _ in range(n)]; k = 0
for i in range(n):
    for j in range(i + 1, n):
        A[i][j], A[j][i] = (1, 0) if s[k] == '1' else (0, 1); k += 1


def auts(M):
    G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if M[i][j])
    return [tuple(m[i] for i in range(n)) for m in DiGraphMatcher(G, G).isomorphisms_iter()]


aut = auts(A)
assert len(aut) == 55, f'|Aut| = {len(aut)}, expected 55'
X = {h[0] for h in aut}
assert len(X) == n // 2, 'vertex 0 does not have an orbit of half the vertices'
a, b = (u, v) if A[u][v] else (v, u)
assert a not in X and b in X, f'the arc {a}->{b} does not point from Y to X'
orb = {(h[a], h[b]) for h in aut}
assert len(orb) == 55 and all(p not in X and q in X for p, q in orb), \
    f'the orbit of {a}->{b} has {len(orb)} arcs, not 55 from Y to X'

T = [r[:] for r in A]; T[a][b], T[b][a] = 0, 1
assert len(auts(T)) == 1, 'the reversed tournament has a non-trivial automorphism'

assert len(base) == 5 and all(sum(T[x][y] for y in base) == 2 for x in base), \
    'BASE does not induce the regular 5-tournament'
K = 5
pairs = [(i, j) for i in range(5) for j in range(i + 1, 5)]
perms = []
for idx in itertools.permutations(range(5)):
    pos = {w: r for r, w in enumerate(idx)}
    perms.append(sum(1 << e for e, (i, j) in enumerate(pairs) if pos[i] < pos[j]))
target = [1 if T[base[i]][base[j]] else 0 for i, j in pairs]
count = 0


def rec(t, lo, cnt):
    global count
    if t == K:
        count += 1; return
    rem = K - t - 1
    for p in range(lo, len(perms)):
        m = perms[p]; c2 = cnt[:]; ok = True
        for e in range(len(pairs)):
            c2[e] += (m >> e) & 1
            sup = c2[e] if target[e] else (t + 1 - c2[e])
            if sup + rem < 3:
                ok = False; break
        if ok:
            rec(t + 1, p, c2)


rec(0, 0, [0] * len(pairs))
assert count == 8031, count

raw = subprocess.run(['zstd', '-dc', arc], capture_output=True, check=True).stdout
mk, tf = {}, tarfile.open(fileobj=io.BytesIO(raw))
for m in tf:
    if m.isfile() and '/exhausted/' in m.name:
        mk[int(m.name.rsplit('/', 1)[1])] = tf.extractfile(m).read().decode()
if drop is not None:
    del mk[sorted(mk)[drop]]
bad, secs = [], 0.0
for st in range(count):
    t = mk.get(st)
    if t is None:
        bad.append(f'{st}: no marker'); continue
    mm = re.match(r'secs=([\d.]+)s? nodes=\d+ ', t)
    if not mm:
        bad.append(f'{st}: not an exhausted-state marker'); continue
    secs += float(mm.group(1))
extra = sorted(set(mk) - set(range(count)))
if extra:
    bad.append(f'{len(extra)} marker(s) outside 0..{count - 1}')
print(f'Aut(Delta_1 - 10) order 55; reversed {a}->{b}, a Y->X arc in an orbit of 55 (not a rung); '
      f'the reversal is rigid; base {base} regular, {count} base states')
if bad:
    print(f'FAIL: {len(bad)} problem(s): ' + '; '.join(bad[:5])); sys.exit(1)
print(f'COMPLETE: all {count} base states exhausted, no witness '
      f'({secs / 3600:.0f} recorded core-hours, cluster and laptop seconds together)')
