#!/usr/bin/env python3
"""Count the self-converse REGULAR tournaments on n vertices, from the regular side.

This exists to check one number by a second, independent route.  The order-13
self-converse campaign derives its regular count as

    listing total - everything order_sym emitted  =  95,458,560 - 95,447,323  =  11,237

which reads the McKay self-converse listing and applies our own imbalance filter.
That is one pipeline.  This script starts from the OTHER end -- generate every
regular tournament with nauty's gentourng and ask which of them are
self-converse, by canonicalising T and its converse with labelg and comparing --
and must land on the same 11,237.  Two pipelines sharing no input file and no
filtering code agreeing on a count is evidence; one pipeline agreeing with
itself is not.

The d6 encoder and the labelg wrapper are imported from deletion_classes rather
than rewritten, because a second copy of the adjacency-to-digraph6 convention is
exactly the kind of thing that drifts and then silently compares the wrong
graphs.

    usage: selfconverse_regular_count.py [n] [--expect N] [--chunk K]

Cost at n = 13: 1,495,297 hosts, two canonicalisations each, a few minutes on
one core.  Single-threaded on purpose so it can run beside a campaign.
"""
import os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deletion_classes import LABELG, d6, canon          # noqa: E402  (path first)

n = 13
expect = None
chunk = 20000
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--expect":
        expect = int(args[i + 1].replace(",", "")); i += 2
    elif args[i] == "--chunk":
        chunk = int(args[i + 1]); i += 2
    else:
        n = int(args[i]); i += 1
if n % 2 == 0:
    sys.exit("regular tournaments exist only in odd order")

GENTOURNG = os.environ.get("GENTOURNG")
if not GENTOURNG:
    for c in (os.path.expanduser("~/Downloads/DownloadedSoftware/nauty2_8_6/gentourng"),
              "/usr/local/bin/gentourng"):
        if os.access(c, os.X_OK):
            GENTOURNG = c
            break
if not GENTOURNG or not os.access(GENTOURNG, os.X_OK):
    sys.exit("set GENTOURNG=/path/to/gentourng (nauty)")

need = n * (n - 1) // 2
d = (n - 1) // 2
print(f"  n={n}, regular means every out-degree {d}")
print(f"  generator: {GENTOURNG} -d{d} -D{d} {n}")
print(f"  canonical: {LABELG}")


def rows_from_bits(b):
    """Upper-triangle bit string -> adjacency matrix, same convention as
    deletion_classes.read_bits: bit k is the pair (i, j) with i < j, and a 1
    means i -> j.  Kept identical on purpose; see the module docstring."""
    A = [[0] * n for _ in range(n)]
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if b[k] == "1":
                A[i][j] = 1
            else:
                A[j][i] = 1
            k += 1
    return A


def converse(A):
    return [[A[j][i] for j in range(n)] for i in range(n)]


gen = subprocess.Popen([GENTOURNG, f"-d{d}", f"-D{d}", str(n)],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

total = sc = 0
batch = []


def flush(batch):
    """Canonicalise each host and its converse in one labelg call, then compare
    pairwise.  Interleaving them keeps the two forms adjacent in the output, so
    a truncated labelg result is caught by the length assert in canon()."""
    if not batch:
        return 0
    forms = canon([s for pair in batch for s in pair])
    return sum(1 for k in range(0, len(forms), 2) if forms[k] == forms[k + 1])


for line in gen.stdout:
    b = "".join(c for c in line if c in "01")
    if len(b) != need:
        continue
    total += 1
    A = rows_from_bits(b)
    batch.append((d6(A), d6(converse(A))))
    if len(batch) >= chunk:
        sc += flush(batch)
        batch = []
        print(f"    {total:,} generated, {sc:,} self-converse so far", flush=True)
sc += flush(batch)
gen.stdout.close()
gen.wait()

print(f"  regular tournaments on {n} vertices : {total:,}")
print(f"  of which SELF-CONVERSE              : {sc:,}")

fail = False
if expect is not None:
    if sc == expect:
        print(f"  MATCHES the self-converse side's count of {expect:,}")
    else:
        print(f"  MISMATCH: this side says {sc:,}, the self-converse side says {expect:,}")
        fail = True
sys.exit(1 if fail else 0)
