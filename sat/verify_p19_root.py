#!/usr/bin/env python3
"""Independently REGENERATE the Paley(19) margin-1 cube CNFs and check they hash
identically to the 2026-09-03 certification.

ROOT (CNF) commits to sha256 of every cube's CNF in cube order and involves NO
solving, so this reproduces it in minutes rather than the 24 core-h the original
solve took.  ROOT (proofs) is deliberately NOT checked: its per-cube record is
    f"{ci} {cnf_h} {lrt_h} VERIFIED {dt:.3f} {dc:.3f}"
i.e. it folds in WALL-CLOCK TIMINGS, so it cannot reproduce even on this same
machine with this same binary.  The LRAT bytes themselves are reproducible on a
fixed cadical (verified 3/3 at the time); the root that commits to them is not.

Compares at three levels so a mismatch is localised, not just detected:
  per-cube CNF sha256   against log/k*.log
  per-chunk chunk_hash_cnf against done/k*.json
  ROOT (CNF)            against the recorded value
"""
import sys, os, json, glob, hashlib, time, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cube_sat import paley, build
from cubes import enumerate_cubes
# do_chunk resolves cube_units to certify_d6's OWN definition, not cube_sat's
spec = importlib.util.spec_from_file_location("c_d6", os.path.join(HERE, "certify_d6.py"))
c_d6 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c_d6)
cube_units = c_d6.cube_units

Q, K, EXACT = 19, 5, True
B = [0, 1, 2, 3, 4, 11]; ARC = (0, 1); NON = (2, 1); CHUNK = 200
ARCH = os.path.join(HERE, 'p19cert_d6')
EXPECT = "0eeb9dd53956fec2c77b752d74b89b12c7d1dddd6dc4047405ecb7907896a78a"

t0 = time.time()
adj = paley(Q)
cubes, bm = enumerate_cubes(adj, B, K, EXACT, 'mask')
live = [c for c in cubes if any((B[pi[0]], B[pi[1]]) in (ARC, NON) for pi in c)]
print(f"  {len(cubes):,} base states -> {len(live):,} live  ({time.time()-t0:.0f}s)")
assert len(live) == 22876, f"live cube count {len(live)} != 22876 -- cube set differs"

cls, arcs, pair, X, nv = build(adj, Q, K, EXACT)
tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), f'p19regen_{os.getpid()}.cnf')
root = hashlib.sha256()
bad_cube = bad_chunk = 0; ncube = 0
for lo in range(0, len(live), CHUNK):
    sl = live[lo:lo + CHUNK]
    h_cnf = hashlib.sha256()
    want = {}
    lg = os.path.join(ARCH, 'log', f'k{lo:07d}.log')
    if os.path.exists(lg):
        for line in open(lg):
            p = line.split()
            if len(p) >= 2 and p[0].isdigit():
                want[int(p[0])] = p[1]
    for off, cube in enumerate(sl):
        ci = lo + off
        node = (list(B), [[B[s] for s in pi] for pi in cube])
        units = cube_units(node, adj, pair, X, K)
        full = cls + [[u] for u in units]
        with open(tmp, 'w') as f:
            f.write(f"p cnf {nv} {len(full)}\n")
            for cl in full:
                f.write(' '.join(map(str, cl)) + " 0\n")
        hh = hashlib.sha256()
        with open(tmp, 'rb') as f:
            for blk in iter(lambda: f.read(1 << 20), b''):
                hh.update(blk)
        cnf_h = hh.hexdigest()
        ncube += 1
        if ci in want and want[ci] != cnf_h:
            bad_cube += 1
            if bad_cube <= 3:
                print(f"    CUBE MISMATCH ci={ci}\n      archived {want[ci]}\n      regen    {cnf_h}")
        h_cnf.update((f"{ci} {cnf_h}\n").encode())
    d = json.load(open(os.path.join(ARCH, 'done', f'k{lo:07d}.json')))
    if d['chunk_hash_cnf'] != h_cnf.hexdigest():
        bad_chunk += 1
        print(f"    CHUNK MISMATCH lo={lo}: archived {d['chunk_hash_cnf'][:16]} regen {h_cnf.hexdigest()[:16]}")
    root.update(h_cnf.hexdigest().encode())
    if (lo // CHUNK) % 20 == 0:
        print(f"    chunk {lo//CHUNK+1}/{(len(live)+CHUNK-1)//CHUNK}  cubes={ncube:,}  "
              f"mismatches={bad_cube}  {time.time()-t0:.0f}s", flush=True)
os.remove(tmp)
got = root.hexdigest()
print()
print(f"  cubes regenerated : {ncube:,}   per-cube mismatches {bad_cube}   per-chunk {bad_chunk}")
print(f"  ROOT (CNF) regen  : {got}")
print(f"  ROOT (CNF) recorded: {EXPECT}")
print("  RESULT:", "IDENTICAL" if got == EXPECT and not bad_cube and not bad_chunk else "*** MISMATCH ***")
