#!/usr/bin/env python3
"""Exact base-state and break-survivor counts for a Paley(q) base, with no search.

This is the tool that selects an anchor configuration: which 5-vertex base
class, which embedding, and which (arc, non-arc) representative pair for the
`--toppair` Aut break.

MIRRORS brec() in kinduce22.c.  A "base state" is a NON-DECREASING K-tuple of
base-permutation indices (the voter lex-sort) whose per-pair support matches the
base tournament -- exactly, for margin-1, or by majority.

THE KEY FACT that makes this search-free: when both coordinates of both
`--toppair` representatives lie in the base, the break is a property of the
BASE STATE ALONE -- some voter's (first, second) within the base must equal
(u1,v1) or (u2,v2).  Survivors are then countable by inclusion-exclusion over
the 20 ordered index pairs, in one pass.

WHY NOT MEASURE SURVIVORS WITH THE ENGINE: `--per-base-nodes 1` looks like a
survivor counter but is not.  It checks the cap only every 4096 nodes, so it
(a) costs ~110 s per configuration and (b) UNDER-counts, because some base
states are fully refuted inside those 4096 nodes -- it reports 2569 where the
true figure is 2591.  It happens to agree on Paley(19); do not trust it.

Self-check reproduces every independently known number:
    python3 base_survivors.py --selfcheck
        Paley(23) base {0,1,2,5,11}  base_states 8031, optimum 2537, in-use 2591
        Paley(23) base {0,1,2,6,7}   base_states 16118, optimum 3246
        Paley(19) base {0,1,2,3,5}   base_states 2200 (margin-1)

Usage:
    python3 base_survivors.py --q 23 --base 0 1 2 6 7            # rank all 100 pairs
    python3 base_survivors.py --q 23 --base 0 1 2 5 11 --margin exact
    python3 base_survivors.py --q 23 --classes                   # rank the 12 base classes
    python3 base_survivors.py --q 23 --embeddings 41             # embeddings of a class
"""
import argparse, itertools, sys
from collections import defaultdict


def qr_set(q):
    return {(x * x) % q for x in range(1, q)}


def make_beats(q):
    """Z/q Paley. ONLY valid for PRIME q -- see load_bits for prime powers."""
    QR = qr_set(q)
    return lambda a, b: (b - a) % q in QR


# --- host loaded from a .bits file (upper triangle, row major) --------------
# Needed for any host that is not a Z/q Paley: prime-power Paley such as
# q=27=3^3 (Z/27 is not a field), deletions, DRTs, arbitrary tournaments.
BEATS = None      # set by load_bits; when not None it overrides make_beats
HOSTN = None


