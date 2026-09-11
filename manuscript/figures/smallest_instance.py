#!/usr/bin/env python3
"""Is Paley(7) really the smallest instance that exercises all of Algorithm 1?

Figure 1's caption claims it is.  The claim came from the parked figure
specification and was never tested, so this tests it: over every tournament on
n <= 7 vertices and every base, at k = 3, which parts of the algorithm actually
fire.

"Every part" has to be pinned down before it can be checked.  Reading Algorithm
1 and the four bullets after it, the parts a worked example can show are:

  states   more than one base state, so the outer loop over them does something
  deadbase a base state killed before the DFS starts, by an empty domain
  mrv      a node where the unplaced vertices differ in domain size, so the
           dynamic order is making a choice rather than following any order
  tie      a node where MRV ties on size and the imbalance rule has to settle it
  keep     a REFINE lift below the inserted slot
  shift    a REFINE lift above it
  split    a REFINE lift ON it, which is the case that doubles a tuple
  empty    a mid-search empty domain, i.e. propagation refuting a subtree
  back     a node with more than one child explored, i.e. real backtracking
  anchor   a branch cut by Lemma 2.1 during the search
  witness  the run ends in a witness rather than a refutation

Both margin regimes are tried, and every base of every order from 3 to n-1.

Usage:  python3 smallest_instance.py [maxn]
"""

import itertools
import os
import subprocess
import sys

import paley7_trace as P

GENTOURNG = os.path.expanduser(
    "~/Downloads/DownloadedSoftware/nauty2_8_6/gentourng")

PARTS = ["states", "deadbase", "mrv", "tie", "keep", "shift", "split",
         "empty", "back", "anchor", "witness"]


def tournaments(n):
    """One representative per isomorphism class, as an arc matrix."""
    if n == 1:
        return [[[0]]]
    out = subprocess.run([GENTOURNG, "-q", str(n)], capture_output=True,
                         text=True, check=True).stdout
    reps = []
    for bits in out.split():
        if len(bits) != n * (n - 1) // 2:
            continue
        A = [[0] * n for _ in range(n)]
        t = 0
        for i in range(n):
            for j in range(i + 1, n):
                if bits[t] == "1":
                    A[i][j] = 1
                else:
                    A[j][i] = 1
                t += 1
        reps.append(A)
    return reps


def reps_from(orbits, B):
    """One representative per ordered-pair orbit, inside B when possible."""
    reps = []
    for orb in orbits:
        inside = [q for q in orb if q[0] in B and q[1] in B]
        reps.append(min(inside) if inside else min(orb))
    return reps, all(a in B and b in B for a, b in reps)


def parts_fired(A, n, k, B, regime, group=None, orbits=None):
    """Which parts of the algorithm this (tournament, base, regime) exercises.

    `group` and `orbits` are accepted so a census can compute them once per
    tournament; recomputing Aut for every base is what made this too slow at
    n = 7, where the group has 5,040 candidates to sift per call.
    """
    if group is None:
        group = P.automorphisms(A)
    if orbits is None:
        orbits = P.pair_orbits(A, group)
    reps, all_in = reps_from(orbits, set(B))
    s = P.Search(A, k, regime, B, reps=reps if all_in else None,
                 check_fresh=False)
    s.run()
    got = set()
    if len(P.base_states(A, B, k, regime)) > 1:
        got.add("states")
    if s.witnesses:
        got.add("witness")
    for r in s.trace:
        if r["kind"] == "empty-root":
            got.add("deadbase")
        if r["kind"] != "node":
            continue
        sizes = [len(d) for d in r["dom"].values()]
        if len(set(sizes)) > 1:
            got.add("mrv")
        best = min(r["keys"].values())
        if sum(1 for kk in r["keys"].values() if kk[0] == best[0]) > 1 and \
                sum(1 for kk in r["keys"].values() if kk[:2] == best[:2]) == 1:
            got.add("tie")
        explored = 0
        for c in r["children"]:
            if c["status"] == "anchor":
                got.add("anchor")
            if c["status"] == "empty":
                got.add("empty")
            if c["status"] in ("empty", "descend"):
                explored += 1
                for w, arrows in c.get("arrows", {}).items():
                    for a in arrows:
                        got |= set(a["cases"])
        if explored > 1:
            got.add("back")
    return got


def main(maxn):
    k = 3
    print("k = %d; a base is any subset of order 3 to n-1; both regimes tried" % k)
    print("\n  n  classes  (tournament, base, regime) triples firing all %d parts"
          % len(PARTS))
    first = None
    for n in range(4, maxn + 1):
        reps = tournaments(n)
        hits, best = [], set()
        for idx, A in enumerate(reps):
            group = P.automorphisms(A)
            orbits = P.pair_orbits(A, group)
            for b in range(3, n):
                for B in itertools.combinations(range(n), b):
                    for regime in ("unit", "majority"):
                        got = parts_fired(A, n, k, list(B), regime,
                                          group, orbits)
                        if len(got) > len(best):
                            best = got
                        if got >= set(PARTS):
                            hits.append((idx, list(B), regime))
        print("  %2d  %7d  %d" % (n, len(reps), len(hits)))
        if hits and first is None:
            first = (n, reps, hits)
        if not hits:
            print("        best any triple manages: %d of %d, missing %s"
                  % (len(best), len(PARTS),
                     ", ".join(sorted(set(PARTS) - best))))
    if first is None:
        print("\n  no tournament on at most %d vertices exercises all of them" % maxn)
        return
    n, reps, hits = first
    print("\n  SMALLEST is n = %d, with %d qualifying triples." % (n, len(hits)))
    p7 = P.paley(7) if n == 7 else None
    if p7 is not None:
        # is Paley(7) among the qualifying tournaments, and with which bases?
        idx7 = [i for i, A in enumerate(reps)
                if sorted(sum(r) for r in A) == sorted(sum(r) for r in p7)
                and iso(A, p7, 7)]
        assert len(idx7) == 1, "Paley(7) should appear exactly once in the census"
        mine = [(B, rg) for i, B, rg in hits if i == idx7[0]]
        print("  Paley(7) is class %d of %d, and qualifies with %d of them:"
              % (idx7[0], len(reps), len(mine)))
        for B, rg in mine[:6]:
            print("     base %s, %s" % (B, rg))
        others = sorted({i for i, _, _ in hits} - {idx7[0]})
        print("  other tournaments at n = %d that also qualify: %d" % (n, len(others)))


def iso(A, B, n):
    return any(all(A[i][j] == B[s[i]][s[j]] for i in range(n) for j in range(n)
                   if i != j) for s in itertools.permutations(range(n)))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
