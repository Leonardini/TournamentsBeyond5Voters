#!/usr/bin/env python3
"""Emit the .bits file for the Paley tournament on GF(q), q = p^k = 3 mod 4.

WHY THIS EXISTS.  kinduce's built-in `--paley q` works in Z/q, which is only a
field when q is PRIME.  For a prime power such as q = 27 = 3^3 the squares mod
27 do not split the nonzero residues, 81 pairs get no arc in either direction,
and the result is not a tournament at all.  The engines now refuse such a q
outright; use this script and pass the result via `--bits`.

Paley(q): vertices are the elements of GF(q), and a -> b iff b - a is a nonzero
square.  Well defined exactly when q = 3 mod 4, since then -1 is a non-square.

Output convention matches make_bits() in kinduce*.c: upper triangle, row major,
bit 1 at position (a,b) with a<b meaning a beats b.  Field elements are indexed
by their base-p digit expansion, c0 + c1*p + ... + c(k-1)*p^(k-1).

  python3 make_paley_gf.py 27            > p27_paley.bits
  python3 make_paley_gf.py 27 --verify   # assert tournament + doubly regular
  python3 make_paley_gf.py --selfcheck   # agree with Z/q on primes, match p27
"""
import itertools, sys


def factor_prime_power(q):
    for p in range(2, q + 1):
        if q % p == 0:
            k, r = 0, q
            while r % p == 0:
                r //= p
                k += 1
            if r != 1:
                raise ValueError(f"{q} is not a prime power")
            return p, k
    raise ValueError(f"{q} is not a prime power")


def find_irreducible(p, k):
    """Monic irreducible of degree k over GF(p), as coefficients [c0..c(k-1)]
    for x^k = -(c0 + c1 x + ... )."""
    if k == 1:
        return []
    for tail in itertools.product(range(p), repeat=k):
        coeffs = list(tail)                      # x^k + c(k-1)x^(k-1) + ... + c0
        # irreducible over GF(p) for k<=3 iff no root (true for k=2,3 only)
        if k <= 3:
            def ev(x):
                v = pow(x, k, p)
                for i, c in enumerate(coeffs):
                    v = (v + c * pow(x, i, p)) % p
                return v % p
            if all(ev(x) != 0 for x in range(p)):
                return coeffs
        else:
            raise NotImplementedError("k > 3 needs a real irreducibility test")
    raise ValueError("no irreducible polynomial found")


class GF:
    def __init__(self, p, k):
        self.p, self.k, self.q = p, k, p ** k
        self.red = find_irreducible(p, k)        # x^k = -sum(red[i] x^i)

    def to_poly(self, n):
        c = []
        for _ in range(self.k):
            c.append(n % self.p)
            n //= self.p
        return c

    def to_int(self, c):
        n = 0
        for i in range(self.k - 1, -1, -1):
            n = n * self.p + (c[i] % self.p)
        return n

    def sub(self, a, b):
        A, B = self.to_poly(a), self.to_poly(b)
        return self.to_int([x - y for x, y in zip(A, B)])

    def mul(self, a, b):
        if self.k == 1:
            return (a * b) % self.p
        A, B = self.to_poly(a), self.to_poly(b)
        r = [0] * (2 * self.k - 1)
        for i in range(self.k):
            for j in range(self.k):
                r[i + j] += A[i] * B[j]
        for d in range(len(r) - 1, self.k - 1, -1):     # reduce top down
            if r[d] % self.p:
                coef = r[d] % self.p
                r[d] = 0
                for i, c in enumerate(self.red):
                    r[d - self.k + i] -= coef * c
        return self.to_int(r[:self.k])

    def squares(self):
        return {self.mul(a, a) for a in range(1, self.q)}


def paley_bits(q, verify=False):
    p, k = factor_prime_power(q)
    if q % 4 != 3:
        raise ValueError(f"Paley needs q = 3 mod 4, got q={q}")
    F = GF(p, k)
    QR = F.squares()
    assert len(QR) == (q - 1) // 2, f"expected {(q-1)//2} squares, got {len(QR)}"
    assert F.sub(0, 1) not in QR, "-1 must be a non-square for q = 3 mod 4"

    A = [[0] * q for _ in range(q)]
    for a in range(q):
        for b in range(q):
            if a != b and F.sub(b, a) in QR:
                A[a][b] = 1

    if verify:
        both = sum(1 for a in range(q) for b in range(a + 1, q) if A[a][b] and A[b][a])
        nei = sum(1 for a in range(q) for b in range(a + 1, q) if not A[a][b] and not A[b][a])
        assert both == 0 and nei == 0, f"not a tournament: both={both} neither={nei}"
        outd = {sum(r) for r in A}
        assert outd == {(q - 1) // 2}, f"not regular: out-degrees {outd}"
        cc = {sum(1 for w in range(q) if A[u][w] and A[v][w])
              for u in range(q) for v in range(q) if u != v}
        assert cc == {(q - 3) // 4}, f"not doubly regular: common out-neighbours {cc}"
        print(f"# GF({p}^{k}) Paley: valid tournament, regular (out-degree "
              f"{(q-1)//2}), doubly regular (lambda = {(q-3)//4})", file=sys.stderr)

    return ''.join('1' if A[a][b] else '0'
                   for a in range(q) for b in range(a + 1, q))


def selfcheck():
    ok = True
    # on PRIME q the GF build must agree with the Z/q construction kinduce uses
    for q in (7, 11, 19, 23, 31, 43):
        QR = {(x * x) % q for x in range(1, q)}
        want = ''.join('1' if (b - a) % q in QR else '0'
                       for a in range(q) for b in range(a + 1, q))
        got = paley_bits(q)
        good = got == want
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  q={q:<3} agrees with the Z/q construction")
    # and the committed q=27 file must reproduce
    try:
        have = open('p27_paley.bits').read().strip()
        got = paley_bits(27, verify=True)
        good = have == got
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  q=27 reproduces p27_paley.bits "
              f"({len(got)} bits)")
    except FileNotFoundError:
        print("  SKIP  p27_paley.bits not present")
    print()
    print("ALL CHECKS PASSED" if ok else "*** SELFCHECK FAILED ***")
    return 0 if ok else 1


if __name__ == '__main__':
    if '--selfcheck' in sys.argv:
        sys.exit(selfcheck())
    q = int(sys.argv[1])
    print(paley_bits(q, verify='--verify' in sys.argv))
