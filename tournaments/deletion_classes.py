#!/usr/bin/env python3
"""How many DISTINCT tournaments the n=20 descent actually covered.

The descent swept one file per (arc reversal, deleted vertex) pair, and the
manuscript states a count of isomorphism classes -- which is smaller, because
the reversals of a common host share that host's own deletion.  Rather than
reason about it, canonicalise every deletion with nauty's labelg and count.

The manuscript quotes only the two totals -- 319 deletions, 289 non-isomorphic.
What this script establishes, of which those are a summary:
  * each of the 15 reversals has exactly 20 distinct deletion classes, the sole
    coincidence being the two endpoints of the reversed arc, which both delete
    that arc and so return the host's own deletion -- so the other 19 are
    pairwise non-isomorphic, and that is checked, not assumed;
  * across the 15, the classes number 15 x 19 + 2 = 287, the two extras being
    h01 - v and h02 - v;
  * with h04 - v and h05 - v that is 289 distinct tournaments on 20 vertices.

    usage: deletion_classes.py            (from KInduceDFS/)
"""
import os, glob, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
LABELG = os.environ.get("LABELG")
if not LABELG:                      # same resolution as gt_path.sh, one line of it
    for c in ("/lustre/fswork/projects/rech/lia/uex76wa/nauty2_9_3/labelg",
              os.path.expanduser("~/Downloads/DownloadedSoftware/nauty2_8_6/labelg")):
        if os.access(c, os.X_OK): LABELG = c; break
assert LABELG and os.access(LABELG, os.X_OK), "set LABELG=/path/to/labelg"

# The 15 reversals are the ones that STAYED obstructions: all ten arc orbits of
# h01 (arc-rigid) and five of h02's ten (arc-semi-critical).  Derived from the
# arc-flip spectrum, not typed as a list of files.
SPECTRUM = {"h01": "UUUUUUUUUU", "h02": "USUSSUUSSU"}
FLIPS = [f"{h}_f{i:02d}" for h, row in SPECTRUM.items()
         for i, v in enumerate(row) if v == "U"]

def read_bits(p):
    b = "".join(c for c in open(p).read() if c in "01")
    n = int((1 + (1 + 8 * len(b)) ** 0.5) / 2)
    assert n * (n - 1) // 2 == len(b), (p, len(b))
    A = [[0] * n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if b[k] == "1": A[i][j] = 1
            else:           A[j][i] = 1
            k += 1
    return n, A

def d6(A):
    n = len(A)
    bits = [A[i][j] for i in range(n) for j in range(n)]
    while len(bits) % 6: bits.append(0)
    out = "&" + chr(63 + n)
    for k in range(0, len(bits), 6):
        v = 0
        for b in bits[k:k + 6]: v = v * 2 + b
        out += chr(63 + v)
    return out

def canon(rows):
    p = subprocess.run([LABELG, "-zq"], input="\n".join(rows) + "\n",
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    forms = p.stdout.split()
    assert len(forms) == len(rows), f"labelg returned {len(forms)} of {len(rows)}"
    return forms

def delete(A, v):
    ks = [i for i in range(len(A)) if i != v]
    return [[A[i][j] for j in ks] for i in ks]

host_del = {}
for h in ("h01", "h02", "h04", "h05"):
    n, A = read_bits(f"vt21_hosts/{h}.bits")
    # |Aut| = 21 acting regularly, so every deletion is isomorphic: take vertex 0
    host_del[h] = canon([d6(delete(A, 0))])[0]

seen, total = {}, 0
print(f"{len(FLIPS)} reversals that remain obstructions: {' '.join(FLIPS)}\n")
for tag in FLIPS:
    n, A = read_bits(f"vt21_arcflip/{tag}.bits")
    forms = canon([d6(delete(A, v)) for v in range(n)])
    total += len(forms)
    hc = host_del[tag[:3]]
    nhost = sum(1 for c in forms if c == hc)
    d = len(set(forms))
    print(f"  {tag}: {n} deletions -> {d} distinct, {nhost} of them {tag[:3]} - v")
    assert d == 20 and nhost == 2, f"{tag}: expected 20 distinct with 2 host-deletions"
    for c in forms: seen.setdefault(c, []).append(tag)

extra = [h for h in ("h04", "h05") if host_del[h] not in seen]
print(f"\n{total} deletions of the reversals -> {len(seen)} classes")
print(f"  + the hosts' own deletions not already among them: {' '.join(f'{h} - v' for h in extra)}")
print(f"  = {len(seen) + len(extra)} distinct tournaments on 20 vertices")
assert len(seen) == 15 * 19 + 2, f"expected 15*19+2 = 287 classes, got {len(seen)}"
assert len(seen) + len(extra) == 289
print("\nmatches Section 3.4: 15 x 19 + 2 = 287, and 289 with h04 - v and h05 - v")
