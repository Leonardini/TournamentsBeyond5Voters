#!/usr/bin/env python3
"""Re-derive every row of verdicts/ledger_supplement.tsv from the package's own files.

The supplement lists the tournaments that Section 6.7 counts among those five voters can
produce but not with unit margin, and that verdicts/verdict_ledger.tsv cannot hold because
its registry indexes catalogue families: the fifteen one-arc reversals of the 21-vertex
vertex-transitive tournaments C_a and C_b that stay unit-margin obstructions, Paley(23)
minus a vertex, and Paley(23) with one arc reversed.  For each row this checks

  * the host: a tournament on n vertices whose least number of directed triangles through
    an arc is the row's tmin;
  * unit margin: the recorded search covers the whole base-state range with no witness --
    slice logs that tile [0, base_states) exactly, each RESULT UNSAT and none capped, or a
    per-base-state times file that lists every index exactly once;
  * majority: the five orders of the recorded witness induce the host, every arc carried by
    at least three voters (recomputed here; no code shared with the search);
  * for the reversals, that the run log's audited spectrum marks that arc orbit `U`, and
    that the arc-flip sweep's own verdicts.tsv records the verified majority witness;
  * that the rows are pairwise non-isomorphic up to converse, that each is self-converse
    exactly when its `converse` column says `self`, and that none is isomorphic, or
    converse, to a host the ledger already counts (canonical forms from nauty's labelg).

It also re-derives the order-23 circulant part of the count from verdicts/vt23/: every
host the unit-margin roll-up calls UNSAT has a complete, uncapped cover and a majority
witness that verifies against tournaments/vt23/.

    usage: separation_supplement.py ROOT [--drop-slice HOST] [--flip ID] [--as-unsat HOST]

The three options are negative controls for tools/check_package.sh: remove one slice log
of HOST, reverse one arc of row ID's host, or demand a complete refutation of a reversal
the spectrum calls `S`.  Each must make the check fail.  Exit 0 iff every check passes.
"""
import argparse
import glob
import io
import itertools
import os
import re
import subprocess
import sys
import tarfile

ap = argparse.ArgumentParser()
ap.add_argument("root")
ap.add_argument("--drop-slice")
ap.add_argument("--flip")
ap.add_argument("--as-unsat")
a = ap.parse_args()
R = os.path.abspath(a.root)
FAIL = []


def fail(msg):
    FAIL.append(msg)


def read_bits(path):
    s = "".join(c for c in open(path).read() if c in "01")
    n = int((1 + (1 + 8 * len(s)) ** 0.5) / 2)
    if n * (n - 1) // 2 != len(s):
        raise SystemExit(f"{path}: {len(s)} bits is not the upper triangle of any order")
    A = [[0] * n for _ in range(n)]
    for (i, j), c in zip(itertools.combinations(range(n), 2), s):
        A[i][j], A[j][i] = (1, 0) if c == "1" else (0, 1)
    return A


def tmin(A):
    n = len(A)
    return min(sum(1 for w in range(n) if A[v][w] and A[w][u])
               for u in range(n) for v in range(n) if A[u][v])


def orders_of(text):
    body = text.split("WITNESS", 1)[1] if "WITNESS" in text else text
    return [list(map(int, m.group(1).split()))
            for m in re.finditer(r"^\s*voter\s+\d+:\s*([\d ]+)$", body, re.M)]


def majority_ok(A, orders):
    n = len(A)
    if len(orders) != 5 or any(sorted(o) != list(range(n)) for o in orders):
        return False
    pos = [{v: i for i, v in enumerate(o)} for o in orders]
    return all(sum(1 for p in pos if p[u] < p[v]) >= 3
               for u in range(n) for v in range(n) if A[u][v])


def member(archive, name):
    with tarfile.open(fileobj=io.BytesIO(zstd(archive))) as t:
        return t.extractfile(name).read().decode()


_Z = {}


def zstd(archive):
    if archive not in _Z:
        p = subprocess.run(["zstd", "-dc", os.path.join(R, archive)], capture_output=True)
        if p.returncode != 0:
            raise SystemExit(f"zstd could not unpack {archive}: {p.stderr.decode()[:200]}")
        _Z[archive] = p.stdout
    return _Z[archive]


