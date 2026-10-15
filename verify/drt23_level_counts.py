#!/usr/bin/env python3
"""Count the classes at each level below the doubly regular tournaments on 23.

The 36 doubly regular tournaments on 23 vertices other than Paley(23) form 18
pairs under reversing every arc.  Deleting j vertices from one member of each
pair, in every possible way, and identifying results that are isomorphic or
converse to each other gives the j-th level of the descent (manuscript,
Appendix G).  A deletion of the converse parent is the converse of a deletion of
the parent, so one parent per pair reaches every class.

    usage: drt23_level_counts.py DRT_DIR PARENTS.txt [--levels 1,2,3]
                                 [--labelg PATH] [--names LEVEL.tsv]

PARENTS.txt holds the 18 parent names (d000, d001, ...), one per line.  For
each level the script prints the number of labelled deletions, isomorphism
classes, and classes up to converse.  With --names, the host names in
LEVEL.tsv (name first, bits last) must be exactly one per class of that
level, each a correctly derived deletion -- which is what makes that file's
witnessed hosts a statement about the classes rather than about file rows.
"""
import itertools
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from level_coverage import canon, digraph6, from_bits


def load(path):
    return from_bits(''.join(c for c in open(path).read() if c in '01'))


def main():
    args = sys.argv[1:]
    opt = {}
    for flag in ('--levels', '--labelg', '--names'):
        if flag in args:
            i = args.index(flag)
            opt[flag] = args[i + 1]
            del args[i:i + 2]
    drt_dir, parents_file = args
    labelg = opt.get('--labelg') or os.environ.get('LABELG') or shutil.which('labelg')
    if not labelg:
        print('FAIL: labelg not found (set LABELG or pass --labelg)')
        return 1
    parents = [l.split()[0] for l in open(parents_file) if l.strip()]
    # The parents must be ONE PER CONVERSE PAIR of the doubly regular
    # tournaments in DRT_DIR other than the self-converse ones (Paley(23)):
    # every other file is a parent or the converse of exactly one parent.
    drts = sorted(f[:-5] for f in os.listdir(drt_dir) if f.endswith('.bits'))
    adjs = {d: load(os.path.join(drt_dir, d + '.bits')) for d in drts}
    cf = dict(zip(drts, canon([digraph6(adjs[d]) for d in drts], labelg)))
    cr = dict(zip(drts, canon([digraph6([list(r) for r in zip(*adjs[d])])
                               for d in drts], labelg)))
    selfc = [d for d in drts if cf[d] == cr[d]]
    others = {cf[d] for d in drts if d not in selfc}
    reached = {cf[p] for p in parents} | {cr[p] for p in parents}
    pairs_ok = (reached == others and len(parents) * 2 == len(others)
                and not set(parents) & set(selfc))
    print('%d tournaments in %s/, %d self-converse (%s); the %d parents and their '
          'converses are exactly the other %d: %s'
          % (len(drts), os.path.basename(os.path.normpath(drt_dir)), len(selfc),
             ','.join(selfc) or 'none', len(parents),
             len(others), 'ok' if pairs_ok else 'FAIL'))
    levels = [int(x) for x in opt.get('--levels', '1,2,3').split(',')]
    named = {}
    if '--names' in opt:
        for line in open(opt['--names']):
            if line.startswith('#') or not line.strip():
                continue
            f = line.split()
            named[f[0]] = f[-1]
    rc = 0 if pairs_ok else 1
    for j in levels:
        fwd, rev, labels = [], [], []
        for p in parents:
            adj = load(os.path.join(drt_dir, p + '.bits'))
            n = len(adj)
            for gone in itertools.combinations(range(n), j):
                keep = [v for v in range(n) if v not in gone]
                sub = [[adj[a][b] for b in keep] for a in keep]
                fwd.append(digraph6(sub))
                rev.append(digraph6([list(r) for r in zip(*sub)]))
                labels.append(p + '_mv' + '_'.join('%02d' % g for g in gone))
        cf, cr = canon(fwd, labelg), canon(rev, labelg)
        key = [min(a, b) for a, b in zip(cf, cr)]
        print('level %d: %d deletions -> %d isomorphism classes -> %d classes '
              'up to converse' % (j, len(fwd), len(set(cf)), len(set(key))))
        if named and len(next(iter(named.values()))) == (n - j) * (n - j - 1) // 2:
            by_label = dict(zip(labels, key))
            index = {h: i for i, h in enumerate(labels)}
            bad = [h for h in named if h not in by_label]
            hit = [by_label[h] for h in named if h in by_label]
            rows = sum(1 for h in named if h in by_label)
            ok = not bad and len(set(hit)) == rows == len(set(key))
            for h in bad[:5]:
                print('  FAIL %s is not a deletion of the listed parents' % h)
            # the row's bits must be the deletion its name says
            wrong = 0
            for h, b in named.items():
                if h in by_label:
                    i = index[h]
                    adj = from_bits(b)
                    if digraph6(adj) != fwd[i]:
                        wrong += 1
            print('  %s: %d rows, %d distinct classes, %d bit strings differ from '
                  'their names' % ('ok' if ok and not wrong else 'FAIL', rows,
                                   len(set(hit)), wrong))
            rc |= 0 if ok and not wrong else 1
    return rc


if __name__ == '__main__':
    sys.exit(main())
