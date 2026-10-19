#!/usr/bin/env python3
"""Section 3.3: reversing a rung of Delta_1 - 10 leaves a 5-inducible tournament.

    usage: rung_reversal.py HOST.bits U V WITNESS.log

Builds the host, reverses the arc between U and V (0-based), and checks three things:

  * the reversed arc is a RUNG: its Aut(T)-orbit has 11 arcs, all pointing from the
    vertex orbit not containing vertex 0 (Y) to the one containing it (X), and every
    vertex is the end of exactly one of them;
  * the arc orbits of T are the five Section 3.3 lists, of sizes 55, 55, 55, 55 and 11;
  * the witness is a majority witness for the reversed tournament
    (verify_witness_bits.py --majority, on a bits file written from the reversal).

Exit 0 only if all three hold."""
import os, subprocess, sys, tempfile
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

hostp, u, v, wit = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
s = ''.join(open(hostp).read().split())
n = int(round((1 + (1 + 8 * len(s)) ** .5) / 2))
A = [[0] * n for _ in range(n)]; k = 0
for i in range(n):
    for j in range(i + 1, n):
        A[i][j] = int(s[k]); A[j][i] = 1 - A[i][j]; k += 1
G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if A[i][j])
auts = [tuple(m[i] for i in range(n)) for m in DiGraphMatcher(G, G).isomorphisms_iter()]
X = {h[0] for h in auts}
orbits, seen = [], set()
for a in sorted(G.edges()):
    if a in seen:
        continue
    o = {(h[a[0]], h[a[1]]) for h in auts}
    seen |= o; orbits.append(o)
sizes = sorted(len(o) for o in orbits)
arc = (u, v) if A[u][v] else (v, u)
orb = next(o for o in orbits if arc in o)
ends = sorted(x for e in orb for x in e)
rung = (len(orb) == 11 and all(a not in X and b in X for a, b in orb) and ends == list(range(n)))
print(f'|Aut| = {len(auts)}; arc orbits of sizes {sizes}; the arc {arc[0]} -> {arc[1]} '
      f'lies in an orbit of {len(orb)} arcs' + (', the rungs Y -> X' if rung else ', NOT the rungs'))
A[u][v], A[v][u] = A[v][u], A[u][v]
bits = ''.join(str(A[i][j]) for i in range(n) for j in range(i + 1, n))
with tempfile.NamedTemporaryFile('w', suffix='.bits', delete=False) as f:
    f.write(bits + '\n'); bf = f.name
r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    'verify_witness_bits.py'), wit, bf, str(n), '5', '--majority'],
                   capture_output=True, text=True)
os.remove(bf)
print('witness for the reversed tournament: ' + r.stdout.strip())
sys.exit(0 if rung and sizes == [11, 55, 55, 55, 55] and r.returncode == 0 else 1)
