#!/usr/bin/env python3
# =====================================================================
# SUPERSEDED -- DO NOT USE FOR A CERTIFICATION.  Kept only as a record.
#
# This runner cubes at depth 5 and DEEPENS to depth 7 using deepen.py's
# mrv()/children().  That places an UNCERTIFIED PYTHON ENUMERATION in the
# trust chain: the proof is valid only if children() never misses an
# insertion tuple, and cover_deep.py -- which would certify exactly that --
# is marked "BROKEN, NEVER VALIDATED, DO NOT TRUST".
#
# Use certify_d6.py instead: it cubes directly at |B|=6, so the cubes are
# base states whose coverage is discharged by the validated Level-1
# mechanism (cover_check.py), and deepen.py is not imported at all.
# =====================================================================
"""Fully certify: Paley(19) is NOT margin-1 5-inducible.

Check-and-discard with a hash-stamped verification log.  Every leaf proof is
generated, INDEPENDENTLY verified, hashed, and deleted; nothing accumulates, so
peak storage is one proof per worker (~4 MB).

PIPELINE (per leaf)
  cadical --lrat --checkproof=0   solve + emit LRAT     ~0.277 s
  lrat-trim <cnf> <lrat>          INDEPENDENT check     ~0.018 s
  sha256 of the CNF and the proof, appended to the log, then proof deleted

`--checkproof=0` deliberately disables cadical's SELF-check: the whole point is
that the checker is a different program by a different author.  lrat-trim
signals success with `s VERIFIED` on stdout and exit code 20 (SAT-solver
convention) -- NOT exit 0, which is a trap worth remembering.

WHY LRAT AND NOT DRAT.  Measured on real leaves here:
    glucose solve+DRAT 0.525 s  +  drat-trim 0.518 s  = 1.043 s/leaf
    cadical solve+LRAT 0.277 s  +  lrat-trim 0.018 s  = 0.295 s/leaf
LRAT carries explicit clause hints so the checker does no backward RAT search:
29x faster checking, and 3.5x cheaper end to end (188 -> 53 core-h).

CONFIGURATION -- the break is the GLOBAL optimum, verified exhaustively over all
12 five-vertex base classes x 100 (arc, non-arc) pairs by base_survivors.py:
    base {0,1,2,3,5} (regular class, mask 217), 2200 base states
    break: arc (0,5) + non-arc (2,1)  ->  781 of 2200 survive (35.5%)
Note estimate.py's default reps=(1,2) gives 1077 live cubes, 38% above optimal,
and a bigger tree too (1866 vs 830 leaves/cube) -- do not use it for sizing.

WHAT THIS DOES AND DOES NOT ESTABLISH.  The machine part is complete: every leaf
is independently verified, and the cube COVERAGE is separately certified in
certs/cover_p19_exact.{drat,lrat}.  Two lemmas remain HUMAN-checked and are not
part of any certificate:
  (L1) the arc-orbit anchoring is WLOG -- Aut(Paley(q)) is transitive on arcs
       and on non-arcs, so some voter's (top,second) may be assumed to equal a
       fixed arc or a fixed non-arc;
  (L2) the voters may be lex-ordered WLOG.
Both are written up in RESEARCH_LOG.md.  The DFS engine inherits exactly the
same two lemmas and shares no implementation, which is what makes agreement
between the two routes meaningful rather than circular.

  usage: certify_p19_m1.py [outdir] [--workers N] [--depth D]
"""
import argparse, hashlib, json, os, random, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from cube_sat import paley, build
from cubes import enumerate_cubes
from deepen import mrv, cube_of

CAD = os.path.expanduser("~/Downloads/DownloadedSoftware/cadical/build/cadical")
LT = os.path.expanduser("~/Downloads/DownloadedSoftware/lrat-trim/lrat-trim")
Q, K, EXACT = 19, 5, True
BASE = [0, 1, 2, 3, 5]
ARC, NON = (0, 5), (2, 1)


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for blk in iter(lambda: f.read(1 << 20), b''):
            h.update(blk)
    return h.hexdigest()


