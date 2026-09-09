#!/usr/bin/env python3
"""Independent check that a kinduce WITNESS realizes Paley(q) minus vertices.

Shares no code with the search or with kinduce's internal verifier: it rebuilds
Paley(q) from its quadratic residues, deletes the given vertices, reads the
voter orders out of the log, and recomputes every pairwise majority.

  python3 verify_paley_minus_witness.py <log> --q 19 --drop 0 --margin exact
  python3 verify_paley_minus_witness.py <log> --q 23 --drop 0 --margin majority

Exit 0 iff the witness is genuine and consistent with the stated margin.
"""
import argparse, re, sys

ap = argparse.ArgumentParser()
ap.add_argument('log')
ap.add_argument('--q', type=int, required=True)
ap.add_argument('--drop', type=int, nargs='+', default=[0])
ap.add_argument('--margin', choices=('exact', 'majority'), required=True)
a = ap.parse_args()

orders = [list(map(int, m.group(1).split()))
          for m in re.finditer(r'voter \d+:\s*([\d ]+)', open(a.log).read())]
if not orders:
    sys.exit("no 'voter i: ...' lines found in the log")
k, n = len(orders), len(orders[0])
print(f"read {k} voter orders over {n} vertices from {a.log}")

for i, o in enumerate(orders):
    if sorted(o) != list(range(n)):
        sys.exit(f"voter {i} is not a permutation of 0..{n-1}")
print(f"all {k} orders are genuine permutations of 0..{n-1}")

# target: Paley(q) minus the dropped vertices, survivors relabelled in order
QR = {(x * x) % a.q for x in range(1, a.q)}
vs = [x for x in range(a.q) if x not in set(a.drop)]
if len(vs) != n:
    sys.exit(f"q={a.q} minus {a.drop} has {len(vs)} vertices, log has {n}")
beats = [[(vs[b] - vs[j]) % a.q in QR for b in range(n)] for j in range(n)]

pos = [{v: r for r, v in enumerate(o)} for o in orders]   # rank 0 = top choice
need = (k + 1) // 2
bad, sup = 0, {}
for x in range(n):
    for y in range(x + 1, n):
        s = sum(1 for p in pos if p[x] < p[y])            # voters ranking x above y
        if (s >= need) != beats[x][y]:
            bad += 1
        w = s if s >= need else k - s
        sup[w] = sup.get(w, 0) + 1
print(f"pairs checked: {n*(n-1)//2}   MISMATCHES: {bad}")
print("winner-support histogram:", dict(sorted(sup.items())))

ok = bad == 0
if a.margin == 'exact':
    tight = set(sup) == {need}
    print(f"margin-1 (every arc exactly {need}-{k-need}): {'yes' if tight else 'NO'}")
    ok &= tight
else:
    print(f"majority (every arc >= {need} of {k}): {'yes' if min(sup) >= need else 'NO'}")
    ok &= min(sup) >= need

print()
print(f"*** GENUINE: Paley({a.q}) minus {a.drop} IS {k}-inducible"
      f"{' (margin-1)' if a.margin == 'exact' else ''} ***" if ok else "*** WITNESS IS WRONG ***")
sys.exit(0 if ok else 1)
