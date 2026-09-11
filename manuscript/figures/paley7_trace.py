"""Trace Algorithm 1 of the manuscript on Paley(7) with k = 3.

This script is the generator behind Figure 1: it runs the placement search of
Appendix A.2 on a small instance that exercises every step of it, and dumps
the state the figure draws.  Nothing in the figure is written by hand.

Every quantity is derived here.  The trace is pinned by four hard cross-checks,
each of which would fail if the pipeline were wrong rather than merely confirm
that it is right:

  T1  base-state counts and the witness count agree with the production engine
      `KInduceDFS/kinduce` on the same instance, at both margin regimes;
  T2  the witness set contains the profile Shepardson and Tovey publish for the
      quadratic residue tournament on 7 vertices, and is a single orbit under
      Aut(P_7) x S_k -- which is their (unproved) uniqueness claim;
  T3  at every node of the search, the incrementally refined domain equals the
      domain recomputed from scratch, which is the claim panel (c) draws;
  T4  every arc of every witness has support exactly (k+1)/2 even when the
      search is run at majority, which is what the 3-cycle bound predicts here;
  T5  imposing Lemma 2.1 during the search only ever removes nodes: the anchored
      search visits a subtree of the unanchored one, and keeps one witness;
  T6  the witness set does not depend on the decomposition -- every base of
      order 3, 4 and 5 returns the same profiles up to voter permutation;
  T7  the witness is the orbit of a single order under an automorphism of order
      k, which is why its stabiliser has order k and there are |Aut|/k of them.

Usage:  python3 paley7_trace.py [--json OUT]
"""

import argparse
import itertools
import json
import os
import subprocess
import sys

# --------------------------------------------------------------------------
# the tournament


def paley(q):
    """Arc matrix of the Paley tournament on Z_q: i -> j iff j - i is a QR."""
    assert q % 4 == 3, f"Paley needs q = 3 mod 4, got {q}"
    assert all(q % p for p in range(2, int(q ** 0.5) + 1)), "q must be prime here"
    qr = {(x * x) % q for x in range(1, q)}
    A = [[0] * q for _ in range(q)]
    for i in range(q):
        for j in range(q):
            if i != j:
                A[i][j] = 1 if (j - i) % q in qr else 0
    for i in range(q):
        for j in range(i + 1, q):
            assert A[i][j] + A[j][i] == 1, "not a tournament"
    return A


def out_degrees(A):
    return [sum(row) for row in A]


def triangles_through(A, u, v):
    """Number of directed triangles containing the arc u -> v."""
    assert A[u][v] == 1
    return sum(1 for w in range(len(A)) if w not in (u, v) and A[v][w] and A[w][u])


# --------------------------------------------------------------------------
# automorphisms, orbits, anchoring representatives


def automorphisms(A):
    n = len(A)
    out = []
    for s in itertools.permutations(range(n)):
        if all(A[i][j] == A[s[i]][s[j]] for i in range(n) for j in range(n) if i != j):
            out.append(s)
    return out


def pair_orbits(A, group):
    """Orbits of the group on ordered pairs of distinct vertices."""
    n = len(A)
    pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    seen, orbits = set(), []
    for p in pairs:
        if p in seen:
            continue
        orb = set()
        for g in group:
            q = (g[p[0]], g[p[1]])
            orb.add(q)
            seen.add(q)
        orbits.append(sorted(orb))
    return orbits


def anchor_reps(A, group, B):
    """One representative per ordered-pair orbit, chosen inside B when possible.

    Returns (reps, all_inside).  Lemma 2.1 may invalidate base states only when
    every representative lies inside B, so the flag is what licenses that use.
    """
    reps = []
    for orb in pair_orbits(A, group):
        inside = [p for p in orb if p[0] in B and p[1] in B]
        reps.append(min(inside) if inside else min(orb))
    all_inside = all(a in B and b in B for a, b in reps)
    return reps, all_inside


# --------------------------------------------------------------------------
# profiles, supports, base states


def support(orders, u, v):
    """Number of voters ranking u above v."""
    return sum(1 for o in orders if o.index(u) < o.index(v))


