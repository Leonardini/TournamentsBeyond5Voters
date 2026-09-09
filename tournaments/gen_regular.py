#!/usr/bin/env python3
"""Random regular tournaments by 3-cycle reversal.

Reversing a directed triangle a->b->c->a to a->c->b->a leaves every out-degree
unchanged (each of a,b,c loses one out-arc and gains one), so the chain stays
inside the regular tournaments; it is known to connect them all.  We seed with
the rotational tournament  i->j  iff  (j-i) mod n in {1..(n-1)/2}, which is
regular but highly symmetric (|Aut| >= n), then mix to destroy that symmetry.
Mixing steps are a difficulty dial: 0 = the symmetric seed, large = generic.
"""
import random, sys

def rotational(n):
    h = (n - 1) // 2
    S = set(range(1, h + 1))
    return [[1 if (j - i) % n in S else 0 for j in range(n)] for i in range(n)]

def mix(adj, n, steps, rng):
    done = 0
    while done < steps:
        a, b, c = rng.sample(range(n), 3)
        if adj[a][b] and adj[b][c] and adj[c][a]:
            adj[a][b] = adj[b][c] = adj[c][a] = 0
            adj[b][a] = adj[c][b] = adj[a][c] = 1
            done += 1
    return adj

def bits(adj, n):
    return ''.join('1' if adj[i][j] else '0' for i in range(n) for j in range(i + 1, n))

def check(adj, n):
    h = (n - 1) // 2
    for i in range(n):
        assert sum(adj[i]) == h, f"vertex {i} out-degree {sum(adj[i])} != {h}"
        for j in range(n):
            if i != j: assert adj[i][j] + adj[j][i] == 1, "not a tournament"

if __name__ == '__main__':
    n = int(sys.argv[1])
    made = []
    for steps in (0, 10, 100, 1000, 10000):
        seeds = [0] if steps == 0 else range(1, 9)
        for s in seeds:
            rng = random.Random(1000 * steps + s)
            adj = mix(rotational(n), n, steps, rng)
            check(adj, n)
            name = f"bench{n}/reg{n}_m{steps}_s{s}.bits"
            open(name, 'w').write(bits(adj, n))
            made.append(name)
    print(f"wrote {len(made)} regular tournaments on {n} vertices (out-degree {(n-1)//2}), verified")
