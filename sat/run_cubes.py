#!/usr/bin/env python3
"""Cube-and-conquer driver over the dissent-boolean encoding.

Encoder comes from cube_sat.py (the object under test); the cube set from
cubes.py (independent of kinduce16.c, count cross-checked against it).

  --fresh     one solver instance per cube: honest per-cube timing, and the
              shape a DRAT run needs.  Default reuses one incremental solver
              (learned clauses carry over -- faster, but not per-cube data).
  --from/--to slice the cube list for parallelism (cubes are independent).
"""
import sys, time, argparse, itertools, subprocess, tempfile, os
from cube_sat import paley, build, cube_units
from cubes import enumerate_cubes, cube_string


def decode(model, arcs, X, n, K):
    """model -> K voter orders on 0..n-1, or None if some voter is intransitive."""
    val = {}
    for e in range(len(arcs)):
        for v in range(K):
            val[(e, v)] = X(e, v) in model
    orders = []
    for v in range(K):
        outdeg = [0] * n
        for e, (a, b) in enumerate(arcs):          # a -> b in T
            if val[(e, v)]:                        # voter dissents: b -> a
                outdeg[b] += 1
            else:
                outdeg[a] += 1
        if sorted(outdeg) != list(range(n)):
            return None                            # not a transitive tournament
        orders.append([u for u in sorted(range(n), key=lambda u: -outdeg[u])])
    return orders


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, required=True)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--margin', default='majority', choices=['majority', 'exact'])
    ap.add_argument('--base', type=int, nargs='+', default=None)
    ap.add_argument('--solver', default='Cadical195')
    ap.add_argument('--fresh', action='store_true')
    ap.add_argument('--from', dest='lo', type=int, default=0)
    ap.add_argument('--to', dest='hi', type=int, default=-1)
    ap.add_argument('--stop-on-sat', action='store_true')
    ap.add_argument('--every', type=int, default=100)
    a = ap.parse_args()

    exact = a.margin == 'exact'
    adj = paley(a.q)
    B = a.base if a.base else ([0, 1, 2, 3, 5] if a.q == 19 else [0, 1, 2, 5, 11])
    cls, arcs, pair, X, nv = build(adj, a.q, a.k, exact)
    cubes, bm = enumerate_cubes(adj, B, a.k, exact)
    hi = len(cubes) if a.hi < 0 else min(a.hi, len(cubes))
    lo = a.lo
    print(f"q={a.q} k={a.k} margin={a.margin} base={B} base_mask={bm} "
          f"vars={nv} clauses={len(cls)} cubes={len(cubes)} slice=[{lo},{hi}) "
          f"fresh={a.fresh} solver={a.solver}", flush=True)

    import pysat.solvers as S
    mk = lambda: getattr(S, a.solver)(bootstrap_with=cls)
    s = None if a.fresh else mk()
    t0 = time.time()
    prev_conf = 0
    worst = (0.0, -1)
    n_sat = 0
    times = []
    for ci in range(lo, hi):
        units = cube_units([[int(t) for t in p.split(',')]
                            for p in cube_string(cubes[ci], B).split(';')],
                           set(B), adj, pair, X, a.k)
        t1 = time.time()
        if a.fresh:
            s = mk()
            sat = s.solve(assumptions=units)
        else:
            sat = s.solve(assumptions=units)
        dt = time.time() - t1
        times.append(dt)
        if dt > worst[0]:
            worst = (dt, ci)
        if sat:
            n_sat += 1
            model = set(l for l in s.get_model() if l > 0)
            orders = decode(model, arcs, X, a.q, a.k)
            print(f"SAT at cube {ci}: {cube_string(cubes[ci], B)}", flush=True)
            if orders is None:
                print("*** decode failed: a voter is intransitive -- ENCODER BUG")
                return 2
            fn = f"/tmp/cubewit_q{a.q}_{a.margin}_{ci}.log"
            with open(fn, 'w') as f:
                f.write("WITNESS\n")
                for v, o in enumerate(orders):
                    f.write(f"  voter {v}: {' '.join(map(str, o))}\n")
            cmd = [sys.executable, 'verify_witness.py', fn, str(a.q), str(a.k)]
            if a.margin == 'majority':
                cmd.append('--majority')
            r = subprocess.run(cmd, capture_output=True, text=True)
            print("  " + r.stdout.strip(), flush=True)
            if r.returncode != 0:
                return 2
            if a.stop_on_sat:
                break
        if a.fresh:
            s.delete()
        if (ci - lo + 1) % a.every == 0:
            conf = '?'
            if not a.fresh:
                try:
                    c = s.accum_stats().get('conflicts', 0)
                    conf, prev_conf = c - prev_conf, c
                except NotImplementedError:
                    pass
            print(f"  ..{ci - lo + 1}/{hi - lo} cubes  {time.time() - t0:7.1f}s "
                  f"conf/batch={conf} worst={worst[0]:.2f}s@{worst[1]}", flush=True)
    el = time.time() - t0
    times.sort()
    med = times[len(times) // 2] if times else 0
    print(f"RESULT {'SAT' if n_sat else 'UNSAT'} cubes={hi - lo} sat_cubes={n_sat} "
          f"time={el:.2f}s mean={el / max(hi - lo, 1):.3f}s median={med:.3f}s "
          f"worst={worst[0]:.2f}s@cube{worst[1]}", flush=True)
    return 0


sys.exit(main())
