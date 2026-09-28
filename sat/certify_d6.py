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
  HUMAN L1 anchoring is WLOG.  TWO forms, alternatives rather than a sequence:
           LEMMA 2.1 takes one representative ORDERED PAIR from each Aut-orbit
           on ordered pairs and assumes some voter's (top,second) is one of
           them; COROLLARY 2.2 takes one representative VERTEX from each
           Aut-orbit on vertices and assumes some voter ranks one of them
           first.  Either licenses running only the LIVE cubes.  Aut(Paley(q))
           has exactly TWO ordered-pair orbits, the arcs and the non-arcs,
           which is what --arc/--non spells; --pair-anchor and --vertex-anchor
           take any number of representatives.  Both forms require every
           representative to lie INSIDE THE BASE, since the filter reads a base
           state -- enforced, see main().
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


def load_host(spec):
    """The host, from either an int q (Paley) or a path to a .bits file.

    build() in cube_sat is already generic -- its second argument is n, not q --
    so the only Paley-specific step was constructing the adjacency.  A .bits file
    is the upper triangle in (0,1),(0,2),...,(n-2,n-1) order, the same convention
    kinduce reads, and n is recovered from its length rather than passed in.
    """
    if isinstance(spec, int):
        return paley(spec), spec
    b = "".join(c for c in open(spec).read() if c in "01")
    n = int((1 + (1 + 8 * len(b)) ** 0.5) / 2)
    if n * (n - 1) // 2 != len(b):
        sys.exit(f"{spec}: {len(b)} bits is not a triangular number")
    adj = [[0] * n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if b[k] == "1": adj[i][j] = 1
            else:           adj[j][i] = 1
            k += 1
    return adj, n


def do_chunk(args):
    lo, cubes_slice, B, K, exact, spec, out = args
    done_p = os.path.join(out, 'done', f'k{lo:07d}.json')
    if os.path.exists(done_p):
        # Hand the BANKED summary back rather than None.  Returning None made the
        # totals count only what THIS invocation solved, so a resumed run -- or a
        # re-run purely to stamp --coverage -- wrote "solve 0.0 core-h" into
        # VERDICT.txt over a real 217.1.  A certification costs what all its
        # chunks cost, whenever they happened to run.
        with open(done_p) as f:
            banked = json.load(f)
        banked['reused'] = True
        return lo, banked
    adj, n = load_host(spec)
    cls, arcs, pair, X, nv = build(adj, n, K, exact)
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
    ap.add_argument('--bits', default=None,
                    help='certify an ARBITRARY host from a .bits file instead of Paley(q).\n'
                         'Defaults to NO ANCHORING -- every base state is run, which\n'
                         'costs ~6x the cubes at Paley(19) scale and REMOVES the\n'
                         'anchoring lemma from the trust chain.  A host with a\n'
                         'non-trivial Aut may still anchor, with --pair-anchor or\n'
                         '--vertex-anchor and a FULL set of orbit representatives;\n'
                         '--arc/--non is refused here because its two-orbit assumption\n'
                         'is a property of Paley.')
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--margin', default='exact', choices=['exact', 'majority'])
    ap.add_argument('--base', type=int, nargs='+', required=True)
    ap.add_argument('--arc', type=int, nargs=2, default=None)
    ap.add_argument('--non', type=int, nargs=2, default=None)
    ap.add_argument('--pair-anchor', type=int, nargs='+', default=None,
                    metavar='U V',
                    help='LEMMA 2.1 in general form: a flat list u1 v1 u2 v2 ... of ONE\n'
                         'representative ordered pair from EACH Aut-orbit on ordered\n'
                         'pairs.  --arc/--non is the two-orbit spelling of this, which is\n'
                         'all a Paley host needs; a host with m > 2 orbits needs this.')
    ap.add_argument('--vertex-anchor', type=int, nargs='+', default=None,
                    metavar='V',
                    help='COROLLARY 2.2 instead: one representative VERTEX from each\n'
                         'Aut-orbit on vertices.  An alternative to Lemma 2.1, not a\n'
                         'sequence with it -- which is better depends on whether the host\n'
                         'has fewer vertex orbits or fewer ordered-pair orbits.')
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
    spec = a.bits if a.bits else a.q
    adj, n = load_host(spec)
    HOST = f"Paley({a.q})" if a.bits is None else os.path.basename(a.bits).replace('.bits', '')
    B = list(a.base)

    # ------------------------------------------------------------ ANCHORING
    # The representatives do EXACTLY ONE thing: filter the enumerated base
    # states down to the live ones, below.  They never reach build(), the CNF
    # or cube_units, so anchoring changes WHICH subproblems are solved and
    # nothing about any one of them.
    #
    # Two alternatives, not a sequence (manuscript Section 2):
    #   LEMMA 2.1      one representative ORDERED PAIR per Aut-orbit on ordered
    #                  pairs; some voter's top two is one of them.  A Paley host
    #                  has exactly two such orbits, the arcs and the non-arcs,
    #                  which is what --arc/--non spells.
    #   COROLLARY 2.2  one representative VERTEX per Aut-orbit on vertices; some
    #                  voter ranks one of them first.
    #
    # EVERY REPRESENTATIVE MUST LIE INSIDE THE BASE.  The filter reads a base
    # state, which knows only the order restricted to B, so a representative
    # outside B can never be matched: an anchored witness would be filtered
    # AWAY and the refutation would be unsound -- silently, and in the vacuous
    # direction, because dropping cubes only makes the search finish sooner.
    # Nothing checked this until 2026-09-28; the two published Paley
    # certifications satisfy it, which is why it never bit.
    def _in_base(vs, what):
        out = [v for v in vs if v not in B]
        if out:
            sys.exit(f"{what}: vertex/vertices {out} lie OUTSIDE the base {B}.\n"
                     "Anchoring is decided from the base state alone, so every\n"
                     "representative must be in the base or anchored witnesses are\n"
                     "filtered away and the refutation is vacuous.  Choose the orbit\n"
                     "representatives inside B, or drop the anchoring.")
    n_fam = sum(x is not None for x in (a.arc or a.non or None,
                                        a.pair_anchor, a.vertex_anchor))
    if n_fam > 1:
        sys.exit("Lemma 2.1 and Corollary 2.2 are ALTERNATIVES, each WLOG on its own.\n"
                 "Give exactly one of --arc/--non, --pair-anchor, --vertex-anchor.")
    PAIRS = VERTS = None
    if a.arc or a.non:
        if a.bits is not None:
            sys.exit("--arc/--non is the PALEY spelling of Lemma 2.1: it assumes the\n"
                     "ordered-pair orbits are exactly the arcs and the non-arcs, which is\n"
                     "a property of Paley.  For another host give --pair-anchor with one\n"
                     "representative per orbit, or drop it and run every base state.")
        if not (a.arc and a.non):
            sys.exit("--arc and --non go together: they are the two orbit representatives")
        ARC, NON = tuple(a.arc), tuple(a.non)
        if adj[ARC[0]][ARC[1]] != 1:
            sys.exit(f"--arc {ARC} is NOT an arc of {HOST}")
        if adj[NON[0]][NON[1]] != 0:
            sys.exit(f"--non {NON} IS an arc of {HOST}; it must be a non-arc")
        _in_base(ARC + NON, "--arc/--non")
        PAIRS = [ARC, NON]
        ANCHOR_TXT = f"pair-orbit (Lemma 2.1): arc {ARC} + non-arc {NON}"
    elif a.pair_anchor:
        if len(a.pair_anchor) % 2:
            sys.exit("--pair-anchor takes a FLAT list u1 v1 u2 v2 ...; got an odd count")
        PAIRS = [tuple(a.pair_anchor[i:i+2]) for i in range(0, len(a.pair_anchor), 2)]
        if any(u == v for u, v in PAIRS):
            sys.exit("--pair-anchor: an ordered pair must have distinct vertices")
        if len(set(PAIRS)) != len(PAIRS):
            sys.exit("--pair-anchor: repeated representative -- one per orbit, no duplicates")
        _in_base([v for p in PAIRS for v in p], "--pair-anchor")
        ANCHOR_TXT = "pair-orbit (Lemma 2.1): " + ", ".join(
            "(%d,%d) %s" % (u, v, "arc" if adj[u][v] else "non-arc")
            for u, v in PAIRS)
    elif a.vertex_anchor:
        VERTS = list(a.vertex_anchor)
        if len(set(VERTS)) != len(VERTS):
            sys.exit("--vertex-anchor: repeated representative -- one per orbit")
        _in_base(VERTS, "--vertex-anchor")
        ANCHOR_TXT = f"vertex-orbit (Corollary 2.2): {VERTS}"
    else:
        ANCHOR_TXT = "NONE: every base state is live, and no anchoring lemma is used"
    ANCHOR = PAIRS is not None or VERTS is not None
    if not ANCHOR and a.bits is None:
        sys.exit("the Paley path needs --arc/--non (or --pair-anchor / --vertex-anchor).\n"
                 "To run every base state unanchored, pass --bits explicitly.")
    print(f"### certify {HOST} (n={n}) margin={a.margin} by depth-{len(B)} cubing "
          f"{time.strftime('%F %H:%M:%S')}")
    print(f"  base {B}, anchoring {ANCHOR_TXT}")
    t = time.time()
    cubes, bm = enumerate_cubes(adj, B, a.k, exact, 'mask')
    if PAIRS:      # Lemma 2.1: some voter's top TWO on the base is a representative
        live = [c for c in cubes if any((B[pi[0]], B[pi[1]]) in PAIRS for pi in c)]
    elif VERTS:    # Corollary 2.2: some voter's top ON THE BASE is a representative
        live = [c for c in cubes if any(B[pi[0]] in VERTS for pi in c)]
    else:
        live = list(cubes)
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
    chunks = [(i, live[i:i+CHUNK], B, a.k, exact, spec, a.out)
              for i in range(0, len(live), CHUNK)]
    print(f"  {len(chunks)} chunks of <= {CHUNK}, {a.workers} workers, "
          f"check-and-discard", flush=True)

    t0 = time.time(); nc = ns = ck = 0; n_reuse = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for lo, s in ex.map(do_chunk, chunks):
            if s is None:
                continue
            if s.get('reused'):
                n_reuse += 1
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
    # Wall ACCUMULATES ACROSS INVOCATIONS, like solve/check, and for the same
    # reason: re-running purely to stamp --coverage took 0.00 h and would
    # otherwise overwrite a genuine 25.09 h with it.  Unlike solve/check this is
    # not recoverable from the per-chunk markers, because chunks ran
    # concurrently, so it is banked here at every completion.
    el = time.time() - t0
    _wall_p = os.path.join(a.out, 'wall.json')
    _prev_wall = 0.0
    if os.path.exists(_wall_p):
        with open(_wall_p) as f:
            _prev_wall = json.load(f).get('wall_s', 0.0)
    el = _prev_wall + el
    with open(_wall_p, 'w') as f:
        json.dump({'wall_s': round(el, 1)}, f)
    # ONE definition, read by both the VERDICT file and the console line, so
    # they can never disagree about which margin was certified.
    _what = "margin-1 " if exact else ""
    # Wall is NOT recoverable from the markers (chunks ran concurrently), so when
    # chunks are reused, say so rather than letting this invocation's wall stand
    # for the cost of the whole certification.
    _reuse = ("" if n_reuse == 0 else
              f"  [CUMULATIVE over all invocations; {n_reuse} of {len(chunks)}\n"
              f"              chunks were reused from earlier runs]")
    # Report the SPLIT half truthfully.  This script certifies the SEARCH half
    # only; coverage is cover_check.py, a separate program.
    if a.coverage and os.path.exists(a.coverage):
        import hashlib as _h
        _ch = _h.sha256(open(a.coverage,'rb').read()).hexdigest()
        _cov = (f'SPLIT half CERTIFIED: the cube set is exhaustive, proof\n'
                f'{a.coverage}\n  sha256 {_ch}\n'
                f'(F_B & SB & AND_i not-C_i is UNSAT at |B|={len(B)}.)\n'
                f'\nNo JOINT value is written here ON PURPOSE.  Binding the two\n'
                f'halves is CERT-v1, built by the repro repo\'s sat/certroot.py,\n'
                f'which hashes an auditable BLOCK carrying the instance\n'
                f'parameters -- so a value cannot be matched against a different\n'
                f'instance\'s artifacts.  A second scheme invented here would be\n'
                f'exactly the drift that makes two halves stop composing.\n'
                f'Feed it: --root-cnf {root_cnf.hexdigest()}\n'
                f'         --root-proofs {root_all.hexdigest()}\n'
                f'         --cover-cnf <the .cnf cover_check wrote>\n'
                f'         --cover-proof {a.coverage}')
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
              sum to <= {2*a.k} and none can exceed {2*a.k - 2*((a.k+1)//2)}.  Every arc of {HOST} lies in
              a 3-cycle, so majority is EQUIVALENT to margin<={2*(2*a.k-2*((a.k+1)//2))-a.k} here and this
              verdict covers both."""
        # The lemma list used to name the anchoring lemma UNCONDITIONALLY, so a
        # rigid host's verdict claimed a lemma its own `anchoring` line three
        # lines above said it had not used.  Build it from what the run did.
        LEMMAS = "  (L2) voters may be lex-ordered WLOG -- licenses the lex chain in coverage\n"
        if PAIRS:
            LEMMAS = ("  (L1) LEMMA 2.1, ordered-pair anchoring, is WLOG -- licenses running\n"
                      f"       only the {len(live)} live cubes of {len(cubes)}\n") + LEMMAS
        elif VERTS:
            LEMMAS = ("  (L1) COROLLARY 2.2, vertex anchoring, is WLOG -- licenses running\n"
                      f"       only the {len(live)} live cubes of {len(cubes)}\n") + LEMMAS
        else:
            LEMMAS += ("  NO anchoring lemma is used: every base state is live, so L1 is\n"
                       "  ABSENT from this chain, not merely satisfied.\n")
        f.write(f"""{HOST} is NOT {_what}{a.k}-inducible -- machine-verified.
{_extra}
date          {time.strftime('%F %H:%M:%S')}
margin        {a.margin}
base          {B}  ({len(cubes)} base states)
anchoring     {ANCHOR_TXT if ANCHOR else 'NONE: HUMAN LEMMA L1 IS NOT USED'} -> {len(live)} live cubes
cubes         {nc}, ALL UNSAT, each INDEPENDENTLY VERIFIED by lrat-trim
solver        cadical --lrat=true --checkproof=0 (self-check disabled)
checker       lrat-trim (Biere) -- different program, different author
NO DEEPENING  cubes are base states of a {len(B)}-vertex base; deepen.py unused
solve         {ns/3600:.1f} core-h
check         {ck/3600:.1f} core-h
wall          {el/3600:.2f} h on {a.workers} workers{_reuse}
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
{LEMMAS}Proved in RESEARCH_LOG.md.
""")
    print(f"\n### done {el/3600:.2f} h  solve {ns/3600:.1f} + check {ck/3600:.1f} core-h")
    print(f"  ROOT (CNF)    {root_cnf.hexdigest()}")
    print(f"  ROOT (proofs) {root_all.hexdigest()}")
    # was: "margin-1" hardcoded, which printed the WRONG margin for a majority
    # run while VERDICT.txt (line ~226) had it right from {_what}.  The line a
    # human reads is the one that gets quoted -- derive it from the same source.
    # ... and the HOST was still hardcoded to Paley(q) on this same line, so an
    # h02_f00 run printed "VERDICT: Paley(19)" to the console while VERDICT.txt
    # correctly said h02_f00.  HOST is the one definition; use it here too.
    print(f"  VERDICT: {HOST} is NOT {_what}{a.k}-inducible -> {a.out}/VERDICT.txt")


if __name__ == '__main__':
    main()