def slices_cover(archive, host, n):
    """Slice logs of `host` must tile [0, base_states) exactly, all UNSAT, none capped."""
    with tarfile.open(fileobj=io.BytesIO(zstd(archive))) as t:
        names = sorted(m.name for m in t.getmembers()
                       if re.search(rf"/{re.escape(host)}_q[\d_]+\.log$", m.name))
        if host == a.drop_slice and names:
            names = names[:len(names) // 2] + names[len(names) // 2 + 1:]
        iv, total = [], None
        for nm in names:
            txt = t.extractfile(nm).read().decode()
            h = re.search(r"^n=(\d+) K=5 margin=(\S+) .* base_states=(\d+)", txt, re.M)
            sl = re.search(r"base_state_slice=\[(\d+),(\d+)\)", txt)
            if not h or not sl:
                return f"{nm}: no engine header or no slice"
            if int(h.group(1)) != n or h.group(2) != "exact1":
                return f"{nm}: n={h.group(1)} margin={h.group(2)}, want n={n} at unit margin"
            if total is None:
                total = int(h.group(3))
            elif total != int(h.group(3)):
                return f"{nm}: base_states {h.group(3)} differs from {total}"
            if not re.search(r"^RESULT UNSAT ", txt, re.M):
                return f"{nm}: not RESULT UNSAT"
            if re.search(r"capped=[1-9]", txt):
                return f"{nm}: a capped base state"
            iv.append((int(sl.group(1)), int(sl.group(2))))
    if not iv:
        return f"no slice logs for {host} in {archive}"
    iv.sort()
    at = 0
    for lo, hi in iv:
        if lo != at:
            return f"slices of {host} do not tile: gap or overlap at {at} (next slice starts {lo})"
        at = hi
    if at != total:
        return f"slices of {host} end at {at}, not at {total}"
    return None


def times_cover(path, want):
    lines = [l for l in open(os.path.join(R, path)).read().splitlines() if l.strip()]
    if not lines[0].startswith("#") or "margin-1" not in lines[0]:
        return f"{path}: first line does not declare a margin-1 search"
    idx = sorted(int(l.split()[0]) for l in lines[1:])
    if idx != list(range(want)):
        return f"{path}: the base-state indices are not exactly 0..{want - 1}"
    return None


def spectrum(path):
    sp = {}
    txt = open(os.path.join(R, path)).read()
    tail = txt[txt.rindex("=== SPECTRUM"):]
    for m in re.finditer(r"^\s*(h\d\d): ([USD.]+)\s", tail, re.M):
        sp[m.group(1)] = m.group(2)
    return sp


# ---------------------------------------------------------------- the supplement
SUP = os.path.join(R, "verdicts", "ledger_supplement.tsv")
rows = [l.split("\t") for l in open(SUP).read().splitlines() if l and not l.startswith("#")]
hdr, rows = rows[0], rows[1:]
col = {c: i for i, c in enumerate(hdr)}
for need in ("id", "n", "tmin", "margin1", "majority", "sources", "converse", "host",
             "unit_cover", "majority_witness"):
    if need not in col:
        raise SystemExit(f"ledger_supplement.tsv has no '{need}' column")
spec = spectrum("verdicts/arcflip_spectrum.log")
flips = {}
for ln in open(os.path.join(R, "tournaments/vt21_arcflip/verdicts.tsv")).read().splitlines()[1:]:
    f = ln.split("\t")
    if f[3] == "majority" and f[4] == "SAT" and f[5] == "1":
        flips[f[0]] = True

hosts = {}
for r in rows:
    g = lambda c: r[col[c]]
    rid, n = g("id"), int(g("n"))
    for p in g("sources").split(";"):
        if not os.path.exists(os.path.join(R, p)):
            fail(f"{rid}: source {p} is not in the package")
    A = read_bits(os.path.join(R, g("host")))
    if rid == a.flip:
        A[0][1], A[1][0] = A[1][0], A[0][1]
    hosts[rid] = A
    if len(A) != n:
        fail(f"{rid}: host has {len(A)} vertices, row says {n}")
    if tmin(A) != int(g("tmin")):
        fail(f"{rid}: tmin is {tmin(A)}, row says {g('tmin')}")
    if g("margin1") != "UNSAT" or g("majority") != "SAT":
        fail(f"{rid}: the supplement holds only unit-margin UNSAT, majority SAT rows")
    kind, _, arg = g("unit_cover").partition(":")
    if kind == "slices":
        archive, host = arg.split(":")
        err = slices_cover(archive, host, n)
        h, f = host.split("_f")
        if spec.get(h, "")[int(f)] != "U":
            fail(f"{rid}: the audited spectrum marks orbit {int(f)} of {h} "
                 f"'{spec.get(h, '?')[int(f)]}', not U")
        if host not in flips:
            fail(f"{rid}: tournaments/vt21_arcflip/verdicts.tsv has no verified majority SAT for {host}")
    elif kind == "times":
        path, want = arg.split(":")
        err = times_cover(path, int(want))
    else:
        err = f"unknown unit_cover kind {kind!r}"
    if err:
        fail(f"{rid}: unit margin: {err}")
    wpath = g("majority_witness")
    text = (member(*wpath.split(":", 1)) if ":" in wpath else open(os.path.join(R, wpath)).read())
    if not majority_ok(A, orders_of(text)):
        fail(f"{rid}: the majority witness {wpath} does not induce the host")

if a.as_unsat:
    err = slices_cover("evidence/vt21_arcflip_slices.tar.zst", a.as_unsat, 21)
    if err:
        fail(f"{a.as_unsat}: unit margin: {err}")

# ------------------------------------------------- distinct, and not already counted
LABELG = os.environ.get("LABELG") or ""
if not (LABELG and os.access(LABELG, os.X_OK)):
    raise SystemExit("LABELG is not set to an executable labelg; the class check cannot run")


def d6(A):
    n = len(A)
    bits = [A[i][j] for i in range(n) for j in range(n)]
    bits += [0] * (-len(bits) % 6)
    return "&" + chr(63 + n) + "".join(
        chr(63 + int("".join(map(str, bits[k:k + 6])), 2)) for k in range(0, len(bits), 6))


def canon(As):
    p = subprocess.run([LABELG, "-zq"], input="".join(d6(A) + "\n" for A in As),
                       capture_output=True, text=True)
    out = p.stdout.split()
    if p.returncode != 0 or len(out) != len(As):
        raise SystemExit(f"labelg failed: {p.stderr[:200]}")
    return out


T = lambda A: [list(c) for c in zip(*A)]
ids = list(hosts)
fw, bw = canon([hosts[i] for i in ids]), canon([T(hosts[i]) for i in ids])
key = {}
for i, f, b in zip(ids, fw, bw):
    selfconv = f == b
    if selfconv != (rows[ids.index(i)][col["converse"]] == "self"):
        fail(f"{i}: self-converse is {selfconv}, the converse column says "
             f"{rows[ids.index(i)][col['converse']]}")
    k = min(f, b)
    if k in key:
        fail(f"{i} and {key[k]} are the same tournament up to isomorphism and converse")
    key[k] = i
ref = (["tournaments/vt19/paley19.bits", "tournaments/drt19/g2.bits"]
       + [f"tournaments/vt21_hosts/{h}.bits" for h in ("h01", "h02", "h04", "h05")]
       + sorted(os.path.relpath(p, R) for p in glob.glob(os.path.join(R, "verdicts/near_dr21/*.bits")))
       + sorted(os.path.relpath(p, R) for p in glob.glob(os.path.join(R, "tournaments/vt23/v*.bits"))))
RA = [read_bits(os.path.join(R, p)) for p in ref]
rk = set(canon(RA)) | set(canon([T(A) for A in RA]))
for k, i in key.items():
    if k in rk:
        fail(f"{i} is isomorphic or converse to a host the ledger already counts")

# ------------------------------------------------------------ order-23 circulants
roll = [l.split("\t") for l in open(os.path.join(R, "verdicts/vt23/vt23_m1.tsv")).read().splitlines()
        if l and not l.startswith("#")]
unsat = [f[0] for f in roll if f[1] == "UNSAT"]
for f in roll:
    if f[1] == "UNSAT" and (f[4] != "0" or int(f[2]) < 1):
        fail(f"vt23 {f[0]}: unit-margin UNSAT row is capped or has no slices")
majr = {l.split("\t")[0]: l.split("\t")[1]
        for l in open(os.path.join(R, "verdicts/vt23/vt23_maj.tsv")).read().splitlines()
        if l and not l.startswith("#")}
for h in unsat:
    if majr.get(h) != "SAT":
        fail(f"vt23 {h}: the majority roll-up does not say SAT")
    A = read_bits(os.path.join(R, "tournaments/vt23", h + ".bits"))
    w = open(os.path.join(R, "verdicts/vt23/out", h + ".majority.txt")).read()
    if not majority_ok(A, orders_of(w)):
        fail(f"vt23 {h}: the majority witness does not induce tournaments/vt23/{h}.bits")

if FAIL:
    print("\n".join("FAIL " + m for m in FAIL))
    sys.exit(1)
print(f"{len(rows)} supplementary unit-margin-only classes re-derived (unit-margin cover, majority "
      f"witness, distinct up to converse, none already in the ledger), and {len(unsat)} order-23 "
      f"circulants unit-margin UNSAT with verified majority witnesses")
