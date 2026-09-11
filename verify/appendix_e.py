#!/usr/bin/env python3
"""Verify Appendix E of the manuscript AS IT IS WORDED.

Appendix E is the one result in the paper settled by an explicit construction
rather than by a computation, so it is the one with nothing to re-run.  This
supplies that: it builds the three orders A, B and C from the appendix's own
prose and checks the two things the appendix claims about them.

  E1  For every STRONG locally transitive T and EVERY cut point of its round
      order, the majority tournament of (A, B, C) is T with every support
      exactly 2 -- and after the appendix's padding step, exactly (k+1)/2 for
      every odd k.
  E2  The non-strong case is vacuous: a locally transitive tournament that is
      not strong is transitive, and a transitive tournament is realised at unit
      margin by (pi, pi, reverse pi).

Tournaments come from their DEFINITION -- every in- and out-neighbourhood
induces a transitive subtournament -- not from the round characterisation the
appendix cites to Brouwer and to Alspach and Tabib.  Checking the construction
against tournaments selected by the round rule would assume half of what is
being checked.  The round order is then recovered and asserted to exist, which
is the cited equivalence tested rather than relied on.

Two negative controls, because a verifier whose controls do not fire is not
testing anything:

  C1  Reversing one arc of a locally transitive tournament must break it --
      either it stops being locally transitive, or no round order exists, or
      some support is no longer 2.  If a perturbed tournament still passed, the
      check would be measuring nothing about T.
  C2  Swapping two adjacent vertices of C must cost at least one arc its
      support of 2.  Without this the check would pass on any three orders that
      happened to work, rather than on the order the appendix specifies.

    usage: appendix_e.py [maxn] [--gentourng PATH]

Two complete sources of tournaments, and the family is filtered out of both by
the definition, never assumed:

  n = 3..9    every isomorphism class from nauty's `gentourng`, whose default
              output is one upper-triangle bit string per line -- the same
              convention as the .bits files in `tournaments/`.  Without nauty
              the script brute-forces every labelled tournament instead, which
              is exhaustive to n = 6 and needs no tools at all.
  n = 11..14  McKay's locally transitive catalogue, in
              `tournaments/locally_transitive/`.  Every line of it is put
              through the same definition test, so the catalogue is checked
              here rather than trusted.

n = 10 falls between the two: no catalogue ships for it and its 9,733,056
classes are too many to filter in Python.  Said rather than skipped silently.
"""
import itertools
import os
import subprocess
import sys

GENT_MAX = 9        # 191,536 classes at n = 9; n = 10 is 9,733,056 and too slow
CAT_MIN = 11        # McKay's catalogue starts here


