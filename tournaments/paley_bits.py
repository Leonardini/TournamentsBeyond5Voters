#!/usr/bin/env python3
"""Generate the Paley tournament on q vertices as a .bits file, and cross-check
the generator against every p{q}_paley.bits already on file.

Nothing is hard-coded per q: adjacency, bit count, out-degree and triangle load
are all computed from q.  The known-answer test is what makes a NEW file
trustworthy -- a generator that reproduces the existing hosts bit for bit is the
same generator that produced them.

Scope of the bit-for-bit test.  For PRIME q the vertex labelling is canonical
(vertex i = the field element i, arc i -> j iff j - i is a quadratic residue mod
q), so the file is reproducible exactly.  For a prime POWER (q = 27 here) the
labelling depends on how GF(p^k) was enumerated, and the on-file p27_paley.bits
came from the doubly-regular census, not from this script; there we check the
defining structure instead of the bits.  Both checks are reported separately so
neither can be mistaken for the other.
"""
import sys, os, glob, re

def is_prime(m):
    if m < 2: return False
    d = 2
    while d * d <= m:
        if m % d == 0: return False
        d += 1
    return True

def paley_bits(q):
    """Upper-triangle bit string over pairs i<j in row-major order, 1 iff i -> j.
    Prime q only -- see the module docstring."""
    assert q % 4 == 3, f"Paley(q) is a tournament only for q = 3 mod 4, got {q}"
    assert is_prime(q), f"q = {q} is not prime; this labelling needs GF(p^k)"
    qr = {(x * x) % q for x in range(1, q)}
    return "".join("1" if (j - i) % q in qr else "0"
                   for i in range(q) for j in range(i + 1, q))

def adj_from_bits(n, bits):
    a = [[0] * n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if bits[k] == "1": a[i][j] = 1
            else:              a[j][i] = 1
            k += 1
    assert k == len(bits), f"bit string has {len(bits)} bits, expected {k}"
    return a

def check_structure(q, bits, path):
    """Every property that DEFINES Paley(q) up to isomorphism: C(q,2) bits,
    regular of out-degree (q-1)/2, and doubly regular -- every arc in exactly
    (q-3)/4 cyclic triangles.  All three derived from q, none written down."""
    assert len(bits) == q * (q - 1) // 2, \
        f"{path}: {len(bits)} bits, expected C({q},2) = {q*(q-1)//2}"
    a = adj_from_bits(q, bits)
    deg = [sum(a[i]) for i in range(q)]
    assert min(deg) == max(deg) == (q - 1) // 2, \
        f"{path}: out-degrees {min(deg)}..{max(deg)}, expected {(q-1)//2}"
    loads = [sum(a[i][w] * a[w][j] for w in range(q))
             for i in range(q) for j in range(q) if a[i][j]]
    assert min(loads) == max(loads) == (q - 3) // 4, \
        f"{path}: triangle loads {min(loads)}..{max(loads)}, " \
        f"expected (q-3)/4 = {(q-3)//4}"
    return (q - 1) // 2, (q - 3) // 4

def selftest(here, quiet=False):
    exact, struct = 0, 0
    for path in sorted(glob.glob(os.path.join(here, "p*_paley.bits")),
                       key=lambda p: int(re.findall(r"\d+", os.path.basename(p))[0])):
        m = re.fullmatch(r"p(\d+)_paley\.bits", os.path.basename(path))
        if not m: continue
        q = int(m.group(1))
        want = open(path).read().strip()
        deg, load = check_structure(q, want, path)
        if is_prime(q):
            got = paley_bits(q)
            if got != want:
                d = next((i for i, (x, y) in enumerate(zip(got, want)) if x != y), None)
                raise SystemExit(f"FAIL {path}: generator disagrees, "
                                 f"first differing bit at index {d}")
            exact += 1
            tag = "bit-for-bit + structure"
        else:
            struct += 1
            tag = "structure only (prime power, labelling not canonical)"
        if not quiet:
            print(f"  OK  Paley({q:>2}): {len(want):>4} bits, out-degree {deg}, "
                  f"triangle load {load} -- {tag}")
    if exact < 2:
        raise SystemExit(f"FAIL: only {exact} prime reference host(s) reproduced "
                         "bit for bit -- the known-answer test is vacuous")
    if not quiet:
        print(f"SELFTEST PASS: {exact} prime hosts reproduced bit for bit, "
              f"{struct} prime-power host(s) structurally verified")

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) == 1 or sys.argv[1] == "--selftest":
        selftest(here)
    else:
        q = int(sys.argv[1])
        selftest(here, quiet=True)
        bits = paley_bits(q)
        out = os.path.join(here, f"p{q}_paley.bits")
        if os.path.exists(out):
            assert open(out).read().strip() == bits, f"{out} exists and DIFFERS"
            print(f"{out} already on file and identical to the generator")
        else:
            open(out, "w").write(bits + "\n")
            print(f"wrote {out}")
        deg, load = check_structure(q, bits, out)
        print(f"Paley({q}): {len(bits)} bits, out-degree {deg}, triangle load {load}")
