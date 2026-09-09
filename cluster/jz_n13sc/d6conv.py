#!/usr/bin/env python3
"""digraph6 -> upper-triangular tournament bit string (kinduce --batch format).

digraph6: '&' then N(n) then R(x) with x the n^2 adjacency bits, row by row.
Each data byte carries 6 bits, most significant first, offset by 63.

Asserts the result really is a TOURNAMENT (exactly one of A[i][j], A[j][i], no
loops).  A silent misparse would otherwise feed the solver well-formed garbage.
"""
import sys

def decode(line):
    s = line.strip()
    assert s.startswith('&'), f"not digraph6: {s[:10]}"
    s = s[1:]
    n = ord(s[0]) - 63
    assert 0 <= n < 63, f"unsupported n encoding: {n}"
    bits = []
    for ch in s[1:]:
        v = ord(ch) - 63
        for b in range(5, -1, -1):
            bits.append((v >> b) & 1)
    A = [[0]*n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(n):
            A[i][j] = bits[k]; k += 1
    for i in range(n):
        assert A[i][i] == 0, "loop present"
        for j in range(i+1, n):
            assert A[i][j] + A[j][i] == 1, f"not a tournament at ({i},{j})"
    return n, A

n_seen = None
out = []
for line in open(sys.argv[1]):
    if not line.strip():
        continue
    n, A = decode(line)
    n_seen = n
    out.append(''.join('1' if A[i][j] else '0'
                       for i in range(n) for j in range(i+1, n)))
sys.stderr.write(f"  {sys.argv[1]}: {len(out)} tournaments on {n_seen} vertices, "
                 f"{len(out[0])} bits each (expect {n_seen*(n_seen-1)//2})\n")
assert len(out[0]) == n_seen*(n_seen-1)//2
print('\n'.join(out))
