#!/usr/bin/env python3
"""Independent witness check for an ARBITRARY tournament given as a bits file.

verify_witness.py rebuilds Paley(q) from its quadratic residues and so cannot
check subtournaments such as Paley(23) minus a vertex.  This reads the same
upper-triangle bit string kinduce/gentourng use and shares no code with the
search.  Exit 0 only if the witness is valid in every respect.
    usage: verify_witness_bits.py LOGFILE BITSFILE n [k] [--majority]
"""
import sys, re

def main():
    majority = "--majority" in sys.argv
    argv = [a for a in sys.argv if a != "--majority"]
    logp, bitsp, n = argv[1], argv[2], int(argv[3])
    k = int(argv[4]) if len(argv) > 4 else 5
    s = ''.join(c for c in open(bitsp).read() if c in '01')
    if len(s) != n * (n - 1) // 2:
        print(f"FAIL: bits file has {len(s)} bits, expected {n*(n-1)//2}"); return 1
    arc = {}
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            arc[(i, j)] = (s[idx] == '1')      # True iff i -> j
            idx += 1
    txt = open(logp).read()
    # A run log marks its witness with a WITNESS line; a standalone .witness file
    # saved from a cluster run is just the ballots under a comment header.  Accept
    # both, rather than forcing the record to be edited to suit the checker --
    # editing a verdict file to make a check pass is exactly backwards.
    if 'WITNESS' in txt:
        body = txt.split('WITNESS', 1)[1]
    elif re.search(r'^\s*voter\s+0:', txt, re.M):
        body = txt[re.search(r'^\s*voter\s+0:', txt, re.M).start():]
    else:
        print("FAIL: no WITNESS block and no 'voter 0:' line"); return 1
    orders = []
    for line in body.splitlines():
        m = re.match(r'\s*voter\s+(\d+):\s*(.*)$', line)
        if m:
            orders.append([int(x) for x in m.group(2).split()])
        elif orders:
            break
    if len(orders) != k:
        print(f"FAIL: {len(orders)} voter orders, expected {k}"); return 1
    for i, o in enumerate(orders):
        if sorted(o) != list(range(n)):
            print(f"FAIL: voter {i} is not a permutation of 0..{n-1}"); return 1
    pos = [{v: p for p, v in enumerate(o)} for o in orders]
    need = (k + 1) // 2
    bad, checked = [], 0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = (i, j) if arc[(i, j)] else (j, i)     # a -> b in T
            sup = sum(1 for t in range(k) if pos[t][a] < pos[t][b])
            checked += 1
            if (sup < need) if majority else (sup != need):
                bad.append((a, b, sup))
    if checked != n * (n - 1) // 2:
        print(f"FAIL: checked {checked} arcs, expected {n*(n-1)//2}"); return 1
    if bad:
        print(f"FAIL: {len(bad)} arcs violate the rule, e.g. {bad[:5]}"); return 1
    rule = f"at least {need} of {k}" if majority else f"exactly {need}:{k-need}"
    print(f"VERIFIED: all {checked} arcs at {rule}, {k} valid permutations "
          f"-- witness is GENUINE")
    return 0

sys.exit(main())
