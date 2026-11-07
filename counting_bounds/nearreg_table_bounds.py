#!/usr/bin/env python3
"""nearreg_bounds.py — does using semi-regular (near-regular, even-n) tournaments
tighten the extended Table 1?

Bijection (proved): a near-regular tournament on even n (scores (n/2)^{n/2}(n/2-1)^{n/2})
extends UNIQUELY to a regular tournament on n+1 by adding a vertex v with v->(high set),
(low set)->v; conversely deleting any vertex of a regular tournament on n+1 gives a
near-regular tournament on n.  Hence  #near-regular(n) = RT(n+1).

Counting witness:
  * odd n, regular class: completion unique from the k-1 orders alone (constant target),
      #{k-inducible regular} <= M(n,k-1);  witness if RT(n) > M(n,k-1).
  * even n, near-regular class: the target out-degree per vertex is NOT fixed by the
      orders (each vertex may be high or low), so per fixed high/low partition the
      completion is unique but there are C(n,n/2) partitions:
      #{k-inducible near-regular} <= C(n,n/2) * M(n,k-1);
      witness if RT(n+1) > C(n,n/2) * M(n,k-1).
  RT(.) lower-bounded by Schrijver: RT(m) >= C(m-1,(m-1)/2)^m / 2^{C(m,2)} (m odd).
"""
from math import comb, factorial, log2

def M(n, j):                       # # of j-multisets of the n! linear orders
    return comb(factorial(n) + j - 1, j)

def schrijver(m):                  # Schrijver lower bound on RT(m), m odd (exact int)
    h = (m - 1) // 2
    return comb(m - 1, h) ** m // (1 << (m * (m - 1) // 2))

def log2_schrijver(m):
    h = (m - 1) // 2
    return m * log2(comb(m - 1, h)) - m * (m - 1) / 2

def odd_witness(n, k):             # regular class, n odd
    return schrijver(n) > M(n, k - 1)

def even_witness(n, k):            # near-regular class, n even
    return schrijver(n + 1) > comb(n, n // 2) * M(n, k - 1)

def even_witness_naive(n, k):      # if one (wrongly) ignored the partition factor
    return schrijver(n + 1) > M(n, k - 1)

def first(pred, k, start, step):
    n = start
    while not pred(n, k): n += step
    for t in range(1, 6): assert pred(n + t * step, k), (k, n)
    return n

# ---- brute-force verification of the bijection at small even n ----
def brute_nearreg(n):
    import itertools
    cnt = 0
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    target = sorted([n // 2] * (n // 2) + [n // 2 - 1] * (n // 2))
    for bitsel in range(1 << len(pairs)):
        outdeg = [0] * n
        for b, (i, j) in enumerate(pairs):
            if bitsel >> b & 1: outdeg[i] += 1
            else: outdeg[j] += 1
        if sorted(outdeg) == target: cnt += 1
    return cnt

RT = {1: 1, 3: 2, 5: 24, 7: 2640, 9: 3230080, 11: 48251508480}   # A007079

if __name__ == "__main__":
    print("== bijection check  #near-regular(n) == RT(n+1) ==")
    for n in (2, 4, 6):
        b = brute_nearreg(n)
        print(f"n={n}: brute near-regular={b}, RT({n+1})={RT[n+1]}  {'OK' if b==RT[n+1] else 'MISMATCH'}")

    print("\n== smallest counting witness by parity (rigorous, Schrijver LB) ==")
    print(f"{'k':>3} {'odd(reg)':>9} {'even(near-reg)':>15} {'even_naive':>11} {'best n^T(k)+1':>13} {'parity':>7}")
    paper = {3:18,5:41,7:66,9:93,11:122,13:152,15:183,17:216,19:249,21:282}
    for k in range(3, 23, 2):
        no = first(odd_witness, k, 3, 2)
        ne = first(even_witness, k, 4, 2)
        nen = first(even_witness_naive, k, 4, 2)
        best = min(no, ne)
        parity = "odd" if no <= ne else "EVEN"
        print(f"{k:>3} {no:>9} {ne:>15} {nen:>11} {best:>13} {parity:>7}")

    print("\n== bit-margin of even vs odd at the odd witness n (k=5) ==")
    k = 5
    no = first(odd_witness, k, 3, 2)
    for n in (no - 3, no - 1):     # odd witness and the even size just below
        if n % 2 == 1:
            lhs, rhs = log2_schrijver(n), log2(M(n, k - 1))
            print(f"n={n} (odd,reg):   Schrijver-RT={lhs:8.1f}  vs  M={rhs:8.1f}  "
                  f"slack={lhs-rhs:+.1f} bits")
        else:
            lhs = log2_schrijver(n + 1)
            rhs = log2(comb(n, n // 2)) + log2(M(n, k - 1))
            rhs0 = log2(M(n, k - 1))
            print(f"n={n} (even,nr):  Schrijver-RT(n+1)={lhs:8.1f}  vs  C+M={rhs:8.1f}  "
                  f"slack={lhs-rhs:+.1f} bits  (partition factor log2 C(n,n/2)={rhs-rhs0:.1f})")
