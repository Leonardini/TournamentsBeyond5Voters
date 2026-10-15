#!/usr/bin/env python3
"""Check every witness of a descent level against a host REBUILT from its name.

A descent host is named after the tournament it comes from and the vertices
deleted from it, 0-based, in the parent's own labelling:

    d005_mv04_15          drt23/d005.bits minus vertices 4 and 15
    d000_mv00_01_02       drt23/d000.bits minus vertices 0, 1 and 2
    p27_mv00_01_mv03_...  (any parent passed with --parent NAME=BITS)

The remaining vertices keep their order, which is how every descent kit built
its hosts.  So the host is derived here from the parent's bit string, and the
search's own host file is never read: a witness that verifies against the
derived host is a witness for the tournament its name says, whatever the kit
did.  Each witness is then checked the way verify/verify_witness_bits.py checks
one -- five permutations of the n vertices, every arc carried by at least 3 of
5 (or exactly 3 at unit margin) -- sharing no code with the search.

Input is any mix of directories and .tar/.tar.zst archives.  A file counts as a
witness when it holds a `WITNESS` block followed by `voter i:` lines; the host
is the file name up to its first dot, or the directory above `log/` for a kit
that logs per base state (`results/<host>/log/c<lo>.log`).  Files whose name
contains `BADWITNESS` are a kit's record of a witness whose verification step
exited non-zero.  That also happens for reasons outside the witness (a full
disk on the cluster stops the checker writing its report), so such a file is
neither counted as evidence nor treated as an error: it is checked and the
outcome reported.

The negative control is --selftest: the first witness found is checked against
its host with one arc reversed, and must fail on exactly that arc.

    usage: verify_descent_witnesses.py [--names FILE] [--parent NAME=BITS ...]
                                       [--drt-dir DIR] [--selftest]
                                       INPUT [INPUT ...]

--names FILE: one host per line; exit non-zero unless EVERY name has at least
one verified witness.  Without it, exit non-zero only on a failed witness.
"""
import io
import itertools
import os
import re
import subprocess
import sys
import tarfile

NAME = re.compile(r'^(?P<parent>.+?)_mv(?P<del>\d+(?:_\d+)*)$')


def load_bits(path):
    s = ''.join(c for c in open(path).read() if c in '01')
    n = int((1 + (1 + 8 * len(s)) ** 0.5) / 2)
    if n * (n - 1) // 2 != len(s):
        raise SystemExit('%s: %d bits is not n(n-1)/2' % (path, len(s)))
    adj = [[False] * n for _ in range(n)]
    for (i, j), c in zip(itertools.combinations(range(n), 2), s):
        adj[i][j] = c == '1'
        adj[j][i] = c != '1'
    return adj


def derive(name, parents, drt_dir, cache):
    """Adjacency of the host a descent name denotes, or None if unknown."""
    if name in cache:
        return cache[name]
    m = NAME.match(name)
    adj = None
    if m:
        # The longest parent prefix wins, so `p27_mv00_01` as a parent beats
        # reading `p27` with deletions 00_01_... .
        par, dels = None, None
        for cand in sorted(parents, key=len, reverse=True):
            if name.startswith(cand + '_mv'):
                par = cand
                dels = name[len(cand) + 3:]
                break
        if par is None:
            par, dels = m.group('parent'), m.group('del')
        src = parents.get(par)
        if src is None and drt_dir and re.match(r'^d\d{3}$', par):
            src = os.path.join(drt_dir, par + '.bits')
        if src and os.path.exists(src) and re.match(r'^\d+(?:_\d+)*$', dels):
            pa = load_bits(src)
            gone = {int(x) for x in dels.split('_')}
            keep = [v for v in range(len(pa)) if v not in gone]
            if len(keep) == len(pa) - len(gone):
                adj = [[pa[a][b] for b in keep] for a in keep]
    cache[name] = adj
    return adj


def ballots(text):
    if 'WITNESS' not in text:
        return None, None, None
    head = re.search(r'\bn=(\d+)', text)
    margin = re.search(r'\bmargin=(\w+)', text)
    body = text.split('WITNESS', 1)[1]
    orders = []
    for line in body.splitlines():
        mm = re.match(r'\s*voter\s+\d+:\s*(.*)$', line)
        if mm:
            orders.append([int(x) for x in mm.group(1).split()])
        elif orders:
            break
    return orders, (margin.group(1) if margin else 'majority'), \
        (int(head.group(1)) if head else None)


