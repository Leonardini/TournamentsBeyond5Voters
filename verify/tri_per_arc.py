#!/usr/bin/env python3
"""min/max 3-cycles per arc for every case we hold a verdict on, against the hypothesis:

   margin-1 infeasible  =>  min >= 5   (necessary, NOT sufficient -- sufficiency is refuted)
   majority  infeasible  =>  min >= 6

The test is only whether an INFEASIBLE case falls BELOW its threshold; nothing is claimed
about feasible ones, which the hypothesis does not constrain.
"""
import numpy as np


def load_bits(p):
    b = "".join(open(p).read().split())
    n = int(round((1 + (1 + 8 * len(b)) ** .5) / 2))
    assert n * (n - 1) // 2 == len(b), f"{p}: {len(b)} bits is not C(n,2)"
    A = np.zeros((n, n), int)
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            A[i, j] = int(b[k])
            A[j, i] = 1 - A[i, j]
            k += 1
    return A


def paley(q):
    sq = {(x * x) % q for x in range(1, q)}
    return np.array([[1 if i != j and (j - i) % q in sq else 0
                      for j in range(q)] for i in range(q)])


def stats(A):
    n = A.shape[0]
    t = [int((A[v] & A[:, u]).sum()) for u in range(n) for v in range(n) if A[u, v]]
    return n, min(t), max(t), sum(t) // 3


CASES = [
    ("Paley(19)", paley(19),                     "INFEASIBLE", "feasible"),
    ("dr19_g2",   load_bits("dr19_g2.bits"),     "INFEASIBLE", "feasible"),
    ("Paley(23)", paley(23),                     "INFEASIBLE", "INFEASIBLE"),
    ("Paley(31)", paley(31),                     None,         "INFEASIBLE"),
    ("Paley(43)", paley(43),                     None,         "INFEASIBLE"),
    ("P19 - v",   load_bits("p19_minus1v.bits"), "feasible",   "feasible"),
    ("P23 - v",   load_bits("p23_minus1v.bits"), "INFEASIBLE", "feasible"),
    ("P43 - v",   load_bits("p43_minus1v.bits"), None,         "INFEASIBLE"),
]

hdr = f"{'case':>11} {'n':>3} {'min':>4} {'max':>4} {'3cyc':>6}  {'margin-1':>11} {'majority':>11}  test"
print(hdr)
for name, A, m1, mj in CASES:
    n, lo, hi, nc = stats(A)
    bad = []
    if m1 == "INFEASIBLE" and lo < 5:
        bad.append(f"margin-1 infeasible but min={lo}<5")
    if mj == "INFEASIBLE" and lo < 6:
        bad.append(f"majority infeasible but min={lo}<6")
    tag = "** REFUTED: " + "; ".join(bad) if bad else "consistent"
    print(f"{name:>11} {n:>3} {lo:>4} {hi:>4} {nc:>6}  {str(m1):>11} {str(mj):>11}  {tag}")
