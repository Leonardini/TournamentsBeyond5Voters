#!/usr/bin/env python3
"""Section 4.2, Conjecture 3: check a K-voter witness at unit margin, independently of the solver.

    usage: unit_margin_witness.py HOST.bits WITNESS.log K

The witness file holds K lines `voter i: v_1 ... v_n`, each an order of the host's vertices
(0-based, best first).  Every arc of the host must be carried by exactly (K+1)/2 of the K orders,
which is unit margin.  Exit 0 only if it is."""
import re, sys
host, log, K = sys.argv[1], sys.argv[2], int(sys.argv[3])
s = ''.join(c for c in open(host).read() if c in '01')
n = int(round((1 + (1 + 8 * len(s)) ** .5) / 2)); assert n * (n - 1) // 2 == len(s)
A = [[0] * n for _ in range(n)]; k = 0
for i in range(n):
    for j in range(i + 1, n):
        A[i][j] = int(s[k]); A[j][i] = 1 - A[i][j]; k += 1
orders = [list(map(int, x.split())) for x in re.findall(r'^\s*voter \d+:\s*([\d ]+)$', open(log).read(), re.M)]
if len(orders) != K or any(sorted(o) != list(range(n)) for o in orders):
    print(f'FAIL: not {K} orders of the {n} vertices'); sys.exit(1)
pos = [{v: r for r, v in enumerate(o)} for o in orders]
sup = [sum(p[i] < p[j] for p in pos) for i in range(n) for j in range(n) if A[i][j]]
if any(c != (K + 1) // 2 for c in sup):
    print(f'FAIL: supports {sorted(set(sup))}, not all {(K + 1) // 2}'); sys.exit(1)
print(f'{K} orders of {n} vertices; all {len(sup)} arcs at support exactly {(K + 1) // 2} (unit margin)')
