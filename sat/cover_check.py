#!/usr/bin/env python3
"""Certify that the cube set COVERS: F_B & SB & AND_i not-C_i is UNSAT.

F_B  = the base-local part of the encoding = build() applied to T|B
       (K * C(|B|,2) vars -- 75 for the 6-vertex bases these campaigns use;
       the '50' this line used to quote was a 5-vertex base and was stale).
SB   = lex chain d_1 <= ... <= d_k on the base-dissent vectors d_v (bit e has
       weight 2^e), which is exactly the canonical form cubes.py --sort mask uses.
C_i  = cube i as a full assignment to those base variables.

UNSAT here means: every assignment to the base variables that satisfies the
base-local constraints AND the lex chain is one of the C_i -- so nothing is
missed.  With a DRAT proof this discharges the coverage half of the symmetry
break mechanically; only "F is invariant under permuting voters" stays human.
"""
import sys, time, argparse, itertools, os, subprocess

CAD = os.path.expanduser("~/Downloads/DownloadedSoftware/cadical/build/cadical")
LT  = os.path.expanduser("~/Downloads/DownloadedSoftware/lrat-trim/lrat-trim")
from cube_sat import paley, build, cube_units
from cubes import enumerate_cubes
# ONE definition of the host loader, shared with the prover.  Copying it here
# would let the two drift, and a coverage proof over a DIFFERENT adj certifies
# a different cube set while complaining about nothing.
from certify_d6 import load_host


