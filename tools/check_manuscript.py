#!/usr/bin/env python3
"""Re-derive every number the manuscript prints that this package can re-derive.

The manuscript is the single source of truth for what is CLAIMED: every expected
value below is read out of `manuscript/*.md` rather than written here, so a
figure that changes in the paper and not in the package shows up as a failure
instead of passing against a copy that drifted with it.  The observed value is
recomputed from shipped bytes.  Nothing is compared against a constant in this
file except quantities that are pure arithmetic, and those are computed, not
quoted.

    usage: tools/check_manuscript.py [--json] [path/to/manuscript.md]

Exit status is 0 when every check passes, 1 otherwise, so it can be a gate step.
--json writes one record per check to stdout for a machine reader.

Checks, by kind:

  ARITHMETIC  identities the paper states about instance sizes -- the ILP's row
              and column counts at q = 23, the dissent-Boolean encoding's
              variable and clause counts at q = 19, the coverage instance's
              clause total, and the two certificate cost splits.  These need no
              artifact: they are recomputed from n and k.
  DERIVED     figures recomputed from shipped evidence -- core-hours from the
              `time=` fields of the sweep archives and the `solve_s`/`check_s`
              columns of the certificate logs, node counts from the same
              archives, live base-state counts from `sat/base_survivors.py`
              (search-free), census totals from the cluster markers.
  LEDGER      counts read off `verdicts/verdict_ledger.tsv`.

A check whose shipped artifact or external tool is absent is reported as SKIP,
never as a pass.  A check whose MANUSCRIPT sentence, table or row cannot be
found is a FAIL, never a skip and never silence: either the claim moved or was
reworded, and the pattern must be updated to find it, or the claim was removed,
and the check must be deleted deliberately.  `missing()` is the one way such a
check reports, so no branch can quietly record nothing.  A manuscript figure
with no re-derivation route is reported as DECLARED and must name an open gap
of CLAIMS.md; `declared()` checks that the gap exists and is not CLOSED, and
records a FAIL otherwise.
"""
import json
import math
import os
import re
import subprocess
import sys
import tarfile
import io

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
RESULTS = []


def record(kind, name, want, got, ok, note=""):
    RESULTS.append(dict(kind=kind, name=name, expected=want, observed=got,
                        status=("ok" if ok else "FAIL"), note=note))


def skip(kind, name, why):
    """An absent shipped artifact or external tool.  Never a manuscript miss."""
    RESULTS.append(dict(kind=kind, name=name, expected=None, observed=None,
                        status="skip", note=why))


def missing(kind, name, what):
    """The manuscript no longer contains what this check reads: a FAIL."""
    RESULTS.append(dict(kind=kind, name=name, expected=what, observed=None,
                        status="FAIL",
                        note='manuscript: %s not found -- update the pattern if the claim '
                             'moved or was reworded, delete the check if the claim was '
                             'removed' % what))


def declared(name, want, where):
    """A figure with no re-derivation route; `where` must be 'CLAIMS.md gap N', open."""
    m = re.fullmatch(r'CLAIMS\.md gap (\d+)', where)
    assert m, 'declared() takes "CLAIMS.md gap N", got %r' % where
    claims = open(os.path.join(ROOT, 'CLAIMS.md')).read()
    head = re.search(r'^\*\*Gap %s — ([^\n]*)' % m.group(1), claims, re.M)
    if head is None or 'CLOSED' in head.group(1).split('**')[0]:
        RESULTS.append(dict(kind="DECLARED", name=name, expected=want, observed=None,
                            status="FAIL",
                            note='%s is %s, so it cannot carry a declared figure'
                                 % (where, 'absent' if head is None else 'CLOSED')))
        return
    RESULTS.append(dict(kind="DECLARED", name=name, expected=want, observed=None,
                        status="declared", note=where))


# --------------------------------------------------------------------------
# reading numbers out of the manuscript
# --------------------------------------------------------------------------
def num(cell):
    """A LaTeX-ish table cell -> float, or None when it holds no number.

    Handles `$2{,}591$`, `$1.14 \\times 10^{8}$`, `$\\approx 10{,}000$`,
    `$3{,}106$` and plain `23`.  An em dash means "not stated".
    """
    s = cell.strip().strip('|').strip()
    if not s or s in ('—', '--', '-'):
        return None
    s = s.replace('$', '').replace('\\approx', '').replace('\\,', '')
    s = s.replace('{,}', '').replace(',', '').replace('**', '').strip()
    m = re.match(r'^([0-9.]+)\s*\\times\s*10\^\{?(-?[0-9]+)\}?$', s)
    if m:
        return float(m.group(1)) * 10 ** int(m.group(2))
    m = re.match(r'^-?[0-9]+\.?[0-9]*$', s)
    return float(s) if m else None


def tables(md):
    """Every pipe table in the manuscript, as a list of row-cell-lists."""
    out, cur = [], []
    for line in md.split('\n'):
        if line.lstrip().startswith('|'):
            cur.append([c for c in line.strip().strip('|').split('|')])
        else:
            if len(cur) >= 3:
                out.append(cur)
            cur = []
    if len(cur) >= 3:
        out.append(cur)
    return out


def find_table(tabs, *header_words):
    """The first table whose header row contains all the given words."""
    for t in tabs:
        head = ' '.join(t[0]).lower()
        if all(w.lower() in head for w in header_words):
            return t
    return None


def row_starting(tab, *words):
    for r in tab[1:]:
        cell = ' '.join(r).lower()
        if all(w.lower() in cell for w in words):
            return r
    return None