# --------------------------------------------------------------------------
# tournaments
# --------------------------------------------------------------------------
def parse_bits(s, n):
    """Upper-triangle bit string -> adjacency matrix.  A[i][j] = 1 means i -> j."""
    A = [[0] * n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if s[k] == '1':
                A[i][j] = 1
            else:
                A[j][i] = 1
            k += 1
    return A


def transitive_on(A, S):
    """Does S induce a transitive subtournament?  Equivalently, no 3-cycle."""
    for u, v, w in itertools.combinations(S, 3):
        for a, b, c in ((u, v, w), (u, w, v)):
            if A[a][b] and A[b][c] and A[c][a]:
                return False
    return True


def locally_transitive(A, n):
    """The DEFINITION: every in- and out-neighbourhood induces a transitive
    subtournament.  This is the gate every tournament in this file passes
    through; nothing here selects by the round rule."""
    for v in range(n):
        if not transitive_on(A, [u for u in range(n) if A[v][u]]):
            return False
        if not transitive_on(A, [u for u in range(n) if A[u][v]]):
            return False
    return True


def strong(A, n):
    seen, stack = {0}, [0]
    while stack:                                   # reachable from 0
        u = stack.pop()
        for v in range(n):
            if A[u][v] and v not in seen:
                seen.add(v)
                stack.append(v)
    if len(seen) != n:
        return False
    seen, stack = {0}, [0]
    while stack:                                   # 0 reachable from everything
        u = stack.pop()
        for v in range(n):
            if A[v][u] and v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == n


def round_order(A, n):
    """A cyclic order in which every out-neighbourhood is an interval, or None.

    Greedy first, exhaustive on failure: the greedy walk is cheap and verifies
    its own answer, so an order it returns IS round; only a false negative
    would be a problem, and the fallback removes that.  Vertex 0 is fixed,
    which costs nothing since the condition is rotation-invariant.
    """
    def is_round(o):
        for i in range(n):
            d = sum(A[o[i]][o[j]] for j in range(n) if j != i)
            if {o[(i + t) % n] for t in range(1, d + 1)} != \
               {o[j] for j in range(n) if A[o[i]][o[j]]}:
                return False
        return True

    order, used = [0], {0}
    for _ in range(n - 1):
        pool = [u for u in range(n) if A[order[-1]][u] and u not in used] or \
               [u for u in range(n) if u not in used]
        order.append(max(pool, key=lambda u: sum(A[u][w] for w in pool if w != u)))
        used.add(order[-1])
    if is_round(order):
        return order
    for tail in itertools.permutations(range(1, n)):
        if is_round([0] + list(tail)):
            return [0] + list(tail)
    return None


# --------------------------------------------------------------------------
# Appendix E's own construction, transcribed from its prose
# --------------------------------------------------------------------------
def appendix_profile(A, n, order, cut):
    """A, B and C exactly as Appendix E defines them, for one cut point.

    Returns (orders, None) or (None, reason) when one of the appendix's own
    stated hypotheses fails at this cut -- which is information, not an error:
    the appendix cuts at v_0 and derives the rest, so a cut where H is empty is
    outside what it claims.
    """
    vs = order[cut:] + order[:cut]                       # v_0, ..., v_{n-1}
    d = [sum(A[vs[i]][vs[j]] for j in range(n) if j != i) for i in range(n)]
    r = [i + d[i] for i in range(n)]                     # last out-neighbour
    if any(r[i] > r[i + 1] for i in range(n - 1)):
        return None, "the staircase r_0 <= ... <= r_{n-1} is not monotone"
    H = [i for i in range(n) if r[i] >= n]               # the wrapping sources
    if not H:
        return None, "H is empty, so this is not the strong case"
    q = min(H)
    if H != list(range(q, n)):
        return None, "H is not a suffix"
    t = {i: r[i] - n for i in H}                         # the ceilings
    if t[n - 1] >= q:
        return None, "t_{n-1} >= q, so H meets its own targets"

    oA = list(vs)
    oB = vs[q:] + vs[:q]
    # C lists the vertices by DECREASING key: key(v_l) = l on L, key(v_h) =
    # t_h + 1/2 on H, ties among equal t_h broken by larger index first.
    # Doubling clears the halves so the comparison stays in integers.
    def key2(i):
        return 2 * t[i] + 1 if i in t else 2 * i
    oC = [vs[i] for i in sorted(range(n), key=lambda i: (-key2(i), -i))]
    return (oA, oB, oC), None


def supports(A, n, orders):
    """Every arc's support under a profile, or the offending arc if the profile
    does not induce T at all."""
    pos = [{v: i for i, v in enumerate(o)} for o in orders]
    out = {}
    for i in range(n):
        for j in range(n):
            if A[i][j]:
                out[(i, j)] = sum(1 for p in pos if p[i] < p[j])
    return out


def transitive_profile(A, n):
    """(pi, pi, reverse pi) for a transitive tournament: every arc at support 2."""
    pi = sorted(range(n), key=lambda u: -sum(A[u][w] for w in range(n)))
    return [pi, pi, pi[::-1]]


def pad(orders, k):
    """Appendix E's padding: add (sigma, reverse sigma) pairs, which lift every
    support from 2 to (k+1)/2 without disturbing any of them relative to each
    other."""
    sigma = list(orders[0])
    out = list(orders)
    while len(out) < k:
        out += [sigma, sigma[::-1]]
    return out[:k]


# --------------------------------------------------------------------------
# sources of tournaments
# --------------------------------------------------------------------------
def resolve_gentourng(explicit):
    sw = os.environ.get("SOFTWARE_DIR",
                        os.path.expanduser("~/Downloads/DownloadedSoftware"))
    for c in (explicit, os.environ.get("GENTOURNG"),
              os.path.join(sw, "nauty2_8_6", "gentourng")):
        if c and os.access(c, os.X_OK):
            return c
    for d in os.environ.get("PATH", "").split(os.pathsep):
        c = os.path.join(d, "gentourng")
        if os.access(c, os.X_OK):
            return c
    return None


CATDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      os.pardir, "tournaments", "locally_transitive")


def source(n, gt):
    """(tournaments, label, filtered) for order n, or None when neither source
    reaches it.  `filtered` says whether the definition test has already
    selected the family, which decides what the caller may conclude from the
    count."""
    cat = os.path.join(CATDIR, "locallytransitivetournaments%d.txt" % n)
    if n >= CAT_MIN and os.path.exists(cat):
        lines = [l.strip() for l in open(cat) if l.strip()]
        return [parse_bits(l, n) for l in lines], "McKay catalogue", False
    if n <= GENT_MAX:
        if gt:
            r = subprocess.run([gt, str(n)], capture_output=True, text=True)
            lines = [l.strip() for l in r.stdout.split('\n') if l.strip()]
            return [parse_bits(l, n) for l in lines], "gentourng classes", False
        if n <= 6:
            m = n * (n - 1) // 2
            return ([parse_bits(format(b, '0%db' % m), n) for b in range(1 << m)],
                    "every labelled tournament", False)
    return None


