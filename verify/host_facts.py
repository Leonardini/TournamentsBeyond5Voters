#!/usr/bin/env python3
"""The structural facts Section 3.2 states about the 22-vertex obstructions.

For each host: its out-degree distribution, the fewest directed triangles any
arc lies in, and whether its automorphism group is trivial; for every pair of
hosts, whether they are isomorphic and whether one is isomorphic to the
converse of the other.

Rigidity is decided with `labelg` alone.  For each vertex v the host gets one
extra vertex with a single arc into v; two such pointed digraphs are isomorphic
exactly when an automorphism of the host maps one marked vertex to the other.
So the host is rigid exactly when its n pointed versions are pairwise
non-isomorphic: every vertex is then fixed by every automorphism, and a
permutation fixing every vertex is the identity.

    usage: host_facts.py [--labelg PATH] HOST.bits [HOST.bits ...]
"""
import itertools
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from level_coverage import canon, digraph6, from_bits


def pointed(adj, v):
    n = len(adj)
    out = [row[:] + [False] for row in adj] + [[False] * (n + 1)]
    out[n][v] = True
    return out


def facts(adj):
    n = len(adj)
    outdeg = sorted(sum(r) for r in adj)
    tmin = min(sum(1 for w in range(n)
                   if (adj[u][v] and adj[v][w] and adj[w][u])
                   or (adj[v][u] and adj[u][w] and adj[w][v]))
               for u, v in itertools.combinations(range(n), 2))
    return outdeg, tmin


def main():
    args = sys.argv[1:]
    labelg = None
    if '--labelg' in args:
        i = args.index('--labelg')
        labelg = args[i + 1]
        del args[i:i + 2]
    labelg = labelg or os.environ.get('LABELG') or shutil.which('labelg')
    if not labelg:
        print('FAIL: labelg not found (set LABELG or pass --labelg)')
        return 1
    hosts = [(os.path.basename(p)[:-5],
              from_bits(''.join(c for c in open(p).read() if c in '01'))) for p in args]
    fwd = canon([digraph6(a) for _, a in hosts], labelg)
    rev = canon([digraph6([list(r) for r in zip(*a)]) for _, a in hosts], labelg)
    for (name, adj), _ in zip(hosts, fwd):
        outdeg, tmin = facts(adj)
        marks = canon([digraph6(pointed(adj, v)) for v in range(len(adj))], labelg)
        dist = {}
        for d in outdeg:
            dist[d] = dist.get(d, 0) + 1
        print('%s: n=%d, out-degrees %s, every arc in >= %d directed triangles, '
              'automorphism group %s'
              % (name, len(adj), ', '.join('%d x%d' % kv for kv in sorted(dist.items())),
                 tmin, 'TRIVIAL' if len(set(marks)) == len(adj)
                 else 'non-trivial (%d vertex orbits)' % len(set(marks))))
    for i, j in itertools.combinations(range(len(hosts)), 2):
        print('%s vs %s: %s, %s' % (hosts[i][0], hosts[j][0],
              'ISOMORPHIC' if fwd[i] == fwd[j] else 'not isomorphic',
              'one is the converse of the other' if fwd[i] == rev[j]
              else 'not converse to each other'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
