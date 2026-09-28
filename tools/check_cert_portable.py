#!/usr/bin/env python3
"""Recompute CERT (portable) from the block each certificate publishes.

ROOT (CNF) commits to the SEARCH half only -- a sha256 chain over the CNF of
every cube.  The coverage instance's hash is a separate value, `split_cover_cnf`.
**CERT (portable) is the only published value that commits to both halves at
once**: it is the sha256 of a block naming the instance, ROOT (CNF) and
`split_cover_cnf`.  The parameters are inside the hash on purpose, so a root
cannot be matched against a different instance's artifacts.

The `*.portable.txt` file IS that block plus one trailing `CERT_PORTABLE=` line,
which makes it self-auditing: strip the last line, re-hash, compare.  That is
what this does, for **both block versions**:

  CERT-v1  names its host `q=<prime power>`, i.e. an isomorphism class.
  CERT-v2  names it `host_sha256=<sha256 of the canonical .bits string>`, an
           adjacency, and points at a local copy with `host_bits`.  For a v2
           block this script ALSO re-derives that hash from the shipped file --
           a block whose stated host identity is not the file it names would
           otherwise pass every check here while describing something else.
           See `certificates/CERT-v2.md` for why the field exists.

    usage: check_cert_portable.py DIR [DIR ...]

Each DIR is a certificate directory holding `*.portable.txt`.  Every positive
check is paired with a control: perturbing one byte of the hashed block, or one
bit of the host, must change the value.  A hash check whose control does not
fire is not testing anything -- it would pass just as happily on a file where
the hash had been copied from the block's own last line.

Exit 0 only if every certificate matches and every control fires.
"""
import glob
import hashlib
import os
import sys


def canonical_bits(path):
    """(n, canonical bit string, sha256 of it) -- the same convention certroot
    uses: `0`/`1` characters only, whitespace stripped, n recovered from the
    length so it cannot disagree with the content."""
    b = "".join(c for c in open(path).read() if c in "01")
    n = int((1 + (1 + 8 * len(b)) ** 0.5) / 2)
    if n * (n - 1) // 2 != len(b):
        raise ValueError("%s: %d bits is not n(n-1)/2 for any n" % (path, len(b)))
    return n, b, hashlib.sha256(b.encode()).hexdigest()


def check_host_binding(path, fields):
    """For a v2 block: the named .bits file must BE the host the block commits
    to.  Returns True/False, printing what it found."""
    name = os.path.basename(path)
    ref = fields.get('host_bits')
    stated = fields.get('host_sha256')
    if not ref or not stated:
        print("  FAIL  %s: a v2 block without host_bits/host_sha256" % name)
        return False
    p = os.path.join(os.path.dirname(os.path.abspath(path)), ref)
    if not os.path.exists(p):
        print("  FAIL  %s: host_bits %s does not resolve" % (name, ref))
        return False
    n, bits, got = canonical_bits(p)
    if got != stated:
        print("  FAIL  %s: %s hashes to %s, block states %s"
              % (name, ref, got, stated))
        return False
    if str(n) != fields.get('host_n'):
        print("  FAIL  %s: host_n=%s but %s holds n=%d"
              % (name, fields.get('host_n'), ref, n))
        return False
    # the control: reversing ONE arc of the host must break the binding
    flipped = ('0' if bits[0] == '1' else '1') + bits[1:]
    if hashlib.sha256(flipped.encode()).hexdigest() == stated:
        print("  FAIL  %s: control did not fire -- a one-arc change to the host "
              "hashed to the same identity" % name)
        return False
    print("  ok    %s: host_sha256 re-derived from %s (n=%d, %s); reversing one "
          "arc breaks it" % (name, ref, n, fields.get('host_name', '?')))
    return True


def check(d):
    hits = glob.glob(os.path.join(d, '*.portable.txt'))
    if not hits:
        print("  skip  %s: no *.portable.txt" % d)
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
        lines = block.strip().split('\n')
        version = lines[0].split()[0] if lines else '?'
        fields = dict(l.split('=', 1) for l in lines if '=' in l)
        # what it commits to, printed so the log says it rather than implying it
        print("  ok    %s: %s recomputes; commits to search_root_cnf=%s… and "
              "split_cover_cnf=%s…, %s cubes; a one-byte change breaks it"
              % (name, version, fields.get('search_root_cnf', '?')[:8],
                 fields.get('split_cover_cnf', '?')[:8], fields.get('cubes', '?')))
        if version == 'CERT-v2':
            ok &= check_host_binding(path, fields)
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
