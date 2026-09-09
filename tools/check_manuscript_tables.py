#!/usr/bin/env python3
"""Check a built manuscript PDF for the two table defects that are invisible in the source.

    python3 check_manuscript_tables.py Tournaments_not_inducible_by_five_voters

Reads the .md for the tables and the .pdf for what they became, and reports

  WRAPPED   a row whose first and last cell did not land on the same output line.
            Pandoc splits pipe-table width evenly across the dash runs of the
            separator line, so one long label in an otherwise narrow table wraps
            while its neighbours sit two-thirds empty.  The fix is proportional
            dash runs, e.g. |------------------|-----|-----|----:|, and only if
            that is not enough is the cell genuinely too wide for the page.

  SPLIT     a table whose header appears on two pages.  Pandoc emits longtable,
            which repeats the header and breaks where it likes.

Comparison is on a reduced alphabet -- letters and digits only, LaTeX macro names
stripped -- so subscripts, \\le, minus signs and monospace cells cannot fake a pass.
Requires pdftotext (poppler).
"""
import re, subprocess, sys, tempfile, os

def key(cell):
    cell = re.sub(r'\\(?:mathrm|mathbb|bar|text|mathcal)\{([^}]*)\}', r'\1', cell)
    cell = re.sub(r'\\[a-zA-Z]+', ' ', cell)          # \le, \mu, \times leave no letters
    return re.sub(r'[^A-Za-z0-9]', '', cell)

def tables(md_lines):
    out, cur = [], []
    for line in md_lines:
        if line.startswith('|'):
            cur.append(line)
        else:
            if len(cur) >= 3: out.append(cur)
            cur = []
    if len(cur) >= 3: out.append(cur)
    return out

def main(stem):
    md = open(stem + '.md').read().split('\n')
    with tempfile.TemporaryDirectory() as d:
        txt = os.path.join(d, 'rendered.txt')
        subprocess.run(['pdftotext', '-layout', stem + '.pdf', txt], check=True)
        raw = open(txt).read()
    rendered = [(l, key(l)) for l in raw.split('\n')]
    pages = raw.split('\f')

    bad = 0
    for t in tables(md):
        rows = [r for r in t if not re.match(r'^\|[\s:|-]+\|$', r)]
        name = key(rows[0].strip('|').split('|')[0]) or '(unnamed)'
        for r in rows:
            cells = [key(c) for c in r.strip('|').split('|')]
            if not cells[0] or not cells[-1]: continue
            first, last = cells[0], cells[-1]
            if not any(first in k and last in k and k.index(first) <= k.rindex(last)
                       for _, k in rendered):
                print("WRAPPED  table[%s] row %r: last cell %r is on another line"
                      % (name, first[:40], last[:28]))
                bad += 1

    # a table header that shows up on two pages means longtable broke the table
    seen = {}
    for i, page in enumerate(pages, 1):
        for line in page.split('\n'):
            if line.strip() and len(re.findall(r'\S {3,}\S', line)) >= 2:
                seen.setdefault(' '.join(line.split()), []).append(i)
    for row, where in seen.items():
        if len(set(where)) > 1:
            print("SPLIT    %r appears on pages %s" % (row[:70], sorted(set(where))))
            bad += 1

    n = len(tables(md))
    print("%d tables checked, %d problem(s)" % (n, bad))
    return 1 if bad else 0

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1].removesuffix('.md').removesuffix('.pdf')))
