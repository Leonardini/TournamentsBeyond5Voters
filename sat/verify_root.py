#!/usr/bin/env python3
"""Independently regenerate a certification's cube CNFs and check ROOT (CNF).

ROOT (CNF) commits only to WHICH problems were solved, so it needs NO solving:
a full reproducibility check costs minutes rather than the hundreds of core-h
the original run took.  It is also the only root that is reproducible on FOREIGN
hardware -- ROOT (proofs) commits to LRAT bytes, and a different cadical build
may emit a different, equally valid proof.

Everything expected is ASSERTED, not printed for a human to eyeball: a wrong
cube count or a wrong root exits non-zero.

  usage: verify_root.py --q 23 --k 5 --margin majority --base 0 1 2 5 6 3 \
                        --arc 2 6 --non 1 6 --cubes 343896 --root <hex> \
                        [--archive DIR]   (also compares per-cube/per-chunk)
"""
import argparse, hashlib, itertools, json, os, sys, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from cube_sat import paley, build
from cubes import enumerate_cubes
spec = importlib.util.spec_from_file_location("c_d6", os.path.join(HERE, "certify_d6.py"))
c_d6 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c_d6)
cube_units = c_d6.cube_units
CHUNK = c_d6.CHUNK

p = argparse.ArgumentParser()
p.add_argument('--q', type=int, required=True); p.add_argument('--k', type=int, default=5)
p.add_argument('--margin', default='majority', choices=['majority', 'exact'])
p.add_argument('--base', type=int, nargs='+', required=True)
p.add_argument('--arc', type=int, nargs=2, required=True)
p.add_argument('--non', type=int, nargs=2, required=True)
p.add_argument('--cubes', type=int, required=True, help='expected live-cube count (asserted)')
p.add_argument('--root', required=True, help='expected ROOT (CNF) (asserted)')
p.add_argument('--archive', default=None, help='optional: also diff per-cube hashes against log/')
a = p.parse_args()

exact = a.margin == 'exact'; B = a.base; ARC = tuple(a.arc); NON = tuple(a.non)
t0 = time.time(); adj = paley(a.q)
cubes, bm = enumerate_cubes(adj, B, a.k, exact, 'mask')
live = [c for c in cubes if any((B[pi[0]], B[pi[1]]) in (ARC, NON) for pi in c)]
print(f"  {len(cubes):,} base states -> {len(live):,} live  ({time.time()-t0:.0f}s)")
if len(live) != a.cubes:
    sys.exit(f"  FAIL live cubes {len(live)} != expected {a.cubes} -- cube set differs")

cls, arcs, pair, X, nv = build(adj, a.q, a.k, exact)
tmp = os.path.join(os.environ.get('JOBSCRATCH', os.environ.get('TMPDIR', '/tmp')),
                   f'regen_{a.q}_{os.getpid()}.cnf')
root = hashlib.sha256(); bad = badc = 0; n = 0
for lo in range(0, len(live), CHUNK):
    h = hashlib.sha256(); want = {}
    if a.archive:
        lg = os.path.join(a.archive, 'log', f'k{lo:07d}.log')
        if os.path.exists(lg):
            for line in open(lg):
                f = line.split()
                if len(f) >= 2 and f[0].isdigit():
                    want[int(f[0])] = f[1]
    for off, cube in enumerate(live[lo:lo + CHUNK]):
        ci = lo + off
        node = (list(B), [[B[s] for s in pi] for pi in cube])
        units = cube_units(node, adj, pair, X, a.k)
        full = cls + [[u] for u in units]
        with open(tmp, 'w') as f:
            f.write(f"p cnf {nv} {len(full)}\n")
            for c in full:
                f.write(' '.join(map(str, c)) + " 0\n")
        hh = hashlib.sha256()
        with open(tmp, 'rb') as f:
            for blk in iter(lambda: f.read(1 << 20), b''):
                hh.update(blk)
        d = hh.hexdigest(); n += 1
        if ci in want and want[ci] != d:
            bad += 1
        h.update((f"{ci} {d}\n").encode())
    if a.archive:
        jp = os.path.join(a.archive, 'done', f'k{lo:07d}.json')
        if os.path.exists(jp) and json.load(open(jp))['chunk_hash_cnf'] != h.hexdigest():
            badc += 1
    root.update(h.hexdigest().encode())
    if (lo // CHUNK) % 100 == 0:
        print(f"    {n:,}/{len(live):,} cubes  mismatches={bad}  {time.time()-t0:.0f}s", flush=True)
os.remove(tmp)
got = root.hexdigest()
print(f"  regenerated {n:,} cubes   per-cube mismatches {bad}   per-chunk {badc}")
print(f"  ROOT (CNF) regen    {got}")
print(f"  ROOT (CNF) expected {a.root}")
if got != a.root or bad or badc:
    sys.exit("  *** MISMATCH")
print("  PASS -- identical")
