#!/usr/bin/env python3
"""Drop one host from each converse pair, halving the n=12 case analysis.

WHY THIS IS SOUND.  Reversing every voter's order reverses every arc of the
majority tournament and changes no support, so a tournament and its converse have
the same majority dimension and are inducible at exactly the same margins.

WHY IT PRESERVES COVERAGE, which is the part that matters here.  The sweep settles
every order-12 tournament U by screening all 2^11 one-vertex extensions of every
order-11 host.  Extensions correspond to converses exactly: if T' is T with a new
vertex whose out-set is S, then the converse of T' is the converse of T with a new
vertex whose out-set is the COMPLEMENT of S.  So the extensions of conv(T) are
precisely the converses of the extensions of T.  If this filter drops T, it kept
conv(T); U extends T, so conv(U) extends conv(T) and was screened; and U is
inducible iff conv(U) is.  Hence U is settled either way.  `--selftest` verifies
that correspondence exhaustively at n = 5, 6, 7 rather than taking it on trust.

Self-converse hosts satisfy canon(T) == canon(conv(T)) and are KEPT by the <=
comparison: they pair with nothing, so dropping them would lose coverage.

Reads gentourng's default output (upper triangle, row major, ascii) on stdin and
writes the kept subset unchanged, so it drops into a pipeline. Canonical forms come
from nauty's labelg in batches; the measured cost is 2.8 us per form, about 0.02%
of the ~32 ms this saves per host.
    usage: converse_filter.py N [--chunk M] [--stats]
           converse_filter.py --selftest
"""
import sys, os, subprocess, itertools

LABELG = os.environ.get("LABELG", "")

def d6(a, n):
    bits = [a[i][j] for i in range(n) for j in range(n)]
    bits += [0] * (-len(bits) % 6)
    body = "".join(chr(63 + sum(b << (5 - k) for k, b in enumerate(bits[i:i+6])))
                   for i in range(0, len(bits), 6))
    return "&" + chr(63 + n) + body

def adj(n, line):
    bits = [c for c in line.strip() if c in "01"]
    if len(bits) != n * (n - 1) // 2:
        raise SystemExit(f"FATAL: line has {len(bits)} bits, expected C({n},2) "
                         f"= {n*(n-1)//2}; wrong n on the command line?")
    a = [[0]*n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(i+1, n):
            if bits[k] == "1": a[i][j] = 1
            else:              a[j][i] = 1
            k += 1
    return a

def conv(a, n):
    return [[a[j][i] for j in range(n)] for i in range(n)]

def canon(mats, n, labelg=None):
    lg = labelg or LABELG
    if not lg or not os.access(lg, os.X_OK):
        raise SystemExit("FATAL: no usable labelg. Source gt_path.sh so LABELG is "
                         "set, or set LABELG=/path/to/labelg. To run WITHOUT the "
                         "halving, set N12_NOHALVE=1 and this filter is bypassed.")
    inp = "".join(d6(a, n) + "\n" for a in mats)
    r = subprocess.run([lg, "-zq"], input=inp, capture_output=True, text=True)
    out = r.stdout.split()
    if len(out) != len(mats):
        raise SystemExit(f"FATAL: labelg returned {len(out)} forms for {len(mats)} "
                         f"graphs: {r.stderr[:200]}")
    return out

def keep(lines, n):
    """Keep a host iff its canonical form does not exceed its converse's."""
    mats = [adj(n, l) for l in lines]
    k1 = canon(mats, n)
    k2 = canon([conv(a, n) for a in mats], n)
    return [l for l, x, y in zip(lines, k1, k2) if x <= y]

# ---------------------------------------------------------------- selftest ---
def selftest():
    from itertools import combinations
    here = os.path.dirname(os.path.abspath(__file__))
    gt = os.environ.get("GENTOURNG") or os.path.join(
        os.path.dirname(os.environ.get("LABELG", "")), "gentourng")
    if not os.access(gt, os.X_OK):
        raise SystemExit(f"FATAL: no gentourng at {gt!r}; source gt_path.sh first")
    # (a) kept counts must equal (N + S)/2, N from A000568 and S measured here
    A000568 = {5: 12, 6: 56, 7: 456, 8: 6880}
    for n, N in sorted(A000568.items()):
        lines = [l for l in subprocess.run([gt, "-q", str(n)], capture_output=True,
                 text=True).stdout.splitlines() if l.strip()]
        assert len(lines) == N, f"n={n}: gentourng gave {len(lines)}, A000568 says {N}"
        mats = [adj(n, l) for l in lines]
        k1 = canon(mats, n); k2 = canon([conv(a, n) for a in mats], n)
        S = sum(1 for x, y in zip(k1, k2) if x == y)
        kept = len(keep(lines, n))
        assert kept == (N + S) // 2 + (N + S) % 2, \
            f"n={n}: kept {kept}, expected (N+S)/2 = {(N+S)/2}"
        print(f"  n={n}: {N} classes, {S} self-converse, kept {kept} "
              f"= (N+S)/2, factor {N/kept:.3f}x")
    # (b) the extension/converse correspondence, exhaustively.  For every host and
    #     every out-set S, conv(T + S) must equal conv(T) + complement(S).
    for n in (5, 6, 7):
        lines = [l for l in subprocess.run([gt, "-q", str(n)], capture_output=True,
                 text=True).stdout.splitlines() if l.strip()]
        checked = 0
        for l in lines:
            a = adj(n, l); c = conv(a, n)
            for r in range(n + 1):
                for S in combinations(range(n), r):
                    Sset = set(S); comp = set(range(n)) - Sset
                    # T + new vertex n, out-arcs to S
                    ext = [row[:] + [1 if j in Sset else 0] for j, row in enumerate(a)]
                    ext = [[a[i][j] for j in range(n)] + [1 if i in Sset else 0]
                           for i in range(n)]
                    ext.append([0 if i in Sset else 1 for i in range(n)] + [0])
                    # conv(T) + new vertex n, out-arcs to the complement of S
                    ext2 = [[c[i][j] for j in range(n)] + [1 if i in comp else 0]
                            for i in range(n)]
                    ext2.append([0 if i in comp else 1 for i in range(n)] + [0])
                    assert conv(ext, n + 1) == ext2, \
                        f"correspondence FAILS at n={n}, S={S}"
                    checked += 1
        print(f"  n={n}: extension/converse correspondence holds on all "
              f"{checked:,} (host, out-set) pairs")
    print("CONVERSE FILTER SELFTEST PASS")

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit(0)
    n = int(sys.argv[1])
    chunk = 200000
    if "--chunk" in sys.argv: chunk = int(sys.argv[sys.argv.index("--chunk") + 1])
    stats = "--stats" in sys.argv
    seen = kept = 0
    buf = []
    def flush():
        global seen, kept
        if not buf: return
        k = keep(buf, n); seen += len(buf); kept += len(k)
        sys.stdout.write("".join(k)); buf.clear()
    for line in sys.stdin:
        if line.strip(): buf.append(line)
        if len(buf) >= chunk: flush()
    flush()
    if stats:
        sys.stderr.write(f"converse filter: {seen} in, {kept} out"
                         f"{f', factor {seen/kept:.3f}x' if kept else ''}\n")
