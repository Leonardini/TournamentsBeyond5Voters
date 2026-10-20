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

Columns: id, n, tmin, margin1, majority, witness (whether the solver output is on disk), source,
converse (registry_converse.tsv: self, the converse class id, or - when the converse is not held).
"""
import glob
import json
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

conv = dict(ln.split("\t") for ln in open(os.path.join(R, "registry_converse.tsv")).read().splitlines()[1:])
assert set(conv) == set(reg), "registry_converse.tsv does not cover registry.tsv -- rerun registry.py"
verdict = {tid: {"exact": None, "majority": None, "wit": set(), "src": set()} for tid in reg}


# ---- witnesses, wherever they were archived ----
# A witness is evidence about a CLASS, not about a directory.  Both readers below
# used to glob the out/ beside the file they were reading, so a profile
# re-derived in one kit for a host recorded in another was invisible BY
# CONSTRUCTION -- which is how all four n=21 witnesses, h01 included, read as
# absent for a day after being recovered into vt21_maj/ for hosts listed in
# vt21_hosts/.  Index every out/ once instead, and key it on the class.
#
# Two guards, because a witness counted against the wrong class is worse than a
# missing one: the host name must resolve to exactly ONE class, and the profile's
# own header must be for a tournament of that class's order.
WIT, OUTSIDE = {}, []
for p_w in sorted(glob.glob(os.path.join(R, "*", "out", "*.txt"))):
    m_w = re.match(r"(.+?)\.(exact|majority)(\.[^.]+)?\.txt$", os.path.basename(p_w))
    if not m_w:
        continue
    host_w, margin_w = m_w.group(1), m_w.group(2)
    txt_w = open(p_w).read()
    if not re.search(r"^WITNESS", txt_w, re.M):
        continue                                   # an ABORTED run leaves a file too
    hn_w = re.search(r"^n=(\d+) ", txt_w, re.M)
    assert hn_w, f"{p_w}: the profile has no 'n=' header line to check the class against"
    n_w = int(hn_w.group(1))
    kit_w = os.path.basename(os.path.dirname(os.path.dirname(p_w)))
    # The kit's own name first: vt15/out/c000 is vt15/c000 and nothing else.  Only
    # when the kit is not itself a host directory -- vt21_maj/ holds profiles for
    # hosts listed in vt21_hosts/ -- fall back to the basename, and then the
    # ORDER decides between namesakes: c000 is a host name at n=15 AND at n=17.
    tid_w = member2id.get(f"{kit_w}/{host_w}")
    if tid_w is None:
        cand_w = sorted({member2id[k] for k in member2id if k.endswith("/" + host_w)})
        byn_w = [t for t in cand_w if reg[t][0] == n_w]
        if not cand_w:
            # Not every witness is about a registry class: vt21_arcflip/ holds
            # profiles for ARC-FLIPPED variants (h01_f00 ...), which are different
            # tournaments and deliberately not in registry.tsv.  Count them, do not
            # credit them to the host they were derived from.
            OUTSIDE.append(os.path.relpath(p_w, R))
            continue
        # A name the registry DOES know, carrying a profile for a different order,
        # is not an unknown host -- it is a mislabelled file, and letting it fall
        # through to the count above would hide it among the arc-flip variants.
        assert byn_w, (
            f"{p_w}: the name resolves to {cand_w} but the profile's header says n={n_w}, "
            f"which none of them is -- one of the two is wrong")
        assert len(byn_w) == 1, (
            f"{p_w}: host {host_w} on {n_w} vertices matches {len(byn_w)} registry classes "
            f"{byn_w} (ignoring order: {cand_w}) -- a witness filed under an ambiguous "
            f"name cannot be credited to one")
        tid_w = byn_w[0]
    assert reg[tid_w][0] == n_w, (
        f"{p_w}: the profile's header says n={n_w} but class {tid_w} is on "
        f"{reg[tid_w][0]} vertices -- this witness is for another host")
    WIT[(tid_w, margin_w)] = p_w


HARD = ("SAT", "UNSAT")
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
        # `witness_on_disk` must mean a witness is on disk.  Testing only that the
        # output FILE exists marks every ABORTED run as having one -- which is how
        # seven vt23_hard hosts came to claim `exact+majority` witnesses while
        # every one of their logs says RESULT ABORTED.  Read the file.
        put(tid, margin, v, f"{d}/verdicts.tsv", (tid, margin) in WIT)

# ---- 1b. campaign roll-ups: one row per HOST, not per case ----
# drt23_m1/ and drt23_maj/ do not use the verdicts.tsv convention.  `rollup.sh`
# writes one row per host only after cover_rollup.awk has checked that the
# chunks tile [0, base_states) with no gap and no overlap, so a verdict here is
# a COMPLETE sweep.  Without this block the finished d003 majority result and
# all 18 margin-1 DRT results are invisible to the ledger.
#
# The margin is a property of the CAMPAIGN, not of any row, so it is declared
# once here; columns are located BY NAME from the `#host verdict ...` header so
# that a schema change fails loudly instead of silently reading the wrong field.
ROLLUPS = [
    ("drt23_m1/drt23_m1.tsv", "drt23", "exact"),
    ("drt23_maj/drt23_maj.tsv", "drt23", "majority"),
    ("jz_drt23maj/jz_drt23maj.tsv", "drt23", "majority"),
    # The nine hard VT hosts at n=23.  Their .bits live in vt23_hard/, which is
    # what the registry knows them by; the sweeps that settled them live in
    # vt23_m1/ and vt23_maj/.
    ("vt23_m1/vt23_m1.tsv", "vt23_hard", "exact"),
    ("vt23_maj/vt23_maj.tsv", "vt23_hard", "majority"),
    # h01/h02/h04/h05 at n=21.  vt21_hosts/verdicts.tsv already carries the SAT
    # verdicts, so this row set exists for the WITNESS column: the profiles were
    # re-derived in vt21_maj/ and archived in ITS out/, and the per-case path
    # above looks only in the verdicts.tsv directory's own out/, which is why
    # four recovered witnesses still read as absent.
    ("vt21_maj/vt21_maj.tsv", "vt21_hosts", "majority"),
]
for rel, hostdir, margin in ROLLUPS:
    p_rl = os.path.join(R, rel)
    if not os.path.exists(p_rl):
        continue
    lines = [ln for ln in open(p_rl).read().splitlines() if ln.strip()]
    # The header is the '#host<TAB>...' line, which need not be the FIRST line: a
    # rollup transcribed from elsewhere should be free to say so above it, and
    # taking lines[0] blindly would read that prose as the column names.
    hdr_i = next((i for i, ln in enumerate(lines)
                  if ln.startswith("#") and ln.lstrip("#").split("\t")[:1] == ["host"]), None)
    assert hdr_i is not None, f"{rel}: no '#host<TAB>...' header line to key columns by name"
    cols = {name: i for i, name in enumerate(lines[hdr_i].lstrip("#").split("\t"))}
    for need in ("host", "verdict", "capped"):
        assert need in cols, f"{rel}: header has no '{need}' column ({sorted(cols)})"
    for ln in lines[hdr_i + 1:]:
        if ln.startswith("#"):
            continue
        f = ln.split("\t")
        host, res = f[cols["host"]], f[cols["verdict"]]
        capped = int(f[cols["capped"]])
        # A campaign's hosts need not all live in one directory: vt23_maj sweeps
        # nine from vt23_hard/ and five from vt23/.  Fall back to a basename match,
        # but only a UNIQUE one -- an ambiguous name must fail rather than pick.
        tid = member2id.get(f"{hostdir}/{host}")
        if tid is None:
            cand = sorted({member2id[m] for m in member2id if m.endswith("/" + host)})
            assert len(cand) == 1, (
                f"{rel}: host {host} is not {hostdir}/{host} and its basename matches "
                f"{len(cand)} classes {cand} -- name it unambiguously")
            tid = cand[0]
        assert tid is not None, f"{rel}: host {host} not in registry.tsv as {hostdir}/{host}"
        # a capped chunk anywhere means the cover is not a proof
        v = res if res in ("SAT", "UNSAT") and capped == 0 else "unresolved"
        # A rollup can have witnesses too.  Without this the witness column reads
        # "-" for every campaign-sourced SAT, which is indistinguishable from a
        # feasibility claim with no evidence behind it -- the exact thing that
        # column exists to expose.  Look in the KIT's out/, not the host dir's.
        put(tid, margin, v, rel, (tid, margin) in WIT)

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

# ---- 3. converse-invariance, the last sound implication ----
# A profile realising T, read backwards, realises the converse of T, so every
# verdict here is converse-invariant and one member of a converse pair settles
# the other.  The campaigns bank on this -- the margin-1 DRT sweep ran 18 hosts
# to settle 36 -- so without this block the ledger reports 18 of those as
# `unresolved` and understates a finished result.
#
# The pairing is NOT written down here: it is read from the json that
# `converse_pairs.py` emits, which asserts closure, involution and that the
# representative list covers every class exactly once.  Regenerate it whenever
# a host directory gains or loses a tournament.
for cp in sorted(glob.glob(os.path.join(R, "*", "converse_pairs.json"))):
    hostdir = os.path.basename(os.path.dirname(cp))
    pairing = json.load(open(cp))
    for host, mate in pairing.items():
        tid, tid_mate = member2id.get(f"{hostdir}/{host}"), member2id.get(f"{hostdir}/{mate}")
        assert tid is not None, f"{cp}: {hostdir}/{host} is not in registry.tsv"
        assert tid_mate is not None, f"{cp}: {hostdir}/{mate} is not in registry.tsv"
        for margin in ("exact", "majority"):
            v = verdict[tid][margin]
            if v in ("SAT", "UNSAT") and verdict[tid_mate][margin] not in ("SAT", "UNSAT"):
                put(tid_mate, margin, v, f"converse of {hostdir}/{host}")

# ---- report ----
rows = sorted(reg.items(), key=lambda kv: (kv[1][0], kv[0]))
print(f"{'id':>9} {'n':>3} {'tmin':>4} {'margin-1':>11} {'majority':>11} {'witness':>8}")
counts = {}
for tid, (n, tmin, mem) in rows:
    v = verdict[tid]
    m1 = v["exact"] or "not run"
    mj = v["majority"] if v["majority"] in HARD else (
        "SAT (implied)" if v["exact"] == "SAT" else v["majority"] or "not run")
    w = "+".join(sorted(v["wit"])) if v["wit"] else "-"
    counts[(n, m1, mj.split(" ")[0])] = counts.get((n, m1, mj.split(" ")[0]), 0) + 1
print(f"  ({len(rows)} classes; per-class rows in verdict_ledger.tsv)")
with open(os.path.join(R, "verdict_ledger.tsv"), "w") as f:
    f.write("id\tn\ttmin\tmargin1\tmajority\twitness_on_disk\tsources\tconverse\n")
    for tid, (n, tmin, mem) in rows:
        v = verdict[tid]
        # The two implications are SOUND, so they must fire whenever the target is
        # not already a hard verdict.  Gating them on `is None` let a single
        # ABORTED run -- recorded as "unresolved", which is truthy -- mask them:
        # t23_058 stood at margin-1 SAT with majority "unresolved", i.e. the table
        # denied that a unit-margin witness is a majority witness.
        m1 = v["exact"] or "not run"
        mj = v["majority"] or "not run"
        if v["exact"] == "SAT" and v["majority"] not in HARD:
            mj = "SAT (implied by margin-1)"
        if v["majority"] == "UNSAT" and v["exact"] not in HARD:
            m1 = "UNSAT (implied by majority)"
        f.write(f"{tid}\t{n}\t{tmin}\t{m1}\t{mj}\t"
                f"{'+'.join(sorted(v['wit'])) or '-'}\t{';'.join(sorted(v['src'])) or '-'}\t{conv[tid]}\n")

print("\nsummary by order:")
for n in sorted({n for n, _, _ in [(v[0], 0, 0) for v in reg.values()]}):
    sub = [tid for tid, (nn, _, _) in reg.items() if nn == n]
    # COUNT WHAT THE ROWS SAY.  The two implications are applied when a row is
    # written, so reading the raw slot here made a class with a sound implied
    # verdict count as "not run" -- the n=22 pair printed "not run 2" beside two
    # rows reading "UNSAT (implied by majority)".  Resolve first, then count.
    # The implication must fire whenever the target is not already a HARD
    # verdict, exactly as the row writer does -- `or` on the raw slot lets a
    # truthy "unresolved" mask it, which is the t23_058 bug this file already
    # documents and which my first version of this resolver reintroduced
    # (majority SAT at n=23 read 92 instead of 93).
    def eff(t, margin):
        v = verdict[t]
        other = "majority" if margin == "exact" else "exact"
        implied = "UNSAT" if margin == "exact" else "SAT"
        trigger = "UNSAT" if margin == "exact" else "SAT"
        if v[other] == trigger and v[margin] not in HARD:
            return implied
        return v[margin]
    m1sat = sum(1 for t in sub if eff(t, "exact") == "SAT")
    m1uns = sum(1 for t in sub if eff(t, "exact") == "UNSAT")
    m1un = sum(1 for t in sub if eff(t, "exact") == "unresolved")
    m1no = sum(1 for t in sub if eff(t, "exact") is None)
    mjsat = sum(1 for t in sub if eff(t, "majority") == "SAT")
    mjuns = sum(1 for t in sub if eff(t, "majority") == "UNSAT")
    wit = sum(1 for t in sub if verdict[t]["wit"])
    assert m1sat + m1uns + m1un + m1no == len(sub), f"n={n}: margin-1 counts do not tile the classes"
    print(f"  n={n:>2}: {len(sub):>3} classes | margin-1 SAT {m1sat:>3}, UNSAT {m1uns:>3}, "
          f"unresolved {m1un:>3}, not run {m1no:>3} | majority SAT {mjsat:>3}, UNSAT {mjuns:>3} "
          f"| witness on disk {wit:>3}")
# ---- the audit the witness column exists for ----
# "witness on disk" per ORDER is not the question; the question is whether any
# individual feasibility claim rests on nothing.  Counting per order hides that:
# n=21 read 106 of 110 for a fortnight and the four missing ones were the four
# that carried weight.  So check every claim, and apply the implication the rest
# of this file applies -- a unit-margin witness IS a majority witness, the
# converse is not -- or every margin-1-witnessed host reads as an evidence gap.
unwit = []
for tid, (n, tmin, mem) in rows:
    v = verdict[tid]
    if v["exact"] == "SAT" and "exact" not in v["wit"]:
        unwit.append((tid, n, "margin-1"))
    if (v["majority"] == "SAT" or v["exact"] == "SAT") and not (v["wit"] & {"exact", "majority"}):
        unwit.append((tid, n, "majority"))
nclaim = sum(1 for tid, _ in rows for k in ("exact", "majority")
             if verdict[tid][k] == "SAT" or (k == "majority" and verdict[tid]["exact"] == "SAT"))
if OUTSIDE:
    print(f"\n{len(OUTSIDE)} archived profile(s) are for hosts outside registry.tsv and were "
          f"not credited to any class, e.g. {OUTSIDE[0]}")
print(f"\nwitness audit: {nclaim} SAT claims, {len(unwit)} resting on no profile"
      + ("" if not unwit else "  <-- FIX THESE BEFORE QUOTING THEM"))
for tid, n, m in unwit:
    print(f"   {tid} (n={n}) has no {m} witness on disk")

# A profile for a class the sweeps call UNSAT means one of the two is wrong, and
# it is the cheapest contradiction in the repo to check for.
for (tid_w, margin_w), p_w in sorted(WIT.items()):
    key = "exact" if margin_w == "exact" else "majority"
    if verdict[tid_w][key] == "UNSAT":
        CONTRA.append(f"{tid_w} {key}: UNSAT, yet {os.path.relpath(p_w, R)} holds a witness")

if CONTRA:
    print("\n!! CONTRADICTORY VERDICTS -- investigate before quoting anything:")
    for c in CONTRA:
        print("   " + c)
nun = sum(1 for t in verdict if verdict[t]["exact"] == "UNSAT" or verdict[t]["majority"] == "UNSAT")
print(f"\nNOTE a capped run is 'unresolved', NEVER UNSAT. Only a complete sharded sweep")
print(f"(vt21_runner.py) proves UNSAT; {nun} row(s) here carry one.")