def ok_support(c, arc, k, regime):
    """Is a support of c voters for u over v admissible, given the arc direction?

    `arc` is 1 when u -> v is an arc of T and 0 when v -> u is.  The winning
    side needs exactly (k+1)/2 voters at unit margin and at least that many at
    majority.
    """
    lo = (k + 1) // 2
    want = c if arc else k - c
    return want == lo if regime == "unit" else want >= lo


def profile_induces(orders, A, S, k, regime):
    for u, v in itertools.combinations(sorted(S), 2):
        if not ok_support(support(orders, u, v), A[u][v], k, regime):
            return False
    return True


def base_states(A, B, k, regime):
    """k-voter profiles over B consistent with T|_B, up to voter permutation.

    Lemma 2.3 is absorbed by keeping only non-decreasing tuples of orders.
    """
    Bs = sorted(B)
    orders = sorted(itertools.permutations(Bs))
    out = []
    for combo in itertools.combinations_with_replacement(orders, k):
        if profile_induces(combo, A, Bs, k, regime):
            out.append(tuple(list(o) for o in combo))
    return out


# --------------------------------------------------------------------------
# domains


def domain_fresh(A, orders, S, v, k, regime):
    """D(v | S) computed from scratch: slot tuples consistent with every v-S arc."""
    m = len(next(iter(orders)))
    D = []
    for p in itertools.product(range(m + 1), repeat=k):
        good = True
        for u in S:
            # v lands at index p_i, so v is above u exactly when p_i <= pos_i(u)
            c = sum(1 for i in range(k) if p[i] <= orders[i].index(u))
            if not ok_support(c, A[v][u], k, regime):
                good = False
                break
        if good:
            D.append(p)
    return D


def refine(D, q, w, u, A, k, regime):
    """REFINE of Algorithm 1: lift each tuple past the slot tuple q used for u.

    Returns (kept, arrows) where arrows records, per source tuple and voter, one
    of 'keep' / 'shift' / 'split', which is what panel (c) draws.
    """
    kept, arrows = [], []
    for p in D:
        lifts = [[]]
        cases = []
        for i in range(k):
            if p[i] < q[i]:
                cases.append("keep")
                lifts = [l + [(p[i], True)] for l in lifts]
            elif p[i] > q[i]:
                cases.append("shift")
                lifts = [l + [(p[i] + 1, False)] for l in lifts]
            else:
                cases.append("split")
                lifts = [l + [(p[i], True)] for l in lifts] + \
                        [l + [(p[i] + 1, False)] for l in lifts]
        for l in lifts:
            tup = tuple(x for x, _ in l)
            c = sum(1 for _, before in l if before)     # voters with w above u
            live = ok_support(c, A[w][u], k, regime)
            arrows.append({"src": p, "cases": cases, "dst": tup,
                           "support": c, "kept": live})
            if live:
                kept.append(tup)
    return kept, arrows


def insert(orders, v, p):
    out = []
    for i, o in enumerate(orders):
        o = list(o)
        o.insert(p[i], v)
        out.append(tuple(o))
    return tuple(out)


# --------------------------------------------------------------------------
# anchoring, tested during the search


def anchored_alive(orders, S, reps):
    """Can this partial profile still meet the condition of Lemma 2.1?

    Some voter must end with a_i first and b_i second.  From a partial profile
    that is still possible exactly when, for some representative and some voter,
    the placed members of {a, b} already sit above all other placed vertices, in
    the right relative order.
    """
    for a, b in reps:
        for o in orders:
            rest = [x for x in o if x not in (a, b)]
            top = [x for x in o if x in (a, b)]
            if o[:len(top)] != tuple(top):
                continue                      # something else is already above
            if a in S and b in S and o.index(a) > o.index(b):
                continue
            return True
    return False


# --------------------------------------------------------------------------
# the search


