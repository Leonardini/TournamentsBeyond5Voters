#!/usr/bin/env python3
"""Section 3.3: the eighth 22-vertex obstruction (Delta_1 - 10 with the arc between U and V reversed)
is vertex-critical.

    usage: r0102_critical.py DELTA1_10.bits U V WITNESSES.tar.zst [--shift]

The reversed tournament R is rebuilt here from Delta_1 - 10 and U, V (0-based), never read from a
file the search wrote.  For each vertex w of R:

  * w in {U, V}: R - w equals (Delta_1 - 10) - w, since the reversed arc is gone with w, and that
    deletion is 5-inducible because Delta_1 - 10 is vertex-critical (gate check 8d).  Checked here:
    the two adjacency matrices are equal.
  * otherwise: the archive must hold a witness for d000mv09_r01_02_mvWW (WW = w, two digits), five
    `voter i:` lines in R - w's labels (R's vertices other than w, in order, renumbered 0..20), and
    every arc of R - w must be carried by at least 3 of the 5 orders.

--shift is the control: each witness is checked against R - (w + 1) instead, which must fail.
Exit 0 only if all 22 deletions are accounted for."""
import io, re, subprocess, sys, tarfile

args = sys.argv[1:]
shift = '--shift' in args
args = [a for a in args if a != '--shift']
host, u, v, arc = args[0], int(args[1]), int(args[2]), args[3]

s = ''.join(c for c in open(host).read() if c in '01')
n = int(round((1 + (1 + 8 * len(s)) ** .5) / 2))
D = [[0] * n for _ in range(n)]; k = 0
for i in range(n):
    for j in range(i + 1, n):
        D[i][j] = int(s[k]); D[j][i] = 1 - D[i][j]; k += 1
R = [row[:] for row in D]
R[u][v], R[v][u] = D[v][u], D[u][v]


def minus(A, w):
    keep = [x for x in range(len(A)) if x != w]
    return [[A[i][j] for j in keep] for i in keep]


raw = subprocess.run(['zstd', '-dc', arc], capture_output=True, check=True).stdout
wit = {}
for m in tarfile.open(fileobj=io.BytesIO(raw)):
    mm = re.search(r'd000mv09_r01_02_mv(\d\d)\.(witness|log)$', m.name)
    if m.isfile() and mm:
        txt = tarfile.open(fileobj=io.BytesIO(raw)).extractfile(m.name).read().decode()
        orders = [list(map(int, x.split())) for x in re.findall(r'^\s*voter \d+:\s*([\d ]+)$', txt, re.M)]
        wit[int(mm.group(1))] = orders


def check(A, orders):
    m = len(A)
    if len(orders) != 5 or any(sorted(o) != list(range(m)) for o in orders):
        return 'not five orders of the vertices'
    pos = [{x: r for r, x in enumerate(o)} for o in orders]
    for i in range(m):
        for j in range(m):
            if A[i][j] and sum(p[i] < p[j] for p in pos) < 3:
                return f'arc {i}->{j} carried by fewer than 3 orders'
    return None


bad, endpoints, witnessed = [], 0, 0
for w in range(n):
    if w in (u, v):
        if minus(R, w) == minus(D, w): endpoints += 1
        else: bad.append(f'{w}: R - w differs from (Delta_1 - 10) - w')
        continue
    if w not in wit:
        bad.append(f'{w}: no witness'); continue
    tgt = (w + 1) % n if shift else w
    if tgt in (u, v): tgt = (tgt + 1) % n
    err = check(minus(R, tgt), wit[w])
    if err: bad.append(f'{w}: {err}')
    else: witnessed += 1
print(f'R = Delta_1 - 10 with {u}-{v} reversed: {endpoints} deletions are deletions of Delta_1 - 10, '
      f'{witnessed} have a verified 5-voter witness, of {n}')
if bad:
    print(f'FAIL: {len(bad)} problem(s): ' + '; '.join(bad[:4])); sys.exit(1)
print(f'VERTEX-CRITICAL: all {n} one-vertex deletions are 5-inducible')
