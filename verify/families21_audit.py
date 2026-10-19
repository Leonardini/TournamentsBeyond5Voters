#!/usr/bin/env python3
"""Appendix G's table: the three near-doubly regular families on 21 vertices, re-counted.

    usage: families21_audit.py FAMILIES_DIR NEAR_DR21_DIR MANUSCRIPT.md --labelg PATH [--drop-witness F/H]

FAMILIES_DIR holds random/, bisector/ and z3free/, each with HOSTS.tsv (name, bits) and
witness/<name>.log.  For each family this counts the classes up to isomorphism and converse
(the key of a tournament is the smaller of the canonical forms of it and its converse) and the
classes with a witness that verifies (verify_witness_bits.py --majority) on some member.  The
Z3-free family's witnesses are those of NEAR_DR21_DIR (zf21_*, zr21_*), matched to its classes
by that key.  Every host must be near-doubly regular.  The counts are compared with the rows of
the manuscript's table; a settled entry still marked [PLACEHOLDER] is reported, not compared.
--drop-witness removes one witness first; the gate uses it as the control."""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from level_coverage import canon, digraph6, from_bits

args = sys.argv[1:]
i = args.index('--labelg'); LG = args[i + 1]; del args[i:i + 2]
drop = None
if '--drop-witness' in args:
    i = args.index('--drop-witness'); drop = args[i + 1]; del args[i:i + 2]
FD, ND, MS = args

ROW = {'random': 'near-doubly regular, rigid, drawn at random',
       'bisector': 'near-doubly regular, with a bisector and an automorphism of order $5$',
       'z3free': 'near-doubly regular, with a fixed-point-free automorphism of order $3$'}


def keys(bitlist):
    adjs = [from_bits(b) for b in bitlist]
    conv = [[[(not a[i][j]) if i != j else False for j in range(21)] for i in range(21)] for a in adjs]
    c1 = canon([digraph6(a) for a in adjs], LG); c2 = canon([digraph6(a) for a in conv], LG)
    return [min(x, y) for x, y in zip(c1, c2)]


def near_dr(b):
    a = from_bits(b)
    return (all(sum(r) == 10 for r in a) and
            all(sum(a[u][w] and a[v][w] for w in range(21)) in (4, 5)
                for u in range(21) for v in range(u + 1, 21)))


def verified(log, b):
    bf = os.path.join(FD, '.audit.bits'); open(bf, 'w').write(b + '\n')
    r = subprocess.run([sys.executable, os.path.join(HERE, 'verify_witness_bits.py'), log, bf, '21', '5',
                        '--majority'], capture_output=True, text=True)
    os.remove(bf)
    return r.returncode == 0


ms = re.sub(r'\s+', ' ', open(MS).read())
ok = True
for fam in ('random', 'bisector', 'z3free'):
    hosts = [l.rstrip('\n').split('\t') for l in open(os.path.join(FD, fam, 'HOSTS.tsv')) if l.strip()]
    if not all(near_dr(b) for _, b in hosts):
        print(f'FAIL {fam}: a host is not near-doubly regular'); ok = False
    wit = []
    for h, b in hosts:
        p = os.path.join(FD, fam, 'witness', h + '.log')
        if os.path.exists(p) and f'{fam}/{h}' != drop and verified(p, b):
            wit.append(b)
    if fam == 'z3free':
        for f in sorted(os.listdir(ND)):
            if f.endswith('.bits') and f.startswith('z'):
                h = f[:-5]; b = ''.join(open(os.path.join(ND, f)).read().split())
                if verified(os.path.join(ND, 'out', h + '.majority.txt'), b):
                    wit.append(b)
    hk = keys([b for _, b in hosts]); classes = set(hk)
    settled = classes & set(keys(wit)) if wit else set()
    if wit and len(settled) < len(set(keys(wit))):
        print(f'FAIL {fam}: a witnessed tournament is in no class of the family'); ok = False
    m = re.search(re.escape('| ' + ROW[fam] + ' |') + r' \$([\d{},]+)\$ \| (\$[\d{},]+\$|\[PLACEHOLDER\]) \|', ms)
    if not m:
        print(f'FAIL {fam}: row not found in the manuscript'); ok = False; continue
    num = lambda t: int(re.sub(r'[^\d]', '', t))
    want_c = num(m.group(1)); want_s = None if 'PLACEHOLDER' in m.group(2) else num(m.group(2))
    good = want_c == len(classes) and (want_s is None or want_s == len(settled))
    ok &= good
    print(f"{'ok  ' if good else 'FAIL'} {fam}: {len(hosts)} hosts, {len(classes)} classes up to isomorphism "
          f"and converse, {len(settled)} settled; the manuscript says {want_c} and "
          f"{'[PLACEHOLDER]' if want_s is None else want_s}")
sys.exit(0 if ok else 1)
