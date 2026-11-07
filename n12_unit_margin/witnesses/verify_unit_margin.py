#!/usr/bin/env python3
"""Check unit-margin five-voter witnesses against a list of tournaments.

The witness file has one line per tournament, "<o1> <o2> <o3> <o4> <o5>",
each <ok> a linear order of the vertices 0..n-1, top to bottom, one character
per vertex.  Line k is the profile for line k of the tournament list, a
bitstring in McKay's upper-triangle order (bit 1 <=> i -> j, for i < j).
For every line this program

  1. checks that each <ok> is a permutation of 0..n-1;
  2. counts, for every pair i < j, the voters ranking i above j, and requires
     exactly 3 or exactly 2 (a 3:2 split, margin one);
  3. builds the majority tournament from these counts and requires it to equal
     the listed tournament, vertex for vertex (no relabelling).

The two files must have the same number of lines, and that number must equal
--expect.  Any failure stops the program with the line number and the reason.
Standard library only; it shares no code with the search (cert_m1k5.c) or
the converter (m1k5_profile.c).

Usage:
  python3 verify_unit_margin.py N WITNESSES TOURNAMENTS --expect COUNT
WITNESSES and TOURNAMENTS may be plain text or .xz; TOURNAMENTS "-" is stdin.
"""
import argparse
import lzma
import sys
import time
from itertools import combinations, zip_longest


def open_text(path):
    if path == "-":
        return sys.stdin
    if path.endswith(".xz"):
        return lzma.open(path, "rt")
    return open(path)


def fail(lineno, reason, line):
    sys.exit(f"VERIFY FAIL at line {lineno:,} ({reason}): {line.rstrip()}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("n", type=int)
    ap.add_argument("witnesses")
    ap.add_argument("tournaments")
    ap.add_argument("--expect", type=int, required=True,
                    help="number of tournaments the list must hold")
    args = ap.parse_args()
    n = args.n
    if not 3 <= n <= 10:
        sys.exit("n must be between 3 and 10 (one character per vertex)")
    pairs = list(combinations(range(n), 2))
    vertex_set = {str(v) for v in range(n)}

    count = 0
    t0 = time.time()
    with open_text(args.witnesses) as wf, open_text(args.tournaments) as tf:
        for lineno, (wline, tline) in enumerate(zip_longest(wf, tf), start=1):
            if wline is None or tline is None:
                sys.exit(f"VERIFY FAIL: line counts differ at line {lineno:,} "
                         f"({'tournament' if wline is None else 'witness'} file is longer)")
            orders = wline.split()
            if len(orders) != 5:
                fail(lineno, "expected five orders", wline)
            positions = []
            for order in orders:
                if len(order) != n or set(order) != vertex_set:
                    fail(lineno, "an order is not a permutation of the vertices", wline)
                pos = [0] * n
                for rank, v in enumerate(order):
                    pos[int(v)] = rank
                positions.append(pos)
            majority = []
            for i, j in pairs:
                above = sum(1 for pos in positions if pos[i] < pos[j])
                if above == 3:
                    majority.append("1")
                elif above == 2:
                    majority.append("0")
                else:
                    fail(lineno, f"pair ({i},{j}) is split {above}:{5 - above}, not 3:2", wline)
            if "".join(majority) != tline.strip():
                fail(lineno, f"majority is not the listed tournament {tline.strip()}", wline)
            count += 1
            if count % 200000 == 0:
                print(f"[{time.strftime('%H:%M:%S')}] {count:,} lines verified "
                      f"({time.time() - t0:.0f} s)", file=sys.stderr, flush=True)
    if count != args.expect:
        sys.exit(f"VERIFY FAIL: {count:,} tournaments, expected {args.expect:,}")
    print(f"n={n}: verified {count:,} unit-margin five-voter profiles; every majority "
          f"is its listed tournament and every arc is carried exactly 3:2")


if __name__ == "__main__":
    main()
