#!/usr/bin/env python3
"""verify_paley47_order.py -- the lower bound MAS(P_47) >= 658 of the Paley table (standard library only).

P_47 has vertices 0..46 and an arc u -> v whenever v - u is a nonzero square modulo 47.  The file
paley47_order658.txt gives a linear order of the vertices (the line starting 'ORDER:', first vertex first).
The script checks that it lists every vertex once and counts the arcs it makes forward; the paper's
table needs at least 658 of the C(47, 2) = 1081 arcs, so alpha*(P_47) >= 658/1081 = 14/23.
Any failure stops it with an AssertionError.  Usage: verify_paley47_order.py [order-file]
"""
import sys
from fractions import Fraction
from pathlib import Path

Q = 47
CLAIM = 658


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "paley47_order658.txt"
    lines = [l for l in path.read_text().splitlines() if l.startswith("ORDER:")]
    assert len(lines) == 1, "expected exactly one line starting 'ORDER:'"
    order = [int(x) for x in lines[0].split()[1:]]
    assert sorted(order) == list(range(Q)), f"the order is not a permutation of 0..{Q - 1}"
    squares = {(x * x) % Q for x in range(1, Q)}
    pos = {v: i for i, v in enumerate(order)}
    arcs = [(u, v) for u in range(Q) for v in range(Q) if u != v and (v - u) % Q in squares]
    assert len(arcs) == Q * (Q - 1) // 2, "P_47 is not a tournament"
    fwd = sum(pos[u] < pos[v] for u, v in arcs)
    assert fwd >= CLAIM, f"the order makes {fwd} arcs forward, fewer than {CLAIM}"
    print(f"P_{Q}: the order makes {fwd} of {len(arcs)} arcs forward, so MAS >= {fwd} "
          f"and alpha* >= {Fraction(fwd, len(arcs))}")


if __name__ == "__main__":
    main()
