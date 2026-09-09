#!/usr/bin/env python3
"""Time the full leaf pipeline: cube -> DIMACS -> solve+DRAT -> drat-trim.

The cube goes in as UNIT CLAUSES (not assumptions) so the proof is a standalone
refutation of F & C_i, which is what drat-trim needs.
"""
import sys, os, time, random, subprocess, argparse, itertools
from cube_sat import paley, build
from cubes import enumerate_cubes
from deepen import mrv, cube_of

DRAT = "/Users/lchindelevitch/Downloads/DownloadedSoftware/drat-trim"

ap = argparse.ArgumentParser()
ap.add_argument('--q', type=int, default=19)
ap.add_argument('--margin', default='exact', choices=['majority', 'exact'])
ap.add_argument('--k', type=int, default=5)
ap.add_argument('--base', type=int, nargs='+', default=None)
ap.add_argument('--cube', type=int, default=0)
ap.add_argument('--depth', type=int, default=7)
ap.add_argument('--sample', type=int, default=5)
ap.add_argument('--seed', type=int, default=11)
ap.add_argument('--keep', default='/tmp/leafbench')
a = ap.parse_args()
random.seed(a.seed)
os.makedirs(a.keep, exist_ok=True)
exact = a.margin == 'exact'
adj = paley(a.q)
B = a.base if a.base else ([0, 1, 2, 3, 5] if a.q == 19 else [0, 1, 2, 5, 11])
cls, arcs, pair, X, nv = build(adj, a.q, a.k, exact)
cubes, bm = enumerate_cubes(adj, B, a.k, exact, 'mask')
node = (list(B), [[B[s] for s in pi] for pi in cubes[a.cube]])

frontier = [node]
while len(frontier[0][0]) < a.depth:
    nxt = []
    for nd in frontier:
        r = mrv(adj, nd[0], nd[1], a.k, exact, a.q)
        if r and r[1]:
            nxt.extend(r[1])
    if not nxt:
        print("subtree emptied before target depth"); sys.exit(0)
    frontier = nxt
print(f"q={a.q} margin={a.margin} cube#{a.cube} depth={a.depth} "
      f"leaves_in_subtree={len(frontier)}", flush=True)

import pysat.solvers as S
samp = random.sample(frontier, min(a.sample, len(frontier)))
tot = {}
for idx, nd in enumerate(samp):
    units = cube_of(nd, adj, pair, X, a.k)
    full = cls + [[u] for u in units]
    cnf = f"{a.keep}/leaf{idx}.cnf"
    with open(cnf, 'w') as f:
        f.write(f"p cnf {nv} {len(full)}\n")
        for c in full:
            f.write(' '.join(map(str, c)) + " 0\n")
    row = {}
    for name in ('Cadical195', 'Glucose42'):
        s = getattr(S, name)(bootstrap_with=full, with_proof=(name == 'Glucose42'))
        t = time.time(); r = s.solve(); dt = time.time() - t
        row[name] = (dt, r)
        if name == 'Glucose42':
            pr = s.get_proof() or []
            open(f"{a.keep}/leaf{idx}.drat", 'w').write('\n'.join(pr) + '\n')
            row['proof_lines'] = len(pr)
        s.delete()
    t = time.time()
    p = subprocess.run([f"{DRAT}/drat-trim", cnf, f"{a.keep}/leaf{idx}.drat"],
                       capture_output=True, text=True)
    row['drat_s'] = time.time() - t
    row['verdict'] = 'VERIFIED' if 's VERIFIED' in p.stdout else 'NOT VERIFIED'
    sz = os.path.getsize(f"{a.keep}/leaf{idx}.drat") / 1e6
    print(f"  leaf {idx}: cadical={row['Cadical195'][0]:6.2f}s "
          f"glucose={row['Glucose42'][0]:6.2f}s "
          f"(sat={row['Glucose42'][1]}) proof={row['proof_lines']:7d} lines "
          f"{sz:5.1f} MB  drat-trim={row['drat_s']:6.2f}s  {row['verdict']}", flush=True)
    for kk in ('Cadical195', 'Glucose42'):
        tot[kk] = tot.get(kk, 0) + row[kk][0]
    tot['drat'] = tot.get('drat', 0) + row['drat_s']
    tot['mb'] = tot.get('mb', 0) + sz
n = len(samp)
print(f"  MEAN per leaf: cadical={tot['Cadical195']/n:.2f}s glucose={tot['Glucose42']/n:.2f}s "
      f"drat-trim={tot['drat']/n:.2f}s proof={tot['mb']/n:.1f} MB")
print(f"  => whole subtree ({len(frontier)} leaves): "
      f"solve+check = {len(frontier)*(tot['Glucose42']+tot['drat'])/n/3600:.3f} core-h, "
      f"proofs would be {len(frontier)*tot['mb']/n/1000:.2f} GB if kept")
