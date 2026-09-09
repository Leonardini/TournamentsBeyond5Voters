#!/usr/bin/env python3
"""What is the LARGEST possible min-3-cycles-per-arc on n vertices?

min <= mean, and mean = 3T/C(n,2) where T = C(n,3) - sum_v C(d_v,2) is maximised by making the
out-degree sequence as equal as possible.  So an upper bound on the mean is an upper bound on
min, for EVERY tournament on n vertices -- no regularity assumed.

If the hypothesis "majority infeasible => min >= 6" holds, then every n whose ceiling is < 6
admits no 5-non-inducible tournament at all.
"""
import math

print(f"{'n':>3} {'max 3-cycles T':>15} {'arcs':>6} {'max mean = 3T/C':>17} {'ceiling on min':>15}")
first6 = None
for n in range(12, 28):
    # out-degrees as equal as possible: n odd -> all (n-1)/2 ; n even -> half n/2-1, half n/2
    if n % 2:
        degs = [(n - 1) // 2] * n
    else:
        degs = [n // 2 - 1] * (n // 2) + [n // 2] * (n // 2)
    assert sum(degs) == n * (n - 1) // 2, "degree sum must equal the number of arcs"
    T = math.comb(n, 3) - sum(math.comb(d, 2) for d in degs)
    C = math.comb(n, 2)
    mean = 3 * T / C
    ceil_min = math.floor(mean)
    if first6 is None and ceil_min >= 6:
        first6 = n
    print(f"{n:>3} {T:>15} {C:>6} {mean:>17.4f} {ceil_min:>15}")
print(f"\nSmallest n whose ceiling reaches 6: {first6}")
print("So on fewer than that many vertices NO tournament can have every arc in >= 6 cyclic")
print("triangles, and the hypothesis would forbid any 5-non-inducible tournament there.")
