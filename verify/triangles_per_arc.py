#!/usr/bin/env python3
"""Directed triangles per arc, for the hosts named on the command line.

This is what turns a `--max-margin 3` run into a MAJORITY verdict.  By the
3-cycle bound of Section 3, the three supports of a directed triangle sum to at
most 2k, so with majority forcing each to be at least 3 no arc lying in a
triangle can reach support 5.  If every arc of a host lies in at least one
directed triangle, then margin <= 3 and plain majority are the same question on
that host, and a refutation at the tighter margin is a refutation at the looser
one.

The paper states the stronger form for the deleted-vertex hosts of Section 3.4:
every arc of P_q - v lies in at least (q-3)/4 directed triangles.  That is the
claim this file checks, host by host, from the shipped bit strings.

    usage: triangles_per_arc.py FILE.bits [FILE.bits ...] [--expect-paley-minus]

`--expect-paley-minus` reads q from each filename of the form pQ_minus1v.bits
and requires the measured minimum to equal (q-3)/4 exactly, exiting non-zero on
any mismatch.  Without it the counts are reported and nothing is asserted.

Replaces an earlier `tri_per_arc.py`, which carried its host list hard-coded in
the source and so could not be pointed at a new host -- which is how the
Paley(31) - v sweep came to have no triangle count of its own.
"""
import os
import re
import sys


def load_bits(path):
    """Upper-triangle bit string -> adjacency matrix.  A[i][j] = 1 means i -> j."""
    b = "".join(open(path).read().split())
    n = int(round((1 + (1 + 8 * len(b)) ** .5) / 2))
    if n * (n - 1) // 2 != len(b):
        sys.exit("%s: %d bits is not C(n,2) for any n" % (path, len(b)))
    A = [[0] * n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if b[k] == '1':
                A[i][j] = 1
            else:
                A[j][i] = 1
            k += 1
    return A, n


def per_arc(A, n):
    """min, max and total directed triangles over the arcs."""
    lo, hi, tot = None, 0, 0
    for i in range(n):
        for j in range(n):
            if not A[i][j]:
                continue
            t = sum(1 for w in range(n) if A[j][w] and A[w][i])
            lo = t if lo is None else min(lo, t)
            hi = max(hi, t)
            tot += t
    return lo, hi, tot // 3


def main(paths, assert_paley):
    bad = 0
    print("%-24s %4s %6s %6s %9s  %s"
          % ("host", "n", "min", "max", "triangles", "verdict"))
    for p in paths:
        A, n = load_bits(p)
        lo, hi, tot = per_arc(A, n)
        note = ""
        m = re.match(r'p(\d+)_minus1v\.bits$', os.path.basename(p))
        if assert_paley:
            if not m:
                note = "FAIL: --expect-paley-minus, but the name is not pQ_minus1v.bits"
                bad += 1
            else:
                q = int(m.group(1))
                want = (q - 3) // 4
                if (q - 3) % 4:
                    note = "FAIL: q = %d is not 3 mod 4" % q
                    bad += 1
                elif lo != want:
                    note = "FAIL: min is %d, (q-3)/4 = %d at q = %d" % (lo, want, q)
                    bad += 1
                else:
                    note = "min = (q-3)/4 = %d at q = %d" % (want, q)
        if lo == 0:
            note = (note + "; " if note else "") + \
                   "FAIL: an arc lies in NO triangle, so margin<=3 is a real restriction"
            bad += 1
        elif not note:
            note = "every arc in >= 1 triangle, so margin<=3 == majority here"
        print("%-24s %4d %6d %6d %9d  %s"
              % (os.path.basename(p), n, lo, hi, tot, note))
    print("\n%s: %d problem(s)" % ("FAILED" if bad else "OK", bad))
    return 1 if bad else 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--expect-paley-minus']
    if not args:
        sys.exit(__doc__)
    sys.exit(main(args, '--expect-paley-minus' in sys.argv[1:]))