def do_cube(args):
    ci, cube, outdir, depth = args
    done = os.path.join(outdir, 'done', f'c{ci:05d}.json')
    if os.path.exists(done):
        return ci, None
    adj = paley(Q)
    cls, arcs, pair, X, nv = build(adj, Q, K, EXACT)
    t0 = time.time()
    node = (list(BASE), [[BASE[s] for s in pi] for pi in cube])
    fr = [node]
    while len(fr[0][0]) < depth:
        nxt = []
        for nd in fr:
            r = mrv(adj, nd[0], nd[1], K, EXACT, Q)
            if r and r[1]:
                nxt.extend(r[1])
        if not nxt:
            fr = []
            break
        fr = nxt
    t_exp = time.time() - t0

    cnf_p = os.path.join(outdir, 'work', f'c{ci:05d}.cnf')
    lrt_p = os.path.join(outdir, 'work', f'c{ci:05d}.lrat')
    # TWO rolling hashes, one of each kind (see VERDICT text):
    #   h      = artifacts (CNF + LRAT bytes)  -> reproducible on a FIXED binary
    #   h_cnf  = CNF only                      -> reproducible by ANYONE, any setup
    # Neither hashes wall-clock: timings live in the log line only.
    recs, h, h_cnf = [], hashlib.sha256(), hashlib.sha256()
    for li, nd in enumerate(fr):
        units = cube_of(nd, adj, pair, X, K)
        full = cls + [[u] for u in units]
        with open(cnf_p, 'w') as f:
            f.write(f"p cnf {nv} {len(full)}\n")
            for cl in full:
                f.write(' '.join(map(str, cl)) + " 0\n")
        t = time.time()
        p = subprocess.run([CAD, '-q', '--lrat=true', '--checkproof=0', cnf_p, lrt_p],
                           capture_output=True, text=True)
        t_solve = time.time() - t
        if 'UNSATISFIABLE' not in p.stdout:
            # SAT here would be a WITNESS: Paley(19) margin-1 5-inducible.
            # Keep everything and stop the whole run.
            os.replace(cnf_p, os.path.join(outdir, f'SAT_c{ci:05d}_l{li}.cnf'))
            open(os.path.join(outdir, 'STOP_SAT'), 'w').write(f"cube {ci} leaf {li}\n")
            return ci, {'error': 'LEAF SAT -- witness, investigate', 'cube': ci, 'leaf': li}
        cnf_h, lrt_h = sha256_file(cnf_p), sha256_file(lrt_p)
        t = time.time()
        v = subprocess.run([LT, cnf_p, lrt_p], capture_output=True, text=True)
        t_chk = time.time() - t
        if 's VERIFIED' not in v.stdout:            # exit code is 20, not 0
            open(os.path.join(outdir, 'STOP_UNVERIFIED'), 'w').write(
                f"cube {ci} leaf {li}\n{v.stdout[-2000:]}\n")
            return ci, {'error': 'CHECK FAILED', 'cube': ci, 'leaf': li}
        # timings stay in the log line, NEVER in the hash (see certify_d6.py)
        rec = f"{li} {cnf_h} {lrt_h} VERIFIED {t_solve:.3f} {t_chk:.3f}"
        h.update((f"{li} {cnf_h} {lrt_h} VERIFIED\n").encode())
        h_cnf.update((f"{li} {cnf_h}\n").encode())
        recs.append(rec)
        os.remove(lrt_p)                            # discard: nothing accumulates

    with open(os.path.join(outdir, 'log', f'c{ci:05d}.log'), 'w') as f:
        f.write(f"# cube {ci} base={BASE} arc={ARC} non={NON} depth={depth} "
                f"leaves={len(fr)} expand={t_exp:.1f}s\n")
        f.write("# leaf sha256(cnf) sha256(lrat) verdict solve_s check_s\n")
        f.write('\n'.join(recs) + ('\n' if recs else ''))
    summary = {'cube': ci, 'leaves': len(fr), 'expand_s': round(t_exp, 1),
               'cube_hash': h.hexdigest(),
               'cube_hash_cnf': h_cnf.hexdigest(),
               'solve_s': round(sum(float(r.split()[4]) for r in recs), 1),
               'check_s': round(sum(float(r.split()[5]) for r in recs), 1)}
    with open(done, 'w') as f:
        json.dump(summary, f)
    if os.path.exists(cnf_p):
        os.remove(cnf_p)
    return ci, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('outdir', nargs='?', default='/tmp/p19cert')
    ap.add_argument('--workers', type=int, default=10)
    ap.add_argument('--depth', type=int, default=7)
    ap.add_argument('--limit', type=int, default=0,
                    help='smoke test: only this many cubes (0 = all 781)')
    a = ap.parse_args()
    for d in ('done', 'log', 'work'):
        os.makedirs(os.path.join(a.outdir, d), exist_ok=True)

    adj = paley(Q)
    cubes, bm = enumerate_cubes(adj, BASE, K, EXACT, 'mask')
    live = [c for c in cubes
            if any((BASE[pi[0]], BASE[pi[1]]) in (ARC, NON) for pi in c)]
    print(f"### certify Paley(19) margin-1  {time.strftime('%F %H:%M:%S')}")
    print(f"  base={BASE} arc={ARC} non={NON}: {len(cubes)} cubes -> {len(live)} live")
    if len(live) != 781:
        print(f"  *** expected 781 live cubes, got {len(live)} -- ABORTING ***")
        sys.exit(1)
    print(f"  depth={a.depth}, {a.workers} workers, check-and-discard")

    t0 = time.time()
    if a.limit:
        live = live[:a.limit]
        print(f'  LIMIT {a.limit} cubes -- SMOKE TEST, not a full certification')
    tasks = [(i, c, a.outdir, a.depth) for i, c in enumerate(live)]
    nl = ns = nc = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for ci, s in ex.map(do_cube, tasks):
            if s is None:
                continue
            if 'error' in s:
                print(f"  *** {s['error']} at cube {s['cube']} leaf {s['leaf']} -- STOPPING ***")
                sys.exit(2)
            nl += s['leaves']; ns += s['solve_s']; nc += s['check_s']
            if (ci + 1) % 50 == 0:
                el = time.time() - t0
                print(f"  {ci+1}/{len(live)} cubes, {nl:,} leaves, {el/60:.0f} min elapsed, "
                      f"ETA {el/(ci+1)*(len(live)-ci-1)/60:.0f} min", flush=True)

    if a.limit:
        print(f"\n### SMOKE TEST COMPLETE -- {a.limit} of 781 cubes, {nl:,} leaves all VERIFIED")
        print(f"  {ns/3600:.2f} core-h solve, {nc/3600:.2f} core-h check, "
              f"{(ns+nc)/max(nl,1):.3f} s/leaf")
        print(f"  projected full run: {781*(ns+nc)/max(a.limit,1)/3600:.0f} core-h")
        print("  NO VERDICT written: a partial run proves nothing.")
        return

    # root hash over the per-cube hashes, in cube order
    root = hashlib.sha256(); root_cnf = hashlib.sha256()
    for i in range(len(live)):
        with open(os.path.join(a.outdir, 'done', f'c{i:05d}.json')) as f:
            d = json.load(f)
        root.update(d['cube_hash'].encode())
        root_cnf.update(d['cube_hash_cnf'].encode())
    el = time.time() - t0
    with open(os.path.join(a.outdir, 'VERDICT.txt'), 'w') as f:
        f.write(f"""Paley(19) is NOT margin-1 5-inducible -- machine-verified.

date            {time.strftime('%F %H:%M:%S')}
base            {BASE} (regular class, 2200 base states)
break           arc {ARC} + non-arc {NON} -> {len(live)} live cubes (global optimum)
cube depth      {a.depth}
leaves          {nl}
all leaves      UNSAT, INDEPENDENTLY VERIFIED by lrat-trim
solver          cadical 2.0.0, --lrat=true --checkproof=0 (self-check disabled)
checker         lrat-trim (Biere), separate program and author
solve time      {ns/3600:.1f} core-h
check time      {nc/3600:.1f} core-h
wall            {el/3600:.2f} h on {a.workers} workers
ROOT (CNF)      {root_cnf.hexdigest()}
ROOT (proofs)   {root.hexdigest()}

TWO ROOTS, ONE OF EACH KIND.  Neither hashes wall-clock time.
  ROOT (CNF) commits to the CNFs only -- it says WHICH problems were solved.
  Anyone who regenerates the cube set must obtain it, on any machine, with any
  implementation.  This is the setup-INDEPENDENT record.
  ROOT (proofs) additionally commits to the LRAT bytes.  cadical is
  deterministic on a fixed binary, so this reproduces under the SAME setup;
  a different version or architecture may emit a different, equally valid
  proof, so a mismatch there is not an error.
  (Before 2026-09-05 the proofs root also hashed timings and so could not be
  reproduced at all; roots from earlier runs are not comparable with these.)

Proofs were verified and DISCARDED; per-leaf sha256 of every CNF and every LRAT
proof is in log/c*.log, each cube's rolling hash in done/c*.json, and the root
hash above commits to all of them in cube order.

Cube coverage is certified separately: certs/cover_p19_exact.{{drat,lrat}}.

Remaining HUMAN lemmas, not covered by any certificate:
  (L1) arc-orbit anchoring is WLOG (Aut is transitive on arcs and on non-arcs)
  (L2) voters may be lex-ordered WLOG
Both are proved in RESEARCH_LOG.md, and the independent DFS engine inherits the
same two lemmas while sharing no implementation.
""")
    print(f"\n### done {time.strftime('%F %H:%M:%S')}  {el/3600:.2f} h")
    print(f"  leaves {nl:,}  solve {ns/3600:.1f} core-h  check {nc/3600:.1f} core-h")
    print(f"  ROOT (CNF)    {root_cnf.hexdigest()}")
    print(f"  ROOT (proofs) {root.hexdigest()}")
    print(f"  VERDICT: Paley(19) is NOT margin-1 5-inducible (see {a.outdir}/VERDICT.txt)")


if __name__ == '__main__':
    main()