def load_bits(path):
    global BEATS, HOSTN
    b = ''.join(c for c in open(path).read() if c in '01')
    n = 1
    while n * (n - 1) // 2 < len(b):
        n += 1
    if n * (n - 1) // 2 != len(b):
        raise ValueError(f"{len(b)} bits is not C(n,2) for any n")
    A = [[0] * n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if b[k] == '1':
                A[i][j] = 1
            else:
                A[j][i] = 1
            k += 1
    for a in range(n):
        for c in range(a + 1, n):
            if A[a][c] + A[c][a] != 1:
                raise ValueError(f"not a tournament at pair ({a},{c})")
    HOSTN = n
    BEATS = lambda a, c: A[a][c] == 1
    return n, A


def beats_fn(q):
    return BEATS if BEATS is not None else make_beats(q)


def enumerate_base_states(S, q=23, K=5, margin='majority'):
    """All base states for base S (ascending) as tuples of permutation indices."""
    beats = beats_fn(q)
    b = len(S)
    pairs = [(i, j) for i in range(b) for j in range(i + 1, b)]   # lex == engine order
    tHI, tLO = (K + 1) // 2, (K - 1) // 2
    target = [tHI if beats(S[i], S[j]) else tLO for i, j in pairs]
    perms = list(itertools.permutations(range(b)))                # perms[p][r] = index at rank r
    pbits = []
    for p in perms:
        pos = {v: r for r, v in enumerate(p)}
        pbits.append(tuple(1 if pos[i] < pos[j] else 0 for i, j in pairs))

    NE, NP = len(pairs), len(perms)
    out, chosen, cnt = [], [0] * K, [0] * NE

    def rec(t, lo):
        if t == K:
            for e in range(NE):
                if margin == 'exact':
                    if cnt[e] != target[e]:
                        return
                elif target[e] == tHI:
                    if cnt[e] < tHI:
                        return
                elif cnt[e] > tLO:
                    return
            out.append(tuple(chosen))
            return
        rem = K - t - 1
        for p in range(lo, NP):                                   # lo => voter lex-sort
            bits = pbits[p]
            ok = True
            for e in range(NE):
                c = cnt[e] + bits[e]
                if margin == 'exact':
                    if c > target[e] or c + rem < target[e]:
                        ok = False
                        break
                elif target[e] == tHI:
                    if c + rem < tHI:
                        ok = False
                        break
                elif c > tLO:
                    ok = False
                    break
            if not ok:
                continue
            for e in range(NE):
                cnt[e] += bits[e]
            chosen[t] = p
            rec(t + 1, p)
            for e in range(NE):
                cnt[e] -= bits[e]

    rec(0, 0)
    return out, perms


def rank_pairs(S, q=23, K=5, margin='majority'):
    """Every (arc, non-arc) rep pair with both coords in S, by survivor count."""
    states, perms = enumerate_base_states(S, q, K, margin)
    beats = beats_fn(q)
    b = len(S)
    ids = {(a, c): n for n, (a, c) in
           enumerate((a, c) for a in range(b) for c in range(b) if a != c)}
    fs = [ids[(p[0], p[1])] for p in perms]
    single = [0] * len(ids)
    inter = defaultdict(int)
    for st in states:
        m = 0
        for p in st:
            m |= 1 << fs[p]
        bits = [i for i in range(len(ids)) if (m >> i) & 1]
        for i in bits:
            single[i] += 1
        for i, j in itertools.combinations(bits, 2):
            inter[(i, j)] += 1

    def surv(A, N):
        i, j = ids[(S.index(A[0]), S.index(A[1]))], ids[(S.index(N[0]), S.index(N[1]))]
        return single[i] + single[j] - inter[(min(i, j), max(i, j))]

    arcs = [(u, v) for u in S for v in S if u != v and beats(u, v)]
    nons = [(u, v) for u in S for v in S if u != v and not beats(u, v)]
    combos = sorted((surv(A, N), A, N) for A in arcs for N in nons)
    return len(states), combos


def mask_of(S, q):
    beats = beats_fn(q)
    m = e = 0
    for i in range(len(S)):
        for j in range(i + 1, len(S)):
            if beats(S[i], S[j]):
                m |= 1 << e
            e += 1
    return m


def canon5(m):
    A = [[0] * 5 for _ in range(5)]
    e = 0
    for i in range(5):
        for j in range(i + 1, 5):
            if (m >> e) & 1:
                A[i][j] = 1
            else:
                A[j][i] = 1
            e += 1
    best = None
    for p in itertools.permutations(range(5)):
        mm = e2 = 0
        for i in range(5):
            for j in range(i + 1, 5):
                if A[p[i]][p[j]]:
                    mm |= 1 << e2
                e2 += 1
        if best is None or mm < best:
            best = mm
    return best


def aut(q):
    """Automorphisms as vertex permutations. For prime Paley these are the
    affine maps x -> a^2 x + b; for a bits host they are computed directly."""
    if BEATS is None:
        return [tuple((a * v + b) % q for v in range(q))
                for a in sorted(qr_set(q)) for b in range(q)]
    n = HOSTN
    A = [[1 if BEATS(i, j) else 0 for j in range(n)] for i in range(n)]
    out, p, used = [], [-1] * n, [False] * n

    def bt(v):
        if v == n:
            out.append(tuple(p))
            return
        for img in range(n):
            if used[img]:
                continue
            if all(A[u][v] == A[p[u]][img] and A[v][u] == A[img][p[u]]
                   for u in range(v)):
                p[v] = img
                used[img] = True
                bt(v + 1)
                used[img] = False
                p[v] = -1
    bt(0)
    return out


def selfcheck():
    ok = True
    def chk(label, got, want):
        nonlocal ok
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  {label:<52} {got}"
              + ("" if good else f"  (expected {want})"))

    nb, combos = rank_pairs((0, 1, 2, 5, 11), 23, 5, 'majority')
    chk("P23 {0,1,2,5,11} base_states", nb, 8031)
    chk("P23 {0,1,2,5,11} optimum over 100 pairs", combos[0][0], 2537)
    d = {(A, N): n for n, A, N in combos}
    chk("P23 {0,1,2,5,11} break in use (0,2)+(0,5)", d[((0, 2), (0, 5))], 2591)
    nb2, c2 = rank_pairs((0, 1, 2, 6, 7), 23, 5, 'majority')
    chk("P23 {0,1,2,6,7} base_states", nb2, 16118)
    chk("P23 {0,1,2,6,7} optimum (anchor2's break)", c2[0][0], 3246)
    nb3, _ = rank_pairs((0, 1, 2, 3, 5), 19, 5, 'exact')
    chk("P19 {0,1,2,3,5} base_states (margin-1)", nb3, 2200)
    print()
    print("ALL CHECKS PASSED" if ok else "*** SELFCHECK FAILED ***")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, default=23)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--margin', choices=('exact', 'majority'), default='majority')
    ap.add_argument('--base', type=int, nargs='+')
    ap.add_argument('--classes', action='store_true')
    ap.add_argument('--embeddings', type=int)
    ap.add_argument('--bits', help='host tournament from a .bits file (needed for\n                    prime-power Paley such as q=27, where Z/q is not a field)')
    ap.add_argument('--selfcheck', action='store_true')
    a = ap.parse_args()

    if a.selfcheck:
        sys.exit(selfcheck())

    if a.bits:
        n, _ = load_bits(a.bits)
        a.q = n
        print(f'host: {a.bits}, n={n} (bits mode; Z/q arithmetic bypassed)')

    if a.classes:
        by = defaultdict(list)
        for S in itertools.combinations(range(a.q), 5):
            by[canon5(mask_of(S, a.q))].append(S)
        rows = []
        for c, sets in by.items():
            nb, combos = rank_pairs(sets[0], a.q, a.k, a.margin)
            rows.append((combos[0][0], nb, c, sets[0], combos[0][1], combos[0][2], len(sets)))
        rows.sort()
        print(f"{'rank':>4} {'canon':>5} {'subsets':>8} {'base_states':>12} {'min surv':>9} "
              f"{'ret%':>6}  best (arc)+(non-arc)")
        for i, (s, nb, c, rep, A, N, cnt) in enumerate(rows, 1):
            print(f"{i:>4} {c:>5} {cnt:>8,} {nb:>12,} {s:>9,} {100*s/nb:>5.1f}%  "
                  f"({A[0]},{A[1]})+({N[0]},{N[1]})   e.g. {set(rep)}")
        return

    if a.embeddings is not None:
        AUT = aut(a.q)
        subs = [S for S in itertools.combinations(range(a.q), 5)
                if canon5(mask_of(S, a.q)) == a.embeddings]
        seen, reps = set(), []
        for S in subs:
            if S in seen:
                continue
            orb = {tuple(sorted(g[v] for v in S)) for g in AUT}
            seen |= orb
            reps.append(S)
        print(f"class {a.embeddings}: {len(subs)} subsets, {len(reps)} Aut-orbits "
              f"(= inequivalent embeddings)")
        for S in reps:
            nb, combos = rank_pairs(S, a.q, a.k, a.margin)
            A, N = combos[0][1], combos[0][2]
            print(f"  {str(set(S)):<22} mask={mask_of(S, a.q):>4}  base_states={nb:>7,}  "
                  f"min_surv={combos[0][0]:>6,}  --toppair {A[0]} {A[1]} {N[0]} {N[1]}")
        print("\nNote: base_states and min_surv are ISO-INVARIANT, so they cannot")
        print("separate embeddings.  Cost can still differ several-fold by labelled")
        print("mask, because the engine's static tail order and MRV tie-breaks are")
        print("label-dependent -- measure, do not infer.")
        return

    if not a.base:
        sys.exit("need --base, --classes, --embeddings or --selfcheck")
    S = tuple(sorted(a.base))
    nb, combos = rank_pairs(S, a.q, a.k, a.margin)
    print(f"Paley({a.q}) base {set(S)}  mask={mask_of(S, a.q)}  margin={a.margin}  "
          f"base_states={nb:,}")
    print(f"{len(combos)} (arc, non-arc) pairs with both coordinates in the base:\n")
    print(f"{'survivors':>10} {'ret%':>6}  arc      non-arc   --toppair")
    for n, A, N in combos:
        print(f"{n:>10,} {100*n/nb:>5.1f}%  ({A[0]},{A[1]})   ({N[0]},{N[1]})    "
              f"--toppair {A[0]} {A[1]} {N[0]} {N[1]}")


if __name__ == '__main__':
    main()
