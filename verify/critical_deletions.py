#!/usr/bin/env python3
"""Is every one-vertex deletion of a host inside a class with a witness?

A tournament T is vertex-critical when T - v is 5-inducible for every vertex v.
The witnesses for those deletions were banked under the names of the descent
level (a deletion of the 23-vertex parent), not under T's own labelling, so
this matches by class: T - v is covered when it is isomorphic, or converse, to
a host that has a verified witness.

    usage: critical_deletions.py HOST.bits LEVEL.tsv WITNESSED.txt [--labelg PATH]

LEVEL.tsv supplies the bit strings of the witnessed hosts (name first, bits
last); WITNESSED.txt lists the hosts whose witnesses verified.  Exit 0 only if
all n deletions are covered.
"""
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from level_coverage import canon, digraph6, from_bits


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
    host, level, witnessed = args
    adj = from_bits(''.join(c for c in open(host).read() if c in '01'))
    n = len(adj)
    bits = {}
    for line in open(level):
        if line.startswith('#') or not line.strip():
            continue
        f = line.split()
        bits[f[0]] = f[-1]
    wit = [l.split()[0] for l in open(witnessed) if l.strip()]
    missing = [w for w in wit if w not in bits]
    wadj = [from_bits(bits[w]) for w in wit if w in bits]
    wf = canon([digraph6(a) for a in wadj], labelg)
    wr = canon([digraph6([list(r) for r in zip(*a)]) for a in wadj], labelg)
    have = {min(a, b) for a, b in zip(wf, wr)}
    dels = []
    for v in range(n):
        keep = [u for u in range(n) if u != v]
        dels.append([[adj[a][b] for b in keep] for a in keep])
    df = canon([digraph6(a) for a in dels], labelg)
    dr = canon([digraph6([list(r) for r in zip(*a)]) for a in dels], labelg)
    open_ = [v for v, (a, b) in enumerate(zip(df, dr)) if min(a, b) not in have]
    print('%s: %d of %d one-vertex deletions lie in a witnessed class%s'
          % (os.path.basename(host), n - len(open_), n,
             '' if not open_ else '; uncovered vertices (0-based): %s' % open_))
    for w in missing[:5]:
        print('FAIL: witnessed host %s has no bit string in %s' % (w, level))
    return 1 if (open_ or missing) else 0


if __name__ == '__main__':
    sys.exit(main())