class Search:
    def __init__(self, A, k, regime, B, reps=None, check_fresh=True):
        self.A, self.k, self.regime, self.B = A, k, regime, sorted(B)
        self.n = len(A)
        self.reps = reps
        self.check_fresh = check_fresh
        self.nodes = 0
        self.witnesses = []
        self.trace = []          # one record per node, in visit order

    def mrv(self, orders, S, dom):
        unplaced = [v for v in range(self.n) if v not in S]
        def key(v):
            imb = abs(sum(self.A[v][u] for u in S) - sum(self.A[u][v] for u in S))
            return (len(dom[v]), -imb, v)
        return min(unplaced, key=key), {v: key(v) for v in unplaced}

    def run(self):
        for bs_index, bs in enumerate(base_states(self.A, self.B, self.k, self.regime)):
            orders = tuple(tuple(o) for o in bs)
            S = set(self.B)
            if self.reps is not None and not anchored_alive(orders, S, self.reps):
                self.trace.append({"kind": "dead-base", "bs": bs_index,
                                   "orders": [list(o) for o in orders]})
                continue
            dom = {v: domain_fresh(self.A, orders, S, v, self.k, self.regime)
                   for v in range(self.n) if v not in S}
            if any(not d for d in dom.values()):
                self.trace.append({"kind": "empty-root", "bs": bs_index,
                                   "orders": [list(o) for o in orders]})
                continue
            self.dfs(orders, S, dom, [], bs_index)
        return self.witnesses

    def dfs(self, orders, S, dom, path, bs_index):
        self.nodes += 1
        if len(S) == self.n:
            self.witnesses.append(orders)
            self.trace.append({"kind": "witness", "bs": bs_index, "path": list(path),
                               "orders": [list(o) for o in orders]})
            return
        vstar, keys = self.mrv(orders, S, dom)
        rec = {"kind": "node", "bs": bs_index, "path": list(path),
               "orders": [list(o) for o in orders], "S": sorted(S),
               "vstar": vstar,
               "dom": {v: [list(p) for p in dom[v]] for v in sorted(dom)},
               "keys": {v: list(keys[v]) for v in sorted(keys)},
               "children": []}
        self.trace.append(rec)
        for p in dom[vstar]:
            o2 = insert(orders, vstar, p)
            S2 = S | {vstar}
            if self.reps is not None and not anchored_alive(o2, S2, self.reps):
                rec["children"].append({"slot": list(p), "status": "anchor"})
                continue
            d2, arrows, dead = {}, {}, None
            for w in dom:
                if w == vstar:
                    continue
                d2[w], arrows[w] = refine(dom[w], p, w, vstar,
                                          self.A, self.k, self.regime)
                if self.check_fresh:
                    fresh = domain_fresh(self.A, o2, S2, w, self.k, self.regime)
                    assert sorted(d2[w]) == sorted(fresh), \
                        f"T3 FAILED: REFINE disagrees with a fresh domain for {w}"
                if not d2[w] and dead is None:
                    dead = w
            child = {"slot": list(p),
                     "arrows": {w: arrows[w] for w in arrows},
                     "dom": {w: [list(x) for x in d2[w]] for w in d2}}
            if dead is not None:
                child["status"] = "empty"
                child["empty_at"] = dead
                rec["children"].append(child)
                continue
            child["status"] = "descend"
            rec["children"].append(child)
            self.dfs(o2, S2, d2, path + [(vstar, p)], bs_index)


# --------------------------------------------------------------------------
# cross-checks

ENGINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "KInduceDFS", "kinduce")

# Shepardson and Tovey, Social Choice and Welfare 33(3):495-503, 2009, p. 502:
# "the most notorious 7-tournament, the quadratic residue tournament, is a
#  majority relation of the profile {0123456}, {5263041}, {4613502}.  (The
#  profile is unique up to symmetry.)"
ST_PROFILE = ((0, 1, 2, 3, 4, 5, 6), (5, 2, 6, 3, 0, 4, 1), (4, 6, 1, 3, 5, 0, 2))


