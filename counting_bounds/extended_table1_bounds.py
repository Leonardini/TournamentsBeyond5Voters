#!/usr/bin/env python3
"""Extended Table 1: exact counting + the all-odd-k counting theorem of the paper (regular completion-
uniqueness: k-inducible regular tournament determined by a (k-1)-multiset of orders)."""
from math import comb, factorial, log2

def multisets(n, j):
    return comb(factorial(n) + j - 1, j)

def their_violated(n, k):   # Lemma 2 of [2] (Fiol relaxation)
    return (1 << (n * (n - 1) // 2)) * factorial(k) > (1 << k) * factorial(n) ** k

def exact_violated(n, k):   # exact multiset count, all tournaments
    return (1 << (n * (n - 1) // 2)) > multisets(n, k)

def schrijver_log2(n):      # log2 of Schrijver lower bound on RT(n), n odd
    m = (n - 1) // 2
    return n * (log2(comb(n - 1, m)) - m)

def reg_violated(n, k):     # Schrijver(n) > C(n!+k-2, k-1)   [drop-one-voter]
    m = (n - 1) // 2
    return comb(n - 1, m) ** n > multisets(n, k - 1) << (m * n)

def first_n(pred, k, start, step):
    n = start
    while not pred(n, k): n += step
    for t in range(1, 11): assert pred(n + t * step, k), (k, n, t)
    return n

paper = {3:18, 5:41, 7:66, 9:93, 11:122, 13:152, 15:183, 17:216, 19:249, 21:282}
print(f"{'k':>3} {'paper':>6} {'exact':>6} {'reg_wit_n':>10} {'nT_reg':>7} {'best_nT':>8} {'margin_bits':>12} {'short_at_n-2':>13}")
for k in range(3, 23, 2):
    their = first_n(their_violated, k, 3, 1) - 1
    assert their == paper[k], (k, their)
    exact = first_n(exact_violated, k, 3, 1) - 1
    nreg  = first_n(reg_violated, k, 3, 2)
    mar   = schrijver_log2(nreg) - log2(multisets(nreg, k - 1))
    short = schrijver_log2(nreg - 2) - log2(multisets(nreg - 2, k - 1))
    best  = min(exact, nreg - 1)
    print(f"{k:>3} {paper[k]:>6} {exact:>6} {nreg:>10} {nreg-1:>7} {best:>8} {mar:>12.1f} {short:>13.1f}")
