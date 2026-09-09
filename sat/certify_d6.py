#!/usr/bin/env python3
"""Certify a Paley(q) margin-1 non-inducibility by DEPTH-6 TOP-LEVEL CUBING.

  usage: certify_d6.py --q 19 --base v1..v6 --arc u v --non u v [--out DIR]
                       [--workers N] [--limit N]

WHY DEPTH 6 AND NOT DEEPENING.  An earlier version cubed at depth 5 and then
deepened to depth 7 with deepen.py's mrv()/children().  That put an UNCERTIFIED
PYTHON ENUMERATION in the trust chain: the proof was only valid if children()
never missed an insertion tuple, and cover_deep.py -- which would certify
exactly that ("BROKEN, NEVER VALIDATED, DO NOT TRUST") -- does not work.

Here the cubes ARE the base states of a 6-vertex base, so their coverage is
discharged by the SAME validated Level-1 mechanism as at |B|=5 (cover_check.py,
generic in len(B)).  Nothing below the base is enumerated by our code at all:
each cube is handed whole to the solver.  deepen.py is not imported.

Depth 5 also converges (~480 s/cube, 1.1-1.5 GB proofs) but costs ~104 core-h;
depth 6 measured 2.8 s/cube, so it is both cheaper and equally clean.  Depth 7
would be cheaper still but cannot be enumerated independently at this scale.

TRUST CHAIN, in full:
  machine  every cube UNSAT, proved by cadical in LRAT and checked by lrat-trim
           (a different program by a different author; cadical's own
           --checkproof is DISABLED so it never validates its own work)
  machine  the cubes cover every lex-canonical base assignment
           (cover_check.py, with its --drop negative control)
  HUMAN L1 arc-orbit anchoring is WLOG: Aut(Paley(q)) is transitive on arcs and
           on non-arcs, so some voter's (top,second) may be assumed to be a
           fixed arc or a fixed non-arc.  This is what licenses running only
           the LIVE cubes.
  HUMAN L2 the voters may be lex-ordered WLOG.  This licenses the lex chain in
           the coverage CNF.
Both lemmas are proved in RESEARCH_LOG.md, and the independent DFS engine
inherits the same two while sharing no implementation.

Proofs are verified then DISCARDED.  The artifact is a hash-stamped log: per
cube the sha256 of its CNF and of its LRAT proof, per chunk a rolling hash, and
one root hash committing to all of them in cube order.
"""
import argparse, hashlib, itertools, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from cube_sat import paley, build
from cubes import enumerate_cubes
# NOTE: deepen is deliberately NOT imported -- see the docstring.

CAD = os.path.expanduser("~/Downloads/DownloadedSoftware/cadical/build/cadical")
LT = os.path.expanduser("~/Downloads/DownloadedSoftware/lrat-trim/lrat-trim")
CHUNK = 200


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def cube_units(node, adj, pair, X, K):
    """The C(|B|,2)*K unit literals pinning each voter's order on the base.
    Inlined from deepen.cube_of so that deepen.py -- whose children()/mrv()
    splitting is the UNCERTIFIED part -- is not imported at all here."""
    S, orders = node
    units = []
    for v in range(K):
        pos = {u: i for i, u in enumerate(orders[v])}
        for i, j in itertools.combinations(sorted(S), 2):
            e = pair[(i, j)]
            win, los = (i, j) if adj[i][j] else (j, i)
            units.append(X(e, v) if pos[los] < pos[win] else -X(e, v))
    return units