def engine(k, base, regime, count=True):
    """Run the production engine and parse its RESULT line."""
    cmd = [ENGINE, "--paley", "7", "--k", str(k), "--base"] + [str(x) for x in base]
    if regime == "majority":
        cmd += ["--max-margin", str(k)]
    if count:
        cmd += ["--count"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    res = {}
    for line in out.splitlines():
        if line.startswith("RESULT"):
            for tok in line.split():
                if "=" in tok:
                    key, val = tok.split("=", 1)
                    res[key] = val
    return res, out


def describe_affine(g, q):
    """Write an automorphism of P_q as x -> a x + b, which every one of them is."""
    b = g[0]
    a = (g[1] - b) % q
    assert all(g[x] == (a * x + b) % q for x in range(q)), "not affine"
    return f"{a}x + {b}" if b else f"{a}x"


def canonical(profile):
    """A profile up to voter permutation: the sorted tuple of its orders."""
    return tuple(sorted(profile))


def orbit_count(profiles, group):
    """Number of orbits of Aut(T) on profiles taken up to voter permutation."""
    remaining = {canonical(p) for p in profiles}
    orbits = 0
    while remaining:
        seed = next(iter(remaining))
        orb = {canonical(tuple(tuple(g[x] for x in o) for o in seed))
               for g in group}
        assert orb <= remaining, "orbits of witnesses should be disjoint"
        orbits += 1
        remaining -= orb
    return orbits


def visited(search):
    """The set of nodes a completed search entered, keyed by insertion path."""
    return {tuple((v, tuple(p)) for v, p in r["path"])
            for r in search.trace if r["kind"] in ("node", "witness")}


def affine_generator(A, group, profile, k):
    """An automorphism whose orbit on one order is the whole profile, if any.

    Returns (g, seed) with {g^0 seed, ..., g^(k-1) seed} = profile as a multiset.
    """
    for g in group:
        for seed in profile:
            orb, cur = [], seed
            for _ in range(k):
                orb.append(cur)
                cur = tuple(g[x] for x in cur)
            if cur == seed and canonical(tuple(orb)) == canonical(profile):
                return g, seed
    return None, None


def crosscheck(A, group, k=3, fig_base=(0, 1, 3), fig_regime="majority"):
    """T1, T2, T4, T5 and T6.  T3 is asserted inside Search, at every node."""
    report = []
    base5 = [0, 1, 2, 3, 4]
    for regime in ("unit", "majority"):
        mine = base_states(A, base5, k, regime)
        res, _ = engine(k, base5, regime)
        assert int(res["base_states"]) == len(mine), (
            f"T1 FAILED: engine says {res['base_states']} base states at "
            f"{regime}, this script says {len(mine)}")
        s = Search(A, k, regime, base5, reps=None)
        s.run()
        assert int(res["sols"]) == len(s.witnesses), (
            f"T1 FAILED: engine finds {res['sols']} witnesses at {regime}, "
            f"this script finds {len(s.witnesses)}")
        report.append(f"T1 {regime:9s}: base states {len(mine):3d}, "
                      f"witnesses {len(s.witnesses)}  (engine agrees on both)")
        if regime == "majority":
            lo = (k + 1) // 2
            for w in s.witnesses:
                for u, v in itertools.combinations(range(len(A)), 2):
                    c = support(w, u, v)
                    assert (c if A[u][v] else k - c) == lo, \
                        "T4 FAILED: a majority witness has a wider margin"
            report.append(f"T4          : every arc of all {len(s.witnesses)} "
                          f"majority witnesses has support exactly {lo}")
            assert canonical(ST_PROFILE) in {canonical(w) for w in s.witnesses}, \
                "T2 FAILED: the published Shepardson-Tovey profile is not found"
            no = orbit_count(s.witnesses, group)
            assert no == 1, f"T2 FAILED: {no} orbits, so the witness is not unique"
            report.append(f"T2          : the published profile is among them, and "
                          f"all {len(s.witnesses)} form ONE orbit under Aut(P_7)")
            reference = {canonical(w) for w in s.witnesses}

    reps, all_in = anchor_reps(A, group, set(fig_base))
    assert all_in, "the figure's base must contain every anchoring representative"
    free = Search(A, k, fig_regime, fig_base, reps=None)
    free.run()
    anch = Search(A, k, fig_regime, fig_base, reps=reps)
    anch.run()
    assert visited(anch) <= visited(free), \
        "T5 FAILED: the anchored search visits a node the free search does not"
    assert len(anch.witnesses) == 1, \
        f"T5 FAILED: anchoring keeps {len(anch.witnesses)} witnesses, not 1"
    report.append(f"T5          : anchoring cuts {free.nodes} nodes to {anch.nodes} "
                  f"and {len(free.witnesses)} witnesses to 1, and removes nothing else")

    for b in (3, 4, 5):
        for B in itertools.combinations(range(len(A)), b):
            s = Search(A, k, "majority", B, reps=None, check_fresh=False)
            s.run()
            assert {canonical(w) for w in s.witnesses} == reference, \
                f"T6 FAILED: base {B} returns a different witness set"
    report.append(f"T6          : all {sum(1 for b in (3,4,5) for _ in itertools.combinations(range(len(A)), b))}"
                  f" bases of order 3, 4 and 5 return the same "
                  f"{len(reference)} profiles")

    w = anch.witnesses[0]
    g, seed = affine_generator(A, group, w, k)
    assert g is not None, "T7 FAILED: the witness is not an orbit of one order"
    stab = [h for h in group if canonical(tuple(tuple(h[x] for x in o) for o in w))
            == canonical(w)]
    assert len(stab) == k and len(group) // k == len(reference), \
        "T7 FAILED: stabiliser order and witness count do not match |Aut|/k"
    report.append(f"T7          : the witness is the orbit of {list(seed)} under "
                  f"x -> {describe_affine(g, len(A))}, of order {k}; its "
                  f"stabiliser has order {len(stab)} = {len(group)}/{len(reference)}")
    return report


# --------------------------------------------------------------------------


def survey(A, group, k=3, regime="unit"):
    """Cost of every candidate base of order 3 and 4, to choose the figure's."""
    rows = []
    for b in (3, 4):
        for B in itertools.combinations(range(len(A)), b):
            reps, all_in = anchor_reps(A, group, set(B))
            bs = base_states(A, B, k, regime)
            s = Search(A, k, regime, B, reps=reps if all_in else None)
            s.run()
            maxdom = max((len(d) for r in s.trace if r["kind"] == "node"
                          for d in r["dom"].values()), default=0)
            live = len(bs) - sum(1 for r in s.trace if r["kind"] == "dead-base")
            rows.append({"B": list(B), "b": b, "states": len(bs), "live": live,
                         "reps_inside": all_in, "nodes": s.nodes,
                         "witnesses": len(s.witnesses), "maxdom": maxdom,
                         "scores": sorted(sum(A[u][v] for v in B) for u in B)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--base", type=int, nargs="+", default=[0, 1, 3])
    ap.add_argument("--regime", default="unit", choices=("unit", "majority"))
    ap.add_argument("--no-anchor", action="store_true")
    args = ap.parse_args()

    k = 3
    A = paley(7)
    n = len(A)
    assert out_degrees(A) == [(n - 1) // 2] * n, "P_7 should be regular"
    tri = {triangles_through(A, u, v) for u in range(n) for v in range(n) if A[u][v]}
    assert tri == {(n + 1) // 4}, f"every arc should lie in {(n+1)//4} triangles"
    group = automorphisms(A)
    assert len(group) == 21, f"|Aut(P_7)| should be 21, got {len(group)}"

    print(f"P_7: regular, |Aut| = {len(group)}, every arc in {tri.pop()} directed "
          f"triangles, so no arc of a witness can be unanimous at k = {k}")
    for line in crosscheck(A, group, k, tuple(args.base), args.regime):
        print("  " + line)

    if args.survey:
        print("\nbase survey (regime = unit):")
        print(f"  {'B':14s} {'T|B scores':12s} {'states':>6s} {'live':>5s} "
              f"{'reps in B':>9s} {'nodes':>6s} {'wit':>4s} {'maxdom':>6s}")
        for r in sorted(survey(A, group, k), key=lambda r: (r["b"], r["nodes"])):
            print(f"  {str(r['B']):14s} {str(r['scores']):12s} {r['states']:6d} "
                  f"{r['live']:5d} {str(r['reps_inside']):>9s} {r['nodes']:6d} "
                  f"{r['witnesses']:4d} {r['maxdom']:6d}")
        return

    B = args.base
    reps, all_in = anchor_reps(A, group, set(B))
    use = None if args.no_anchor else (reps if all_in else None)
    s = Search(A, k, args.regime, B, reps=use)
    s.run()
    anch = "off" if use is None else f"on, reps {reps}"
    print(f"\nbase {B}, regime {args.regime}: "
          f"{len(base_states(A, B, k, args.regime))} base states, {s.nodes} nodes, "
          f"{len(s.witnesses)} witnesses, anchoring {anch} (reps inside B: {all_in})")
    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"base": B, "regime": args.regime, "k": k,
                       "reps": [list(p) for p in reps], "reps_inside": all_in,
                       "arcs": A, "nodes": s.nodes,
                       "witnesses": [[list(o) for o in w] for w in s.witnesses],
                       "trace": s.trace}, fh, indent=1)
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
