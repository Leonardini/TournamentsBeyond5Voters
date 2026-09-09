#!/usr/bin/env python3
"""One consolidated verdict table, keyed on the registry's isomorphism-class ids.

Sources, in order of trust:
  1. `<dir>/verdicts.tsv`  -- per-case, written and fsynced as each run finished
  2. the sweep logs         -- aggregate only; used to recover verdicts from runs that predate
                               per-case persistence, and marked as such
Two sound implications are used, in opposite directions:
  margin-1 SAT  => majority SAT      (a unit-margin witness is a majority witness)
  majority UNSAT => margin-1 UNSAT   (if no profile reaches a majority, none reaches exactly 3)
A capped/ABORTED run is never a verdict -- it is `unresolved`.

Columns: id, n, tmin, margin1, majority, witness (whether the solver output is on disk), source.
"""
import glob
import os
import re

R = os.path.dirname(os.path.abspath(__file__))

# ---- registry: id -> (n, tmin, [dir/name ...]) ----
reg, member2id = {}, {}
_reg = open(os.path.join(R, "registry.tsv")).read().splitlines()
assert _reg[0].startswith("id\t"), "registry.tsv lost its header -- the [1:] below would eat a class"
for ln in _reg[1:]:
    tid, n, tmin, members = ln.split("\t")
    reg[tid] = (int(n), tmin, members.split(","))
    for m in members.split(","):
        member2id[m] = tid

verdict = {tid: {"exact": None, "majority": None, "wit": set(), "src": set()} for tid in reg}


CONTRA = []

def put(tid, margin, v, src, wit=False):
    if tid is None:
        return
    cur = verdict[tid][margin]
    if cur in ("SAT", "UNSAT") and v in ("SAT", "UNSAT") and cur != v:
        CONTRA.append(f"{tid} {margin}: {cur} vs {v} (from {src})")
    rank = {None: 0, "unresolved": 1, "SAT": 3, "UNSAT": 3}
    if rank[v] >= rank.get(cur, 0):
        verdict[tid][margin] = v
    verdict[tid]["src"].add(src)
    if wit:
        verdict[tid]["wit"].add(margin)


# ---- 1. persisted per-case verdicts ----
def data_rows(path):
    """Rows of a verdicts.tsv, dropping the header ONLY IF THERE IS ONE.

    An unconditional [1:] silently eats the first DATA row of any hand-written file that has no
    header -- which is how Paley(23)'s `majority UNSAT` (the N(5) <= 23 result) went missing from
    every ledger rebuild while the file on disk was correct all along.
    """
    lines = open(path).read().splitlines()
    return lines[1:] if lines and lines[0].split("\t")[:1] == ["name"] else lines


for vf in sorted(glob.glob(os.path.join(R, "*", "verdicts.tsv"))):
    d = os.path.basename(os.path.dirname(vf))
    for ln in data_rows(vf):
        f = ln.split("\t")
        if len(f) < 7:
            continue
        name, margin, res = f[0], f[3], f[4]
        tid = member2id.get(f"{d}/{name}")
        if tid is None:                      # recovery dirs are copies; map by basename
            cand = [m for m in member2id if m.endswith("/" + name)]
            tid = member2id[cand[0]] if cand else None
        v = res if res in ("SAT", "UNSAT") else "unresolved"
        wit = os.path.exists(os.path.join(R, d, "out", f"{name}.{margin}.txt"))
        put(tid, margin, v, f"{d}/verdicts.tsv", wit)

# ---- 2. logs, for sweeps that predate per-case persistence ----
for lg in ("vt23_sweep.log", "sweep_queue.log"):
    p = os.path.join(R, lg)
    if not os.path.exists(p):
        continue
    txt = open(p).read()
    for m in re.finditer(r"^   survivor: (\S+) -> \w+ after", txt, re.M):
        cand = [k for k in member2id if k.endswith("/" + m.group(1))]
        for k in cand:
            put(member2id[k], "exact", "unresolved", lg + " (aggregate only)")

# ---- report ----
rows = sorted(reg.items(), key=lambda kv: (kv[1][0], kv[0]))
print(f"{'id':>9} {'n':>3} {'tmin':>4} {'margin-1':>11} {'majority':>11} {'witness':>8}")
counts = {}
for tid, (n, tmin, mem) in rows:
    v = verdict[tid]
    m1 = v["exact"] or "not run"
    mj = v["majority"] or ("SAT (implied)" if v["exact"] == "SAT" else "not run")
    w = "+".join(sorted(v["wit"])) if v["wit"] else "-"
    counts[(n, m1, mj.split(" ")[0])] = counts.get((n, m1, mj.split(" ")[0]), 0) + 1
print(f"  ({len(rows)} classes; per-class rows in verdict_ledger.tsv)")
with open(os.path.join(R, "verdict_ledger.tsv"), "w") as f:
    f.write("id\tn\ttmin\tmargin1\tmajority\twitness_on_disk\tsources\n")
    for tid, (n, tmin, mem) in rows:
        v = verdict[tid]
        m1 = v["exact"] or "not run"
        mj = v["majority"] or ("SAT (implied by margin-1)" if v["exact"] == "SAT" else "not run")
        if v["exact"] is None and v["majority"] == "UNSAT":
            m1 = "UNSAT (implied by majority)"
        f.write(f"{tid}\t{n}\t{tmin}\t{m1}\t{mj}\t"
                f"{'+'.join(sorted(v['wit'])) or '-'}\t{';'.join(sorted(v['src'])) or '-'}\n")

print("\nsummary by order:")
for n in sorted({n for n, _, _ in [(v[0], 0, 0) for v in reg.values()]}):
    sub = [tid for tid, (nn, _, _) in reg.items() if nn == n]
    m1sat = sum(1 for t in sub if verdict[t]["exact"] == "SAT")
    m1un = sum(1 for t in sub if verdict[t]["exact"] == "unresolved")
    m1no = sum(1 for t in sub if verdict[t]["exact"] is None)
    mjsat = sum(1 for t in sub if verdict[t]["majority"] == "SAT" or verdict[t]["exact"] == "SAT")
    wit = sum(1 for t in sub if verdict[t]["wit"])
    print(f"  n={n:>2}: {len(sub):>3} classes | margin-1 SAT {m1sat:>3}, unresolved {m1un:>3}, "
          f"not run {m1no:>3} | majority SAT {mjsat:>3} | witness on disk {wit:>3}")
if CONTRA:
    print("\n!! CONTRADICTORY VERDICTS -- investigate before quoting anything:")
    for c in CONTRA:
        print("   " + c)
nun = sum(1 for t in verdict if verdict[t]["exact"] == "UNSAT" or verdict[t]["majority"] == "UNSAT")
print(f"\nNOTE a capped run is 'unresolved', NEVER UNSAT. Only a complete sharded sweep")
print(f"(vt21_runner.py) proves UNSAT; {nun} row(s) here carry one.")