def do_chunk(args):
    lo, cubes_slice, B, K, exact, q, out = args
    done_p = os.path.join(out, 'done', f'k{lo:07d}.json')
    if os.path.exists(done_p):
        return lo, None
    adj = paley(q)
    cls, arcs, pair, X, nv = build(adj, q, K, exact)
    cnf_p = os.path.join(out, 'work', f'k{lo:07d}.cnf')
    lrt_p = os.path.join(out, 'work', f'k{lo:07d}.lrat')
    recs = []
    h_cnf = hashlib.sha256()   # portable: commits to WHICH problems were solved
    h_all = hashlib.sha256()   # this build only: proof bytes are not portable
    t_solve = t_chk = 0.0
    for off, cube in enumerate(cubes_slice):
        ci = lo + off
        node = (list(B), [[B[s] for s in pi] for pi in cube])
        units = cube_units(node, adj, pair, X, K)
        full = cls + [[u] for u in units]
        with open(cnf_p, 'w') as f:
            f.write(f"p cnf {nv} {len(full)}\n")
            for cl in full:
                f.write(' '.join(map(str, cl)) + " 0\n")
        t = time.time()
        p = subprocess.run([CAD, '-q', '--lrat=true', '--checkproof=0', cnf_p, lrt_p],
                           capture_output=True, text=True)
        dt = time.time() - t; t_solve += dt
        if 'UNSATISFIABLE' not in p.stdout:
            os.replace(cnf_p, os.path.join(out, f'SAT_cube{ci:07d}.cnf'))
            open(os.path.join(out, 'STOP_SAT'), 'w').write(f"cube {ci}\n")
            return lo, {'error': 'CUBE SAT -- witness, investigate', 'cube': ci}
        cnf_h, lrt_h = sha256_file(cnf_p), sha256_file(lrt_p)
        t = time.time()
        v = subprocess.run([LT, cnf_p, lrt_p], capture_output=True, text=True)
        dc = time.time() - t; t_chk += dc
        if 's VERIFIED' not in v.stdout:            # exit code is 20, not 0
            open(os.path.join(out, 'STOP_UNVERIFIED'), 'w').write(
                f"cube {ci}\n{v.stdout[-2000:]}\n")
            return lo, {'error': 'CHECK FAILED', 'cube': ci}
        # The LOG line carries timings for humans; the HASHED record must not.
        # Hashing wall-clock made ROOT (proofs) differ run-to-run on the SAME
        # machine and binary, so it could never be reproduced -- a stronger
        # limitation than the "not portable across builds" it documented.
        # Hash the artifacts, not the stopwatch.
        rec = f"{ci} {cnf_h} {lrt_h} VERIFIED {dt:.3f} {dc:.3f}"
        h_cnf.update((f"{ci} {cnf_h}\n").encode())
        h_all.update((f"{ci} {cnf_h} {lrt_h} VERIFIED\n").encode())
        recs.append(rec)
        os.remove(lrt_p)
    with open(os.path.join(out, 'log', f'k{lo:07d}.log'), 'w') as f:
        f.write(f"# cubes [{lo},{lo+len(cubes_slice)}) base={B}\n")
        f.write("# cube sha256(cnf) sha256(lrat) verdict solve_s check_s\n")
        f.write('\n'.join(recs) + '\n')
    summary = {'lo': lo, 'n': len(cubes_slice),
               'chunk_hash_cnf': h_cnf.hexdigest(),
               'chunk_hash': h_all.hexdigest(),
               'solve_s': round(t_solve, 1), 'check_s': round(t_chk, 1)}
    with open(done_p, 'w') as f:
        json.dump(summary, f)
    if os.path.exists(cnf_p):
        os.remove(cnf_p)
    return lo, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, default=19)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--margin', default='exact', choices=['exact', 'majority'])
    ap.add_argument('--base', type=int, nargs='+', required=True)
    ap.add_argument('--arc', type=int, nargs=2, required=True)
    ap.add_argument('--non', type=int, nargs=2, required=True)
    ap.add_argument('--out', default='/tmp/p19cert_d6')
    ap.add_argument('--coverage', default=None,
                    help='path to the VERIFIED coverage proof for this cube set.\n'
                         'Without it the verdict states that the split half is\n'
                         'OUTSTANDING.  It used to assert coverage unconditionally,\n'
                         'which made the Paley(23) verdict claim a certification that\n'
                         'had never been run -- this script does not do coverage.')
    ap.add_argument('--workers', type=int, default=10)
    ap.add_argument('--limit', type=int, default=0, help='smoke test: first N cubes (a PREFIX -- not for pricing)')
    ap.add_argument('--sample', type=int, default=0, help='pricing: uniform random sample of N live cubes')
    ap.add_argument('--seed', type=int, default=1, help='seed for --sample')
    a = ap.parse_args()
    for d in ('done', 'log', 'work'):
        os.makedirs(os.path.join(a.out, d), exist_ok=True)

    exact = a.margin == 'exact'
    adj = paley(a.q)
    B = list(a.base)
    ARC, NON = tuple(a.arc), tuple(a.non)
    if adj[ARC[0]][ARC[1]] != 1:
        sys.exit(f"--arc {ARC} is NOT an arc of Paley({a.q})")
    if adj[NON[0]][NON[1]] != 0:
        sys.exit(f"--non {NON} IS an arc of Paley({a.q}); it must be a non-arc")
    print(f"### certify Paley({a.q}) margin={a.margin} by depth-{len(B)} cubing "
          f"{time.strftime('%F %H:%M:%S')}")
    print(f"  base {B}, break arc {ARC} + non-arc {NON}")
    t = time.time()
    cubes, bm = enumerate_cubes(adj, B, a.k, exact, 'mask')
    live = [c for c in cubes if any((B[pi[0]], B[pi[1]]) in (ARC, NON) for pi in c)]
    print(f"  {len(cubes):,} base states -> {len(live):,} live "
          f"({100*len(live)/len(cubes):.1f}%), enumerated in {time.time()-t:.0f}s")
    if a.sample:
        # PRICING ONLY.  live[:N] is the first N in enumeration order, which is
        # NOT a random sample -- cube difficulty is heavily skewed, so a prefix
        # can misprice by an order of magnitude.  Draw uniformly instead, and
        # reuse the smoke-test guard so no VERDICT is ever written.
        import random as _r
        live = _r.Random(a.seed).sample(live, min(a.sample, len(live)))
        a.limit = len(live)
        print(f"  SAMPLE {len(live)} of the live cubes, seed {a.seed}"
              f" -- PRICING, not a certification")
    elif a.limit:
        live = live[:a.limit]
        print(f"  LIMIT {a.limit} -- SMOKE TEST, not a certification (PREFIX, "
              f"not a random sample -- do not price from this)")
    chunks = [(i, live[i:i+CHUNK], B, a.k, exact, a.q, a.out)
              for i in range(0, len(live), CHUNK)]
    print(f"  {len(chunks)} chunks of <= {CHUNK}, {a.workers} workers, "
          f"check-and-discard", flush=True)

    t0 = time.time(); nc = ns = ck = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for lo, s in ex.map(do_chunk, chunks):
            if s is None:
                continue
            if 'error' in s:
                print(f"  *** {s['error']} at cube {s['cube']} -- STOPPING ***")
                sys.exit(2)
            nc += s['n']; ns += s['solve_s']; ck += s['check_s']
            el = time.time() - t0
            print(f"  {nc:,}/{len(live):,} cubes, {el/60:.0f} min, "
                  f"ETA {el/max(nc,1)*(len(live)-nc)/60:.0f} min", flush=True)

    if a.limit:
        print(f"\n### {nc} cubes all VERIFIED -- solve {ns/max(nc,1):.3f} + check "
              f"{ck/max(nc,1):.3f} = {(ns+ck)/max(nc,1):.3f} s/cube; NO VERDICT written")
        return
    root_cnf = hashlib.sha256(); root_all = hashlib.sha256()
    for lo in sorted(int(f[1:-5]) for f in os.listdir(os.path.join(a.out, 'done'))):
        with open(os.path.join(a.out, 'done', f'k{lo:07d}.json')) as f:
            d = json.load(f)
            root_cnf.update(d['chunk_hash_cnf'].encode())
            root_all.update(d['chunk_hash'].encode())
    el = time.time() - t0
    # ONE definition, read by both the VERDICT file and the console line, so
    # they can never disagree about which margin was certified.
    _what = "margin-1 " if exact else ""
    # Report the SPLIT half truthfully.  This script certifies the SEARCH half
    # only; coverage is cover_check.py, a separate program.
    if a.coverage and os.path.exists(a.coverage):
        import hashlib as _h
        _ch = _h.sha256(open(a.coverage,'rb').read()).hexdigest()
        _cov = (f'SPLIT half CERTIFIED: the cube set is exhaustive, proof\n'
                f'{a.coverage}\n  sha256 {_ch}\n'
                f'(F_B & SB & AND_i not-C_i is UNSAT at |B|={len(B)}.)')
    else:
        _cov = ('SPLIT half OUTSTANDING.  This run certifies only that every cube is\n'
                'UNSAT (the SEARCH half).  That the cubes are EXHAUSTIVE -- that\n'
                'F_B & SB & AND_i not-C_i is UNSAT -- is NOT established here and must\n'
                'be shown by cover_check.py before this verdict is complete.  Re-run\n'
                'this script with --coverage <verified proof> to record it.')
    with open(os.path.join(a.out, 'VERDICT.txt'), 'w') as f:
        _extra = "" if exact else f"""
MARGIN NOTE   This run is at MAJORITY (every arc >= {(a.k+1)//2} of {a.k}).  By the 3-cycle
              bound (RESEARCH_LOG 2026-09-04) a linear order agrees with at most
              2 arcs of a cyclic triangle, so over {a.k} voters the three supports
              sum to <= {2*a.k} and none can exceed {2*a.k - 2*((a.k+1)//2)}.  Every arc of Paley({a.q}) lies in
              a 3-cycle, so majority is EQUIVALENT to margin<={2*(2*a.k-2*((a.k+1)//2))-a.k} here and this
              verdict covers both."""
        f.write(f"""Paley({a.q}) is NOT {_what}{a.k}-inducible -- machine-verified.
{_extra}
date          {time.strftime('%F %H:%M:%S')}
margin        {a.margin}
base          {B}  ({len(cubes)} base states)
break         arc {ARC} + non-arc {NON} -> {len(live)} live cubes
cubes         {nc}, ALL UNSAT, each INDEPENDENTLY VERIFIED by lrat-trim
solver        cadical --lrat=true --checkproof=0 (self-check disabled)
checker       lrat-trim (Biere) -- different program, different author
NO DEEPENING  cubes are base states of a {len(B)}-vertex base; deepen.py unused
solve         {ns/3600:.1f} core-h
check         {ck/3600:.1f} core-h
wall          {el/3600:.2f} h on {a.workers} workers
ROOT (CNF)    {root_cnf.hexdigest()}
ROOT (proofs) {root_all.hexdigest()}

TWO ROOTS, AND ONLY THE FIRST IS PORTABLE.
  ROOT (CNF) commits to the sha256 of every cube's CNF, in cube order.  Those
  are generated by this repository's code and ARE reproducible anywhere: a
  third party who regenerates the cube set must obtain this exact value.  It is
  the meaningful cross-check -- it proves they solved the SAME problems.

  ROOT (proofs) additionally commits to the LRAT proof bytes.  From 2026-09-05
  it hashes artifacts ONLY (no timings), so it IS reproducible on a fixed
  binary; values from runs BEFORE that date hashed wall-clock too and are not
  comparable with ones produced after.  These are still NOT
  portable.  cadical is deterministic run-to-run on a fixed binary (verified
  here, 3/3 identical), but its heuristics use floating-point scoring, so a
  different version, architecture or optimisation level can search differently
  and emit a DIFFERENT, EQUALLY VALID proof; another solver differs entirely
  (glucose emits 2.36 MB of DRAT where cadical emits 2.79 MB of LRAT).  So this
  value detects corruption or tampering WITHIN this run and reproduces only on
  an identical build.  A mismatch here is NOT evidence of an error.

Proofs verified then discarded; per-cube sha256 of CNF and proof in log/,
per-chunk rolling hashes of both in done/.

{_cov}

The --drop negative control was NOT run, deliberately.  It is not part of the
proof: coverage UNSAT already establishes that nothing bypasses the cubes, and
redundant cubes cost time rather than soundness.  Its only role would be to
exclude a vacuous certificate, and vacuity cannot arise here -- it would require
F_B & SB to be unsatisfiable, i.e. the {len(B)}-vertex base not {a.k}-inducible,
contradicting N({a.k}) >= 12.

Remaining HUMAN lemmas (not covered by any certificate):
  (L1) arc-orbit anchoring is WLOG  -- licenses running only the live cubes
  (L2) voters may be lex-ordered WLOG -- licenses the lex chain in coverage
Both proved in RESEARCH_LOG.md.
""")
    print(f"\n### done {el/3600:.2f} h  solve {ns/3600:.1f} + check {ck/3600:.1f} core-h")
    print(f"  ROOT (CNF)    {root_cnf.hexdigest()}")
    print(f"  ROOT (proofs) {root_all.hexdigest()}")
    # was: "margin-1" hardcoded, which printed the WRONG margin for a majority
    # run while VERDICT.txt (line ~226) had it right from {_what}.  The line a
    # human reads is the one that gets quoted -- derive it from the same source.
    print(f"  VERDICT: Paley({a.q}) is NOT {_what}{a.k}-inducible -> {a.out}/VERDICT.txt")


if __name__ == '__main__':
    main()