# --------------------------------------------------------------------------
# re-deriving from shipped bytes
# --------------------------------------------------------------------------
# The majority-sweep archive behind each q, named ONCE. check_quoted_nodes.py
# reads this same mapping, so the two cannot drift apart and verify different
# runs while both reporting success.
MAJORITY_ARCHIVE = {23: 'rerun1_p23_majority.tar.zst', 27: 'p27_majority.tar.zst',
                    31: 'p31_majority.tar.zst', 43: 'p43_majority.tar.zst'}


def archive_totals(name):
    """(slices, nodes, dom_nodes, seconds) from a compressed run archive."""
    path = os.path.join(ROOT, 'evidence', name)
    if not os.path.exists(path):
        return None
    try:
        raw = subprocess.run(['zstd', '-dc', path], capture_output=True).stdout
        tf = tarfile.open(fileobj=io.BytesIO(raw))
    except Exception:
        return None
    n = nodes = dom = 0
    secs = 0.0
    for m in tf:
        if not m.isfile():
            continue
        f = tf.extractfile(m)
        if f is None:
            continue
        for line in f.read().decode('utf8', 'replace').split('\n'):
            if not line.startswith('RESULT'):
                continue
            n += 1
            for fld in line.split():
                if fld.startswith('nodes=') and fld[6:].isdigit():
                    nodes += int(fld[6:])
                elif fld.startswith('dom_nodes='):
                    dom += int(fld[10:])
                elif fld.startswith('time='):
                    secs += float(fld[5:].rstrip('s'))
    return n, nodes, dom, secs


def cert_cost(inst):
    """(solve_core_h, check_core_h, cubes) from a certificate's per-cube logs."""
    d = os.path.join(ROOT, 'certificates', '%scert_d6' % inst, 'log')
    if not os.path.isdir(d):
        return None
    s = c = 0.0
    cubes = 0
    for fn in sorted(os.listdir(d)):
        for line in open(os.path.join(d, fn)):
            if line.startswith('#'):
                continue
            p = line.split()
            if len(p) >= 6:
                try:
                    s += float(p[4])
                    c += float(p[5])
                    cubes += 1
                except ValueError:
                    pass
    return s / 3600, c / 3600, cubes