def check(adj, orders, margin, k=5):
    n = len(adj)
    if len(orders) != k:
        return 'expected %d voters, got %d' % (k, len(orders))
    for o in orders:
        if sorted(o) != list(range(n)):
            return 'a voter order is not a permutation of 0..%d' % (n - 1)
    pos = [{v: i for i, v in enumerate(o)} for o in orders]
    need = (k + 1) // 2
    for i in range(n):
        for j in range(i + 1, n):
            u, v = (i, j) if adj[i][j] else (j, i)
            c = sum(1 for p in pos if p[u] < p[v])
            if c < need or (margin == 'exact' and c != need):
                return 'arc %d->%d carried by %d of %d' % (u, v, c, k)
    return None


def files(inputs):
    """(display name, host, text) for every candidate file in the inputs."""
    for inp in inputs:
        if os.path.isdir(inp):
            for dp, _, fns in os.walk(inp):
                for fn in sorted(fns):
                    p = os.path.join(dp, fn)
                    yield p, open(p, errors='replace').read()
        else:
            if inp.endswith('.zst'):
                raw = subprocess.run(['zstd', '-dc', inp], capture_output=True,
                                     check=True).stdout
                tf = tarfile.open(fileobj=io.BytesIO(raw))
            else:
                tf = tarfile.open(inp)
            for m in tf:
                if m.isfile():
                    yield (inp + ':' + m.name,
                           tf.extractfile(m).read().decode('utf8', 'replace'))


def host_of(path):
    base = os.path.basename(path.split(':')[-1])
    parts = path.split(':')[-1].split('/')
    if len(parts) >= 3 and parts[-2] == 'log' and re.match(r'^c\d+\.log$', base):
        return parts[-3]
    return base.split('.', 1)[0]


def main():
    args = sys.argv[1:]
    names_file, parents, drt_dir, selftest, inputs = None, {}, None, False, []
    while args:
        a = args.pop(0)
        if a == '--names':
            names_file = args.pop(0)
        elif a == '--parent':
            k, v = args.pop(0).split('=', 1)
            parents[k] = v
        elif a == '--drt-dir':
            drt_dir = args.pop(0)
        elif a == '--selftest':
            selftest = True
        else:
            inputs.append(a)
    cache, good, rej, fails, unknown, seen = {}, set(), 0, 0, 0, 0
    control = None
    for path, text in files(inputs):
        orders, margin, n = ballots(text)
        if not orders:
            continue
        seen += 1
        host = host_of(path)
        adj = derive(host, parents, drt_dir, cache)
        rejected = 'BADWITNESS' in path
        if adj is None:
            unknown += 1
            print('UNKNOWN  %s: cannot rebuild host %s from its name' % (path, host))
            continue
        why = 'log says n=%s, host has %d vertices' % (n, len(adj)) \
            if n is not None and n != len(adj) else check(adj, orders, margin)
        if selftest and control is None and why is None and not rejected:
            control = (path, adj, orders, margin)
        if rejected:
            rej += 1
            print('note     %s: rejected by its kit; here it %s' % (
                path, 'VERIFIES' if why is None else 'fails (%s)' % why))
        elif why is None:
            good.add(host)
        else:
            fails += 1
            print('FAIL     %s: %s' % (path, why))
    if selftest:
        if control is None:
            print('FAIL     selftest: no verified witness to perturb')
            fails += 1
        else:
            path, adj, orders, margin = control
            flipped = [row[:] for row in adj]
            flipped[0][1], flipped[1][0] = adj[1][0], adj[0][1]
            why = check(flipped, orders, margin)
            if why and why.startswith(('arc 0->1', 'arc 1->0')):
                print('control  %s: with arc (0,1) reversed the witness fails, '
                      'on that arc (%s)' % (path, why))
            else:
                fails += 1
                print('FAIL     selftest: reversing arc (0,1) gave %r' % (why,))
    missing = []
    if names_file:
        want = [l.split()[0] for l in open(names_file)
                if l.strip() and not l.startswith('#')]
        missing = [w for w in want if w not in good]
        for w in missing[:20]:
            print('MISSING  %s: no verified witness' % w)
        print('%d named hosts, %d with a verified witness, %d missing'
              % (len(want), len(want) - len(missing), len(missing)))
    print('%d witness files: %d hosts verified, %d failed, %d unrebuildable, '
          '%d rejected by their kit (not counted)'
          % (seen, len(good), fails, unknown, rej))
    return 1 if (fails or unknown or missing) else 0


if __name__ == '__main__':
    sys.exit(main())
