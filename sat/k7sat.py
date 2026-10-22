#!/usr/bin/env python3
"""Is HOST K-inducible at unit margin?  Dissent-Boolean SAT encoding (paper 2, Appendix A.3), solved
by CaDiCaL; a satisfying assignment is decoded into K orders and written as `voter i:` lines.

    k7sat.py HOST.bits K SECONDS OUT.log

d[v,e] (voter v, arc e = i -> j of HOST) is true when v ranks j above i, i.e. dissents from e.
  unit margin : every arc has exactly (K-1)/2 dissenters  (at-most by (K+1)/2-subsets of negated
                literals, at-least by (K+3)/2-subsets of positive ones -- plain binomial clauses)
  linear order: for every voter and every triple, forbid the two dissent patterns that would make
                the voter's relation on the triple cyclic.
The orders are recovered by sorting each voter's vertices by out-degree in its (transitive) relation.
Exit status: 10 SAT, 20 UNSAT, 0 unknown (time limit), as CaDiCaL's."""
import itertools, os, subprocess, sys
CAD = os.environ.get("CADICAL") or os.path.expanduser("~/Downloads/DownloadedSoftware/cadical/build/cadical")
host, K, secs, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
assert K % 2 == 1
s = ''.join(c for c in open(host).read() if c in '01')
n = int(round((1 + (1 + 8 * len(s)) ** .5) / 2)); assert n * (n - 1) // 2 == len(s)
A = [[0] * n for _ in range(n)]; k = 0
for i in range(n):
    for j in range(i + 1, n):
        A[i][j] = int(s[k]); A[j][i] = 1 - A[i][j]; k += 1
arcs = [(i, j) for i in range(n) for j in range(n) if A[i][j]]
aid = {a: t for t, a in enumerate(arcs)}
var = lambda v, t: v * len(arcs) + t + 1
D = (K - 1) // 2
cls = []
for t in range(len(arcs)):
    for S in itertools.combinations(range(K), D + 1):  cls.append([-var(v, t) for v in S])   # <= D dissent
    for S in itertools.combinations(range(K), K - D + 1): cls.append([var(v, t) for v in S])  # >= D dissent


def fwd(v, a, b):
    """literal: voter v ranks a above b."""
    return -var(v, aid[(a, b)]) if A[a][b] else var(v, aid[(b, a)])


for v in range(K):
    for a, b, c in itertools.combinations(range(n), 3):
        cls.append([-fwd(v, a, b), -fwd(v, b, c), -fwd(v, c, a)])   # no a>b>c>a
        cls.append([-fwd(v, b, a), -fwd(v, c, b), -fwd(v, a, c)])   # no a>c>b>a
cnf = out + '.cnf'
with open(cnf, 'w') as f:
    f.write(f'p cnf {K * len(arcs)} {len(cls)}\n')
    for c in cls: f.write(' '.join(map(str, c)) + ' 0\n')
print(f'n={n} K={K} unit margin: {K * len(arcs)} variables, {len(cls)} clauses, limit {secs}s', file=sys.stderr)
r = subprocess.run([CAD, '-q', f'-t', str(secs), cnf], capture_output=True, text=True)
vals = {int(x) for ln in r.stdout.splitlines() if ln.startswith('v ') for x in ln[2:].split()}
with open(out, 'w') as f:
    f.write(f'n={n} K={K} margin=unit vars={K * len(arcs)} clauses={len(cls)} limit={secs}s\n')
    if r.returncode == 10:
        f.write('RESULT SAT\n')
        for v in range(K):
            wins = [sum((fwd(v, a, b) in vals) for b in range(n) if b != a) for a in range(n)]
            f.write(f'  voter {v}: ' + ' '.join(map(str, sorted(range(n), key=lambda a: -wins[a]))) + '\n')
    else:
        f.write('RESULT ' + {20: 'UNSAT', 0: 'UNKNOWN (time limit)'}.get(r.returncode, f'rc={r.returncode}') + '\n')
os.remove(cnf)
print(open(out).read().splitlines()[1], file=sys.stderr)
sys.exit(r.returncode)
