#!/usr/bin/env python3
"""Check that witnessed hosts cover EVERY class of a descent level.

A level lists hosts by name with their bit strings, and may hold several
labellings of one tournament.  5-inducibility is invariant under isomorphism
and under reversing every arc (the converse), so a level is settled when every
class under those two operations contains a host with a verified witness.
This recomputes the classes from the bit strings with nauty's `labelg` -- a
class key is the smaller of the canonical forms of T and of its converse -- and
reports any class that no witnessed host reaches.

    usage: level_coverage.py LEVEL.tsv WITNESSED.txt [--labelg PATH]

LEVEL.tsv: name, n, base, base_states, bits (comment lines start with #).
WITNESSED.txt: one host name per line, each with a verified witness; every name
must also appear in LEVEL.tsv, so a witness for some other tournament cannot be
counted.  Exit 0 only if every class is covered.
"""
import itertools
import os
import shutil
import subprocess
import sys


def digraph6(adj):
    n = len(adj)
    assert n < 63
    bits = [1 if adj[i][j] else 0 for i in range(n) for j in range(n)]
    bits += [0] * (-len(bits) % 6)
    out = '&' + chr(63 + n)
    for k in range(0, len(bits), 6):
        v = 0
        for b in bits[k:k + 6]:
            v = 2 * v + b
        out += chr(63 + v)
    return out


def from_bits(s):
    n = int((1 + (1 + 8 * len(s)) ** 0.5) / 2)
    adj = [[False] * n for _ in range(n)]
    for (i, j), c in zip(itertools.combinations(range(n), 2), s):
        adj[i][j] = c == '1'
        adj[j][i] = c != '1'
    return adj


def canon(lines, labelg):
    r = subprocess.run([labelg, '-q'], input='\n'.join(lines) + '\n',
                       capture_output=True, text=True, check=True)
    out = r.stdout.split()
    assert len(out) == len(lines), 'labelg returned %d of %d' % (len(out), len(lines))
    return out


def main():
    args = sys.argv[1:]
    labelg = None
    if '--labelg' in args:
        i = args.index('--labelg')
        labelg = args[i + 1]
        del args[i:i + 2]
    labelg = labelg or os.environ.get('LABELG') or shutil.which('labelg')
    if not labelg:
        print('FAIL: labelg not found (set LABELG or pass --labelg)')
        return 1
    level, witnessed = args
    hosts = []
    for line in open(level):
        if line.startswith('#') or not line.strip():
            continue
        f = line.split()
        hosts.append((f[0], f[-1]))
    names = {h for h, _ in hosts}
    wit = [l.split()[0] for l in open(witnessed) if l.strip()]
    stray = [w for w in wit if w not in names]
    fwd, rev = [], []
    for _, b in hosts:
        adj = from_bits(b)
        fwd.append(digraph6(adj))
        rev.append(digraph6([list(r) for r in zip(*adj)]))
    cf, cr = canon(fwd, labelg), canon(rev, labelg)
    iso = {c for c in cf}
    key = {h: min(a, b) for (h, _), a, b in zip(hosts, cf, cr)}
    classes = set(key.values())
    hit = {key[w] for w in wit if w in key}
    open_ = classes - hit
    print('%d hosts -> %d isomorphism classes -> %d classes up to converse; '
          '%d witnessed hosts reach %d of them, %d uncovered'
          % (len(hosts), len(iso), len(classes), len(set(wit)), len(hit), len(open_)))
    for w in stray[:10]:
        print('FAIL: witnessed host %s is not in the level' % w)
    return 1 if (open_ or stray) else 0


if __name__ == '__main__':
    sys.exit(main())
