#!/usr/bin/env python3
"""Verify every node count quoted in the package's PROSE against the archives.

Why this exists.  Appendix A.3's q=27 cell once printed `dom_nodes` where the
column is `nodes` (1.14e8 against the true 6.22e9).  The manuscript was fixed on
2026-09-11; REPRODUCE.md and evidence/README.md were not, and kept the wrong
number for five days while `tools/check_package.sh` passed 37/0 every time.
Nothing caught it because `check_manuscript.py` re-derives the column but reads
only `manuscript/*.md`, and MANIFEST.sha256 pins BYTES, not MEANING -- a file
whose content is wrong but unchanged hashes clean for ever.

So this points the same re-derivation at the prose.  Two checks:

  1. WRONG COUNTER (the one that would have caught it).  Every archive's
     `dom_nodes` total is computed, and any prose that presents that value as a
     node count FAILS, naming the counter and giving the right figure.  There is
     no parsing guesswork: we know exactly what the wrong number looks like
     because we compute it.
  2. QUOTED VALUE.  Where a line or its heading identifies a q -- `Paley(27)`,
     `p27_majority.tar.zst`, `q = 27`, or a markdown table row under a `nodes`
     column -- the quoted figure is compared with that archive's `nodes` total.

A number matching neither is reported as UNATTRIBUTED, not as a failure: plenty
of legitimate node counts come from runs with no archive here.

Both checks read `MAJORITY_ARCHIVE` from check_manuscript.py rather than
restating it, so the two tools cannot verify different runs while both passing.

    usage: check_quoted_nodes.py [--verbose]     (exit 1 if anything FAILs)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from check_manuscript import MAJORITY_ARCHIVE, ROOT, archive_totals, close

SUPER = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹', '0123456789')

# a number in any rendering the package actually uses, then `nodes` close by
NUM = r'(?:[0-9][0-9,]*(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)'
LATEX = re.compile(r'([0-9.]+)\s*(?:\\times|×)\s*10\s*\^?\s*\{?\s*(-?[0-9]+)\s*\}?')
UNI = re.compile(r'([0-9.]+)\s*×\s*10([⁰¹²³⁴⁵⁶⁷⁸⁹]+)')
INLINE = re.compile(r'(\$?' + NUM + r'(?:\s*(?:\\times|×)\s*10\s*\^?\s*\{?-?[0-9]+\}?)?\$?)'
                    r'[\s,\$}]{0,4}nodes\b')
# A node count is only CHECKED where the context names the majority sweep beyond
# doubt.  Anything looser is noise: the package quotes node counts for dozens of
# other runs -- arc-reversed hosts, minus-vertex hosts, per-state probes -- and a
# checker that flags those trains its reader to ignore it.  Three anchors, all
# unambiguous:
ARCHIVE_NAME = re.compile(r'(?:rerun1_)?p([0-9]{2})_majority')      # evidence/README.md
SWEEP_SHAPE = re.compile(                                          # REPRODUCE.md
    r'([0-9.]+)\s*core-h,\s*(' + NUM + r')\s*nodes,\s*coverage')
Q_CELL = re.compile(r'^\$?([0-9]{2})\$?$')


def to_float(tok):
    """Parse 6.22e9 / 6,216,913,092 / $6.22 \\times 10^{9}$ / 6.22 x 10^9."""
    t = tok.strip().strip('$').strip()
    m = UNI.search(t)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2).translate(SUPER))
    m = LATEX.search(t)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2))
    t = t.replace(',', '')
    try:
        return float(t)
    except ValueError:
        return None


def totals():
    """{q: (nodes, dom_nodes)} for every archive present."""
    out = {}
    for q, name in sorted(MAJORITY_ARCHIVE.items()):
        tot = archive_totals(name)
        if tot:
            out[q] = (tot[1], tot[2])
    return out


def prose_files():
    skip = {'.git', 'manuscript'}       # manuscript is check_manuscript.py's job
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith('.')]
        for fn in sorted(filenames):
            if fn.endswith('.md'):
                yield os.path.join(dirpath, fn)


def quoted(path):
    """Every `<number> nodes` in the file: (lineno, token, value)."""
    out = []
    for i, line in enumerate(open(path, errors='replace').read().splitlines(), 1):
        for tok in INLINE.findall(line):
            v = to_float(tok)
            if v is not None:
                out.append((i, tok, v))
    return out


def attributed(path):
    """Only node counts whose q is beyond doubt: (lineno, token, value, q)."""
    out = []
    nodes_col = q_col = None
    for i, line in enumerate(open(path, errors='replace').read().splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            if any(c.lower() == 'nodes' for c in cells):
                nodes_col = next(j for j, c in enumerate(cells) if c.lower() == 'nodes')
                q_col = 0 if Q_CELL.match(cells[0]) or cells[0].strip('$') in ('q', '') else None
                continue
            if set(''.join(cells)) <= set('-: '):
                continue
            if nodes_col is not None and q_col is not None and len(cells) > nodes_col:
                m = Q_CELL.match(cells[q_col])
                v = to_float(cells[nodes_col])
                if m and v is not None:
                    out.append((i, cells[nodes_col], v, int(m.group(1))))
                continue
        else:
            nodes_col = q_col = None
        m = SWEEP_SHAPE.search(line)
        a = ARCHIVE_NAME.search(line)
        if m and a:
            v = to_float(m.group(2))
            if v is not None:
                out.append((i, m.group(2), v, int(a.group(1))))
        elif a:
            for tok in INLINE.findall(line):
                v = to_float(tok)
                if v is not None:
                    out.append((i, tok, v, int(a.group(1))))
        elif m:
            out.append((i, m.group(2), to_float(m.group(2)), None))
    return [(i, t, v, q) for i, t, v, q in out if v is not None]


def run(verbose=False):
    tot = totals()
    if not tot:
        print("  skip  no archives readable (zstd missing?)")
        return 0
    fails = ok = seen = 0

    def wrong_counter(val):
        """q whose dom_nodes this value is, if it is not also a nodes total."""
        for aq, (n, d) in tot.items():
            if close(val, d, 0.01) and not close(val, n, 0.01):
                return aq
        return None

    for path in prose_files():
        rel = os.path.relpath(path, ROOT)
        reported = set()

        # 1. WRONG COUNTER -- applies everywhere, and needs no attribution.
        #    Only sees `<number> nodes` in running text.
        for lineno, tok, val in quoted(path):
            seen += 1
            aq = wrong_counter(val)
            if aq is not None:
                print("  FAIL  %s:%d quotes %s as a node count -- that is "
                      "dom_nodes for q=%d; nodes is %.3g"
                      % (rel, lineno, tok, aq, tot[aq][0]))
                fails += 1
                reported.add(lineno)

        # 2. QUOTED VALUE -- only where the sweep is named beyond doubt.  This
        #    also carries the dom_nodes diagnosis for TABLE CELLS, which check 1
        #    cannot see: a cell has no adjacent word `nodes`, the column header
        #    does.  Deferring to check 1 here would let exactly that case pass.
        for lineno, tok, val, q in attributed(path):
            if q not in tot or lineno in reported:
                continue
            n, d = tot[q]
            if close(val, n, 0.01):
                ok += 1
                if verbose:
                    print("  ok    %s:%d q=%d nodes %s" % (rel, lineno, q, tok))
                continue
            aq = wrong_counter(val)
            if aq is not None:
                print("  FAIL  %s:%d quotes %s as a node count -- that is "
                      "dom_nodes for q=%d; nodes is %.3g"
                      % (rel, lineno, tok, aq, tot[aq][0]))
            else:
                print("  FAIL  %s:%d q=%d quotes %s, the archive says %.3g"
                      % (rel, lineno, q, tok, n))
            fails += 1
            reported.add(lineno)
    print("  %d node counts scanned, %d verified against an archive, %d FAIL"
          % (seen, ok, fails))
    return 1 if fails else 0


def selftest():
    """Negative control: the check must FAIL on a dom_nodes value presented as nodes.

    A check that has never been seen to fire is not evidence of anything.
    """
    tot = totals()
    if not tot:
        return 0
    q = sorted(tot)[0]
    n, d = tot[q]
    for label, val, want_fail in (('dom_nodes as nodes', d, True), ('true nodes', n, False)):
        fired = any(close(val, dd, 0.01) and not close(val, nn, 0.01)
                    for nn, dd in tot.values())
        status = 'ok  ' if fired == want_fail else 'FAIL'
        print("  %s  control: %-20s -> %s" % (status, label, 'fires' if fired else 'silent'))
        if fired != want_fail:
            return 1
    return 0


if __name__ == '__main__':
    rc = selftest()
    rc |= run('--verbose' in sys.argv[1:])
    sys.exit(rc)
