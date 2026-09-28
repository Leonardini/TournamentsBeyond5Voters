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
import re
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


ANCHOR_RE = re.compile(r'^(none|(pair|vertex)-orbit\(([^()]*)\))$')


def check_anchoring(path, fields, bits, n):
    """The `anchoring=` field names the representatives that filtered the cube
    set down to `cubes=`, under Lemma 2.1 (ordered pairs) or Corollary 2.2
    (vertices).  Two things are checkable from shipped bytes, and both are
    checked here because a wrong one silently shrinks the search:

      * every representative lies IN THE BASE -- anchoring is decided from a
        base state, which knows only the order restricted to B, so a
        representative outside B matches nothing and filters anchored witnesses
        away;
      * a pair-orbit representative is an arc or a non-arc of THIS host, which
        the .bits now makes decidable (under v1's `q=` it was not).

    Orbit COMPLETENESS is not checkable from here and stays a human obligation,
    like the lemma itself; the point of recording the representatives is that it
    becomes auditable rather than implicit.
    """
    name = os.path.basename(path)
    anc = fields.get('anchoring')
    if anc is None:
        print("  FAIL  %s: a v2 block with no anchoring field" % name)
        return False
    m = ANCHOR_RE.match(anc)
    if not m:
        print("  FAIL  %s: unrecognised anchoring %r -- expected none, "
              "pair-orbit(...) or vertex-orbit(...)" % (name, anc))
        return False
    if anc == 'none':
        print("  ok    %s: anchoring=none, so every base state is live and no "
              "anchoring lemma is in the trust chain" % name)
        return True
    kind, body = m.group(2), m.group(3)
    base = [int(x) for x in fields.get('base', '').split(',') if x != '']
    reps = [f.split('=', 1)[1] for f in body.split(';')]
    if kind == 'vertex':
        vs = [[int(r)] for r in reps]
        lemma, what = 'Corollary 2.2', 'vertex'
    else:
        vs = [[int(x) for x in r.split(',')] for r in reps]
        lemma, what = 'Lemma 2.1', 'ordered-pair'
    flat = [v for p in vs for v in p]
    outside = sorted({v for v in flat if v not in base})
    if outside:
        print("  FAIL  %s: anchoring names %s, outside base %s -- anchored "
              "witnesses would be filtered away" % (name, outside, base))
        return False
    if any(v < 0 or v >= n for v in flat):
        print("  FAIL  %s: anchoring names a vertex outside 0..%d" % (name, n - 1))
        return False
    note = ''
    if kind == 'pair':
        # upper-triangle index of (i,j), i<j, in (0,1),(0,2),...,(n-2,n-1) order
        def is_arc(u, v):
            i, j = (u, v) if u < v else (v, u)
            k = sum(n - 1 - t for t in range(i)) + (j - i - 1)
            fwd = bits[k] == '1'
            return fwd if u < v else not fwd
        note = ', '.join('(%d,%d) %s' % (u, v, 'arc' if is_arc(u, v) else 'non-arc')
                         for u, v in vs)
        note = ' -- ' + note + ', derived from the host'
    print("  ok    %s: anchoring is %d %s representative(s) under %s, all inside "
          "the base%s" % (name, len(vs), what, lemma, note))
    return True


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
    return (n, bits)


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
            bound = check_host_binding(path, fields)
            if bound is False:
                ok = False
            else:
                n, bits = bound
                ok &= check_anchoring(path, fields, bits, n)
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
