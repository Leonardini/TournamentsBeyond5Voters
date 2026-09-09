#!/usr/bin/env python3
"""Enumerate the cube set for the dissent-boolean encoding: sorted k-multisets
of linear orders of a base B whose per-pair dissent counts meet the margin rule.

Written independently of kinduce16.c; the base-state COUNT is the cross-check
(kinduce16 prints base_states=... for the same base).

Pair order e = 0..C(b,2)-1 is (i,j) lexicographic over base SLOTS 0..b-1.
Perm order is lexicographic on the slot sequence, matching itertools.permutations.
Counting convention matches the C code: cnt[e] = #voters ranking slot i_e ABOVE
slot j_e, with target tHI=(k+1)/2 if T has base[i_e]->base[j_e] else tLO=k-tHI.
SWAR: nibble e of a 4-bit-packed accumulator holds cnt[e] (<= k <= 5 < 16).
"""
import sys, itertools, argparse

# (A module-level SWAR mask used to live here, hardwired to 10 nibbles =
# C(5,2), i.e. a FIVE-vertex base.  It was dead code and these campaigns use
# SIX-vertex bases (15 pairs), so it was removed rather than left to be
# reused at the wrong width.  Derive any such mask from NE = C(len(B),2).)
def nibble_hi(ne):
    """High bit of each of `ne` nibbles -- derived, never hardcoded."""
    return int('8' * ne, 16)


def paley(q):
    QR = {(x * x) % q for x in range(1, q)}
    return [[1 if (j - i) % q in QR else 0 for j in range(q)] for i in range(q)]


def base_mask(adj, B):
    """bit e set iff T has B[i_e] -> B[j_e]."""
    bm = 0
    for e, (i, j) in enumerate(itertools.combinations(range(len(B)), 2)):
        if adj[B[i]][B[j]]:
            bm |= 1 << e
    return bm


def enumerate_cubes(adj, B, K, exact, sort='perm'):
    b = len(B)
    pairs = list(itertools.combinations(range(b), 2))
    NE = len(pairs)
    hi = (K + 1) // 2
    lo = K - hi
    bm = base_mask(adj, B)
    # per-pair bounds on cnt[e] = #voters ranking slot i_e above slot j_e
    #   exact    : cnt == hi  (T: i->j)          cnt == lo  (T: j->i)
    #   majority : cnt >= hi                     cnt <= lo
    U, L = [], []
    for e in range(NE):
        if (bm >> e) & 1:
            U.append(hi if exact else K); L.append(hi)
        else:
            U.append(lo);                 L.append(lo if exact else 0)
    hmask = sum(1 << (4 * e + 3) for e in range(NE))

    perms = list(itertools.permutations(range(b)))
    packed = []
    for p in perms:
        pos = {s: r for r, s in enumerate(p)}
        packed.append(sum(1 << (4 * e) for e, (i, j) in enumerate(pairs)
                          if pos[i] < pos[j]))

    # (S + KGT) has nibble-e high bit set  <=>  cnt[e] > U[e]        (illegal)
    KGT = sum((7 - U[e]) << (4 * e) for e in range(NE))
    # (S + KGE[r]) has ALL nibble high bits set  <=>  cnt[e] + r >= L[e] for all e
    KGE = [sum((8 - max(L[e] - r, 0)) << (4 * e) for e in range(NE))
           for r in range(K + 1)]

    if sort == 'mask':
        # dissent vector of perm p vs T, as an NE-bit number (NE = C(b,2);
        # 15 for the 6-vertex bases these campaigns use): bit e = 1 iff p
        # DISAGREES with T on pair e.  Sorting the perm list by it makes the
        # existing 'non-decreasing index' break exactly a lex chain on the
        # cube variables themselves.
        key = lambda p: sum(1 << e for e in range(NE)
                            if bool((packed[p] >> (4 * e)) & 1) != bool((bm >> e) & 1))
        idx = sorted(range(len(perms)), key=key)
        perms = [perms[i] for i in idx]
        packed = [packed[i] for i in idx]

    out = []
    chosen = [0] * K

    def rec(t, lo_idx, S):
        if t == K:
            out.append(tuple(chosen))
            return
        rem = K - t - 1
        for p in range(lo_idx, len(perms)):
            S2 = S + packed[p]
            if (S2 + KGT) & hmask:                             # some cnt too big
                continue
            if ((S2 + KGE[rem]) & hmask) != hmask:             # some cnt unreachable
                continue
            chosen[t] = p
            rec(t + 1, p, S2)

    rec(0, 0, 0)
    return [tuple(perms[p] for p in c) for c in out], bm


def cube_string(cube, B):
    """cube = k-tuple of slot-permutations -> 'v,v,v,v,v;...' in VERTEX labels."""
    return ';'.join(','.join(str(B[s]) for s in pi) for pi in cube)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--q', type=int, required=True)
    ap.add_argument('--k', type=int, default=5)
    ap.add_argument('--margin', default='majority', choices=['majority', 'exact'])
    ap.add_argument('--base', type=int, nargs='+', default=[0, 1, 2, 3, 5])
    ap.add_argument('--sort', default='perm', choices=['perm', 'mask'],
                    help="canonical form for the voter symmetry break: 'perm' = "
                         "non-decreasing permutation index (matches kinduce16), "
                         "'mask' = non-decreasing C(b,2)-bit base-dissent vector "
                         "(encodable as a CNF lex-chain)")
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    adj = paley(a.q)
    cubes, bm = enumerate_cubes(adj, a.base, a.k, a.margin == 'exact', a.sort)
    print(f"q={a.q} k={a.k} margin={a.margin} base={a.base} base_mask={bm} "
          f"sort={a.sort} cubes={len(cubes)}", file=sys.stderr)
    lines = [cube_string(c, a.base) for c in cubes]
    if a.out:
        open(a.out, 'w').write('\n'.join(lines) + '\n')
    else:
        print('\n'.join(lines))
