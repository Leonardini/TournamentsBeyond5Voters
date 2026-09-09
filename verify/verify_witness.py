#!/usr/bin/env python3
"""Independent check of a margin-1 5-voter witness for Paley(q).

Deliberately shares NO code with kinduce: it rebuilds Paley(q) from the
quadratic residues itself and recomputes every arc's support from the printed
orders.  Exit 0 only if the witness is valid in every respect.
    usage: verify_witness.py LOGFILE q [k]
"""
import sys, re

def paley_arc(q, a, b):
    QR = {(x * x) % q for x in range(1, q)}
    return ((b - a) % q) in QR          # True iff a -> b

def main():
    majority = "--majority" in sys.argv
    argv = [a for a in sys.argv if a != "--majority"]
    path, q = argv[1], int(argv[2])
    k = int(argv[3]) if len(argv) > 3 else 5
    txt = open(path).read()
    if 'WITNESS' not in txt:
        print("FAIL: no WITNESS block"); return 1
    block = txt.split('WITNESS', 1)[1]
    orders = []
    for line in block.splitlines():
        m = re.match(r'\s*voter\s+(\d+):\s*(.*)$', line)
        if m:
            orders.append([int(x) for x in m.group(2).split()])
        elif orders:
            break
    if len(orders) != k:
        print(f"FAIL: found {len(orders)} voter orders, expected {k}"); return 1
    for i, o in enumerate(orders):
        if sorted(o) != list(range(q)):
            print(f"FAIL: voter {i} is not a permutation of 0..{q-1}"); return 1
    pos = [{v: j for j, v in enumerate(o)} for o in orders]
    need = (k + 1) // 2
    bad = []
    checked = 0
    for a in range(q):
        for b in range(q):
            if a == b or not paley_arc(q, a, b):
                continue                      # consider each arc once, in its true direction
            sup = sum(1 for i in range(k) if pos[i][a] < pos[i][b])
            checked += 1
            if (sup < need) if majority else (sup != need):
                bad.append((a, b, sup))
    if checked != q * (q - 1) // 2:
        print(f"FAIL: checked {checked} arcs, expected {q*(q-1)//2}"); return 1
    if bad:
        print(f"FAIL: {len(bad)} arcs violate the {'majority' if majority else 'exact margin-1'} rule, e.g. {bad[:5]}"); return 1
    rule = f"at least {need} of {k}" if majority else f"exactly {need}:{k-need}"
    print(f"VERIFIED: all {checked} arcs of Paley({q}) at {rule}, "
          f"{k} valid permutations -- witness is GENUINE")
    return 0

sys.exit(main())
