#!/usr/bin/env python3
"""Recompute CERT (portable) from the block each certificate publishes.

ROOT (CNF) commits to the SEARCH half only -- a sha256 chain over the CNF of
every cube.  The coverage instance's hash is a separate value, `split_cover_cnf`.
**CERT (portable) is the only published value that commits to both halves at
once**: it is the sha256 of a ten-line block naming q, k, the margin, the base,
the two orbit representatives, the cube count, ROOT (CNF) and `split_cover_cnf`.
The parameters are inside the hash on purpose, so a root cannot be matched
against a different instance's artifacts.

The `<inst>_cert.portable.txt` file IS that block plus one trailing
`CERT_PORTABLE=` line, which makes it self-auditing: strip the last line,
re-hash, compare.  That is what this does.

    usage: check_cert_portable.py DIR [DIR ...]

Each DIR is a certificate directory holding `*_cert.portable.txt`.  Every
positive check is paired with a control: perturbing one byte of the hashed block
must change the value.  A hash check whose control does not fire is not testing
anything -- it would pass just as happily on a file where the hash had been
copied from the block's own last line.

Exit 0 only if every certificate matches and every control fires.
"""
import glob
import hashlib
import os
import sys


def check(d):
    hits = glob.glob(os.path.join(d, '*_cert.portable.txt'))
    if not hits:
        print("  skip  %s: no *_cert.portable.txt" % d)
        return None
    ok = True
    for path in sorted(hits):
        txt = open(path).read()
        if 'CERT_PORTABLE=' not in txt:
            print("  FAIL  %s: no CERT_PORTABLE line" % path)
            ok = False
            continue
        i = txt.index('CERT_PORTABLE=')
        block, stated = txt[:i], txt[i:].split('=', 1)[1].strip()
        got = hashlib.sha256(block.encode()).hexdigest()
        name = os.path.basename(path)
        if got != stated:
            print("  FAIL  %s: recomputed %s, file states %s" % (name, got, stated))
            ok = False
            continue
        # the control: one byte of the block must change the value
        alt = block.replace('cubes=', 'cubes= ', 1)
        if alt == block:
            alt = block + ' '
        if hashlib.sha256(alt.encode()).hexdigest() == stated:
            print("  FAIL  %s: control did not fire -- a perturbed block hashed "
                  "to the same value" % name)
            ok = False
            continue
        # what it commits to, printed so the log says it rather than implying it
        fields = dict(l.split('=', 1) for l in block.strip().split('\n')
                      if '=' in l)
        print("  ok    %s: CERT (portable) recomputes; commits to "
              "search_root_cnf=%s… and split_cover_cnf=%s…, %s cubes; "
              "a one-byte change breaks it"
              % (name, fields.get('search_root_cnf', '?')[:8],
                 fields.get('split_cover_cnf', '?')[:8], fields.get('cubes', '?')))
    return ok


if __name__ == '__main__':
    dirs = sys.argv[1:]
    if not dirs:
        sys.exit(__doc__)
    results = [check(d) for d in dirs]
    if all(r is None for r in results):
        print("  FAIL  no certificate directory held a portable block")
        sys.exit(1)
    sys.exit(0 if all(r is not False for r in results) else 1)