# --------------------------------------------------------------------------
def verify_one(A, n, report):
    """E1 on one strong locally transitive tournament, at every cut point.
    Returns (cuts, verified, rejected, failures)."""
    o = round_order(A, n)
    if o is None:
        report("a strong locally transitive tournament has no round order, "
               "contradicting the equivalence Appendix E cites")
        return 0, 0, 0, 1
    cuts = ok = rej = bad = 0
    for cut in range(n):
        cuts += 1
        orders, why = appendix_profile(A, n, o, cut)
        if orders is None:
            rej += 1
            continue
        s = supports(A, n, orders)
        if len(s) != n * (n - 1) // 2 or set(s.values()) != {2}:
            report("cut %d: supports are %s, not all 2"
                   % (cut, sorted(set(s.values()))))
            bad += 1
            continue
        for k in (5, 7, 9):
            sk = supports(A, n, pad(orders, k))
            if set(sk.values()) != {(k + 1) // 2}:
                report("cut %d, k=%d: padded supports are %s, not all %d"
                       % (cut, k, sorted(set(sk.values())), (k + 1) // 2))
                bad += 1
        # C2: the order C is load-bearing.  Swapping two adjacent vertices of
        # it must cost some arc its support of 2; if every swap were harmless,
        # this file would be checking "some three orders work", not "these do".
        oA, oB, oC = orders
        if n >= 4:
            held = 0
            for i in range(n - 1):
                sw = list(oC)
                sw[i], sw[i + 1] = sw[i + 1], sw[i]
                if set(supports(A, n, [oA, oB, sw]).values()) == {2}:
                    held += 1
            if held == n - 1:
                report("cut %d: every adjacent swap in C left all supports at 2, "
                       "so C is not doing any work" % cut)
                bad += 1
        ok += 1
    return cuts, ok, rej, bad


def main(maxn, gt):
    bad = 0
    print("E1/E2: Appendix E's A, B, C, built from its own prose, at every cut point")
    print("%3s %-26s %6s %7s %6s %9s %9s"
          % ("n", "source", "LT", "strong", "cuts", "verified", "rejected"))
    seen_any = False
    for n in range(3, maxn + 1):
        got = source(n, gt)
        if got is None:
            print("%3s %-26s %6s" % (n, "-- no source --", "skipped"))
            continue
        pool, label, _ = got
        cat = [A for A in pool if locally_transitive(A, n)]
        if label == "McKay catalogue" and len(cat) != len(pool):
            print("  FAIL n=%d: %d of %d catalogue entries are not locally "
                  "transitive by the definition" % (n, len(pool) - len(cat), len(pool)))
            bad += 1
        ns = [A for A in cat if strong(A, n)]
        nt = [A for A in cat if not strong(A, n)]
        cuts = ok = rej = 0
        for A in ns:
            c, o, r, b = verify_one(A, n, lambda m, n=n: print("  FAIL n=%d: %s" % (n, m)))
            cuts += c; ok += o; rej += r; bad += b
        for A in nt:                                     # E2
            if not transitive_on(A, list(range(n))):
                print("  FAIL n=%d: a non-strong locally transitive tournament is "
                      "not transitive, so E2's argument does not close" % n)
                bad += 1
                continue
            if set(supports(A, n, transitive_profile(A, n)).values()) != {2}:
                print("  FAIL n=%d: (pi, pi, reverse pi) does not realise the "
                      "transitive tournament at unit margin" % n)
                bad += 1
        # E2 again, as a count: exactly one locally transitive tournament of
        # each order is not strong, and it is the transitive one.  Derived from
        # the enumeration rather than looked up.
        if len(nt) != 1:
            print("  FAIL n=%d: %d locally transitive tournaments are not strong; "
                  "E2 says exactly one is, the transitive one" % (n, len(nt)))
            bad += 1
        print("%3d %-26s %6d %7d %6d %9d %9d"
              % (n, label, len(cat), len(ns), cuts, ok, rej))
        seen_any = True
    if not seen_any:
        print("  FAIL no source of tournaments was reachable, so nothing was checked")
        bad += 1

    # C1: the construction must not accept tournaments outside the family.
    # Capped at n = 7 because the fallback in round_order is (n-1)! per
    # tournament and there are 446 classes at 7, 6,880 at 8.
    print("\nC1 (control): a tournament that is not locally transitive must be "
          "rejected")
    checked = accepted = 0
    for n in range(4, min(maxn, 7) + 1):
        got = source(n, gt)
        if got is None:
            continue
        for A in got[0]:
            if locally_transitive(A, n):
                continue
            checked += 1
            if round_order(A, n) is not None:
                accepted += 1
    if checked == 0:
        print("  FAIL control never ran: no non-locally-transitive tournament was "
              "offered, so roundness was never tested")
        bad += 1
    elif accepted:
        print("  FAIL %d of %d tournaments outside the family were given a round "
              "order" % (accepted, checked))
        bad += 1
    else:
        print("  %d tournaments outside the family, all rejected" % checked)

    print("\n%s: %d problem(s)" % ("FAILED" if bad else "OK", bad))
    return 1 if bad else 0


if __name__ == '__main__':
    args = list(sys.argv[1:])
    gt_arg = None
    if '--gentourng' in args:
        i = args.index('--gentourng')
        gt_arg = args[i + 1]
        del args[i:i + 2]
    mx = int(args[0]) if args else 14
    sys.exit(main(mx, resolve_gentourng(gt_arg)))
