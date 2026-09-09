#!/usr/bin/env python3
"""Emit the .bits file for Paley(q) minus a set of vertices.

Convention (must match make_bits() in kinduce*.c): upper-triangle only, row
major, bit 1 at position (a,b) with a<b meaning a beats b.  Surviving vertices
are relabelled 0..n-1 in increasing order of their original label.
Paley: i beats j iff (j-i) mod q is a non-zero quadratic residue.

  python3 make_paley_minus.py 19 0            > p19_minus1v.bits
  python3 make_paley_minus.py 23 0            > p23_minus1v.bits
  python3 make_paley_minus.py 23 0 1          > p23_minus2v.bits
  python3 make_paley_minus.py 23 --selfcheck  (verify against tracked files)
"""
import sys

def paley_minus(q, drop):
    QR = {(x * x) % q for x in range(1, q)}
    vs = [x for x in range(q) if x not in drop]
    n = len(vs)
    out = []
    for a in range(n):
        for b in range(a + 1, n):
            out.append('1' if (vs[b] - vs[a]) % q in QR else '0')
    return ''.join(out)

if __name__ == '__main__':
    q = int(sys.argv[1])
    if '--selfcheck' in sys.argv:
        ok = True
        for path, drop in (('p23_minus1v.bits', {0}), ('p23_minus2v.bits', {0, 1})):
            try:
                have = open(path).read().strip()
            except FileNotFoundError:
                print(f"{path}: MISSING"); ok = False; continue
            want = paley_minus(23, drop)
            same = have == want
            ok &= same
            print(f"{path}: {'OK' if same else 'MISMATCH'} ({len(have)} bits on file, {len(want)} expected)")
        sys.exit(0 if ok else 1)
    drop = set(map(int, sys.argv[2:]))
    print(paley_minus(q, drop))
