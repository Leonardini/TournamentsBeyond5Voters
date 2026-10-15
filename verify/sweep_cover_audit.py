#!/usr/bin/env python3
"""Audit a complete per-base-state sweep from its markers alone.

A sweep refutes its host only if its markers tile [0, base_states) exactly,
every one reports UNSAT with capped=0, and all of them were written against the
same host, n, base and base-state count -- markers from two different bases
would tile the range perfectly and cover nothing.  This reads the markers out
of a .tar.zst (or a directory), checks all of that, recomputes the tree hash the
sweep's VERDICT.txt records (sha256 over name || bytes in sorted name order),
and prints the summed core-hours and nodes.

    usage: sweep_cover_audit.py MARKERS(.tar.zst|dir) [--verdict VERDICT.txt]

Marker lines look like
    host=d005_mv04 n=22 lo=0 hi=1 verdict=UNSAT capped=0 nodes=... secs=...
    base_states=8031 base=0,1,2,11,17
Exit 0 only for a complete, uncapped, uniform UNSAT cover whose tree hash
matches the verdict file when one is given.
"""
import hashlib
import io
import os
import re
import subprocess
import sys
import tarfile


def markers(src):
    """{file name: bytes} for every file under a `done/` directory."""
    out = {}
    if os.path.isdir(src):
        for dp, _, fns in os.walk(src):
            if os.path.basename(dp) == 'done':
                for fn in fns:
                    out[fn] = open(os.path.join(dp, fn), 'rb').read()
        return out
    raw = subprocess.run(['zstd', '-dc', src], capture_output=True, check=True).stdout
    tf = tarfile.open(fileobj=io.BytesIO(raw))
    for m in tf:
        if m.isfile() and '/done/' in m.name:
            out[os.path.basename(m.name)] = tf.extractfile(m).read()
    return out


def main():
    args = sys.argv[1:]
    verdict = None
    if '--verdict' in args:
        i = args.index('--verdict')
        verdict = args[i + 1]
        del args[i:i + 2]
    src = args[0]
    mk = markers(src)
    if not mk:
        print('FAIL: no markers under a done/ directory in %s' % src)
        return 1
    recs = {}
    for name, data in mk.items():
        recs[name] = dict(kv.split('=', 1) for kv in data.decode().split() if '=' in kv)
    problems = []
    for field in ('host', 'n', 'base', 'base_states'):
        vals = {r.get(field) for r in recs.values()}
        if len(vals) != 1:
            problems.append('%s is not uniform: %s' % (field, sorted(vals)[:4]))
    total = int(next(iter(recs.values())).get('base_states', 0))
    spans = sorted((int(r['lo']), int(r['hi'])) for r in recs.values())
    pos = 0
    for lo, hi in spans:
        if lo != pos:
            problems.append('gap or overlap at base state %d (next marker starts %d)'
                            % (pos, lo))
            break
        pos = hi
    if pos != total:
        problems.append('cover ends at %d, base_states is %d' % (pos, total))
    bad = [n for n, r in recs.items() if r.get('verdict') != 'UNSAT'
           or r.get('capped') != '0']
    if bad:
        problems.append('%d markers not UNSAT with capped=0 (e.g. %s)' % (len(bad), bad[0]))
    misnamed = [n for n, r in recs.items() if n != 'c' + r.get('lo', '')]
    if misnamed:
        problems.append('%d marker names do not match their lo field' % len(misnamed))
    h = hashlib.sha256()
    for name in sorted(mk):
        h.update(name.encode())
        h.update(mk[name])
    tree = h.hexdigest()
    if verdict:
        m = re.search(r'tree sha256\s+([0-9a-f]{64})', open(verdict).read())
        if not m:
            problems.append('no tree sha256 in %s' % verdict)
        elif m.group(1) != tree:
            problems.append('tree sha256 %s, the verdict records %s' % (tree, m.group(1)))
    r0 = next(iter(recs.values()))
    secs = sum(float(r['secs']) for r in recs.values())
    nodes = sum(int(r['nodes']) for r in recs.values())
    print('%s: %d markers, base %s, %s of %d base states, %.1f core-h, %d nodes, '
          'tree sha256 %s' % (r0.get('host'), len(recs), r0.get('base'),
                              'complete UNSAT cover' if not problems else 'NOT a cover',
                              total, secs / 3600, nodes, tree[:16]))
    for p in problems:
        print('FAIL: %s' % p)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