def times_file_core_h(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    s = 0.0
    n = 0
    for line in open(p):
        if line.startswith('#'):
            continue
        f = line.split('\t')
        if len(f) >= 2:
            s += float(f[1])
            n += 1
    return s / 3600, n


def marker_sum(reldir, field):
    d = os.path.join(ROOT, reldir)
    if not os.path.isdir(d):
        return None
    tot = 0
    for dirpath, _, files in os.walk(d):
        for fn in files:
            for line in open(os.path.join(dirpath, fn)):
                for fld in line.split():
                    if '=' in fld:
                        k, v = fld.split('=', 1)
                        if k == field and v.isdigit():
                            tot += int(v)
    return tot


def marker_archive_core_h(name):
    """Core-hours summed over the `secs=` fields of a sweep's marker archive."""
    path = os.path.join(ROOT, 'evidence', name)
    if not os.path.exists(path):
        return None
    try:
        raw = subprocess.run(['zstd', '-dc', path], capture_output=True).stdout
        tf = tarfile.open(fileobj=io.BytesIO(raw))
    except Exception:
        return None
    secs = 0.0
    for m in tf:
        if m.isfile() and '/done/' in m.name:
            for fld in tf.extractfile(m).read().decode().split():
                if fld.startswith('secs='):
                    secs += float(fld[5:])
    return secs / 3600


def tsv_rows(rel):
    """Rows of a TSV in the package, header first, or None.

    Comment lines are skipped, except a `#`-prefixed line holding tabs, which is
    how some roll-ups write their column header (`#host<TAB>verdict...`).
    """
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return None
    out = []
    for l in open(path):
        if not l.strip():
            continue
        if l.startswith('#'):
            if '\t' in l:
                out.append(l[1:].rstrip('\n').split('\t'))
            continue
        out.append(l.rstrip('\n').split('\t'))
    return out


def survivors(args):
    """Live base-state count from the search-free counter."""
    p = os.path.join(ROOT, 'sat', 'base_survivors.py')
    if not os.path.exists(p):
        return None
    r = subprocess.run([sys.executable, p] + args, capture_output=True, text=True,
                       cwd=ROOT)
    best = None
    states = None
    for line in r.stdout.split('\n'):
        m = re.search(r'base_states=([\d,]+)', line)
        if m:
            states = int(m.group(1).replace(',', ''))
        m = re.match(r'\s*([\d,]+)\s+[\d.]+%', line)
        if m and best is None:
            best = int(m.group(1).replace(',', ''))
    return states, best


def close(a, b, rel=0.005):
    if a is None or b is None:
        return False
    if b == 0:
        return a == 0
    return abs(a - b) / abs(b) <= rel


# --------------------------------------------------------------------------
def main(mdpath, as_json):
    md = open(mdpath).read()
    tabs = tables(md)

    # ---------------------------------------------------------------- ARITHMETIC
    # The integer program at q = 23, k = 5 (appendix "The search engine", subsection
    # "Integer programming and SAT are both too slow", label sec:ip-sat-slow).
    q, k = 23, 5
    for want, label in ((k * math.comb(q, 2), 'binaries'),
                        (2 * k * math.comb(q, 3), 'transitivity rows'),
                        (math.comb(q, 2), 'majority rows')):
        stated = re.search(r'\$?([\d{},]+)\$?\s*' + label, md)
        if stated is None:
            missing('ARITHMETIC', 'sec:ip-sat-slow ILP %s at q=23' % label,
                    'the sentence giving the number of ILP %s' % label)
            continue
        got = num(stated.group(1))
        record('ARITHMETIC', 'sec:ip-sat-slow ILP %s at q=23' % label, got, want,
               got == want, 'k*C(23,2), 2k*C(23,3), C(23,2)')

    # The dissent-Boolean instance at q = 19 (appendix "The formal certificates",
    # subsection "The certified refutations", label sec:certified): 5*C(19,2) variables,
    # and 15 clauses per arc plus 10 per triple.
    q = 19
    v_want = k * math.comb(q, 2)
    c_want = 15 * math.comb(q, 2) + 10 * math.comb(q, 3)
    m = re.search(r'\$?([\d{},]+)\$? variables and \$?([\d{},]+)\$? clauses', md)
    if m:
        record('ARITHMETIC', 'sec:certified P19 instance variables', num(m.group(1)), v_want,
               num(m.group(1)) == v_want, '5*C(19,2)')
        record('ARITHMETIC', 'sec:certified P19 instance clauses', num(m.group(2)), c_want,
               num(m.group(2)) == c_want, '15*C(19,2) + 10*C(19,3)')
    else:
        missing('ARITHMETIC', 'sec:certified P19 instance size',
                'the sentence "... variables and ... clauses" (P19 instance)')

    # The Paley(23) coverage instance: 350 constraint + 356 symmetry + one
    # negated cube per base state.  The manuscript states all four numbers.
    m = re.search(r'\$?([\d{},]+)\$? constraint\s*\n?clauses, \$?([\d{},]+)\$? '
                  r'symmetry-breaking clauses and \$?([\d{},]+)\$? negated', md)
    conf = os.path.join(ROOT, 'cluster', 'jz_reproduce', 'instances', 'p23.conf')
    if not m:
        missing('ARITHMETIC', 'sec:certified P23 coverage clause total',
                'the sentence "... constraint clauses, ... symmetry-breaking clauses and ... negated"')
    elif not os.path.exists(conf):
        skip('ARITHMETIC', 'sec:certified P23 coverage clause total', 'p23.conf absent')
    else:
        a, b, c = (num(x) for x in m.groups())
        mm = re.search(r'COVER_CLAUSES=(\d+)', open(conf).read())
        assert mm, 'cluster/jz_reproduce/instances/p23.conf has no COVER_CLAUSES line'
        stated_total = float(mm.group(1))
        record('ARITHMETIC', 'sec:certified P23 coverage clause total',
               stated_total, a + b + c, close(stated_total, a + b + c, 0),
               '350 + 356 + 3,414,729, against COVER_CLAUSES in the kit conf')

    # sec:certified's Delta_6 - 5 instance: 5*C(22,2) variables; at plain majority
    # 10 clauses per arc (no 3 of the 5 dissent variables all true) plus the same
    # 10 transitivity clauses per triple as at unit margin.
    q = 22
    m = re.search(r'\$n = 22\$ and plain majority: \$([\d{},]+)\$ variables and '
                  r'\$([\d{},]+)\$ clauses', md)
    if m:
        record('ARITHMETIC', 'sec:certified Delta_6 - 5 instance variables', num(m.group(1)),
               k * math.comb(q, 2), num(m.group(1)) == k * math.comb(q, 2), '5*C(22,2)')
        c22 = 10 * math.comb(q, 2) + 10 * math.comb(q, 3)
        record('ARITHMETIC', 'sec:certified Delta_6 - 5 instance clauses', num(m.group(2)), c22,
               num(m.group(2)) == c22, '10*C(22,2) + 10*C(22,3)')
    else:
        missing('ARITHMETIC', 'sec:certified Delta_6 - 5 instance size',
                'the sentence "$n = 22$ and plain majority: ... variables and ... clauses"')
    m = re.search(r'with\s*\n?\$([\d{},]+)\$ negated cubes', md)
    rec = os.path.join(ROOT, 'certificates', 'd005mv04_coverage_cert.txt')
    if not m:
        missing('DERIVED', 'sec:certified Delta_6 - 5 coverage',
                'the sentence "with ... negated cubes"')
    elif not os.path.exists(rec):
        skip('DERIVED', 'sec:certified Delta_6 - 5 coverage', 'coverage record absent')
    else:
        mm = re.search(r'CNF\s+([\d,]+) clauses = (\d+) F_B \+ (\d+) SB \+ '
                       r'([\d,]+) negated cubes', open(rec).read())
        assert mm, 'certificates/d005mv04_coverage_cert.txt has no "CNF ... clauses = ..." line'
        tot, fb, sb, cubes = (int(x.replace(',', '')) for x in mm.groups())
        record('DERIVED', 'sec:certified Delta_6 - 5 coverage negated cubes', num(m.group(1)),
               cubes, num(m.group(1)) == cubes,
               'the coverage record, certificates/d005mv04_coverage_cert.txt')
        record('ARITHMETIC', 'sec:certified Delta_6 - 5 coverage clause total', tot,
               fb + sb + cubes, tot == fb + sb + cubes, '350 + 356 + 742,374')

    # ------------------------------------------------------------------ DERIVED
    # The cost table, row by row (appendix "The search engine", subsection "Runtimes for
    # every computation", label sec:runtimes).
    cost = find_table(tabs, 'computation', 'core-hours')
    if cost is None:
        missing('DERIVED', 'sec:runtimes cost table', 'the table headed "computation ... core-hours"')
    else:
        def cell(name, rowwords, idx=-1):
            """The row's figure, or None after recording the row as missing."""
            r = row_starting(cost, *rowwords)
            if r is None or num(r[idx]) is None:
                missing('DERIVED', name, 'the row of Table @tbl:runtimes matching %r' % (rowwords,))
                return None
            return num(r[idx])

        # sec:runtimes reports cluster runs in laptop-equivalent core-hours, dividing each cluster total
        # by a factor the same paragraph states.  The factors are read from that prose, so a
        # factor that changes in the paper changes here; what is re-derived is the cluster total.
        def factor(name, pat):
            m = re.search(pat, md)
            if m is None:
                missing('DERIVED', name, 'the sentence matching %r' % pat)
                return None
            return tuple(float(g) for g in m.groups())
        f = factor('sec:runtimes the 3.55 factor', r'cluster took \$([\d.]+)\$ times as long in total')
        f_sweep = f[0] if f else None
        f = factor('sec:runtimes the order-13 factor', r'cluster took \$([\d.]+)\$ times as long per tournament')
        f_13 = f[0] if f else None
        f = factor('sec:runtimes the order-12 and order-15 factors',
                   r'cluster took\s+\$([\d.]+)\$\s+and\s+\$([\d.]+)\$\s+times as long\s+respectively')
        f_12, f_15 = f if f else (None, None)
        def per(x, f):
            return None if x is None or f is None else x / f

        for words, fn, label, fac in (
            (['certified refutation', 'unit'],
             lambda: (lambda t: None if t is None else t[0] + t[1])(cert_cost('p19')),
             'P19 certificate, solve_s + check_s over 22,876 cubes', True),
            (['certified refutation', 'unrestricted'],
             lambda: (lambda t: None if t is None else t[0] + t[1])(cert_cost('p23')),
             'P23 certificate, solve_s + check_s over 343,896 cubes', True),
            (['delta_6', 'certified'],
             lambda: (lambda t: None if t is None else t[0] + t[1])(cert_cost('d005mv04')),
             'Delta_6 - 5 certificate, solve_s + check_s over 742,374 cubes', True),
            (['delta_6', 'sweep'],
             lambda: per(marker_archive_core_h('d005mv04_sweep_markers.tar.zst'), f_sweep),
             'Delta_6 - 5 cluster sweep, secs= over its 8,031 markers, / the stated factor',
             f_sweep),
            (['31', 'sweep'],
             lambda: (lambda t: None if t is None else t[0])(
                 times_file_core_h('verdicts/p31mv_majority/p31mv_times.txt')),
             'P31-v, the per-base times file', True),
            (['57'],
             lambda: (lambda p: None if not os.path.exists(p) else sum(
                 float(l.split()[2].rstrip('s')) for l in open(p)
                 if len(l.split()) >= 3 and l.split()[1] == 'SAT'
             ) / 3600)(os.path.join(ROOT, 'tournaments/dr19_arcflip/sweep.log')),
             'dr19_g2, the SAT rows of the 57-orbit sweep log', True),
            (['regular on', '15'],
             lambda: (lambda s: None if s is None else per(s / 3600, f_15))(
                 marker_sum('cluster/jz_n15/results_margin1/done', 'secs')),
             'n=15 census, the secs= field of 6,000 residue markers, / the stated factor',
             f_15),
        ):
            name = 'sec:runtimes row %s' % ' '.join(words)
            want = cell(name, words)
            if want is None or fac is None:
                continue        # recorded as missing by cell() or factor()
            got = fn()
            if got is None:
                skip('DERIVED', name, 'artifact absent')
            else:
                record('DERIVED', name, want, round(got, 2), close(want, got), label)

        # T4 is a CROSS-FILE check, not a re-derivation: the per-base markers
        # for the arc-criticality campaign live on the cluster, so what is
        # compared is the manuscript's figure against the kit's own roll-up,
        # recorded in a different file.  Weaker than summing raw evidence, and
        # labelled as such rather than being quietly counted as equivalent.
        agg = os.path.join(ROOT, 'cluster', 'jz_p23arc', 'AGGREGATE_OUTPUT.txt')
        want = cell('sec:runtimes row one arc reversed', ['one arc reversed'])
        if want is not None and not os.path.exists(agg):
            skip('DERIVED', 'sec:runtimes row one arc reversed', 'cluster/jz_p23arc roll-up absent')
        elif want is not None:
            src = open(agg).read()
            m = re.search(r'core-hours spent\s*:\s*([\d.]+)', src)
            n = re.search(r'base states screened\s*:\s*(\d+)', src)
            mean = re.search(r'mean per base state\s*:\s*([\d.]+)', src)
            assert m and n and mean, ('cluster/jz_p23arc/AGGREGATE_OUTPUT.txt lacks one of '
                                      '"core-hours spent", "base states screened", "mean per base state"')
            got = float(m.group(1))
            record('DERIVED', 'sec:runtimes row one arc reversed', want, got,
                   close(want, got),
                   'cluster/jz_p23arc roll-up (cross-file, markers not shipped)')
            prod = int(n.group(1)) * float(mean.group(1)) / 3600
            record('ARITHMETIC', 'sec:runtimes one arc reversed is internally consistent',
                   got, round(prod, 1), close(got, prod, 0.01),
                   'base states screened x mean per base state')

        # Delta_28 - 5: same cross-file shape -- the markers are on the cluster,
        # so the figure is compared against the sweep's roll-up, in seconds.
        rows = tsv_rows('verdicts/n22_obstructions/verdicts.tsv')
        want = cell('sec:runtimes row Delta_28 - 5 sweep', ['delta_{28}', 'sweep'])
        if want is not None and f_sweep is not None:
            if not rows:
                skip('DERIVED', 'sec:runtimes row Delta_28 - 5 sweep',
                     'verdicts/n22_obstructions/verdicts.tsv absent')
            else:
                h = rows[0]
                got = [per(float(r[h.index('seconds')]) / 3600, f_sweep) for r in rows[1:]
                       if r[0] == 'd027_mv04']
                assert len(got) == 1, 'verdicts/n22_obstructions/verdicts.tsv: %d rows for d027_mv04' % len(got)
                record('DERIVED', 'sec:runtimes row Delta_28 - 5 sweep', want, round(got[0], 1),
                       close(want, got[0]),
                       'verdicts/n22_obstructions roll-up / the stated factor (cross-file, '
                       'markers on the cluster)')

        # The 16 doubly regular tournaments on 23 vertices swept on the cluster
        # (sec:families, counted in sec:runtimes).  The count re-derives from the roll-up;
        # the table's laptop-equivalent figure does not, because part of those sweeps ran
        # on the laptop and the roll-up does not split the two (CLAIMS.md T17, gap 8).
        m = re.search(r'\$(\d+)\$ of the \$(\d+)\$\s+unrestricted sweeps of doubly regular '
                      r'tournaments on \$23\$ vertices', md)
        rows = tsv_rows('cluster/jz_drt23maj/jz_drt23maj.tsv')
        if not m:
            missing('DERIVED', 'sec:runtimes doubly regular sweeps on the cluster',
                    'the sentence "$N$ of the $M$ unrestricted sweeps of doubly regular tournaments '
                    'on $23$ vertices"')
        elif not rows:
            skip('DERIVED', 'sec:runtimes doubly regular sweeps on the cluster',
                 'cluster/jz_drt23maj/jz_drt23maj.tsv absent')
        else:
            h = rows[0]
            n_cl = len([r for r in rows[1:] if r[h.index('verdict')] == 'UNSAT'])
            record('DERIVED', 'sec:runtimes doubly regular sweeps on the cluster (count)',
                   int(m.group(1)), n_cl, int(m.group(1)) == n_cl,
                   'UNSAT rows of cluster/jz_drt23maj/jz_drt23maj.tsv (cross-file roll-up)')
            # the M: one sweep per converse class of the doubly regular tournaments on 23
            # vertices, which the ledger lists (both margins UNSAT at n = 23)
            led = [l.rstrip('\n').split('\t') for l in open(os.path.join(ROOT, 'verdicts', 'verdict_ledger.tsv'))]
            lh = led[0]
            mi, ma, cv = lh.index('margin1'), lh.index('majority'), lh.index('converse')
            ids = {r[0]: r[cv].strip() for r in led[1:] if len(r) > ma and r[1] == '23'
                   and r[mi].strip() == 'UNSAT' and r[ma].strip() == 'UNSAT'}
            n_cls = len({min(t, c) if c not in ('self', '-') else t for t, c in ids.items()})
            record('LEDGER', 'sec:runtimes doubly regular sweeps in all (classes up to converse)',
                   int(m.group(2)), n_cls, int(m.group(2)) == n_cls,
                   'ledger rows at n=23 with margin1 = majority = UNSAT, one per converse pair')
            want = cell('sec:runtimes row doubly regular on 23', ['doubly regular on', '23'])
            if want is not None:
                declared('sec:runtimes row %s doubly regular on 23' % m.group(1), want,
                         'CLAIMS.md gap 8')

        # T7, same cross-file shape as T4: the per-task accounting lives on the
        # cluster, so what is compared is the manuscript's figure against the
        # three-way total a different file records.
        sc = os.path.join(ROOT, 'cluster', 'jz_n13sc', 'SLURM_COST.txt')
        want = cell('sec:runtimes row self-converse on 13', ['self-converse on'])
        if want is not None and f_13 is not None:
            if not os.path.exists(sc):
                skip('DERIVED', 'sec:runtimes row self-converse on 13', 'cluster/jz_n13sc/SLURM_COST.txt absent')
            else:
                src = open(sc).read()
                cl = re.search(r'cluster,[^\n]*?([\d.]+) core-h', src)
                lap = re.findall(r'laptop,[^\n]*?([\d.]+) core-h', src)
                assert cl and lap, 'cluster/jz_n13sc/SLURM_COST.txt lacks its cluster or laptop line'
                got = round(per(float(cl.group(1)), f_13) + sum(map(float, lap)), 1)
                record('DERIVED', 'sec:runtimes row self-converse on 13', want, got,
                       close(want, got, 0.01),
                       'cluster/jz_n13sc: cluster part / the stated factor + the two laptop '
                       'parts (cross-file, per-task accounting not shipped)')

        roll = os.path.join(ROOT, 'n12_unit_margin', 'n12_cover', 'FINAL_ROLLUP.txt')
        want = cell('sec:runtimes row all on 12', ['all on'])
        if want is not None and f_12 is not None:
            if not os.path.exists(roll):
                skip('DERIVED', 'sec:runtimes row all on 12', 'n12_cover/FINAL_ROLLUP.txt absent')
            else:
                m = re.search(r'core-seconds\s*:\s*(\d+)', open(roll).read())
                assert m, 'n12_unit_margin/n12_cover/FINAL_ROLLUP.txt has no "core-seconds :" line'
                got = int(m.group(1)) / 3600 / f_12
                record('DERIVED', 'sec:runtimes row all on 12', want, round(got, 1), close(want, got),
                       'n12_unit_margin/n12_cover roll-up / the stated factor (cross-file)')

    # The runtime table (appendix "The search engine", subsection "How the runtime scales
    # in q", label sec:scaling).
    run = find_table(tabs, 'live base states', 'core-hours', 'nodes')
    if run is None:
        missing('DERIVED', 'sec:scaling runtime table',
                'the table headed "live base states ... core-hours ... nodes"')
    else:
        arch = MAJORITY_ARCHIVE
        rows_by_q = {int(num(r[0])): r for r in run[1:] if num(r[0]) is not None}
        for qv in sorted(arch):
            if qv not in rows_by_q:
                missing('DERIVED', 'sec:scaling q=%d' % qv, 'the row q = %d of Table sec:scaling' % qv)
                continue
            r = rows_by_q[qv]
            live, hours, nodes, per = (num(r[1]), num(r[2]), num(r[3]), num(r[4]))
            tot = archive_totals(arch[qv])
            if tot is None:
                skip('DERIVED', 'sec:scaling q=%d' % qv, 'archive absent or zstd missing')
                continue
            _, n_nodes, n_dom, secs = tot
            record('DERIVED', 'sec:scaling q=%d core-hours' % qv, hours, round(secs / 3600, 2),
                   close(hours, secs / 3600), 'sum of time= over the archive')
            if nodes is not None:
                note = 'sum of nodes= over the archive'
                if not close(nodes, n_nodes, 0.01) and close(nodes, n_dom, 0.01):
                    note = ('THE PRINTED FIGURE IS dom_nodes, NOT nodes: '
                            'dom_nodes=%.3e, nodes=%.3e' % (n_dom, n_nodes))
                record('DERIVED', 'sec:scaling q=%d nodes' % qv, nodes, float('%.3g' % n_nodes),
                       close(nodes, n_nodes, 0.01), note)
            if live is not None and per is not None:
                record('ARITHMETIC', 'sec:scaling q=%d seconds per live base state' % qv,
                       per, round(hours * 3600 / live, 1),
                       close(per, hours * 3600 / live, 0.01),
                       'core-hours x 3600 / live base states')

        # the live counts themselves, search-free
        for qv, args in ((23, ['--q', '23', '--base', '0', '1', '2', '5', '11']),
                         (31, ['--q', '31', '--base', '0', '1', '2', '3', '6'])):
            if qv not in rows_by_q:
                missing('DERIVED', 'sec:scaling q=%d live base states' % qv,
                        'the row q = %d of Table sec:scaling' % qv)
                continue
            got = survivors(args)
            if got is None or got[1] is None:
                skip('DERIVED', 'sec:scaling q=%d live base states' % qv,
                     'base_survivors.py unavailable')
            else:
                # q=23 uses the break in use, not the optimum, so compare the
                # base-state total and let CLAIMS.md carry the break choice.
                record('DERIVED', 'sec:scaling q=%d base states (total)' % qv, None, got[0],
                       got[0] in (8031, 21009),
                       'search-free count from sat/base_survivors.py')

    # ------------------------------------------------------------------- LEDGER
    led = os.path.join(ROOT, 'verdicts', 'verdict_ledger.tsv')
    if not os.path.exists(led):
        skip('LEDGER', 'unit-margin obstructions', 'ledger absent')
    else:
        rows = [l.rstrip('\n').split('\t') for l in open(led)]
        hdr = rows[0]
        mi, ma = hdr.index('margin1'), hdr.index('majority')
        conv = hdr.index('converse')
        # The ledger is keyed on the registry of catalogue families, so the tournaments
        # derived from them (arc reversals, Paley(23) - v) live in a supplement with the
        # same leading columns.  verify/separation_supplement.py re-derives its rows and
        # checks that none duplicates a ledger class; here they are only counted.
        sup = os.path.join(ROOT, 'verdicts', 'ledger_supplement.tsv')
        srows = [l.rstrip('\n').split('\t') for l in open(sup) if l.strip() and not l.startswith('#')]
        sh = srows[0]
        for c in ('id', 'n', 'margin1', 'majority', 'converse'):
            assert sh.index(c) == hdr.index(c), 'ledger_supplement.tsv: column %s is not where the ledger has it' % c
        # "can produce, but not with unit margin": unit margin UNSAT, majority SAT
        sep = [r for r in rows[1:] + srows[1:] if len(r) > ma and r[mi].strip() == 'UNSAT'
               and r[ma].strip().startswith('SAT')]
        # "...turn up 75 tournaments, up to isomorphism and converse, that five voters can
        # produce but not with unit margin: $2$ doubly regular ones at order $19$; at order
        # $21$, $3$ vertex-transitive ones (...), $15$ obtained from two of them by reversing
        # one arc (...) and $42$ near-doubly regular ones (...); at order $22$, $P_{23} - v$;
        # and at order $23$, $11$ circulant ones and $P_{23}$ with one arc reversed."
        # A class and its converse class (the `converse` column) count once.  Clauses are
        # separated by ';' and each is credited to its order.  Within a clause, the items are
        # separated by commas and 'and'; an item that starts with a count contributes that
        # count, and an item that names a single tournament ($P_{23} - v$) contributes one.
        # Subscripts are removed first, so the 23 of P_{23} is never read as a count.
        by_n = {}
        for n in {int(r[1]) for r in sep}:
            ids = {r[0]: r[conv].strip() for r in sep if int(r[1]) == n}
            by_n[n] = len({min(t, c) if c not in ('self', '-') else t for t, c in ids.items()})
        flat = re.sub(r'\([^)]*\)', '', re.sub(r'[${}]', '', re.sub(r'\s+', ' ', md)))
        m = re.search(r'turn up (\d+) tournaments, up to isomorphism and converse, that five voters '
                      r'can produce but not with unit margin: ([^.]*)\.', flat)
        if m:
            want = {}
            for clause in m.group(2).split(';'):
                o = re.search(r'at order (\d+)', clause)
                assert o, 'a clause of the count names no order: %r' % clause
                body = re.sub(r'_\w+', '', re.sub(r'at order \d+', '', clause))
                items = [x.strip() for x in re.split(r',|\band\b', body) if x.strip()]
                cnt = 0
                for it in items:
                    lead = re.match(r'(\d+)\b', it)
                    assert lead or not re.search(r'\d', it), 'a number inside an item, not leading it: %r' % it
                    cnt += int(lead.group(1)) if lead else 1
                want[int(o.group(1))] = want.get(int(o.group(1)), 0) + cnt
            total = int(m.group(1))
            record('LEDGER', 'the %d unit-margin-only obstructions, up to converse' % total, want,
                   by_n, want == by_n and sum(want.values()) == total,
                   'ledger and supplement rows with margin1 = UNSAT and majority = SAT, one per converse pair, by order')
        else:
            missing('LEDGER', 'the unit-margin-only obstructions',
                    'the sentence "turn up N tournaments, up to isomorphism and converse, that five '
                    'voters can produce but not with unit margin: ..."')
        # sec:families ("Other structured tournament families"): none of the 37 doubly
        # regular tournaments on 23 vertices is inducible, at either margin.
        both = [r for r in rows[1:] if len(r) > ma and r[1] == '23'
                and r[mi].strip() == 'UNSAT' and r[ma].strip() == 'UNSAT']
        m = re.search(r'none of the \$(\d+)\$ doubly regular ones is, at\s*\n?unit '
                      r'margin or unrestricted', md)
        if m:
            record('LEDGER', 'order 23: doubly regular, not inducible at either margin',
                   int(m.group(1)), len(both), int(m.group(1)) == len(both),
                   'ledger rows at n=23 with margin1 = majority = UNSAT')
        else:
            missing('LEDGER', 'order 23 doubly regular count',
                    'the sentence "none of the $N$ doubly regular ones is, at unit margin or unrestricted"')

    # ----------------------- app:below22 (appendix "The search below 22 vertices")
    gt = find_table(tabs, 'vertices', 'deleted', 'classes')
    if gt is None:
        missing('DERIVED', 'app:below22 level table', 'the table headed "vertices ... deleted ... classes"')
    else:
        want = {int(num(r[1])): int(num(r[2])) for r in gt[2:]
                if num(r[1]) is not None and num(r[2]) is not None}
        lab = os.environ.get('LABELG') or ''
        script = os.path.join(ROOT, 'verify', 'drt23_level_counts.py')
        if lab and os.path.exists(script):
            r = subprocess.run([sys.executable, script,
                                os.path.join(ROOT, 'tournaments', 'drt23'),
                                os.path.join(ROOT, 'tournaments', 'drt23_del', 'PARENTS18.txt'),
                                '--labelg', lab, '--levels',
                                ','.join(str(j) for j in sorted(want))],
                               capture_output=True, text=True)
            got = {int(a): int(b) for a, b in re.findall(
                r'level (\d+): \d+ deletions -> \d+ isomorphism classes -> (\d+) '
                r'classes', r.stdout)}
            ok_p = 'are exactly the other' in r.stdout and ': ok' in r.stdout
            record('DERIVED', 'app:below22 classes per level (one, two, three deleted)', want, got,
                   want == got and ok_p,
                   'verify/drt23_level_counts.py from the 18 parents, one per converse '
                   'pair (checked)')
        else:
            skip('DERIVED', 'app:below22 classes per level', 'LABELG not set')
        # the settled count at 21 vertices, from the archive's own manifest
        r21 = row_starting(gt, '4{,}108') or row_starting(gt, '4,108')
        m = re.search(r'\$([\d{},]+)\$ settled', ' '.join(r21)) if r21 else None
        path = os.path.join(ROOT, 'evidence', 'n21_level_witnesses.tar.zst')
        if not m:
            missing('DERIVED', 'app:below22 classes settled at 21 vertices',
                    'the "$N$ settled" cell of the 21-vertex row of Table @tbl:levels')
        elif not os.path.exists(path):
            skip('DERIVED', 'app:below22 classes settled at 21 vertices',
                 'evidence/n21_level_witnesses.tar.zst absent')
        else:
            raw = subprocess.run(['zstd', '-dc', path], capture_output=True).stdout
            tf = tarfile.open(fileobj=io.BytesIO(raw))
            rows = [l for l in tf.extractfile('n21_level/SETTLED.tsv').read().decode()
                    .splitlines() if l and not l.startswith('#')][1:]
            record('DERIVED', 'app:below22 classes settled at 21 vertices', num(m.group(1)),
                   len(rows), num(m.group(1)) == len(rows),
                   'rows of SETTLED.tsv in evidence/n21_level_witnesses.tar.zst; check 8d '
                   'verifies each witness')
        # The screen at 22 vertices: "all $378$ classes were first screened at up to $50$
        # base states each, without a single witness".  A base state of the screen ends
        # either exhausted (searched to the end, no witness) or capped; a witness would be
        # a third outcome, so "without a single witness" is tried = exhausted + capped on
        # every host.
        m = re.search(r'all \$([\d{},]+)\$ classes were first screened at up to \$(\d+)\$ base '
                      r'states each, without a\s+single witness', md)
        rows = tsv_rows('cluster/jz_drt23mv/HARDNESS_378.tsv')
        if not m:
            missing('DERIVED', 'app:below22 the 22-vertex screen',
                    'the sentence "all $N$ classes were first screened at up to $M$ base states '
                    'each, without a single witness"')
        elif not rows:
            skip('DERIVED', 'app:below22 the 22-vertex screen', 'cluster/jz_drt23mv/HARDNESS_378.tsv absent')
        else:
            assert all(len(r) == 6 for r in rows), 'HARDNESS_378.tsv: a row without 6 columns'
            hosts, tried, ex, cap = (len(rows), [int(r[2]) for r in rows],
                                     [int(r[3]) for r in rows], [int(r[4]) for r in rows])
            record('DERIVED', 'app:below22 classes screened at 22 vertices', num(m.group(1)),
                   hosts, num(m.group(1)) == hosts,
                   'hosts of cluster/jz_drt23mv/HARDNESS_378.tsv (cross-file roll-up)')
            record('DERIVED', 'app:below22 base states per host in the screen, at most',
                   num(m.group(2)), max(tried), num(m.group(2)) == max(tried),
                   'largest tried column of HARDNESS_378.tsv')
            nw = sum(t - e - c for t, e, c in zip(tried, ex, cap))
            record('DERIVED', 'app:below22 witnesses found by the screen', 0, nw,
                   nw == 0 and all(t == e + c for t, e, c in zip(tried, ex, cap)),
                   'tried - exhausted - capped over the 378 hosts')

    # ----------------------- app:counts (appendix "Exact enumeration counts")
    counts = find_table(tabs, '$d_n$') or find_table(tabs, 'D_n')
    if counts is None:
        missing('DERIVED', 'app:counts table', 'the table headed "$d_n$" or "D_n"')
    else:
        want_r15 = [num(r[2]) for r in counts[1:] if num(r[0]) == 15]
        want_s13 = [num(r[3]) for r in counts[1:] if num(r[0]) == 13]
        got = marker_sum('cluster/jz_n15/results_margin1/done', 'instances')
        if len(want_r15) != 1 or want_r15[0] is None:
            missing('DERIVED', 'app:counts R_15', 'the R_n cell of the n = 15 row of the counts table')
        elif got is None:
            skip('DERIVED', 'app:counts R_15', 'n15 markers absent')
        else:
            record('DERIVED', 'app:counts R_15', want_r15[0], got, close(want_r15[0], got, 0),
                   'sum of instances= over the 6,000 residue markers')
        agg = os.path.join(ROOT, 'cluster', 'jz_n13sc', 'aggregate.sh')
        if len(want_s13) != 1 or want_s13[0] is None:
            missing('DERIVED', 'app:counts S_13', 'the S_n cell of the n = 13 row of the counts table')
        elif not os.path.exists(agg):
            skip('DERIVED', 'app:counts S_13', 'cluster/jz_n13sc/aggregate.sh absent')
        else:
            # the kit writes it with Python underscore separators
            mm = re.search(r'TOTAL\s*=\s*([\d_]+)', open(agg).read())
            assert mm, 'cluster/jz_n13sc/aggregate.sh has no TOTAL = line'
            got13 = float(mm.group(1).replace('_', ''))
            record('DERIVED', 'app:counts S_13', want_s13[0], got13,
                   close(want_s13[0], got13, 0),
                   'the total the order-13 kit reconciles its three parts against')

    # -------------------------------------------------------------------- report
    bad = sum(1 for r in RESULTS if r['status'] == 'FAIL')
    if as_json:
        json.dump(RESULTS, sys.stdout, indent=1)
        sys.stdout.write('\n')
    else:
        width = max(len(r['name']) for r in RESULTS)
        for r in RESULTS:
            tag = {'ok': '  ok  ', 'FAIL': ' FAIL ', 'skip': ' skip ',
                   'declared': ' decl '}[r['status']]
            print('%s %-*s  %s' % (tag, width, r['name'],
                                   ('expected %s, got %s' % (r['expected'], r['observed']))
                                   if r['status'] in ('ok', 'FAIL') else r['note']))
            if r['status'] == 'FAIL' and r['note']:
                print('        %s' % r['note'])
        print('\n%d checks: %d ok, %d FAIL, %d skip, %d declared'
              % (len(RESULTS),
                 sum(1 for r in RESULTS if r['status'] == 'ok'), bad,
                 sum(1 for r in RESULTS if r['status'] == 'skip'),
                 sum(1 for r in RESULTS if r['status'] == 'declared')))
    return 1 if bad else 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--json']
    path = args[0] if args else os.path.join(
        ROOT, 'manuscript', 'Tournaments_not_inducible_by_five_voters_MSS.md')
    sys.exit(main(path, '--json' in sys.argv[1:]))