def lex_chain(dvecs, nv):
    """dvecs[v] = list of literals, MOST significant first. Returns (clauses, nv)."""
    cls = []
    for v in range(len(dvecs) - 1):
        A, Bv = dvecs[v], dvecs[v + 1]
        m = len(A)
        eq = [None] * (m + 1)          # eq[t] = "A,B agree on positions < t"
        for t in range(m):
            a, b = A[t], Bv[t]
            pre = [] if eq[t] is None else [-eq[t]]
            cls.append(pre + [-a, b])                      # eq_t & a -> b
            nv += 1
            e2 = nv                                        # eq[t+1]
            # e2 <-> eq_t & (a <-> b)
            if eq[t] is None:
                cls += [[-e2, -a, b], [-e2, a, -b],
                        [e2, a, b], [e2, -a, -b]]
            else:
                cls += [[-e2, eq[t]], [-e2, -a, b], [-e2, a, -b],
                        [e2, -eq[t], a, b], [e2, -eq[t], -a, -b]]
            eq[t + 1] = e2
    return cls, nv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, default=None,
                    help='Paley(q) host.  Exactly one of --q / --bits.')
    ap.add_argument('--bits', default=None,
                    help='cover an ARBITRARY host from a .bits file, the same\n'
                         'flag and the same loader certify_d6.py uses.  Needed\n'
                         'for any host that is not a Paley tournament -- e.g.\n'
                         'h02_f00 on 21 vertices, where no q exists at all.')
    ap.add_argument('--expect-cubes', type=int, default=None,
                    help='ASSERT the enumerated cube count equals this.  Pass the\n'
                         'count the prover reported: the coverage proof is only\n'
                         'about the cube set it enumerates itself, so a silent\n'
                         'disagreement would certify the wrong set.')
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--margin', default='majority', choices=['majority', 'exact'])
    ap.add_argument('--base', type=int, nargs='+', default=None)
    ap.add_argument('--solver', default='Cadical195')
    ap.add_argument('--dimacs', default=None, help='write the coverage CNF here')
    ap.add_argument('--drat', default=None, help='write a DRAT refutation here')
    ap.add_argument('--stream', action='store_true',
                    help='write the CNF clause-by-clause and solve with an EXTERNAL\n'
                         'cadical instead of materialising every clause in memory.\n'
                         'The in-memory path holds ~9 GB for Paley(23) (343,896\n'
                         'negated cubes x 75 boxed-int literals for an 838 MB file)\n'
                         'and was killed at 8.99 GB; streaming is near-constant.')
    ap.add_argument('--drop', type=int, default=-1,
                    help='NEGATIVE CONTROL: omit cube i; the answer must flip to SAT')
    a = ap.parse_args()

    exact = a.margin == 'exact'
    if (a.q is None) == (a.bits is None):
        sys.exit('give exactly one of --q and --bits')
    spec = a.bits if a.bits is not None else a.q
    adj, n = load_host(spec)
    HOST = f'Paley({a.q})' if a.bits is None else os.path.basename(a.bits).replace('.bits', '')
    if a.bits is not None and not a.base:
        sys.exit('--bits needs an explicit --base: the Paley defaults are not meaningful here')
    B = a.base if a.base else ([0, 1, 2, 3, 5] if a.q == 19 else [0, 1, 2, 5, 11])
    b = len(B)
    # F_B: the encoding of T|B on its own K*C(|B|,2) variables
    sub = [[adj[u][w] for w in B] for u in B]
    clsB, arcsB, pairB, XB, nvB = build(sub, b, a.k, exact)
    cubes, bm = enumerate_cubes(adj, B, a.k, exact, 'mask')

    # SOUNDNESS CHECK, not an assumption: F_B must literally be the set of
    # clauses of the full F that mention only the base variables.  Map the
    # sub-instance's (arc,voter) vars onto the full instance's and compare.
    # build()'s second argument is n, NOT q -- they coincided only because every
    # host here had been a Paley tournament.
    clsF, arcsF, pairF, XF, _ = build(adj, n, a.k, exact)
    lift = {}
    for e, (i, j) in enumerate(arcsB):
        eF = pairF[(B[i], B[j])]
        assert set(arcsF[eF]) == {B[i], B[j]}, "arc correspondence broken"
        for v in range(a.k):
            lift[XB(e, v)] = XF(eF, v)
    def lf(c): return frozenset(
        (1 if l > 0 else -1) * lift[abs(l)] for l in c)
    Wfull = set(lift.values())
    got = {lf(c) for c in clsB}
    want = {frozenset(c) for c in clsF if all(abs(l) in Wfull for l in c)}
    if got != want:
        print(f"*** F_B MISMATCH: {len(got - want)} extra, {len(want - got)} missing"
              f"  (|F_B|={len(got)}, |F restricted|={len(want)})")
        return 3
    print(f"  F_B check: the {len(got)} base-local clauses of F_B are EXACTLY the "
          f"clauses of F over the {len(Wfull)} base variables")

    # d_v: dissent vector of voter v over the base pairs, MOST significant first.
    # cubes.py --sort mask gives pair e the weight 2^e, so e = NE-1 is the MSB.
    NE = len(arcsB)
    dvec = [[XB(e, v) for e in range(NE - 1, -1, -1)] for v in range(a.k)]
    sb, nv = lex_chain(dvec, nvB)

    # not-C_i, expressed on the SUB-instance variables
    def neg_clauses():
        """Negated cubes, one at a time -- never all in memory at once."""
        for i, c in enumerate(cubes):
            if i == a.drop:
                continue
            units = cube_units([[B.index(B[s]) for s in pi] for pi in c],
                               set(range(b)), sub, pairB, XB, a.k)
            yield [-u for u in units]
    n_negs = len(cubes) - (1 if a.drop >= 0 else 0)
    negs = [] if a.stream else list(neg_clauses())

    if a.drop >= 0:
        print(f"  NEGATIVE CONTROL: dropping cube {a.drop}")
    cls = None if a.stream else (clsB + sb + negs)
    if a.expect_cubes is not None and len(cubes) != a.expect_cubes:
        print(f"*** CUBE COUNT MISMATCH: enumerated {len(cubes)}, prover reported "
              f"{a.expect_cubes} -- these are DIFFERENT cube sets, coverage proves nothing")
        return 4
    print(f"host={HOST} n={n} k={a.k} margin={a.margin} base={B} (|B|={b}, "
          f"{a.k}*C({b},2)={a.k * b * (b - 1) // 2} base vars) "
          f"base_mask={bm} cubes={len(cubes)}"
          + (" [cube count ASSERTED against the prover]" if a.expect_cubes else "") + "\n"
          f"coverage CNF: vars={nv} ({nvB} base + {nv - nvB} lex aux) "
          f"clauses={len(clsB) + len(sb) + n_negs} = {len(clsB)} F_B + {len(sb)} SB "
          f"+ {n_negs} neg-cubes" + ("  [streaming]" if a.stream else ""),
          flush=True)
    if a.dimacs and not a.stream:      # the streaming path writes its own
        with open(a.dimacs, 'w') as f:
            f.write(f"p cnf {nv} {len(cls)}\n")
            for c in cls:
                f.write(' '.join(map(str, c)) + " 0\n")
    if a.stream:
        if not a.dimacs:
            sys.exit('--stream requires --dimacs (the CNF is solved from disk)')
        t0 = time.time()
        with open(a.dimacs, 'w') as f:
            f.write(f'p cnf {nv} {len(clsB) + len(sb) + n_negs}\n')
            for c in clsB: f.write(' '.join(map(str, c)) + ' 0\n')
            for c in sb:   f.write(' '.join(map(str, c)) + ' 0\n')
            for c in neg_clauses(): f.write(' '.join(map(str, c)) + ' 0\n')
        # Hash the INSTANCE, not just the proof.  The DRAT is not reproducible on
        # a different solver build, but this CNF is fully determined by
        # (host, base, k, margin), so its sha256 is the portable half of the
        # JOINT hash that binds coverage to the search half.  Printing it here
        # means nobody has to remember to hash a file that lives in a scratchpad.
        import hashlib as _h
        _hh = _h.sha256()
        with open(a.dimacs, 'rb') as _f:
            for _blk in iter(lambda: _f.read(1 << 20), b''):
                _hh.update(_blk)
        print(f'  CNF written in {time.time()-t0:.0f}s '
              f'({os.path.getsize(a.dimacs)/2**30:.2f} GiB)\n'
              f'  CNF sha256 {_hh.hexdigest()}  '
              f'(PORTABLE -- pass to certify_d6 --coverage-cnf)', flush=True)
        prf = a.drat or (a.dimacs + '.lrat')
        t0 = time.time()
        r = subprocess.run([CAD, '-q', '--lrat=true', '--checkproof=0', a.dimacs, prf],
                           capture_output=True, text=True)
        el = time.time() - t0
        # THREE outcomes, not two.  CaDiCaL exits 10 for SATISFIABLE and 20 for
        # UNSATISFIABLE; anything else means it did not decide -- killed by the OOM
        # killer or the scheduler, crashed, or out of disk part-way through a proof.
        # This used to read `if 'UNSATISFIABLE' not in r.stdout` and call everything
        # else SAT, so every such failure was reported as `RESULT SAT *** DOES NOT
        # COVER -- BUG`: a refuted coverage proof, which is the most alarming thing
        # this kit can say and was in those cases simply false.  It happened on
        # 2026-09-12, on a p23 run whose root stage had already been SIGKILLed in the
        # same allocation, and the giveaway was a suspiciously exact time=1840.00s.
        # An undecided run must never be reported as a verdict in either direction.
        unsat = r.returncode == 20 and 'UNSATISFIABLE' in r.stdout
        sat   = r.returncode == 10 and 'UNSATISFIABLE' not in r.stdout \
                                   and 'SATISFIABLE' in r.stdout
        if not (unsat or sat):
            print(f'RESULT UNKNOWN time={el:.2f}s exit={r.returncode}  '
                  f'*** the solver did not decide -- this is NOT a verdict on coverage')
            print(f'  proof file is {os.path.getsize(prf)/2**20:.0f} MiB and is incomplete; '
                  f'rerun with more memory or a longer wall')
            if r.stderr.strip():
                print('  solver stderr:', r.stderr.strip()[:400])
            return 3
        if sat:
            tag = 'expected (control)' if a.drop >= 0 else '*** DOES NOT COVER -- BUG'
            print(f'RESULT SAT time={el:.2f}s  {tag}')
            return 0 if a.drop >= 0 else 2
        v = subprocess.run([LT, a.dimacs, prf], capture_output=True, text=True)
        ok = 's VERIFIED' in v.stdout          # lrat-trim exits 20, not 0
        print(f'RESULT UNSAT time={el:.2f}s proof={os.path.getsize(prf)/2**20:.0f} MiB '
              f'CHECK={"VERIFIED" if ok else "*** NOT VERIFIED"}  '
              f'-> the {n_negs} cubes cover every lex-canonical base assignment')
        if a.drop >= 0:
            print('  *** CONTROL FAILED: coverage still holds with a cube missing')
            return 2
        return 0 if ok else 2

    import pysat.solvers as S
    t0 = time.time()
    with getattr(S, a.solver)(bootstrap_with=cls, with_proof=bool(a.drat)) as s:
        sat = s.solve()
        el = time.time() - t0
        if sat:
            tag = "expected (control)" if a.drop >= 0 else "*** DOES NOT COVER -- BUG"
            print(f"RESULT SAT time={el:.2f}s  {tag}")
            m = set(l for l in s.get_model() if l > 0)
            print("   witness base assignment:",
                  [[1 if XB(e, v) in m else 0 for e in range(NE)] for v in range(a.k)])
            return 0 if a.drop >= 0 else 2
        pl = 0
        if a.drat:
            p = s.get_proof() or []
            open(a.drat, 'w').write('\n'.join(p) + '\n')
            pl = len(p)
        print(f"RESULT UNSAT time={el:.2f}s proof_lines={pl}  "
              f"-> the {len(negs)} cubes cover every lex-canonical base assignment")
        if a.drop >= 0:
            print("  *** CONTROL FAILED: coverage still holds with a cube missing")
            return 2
    return 0


sys.exit(main())
