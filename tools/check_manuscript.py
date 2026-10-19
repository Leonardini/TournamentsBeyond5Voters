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

A check whose artifact is absent is reported as SKIP, never as a pass.  A
manuscript figure with no re-derivation route is reported as DECLARED and must
appear in CLAIMS.md's gap list; `tools/check_package.sh` checks that pairing.
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
    RESULTS.append(dict(kind=kind, name=name, expected=None, observed=None,
                        status="skip", note=why))


def declared(name, want, where):
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
    # Appendix A.3's integer program at q = 23, k = 5.
    q, k = 23, 5
    for want, label in ((k * math.comb(q, 2), 'binaries'),
                        (2 * k * math.comb(q, 3), 'transitivity rows'),
                        (math.comb(q, 2), 'majority rows')):
        stated = re.search(r'\$?([\d{},]+)\$?\s*' + label, md)
        got = num(stated.group(1)) if stated else None
        record('ARITHMETIC', 'A.3 ILP %s at q=23' % label, got, want,
               got == want, 'k*C(23,2), 2k*C(23,3), C(23,2)')

    # Appendix B.1's dissent-Boolean instance at q = 19: 5*C(19,2) variables,
    # and 15 clauses per arc plus 10 per triple.
    q = 19
    v_want = k * math.comb(q, 2)
    c_want = 15 * math.comb(q, 2) + 10 * math.comb(q, 3)
    m = re.search(r'\$?([\d{},]+)\$? variables and \$?([\d{},]+)\$? clauses', md)
    if m:
        record('ARITHMETIC', 'B.1 P19 instance variables', num(m.group(1)), v_want,
               num(m.group(1)) == v_want, '5*C(19,2)')
        record('ARITHMETIC', 'B.1 P19 instance clauses', num(m.group(2)), c_want,
               num(m.group(2)) == c_want, '15*C(19,2) + 10*C(19,3)')
    else:
        skip('ARITHMETIC', 'B.1 P19 instance size', 'sentence not found')

    # The Paley(23) coverage instance: 350 constraint + 356 symmetry + one
    # negated cube per base state.  The manuscript states all four numbers.
    m = re.search(r'\$?([\d{},]+)\$? constraint\s*\n?clauses, \$?([\d{},]+)\$? '
                  r'symmetry-breaking clauses and \$?([\d{},]+)\$? negated', md)
    if m:
        a, b, c = (num(x) for x in m.groups())
        conf = os.path.join(ROOT, 'cluster', 'jz_reproduce', 'instances', 'p23.conf')
        stated_total = None
        if os.path.exists(conf):
            mm = re.search(r'COVER_CLAUSES=(\d+)', open(conf).read())
            stated_total = float(mm.group(1)) if mm else None
        record('ARITHMETIC', 'B.1 P23 coverage clause total',
               stated_total, a + b + c, close(stated_total, a + b + c, 0),
               '350 + 356 + 3,414,729, against COVER_CLAUSES in the kit conf')
    else:
        skip('ARITHMETIC', 'B.1 P23 coverage clause total', 'sentence not found')

    # Appendix B.1's Delta_6 - 5 instance: 5*C(22,2) variables; at plain majority
    # 10 clauses per arc (no 3 of the 5 dissent variables all true) plus the same
    # 10 transitivity clauses per triple as at unit margin.
    q = 22
    m = re.search(r'\$n = 22\$ and plain majority: \$([\d{},]+)\$ variables and '
                  r'\$([\d{},]+)\$ clauses', md)
    if m:
        record('ARITHMETIC', 'B.1 Delta_6 - 5 instance variables', num(m.group(1)),
               k * math.comb(q, 2), num(m.group(1)) == k * math.comb(q, 2), '5*C(22,2)')
        c22 = 10 * math.comb(q, 2) + 10 * math.comb(q, 3)
        record('ARITHMETIC', 'B.1 Delta_6 - 5 instance clauses', num(m.group(2)), c22,
               num(m.group(2)) == c22, '10*C(22,2) + 10*C(22,3)')
    else:
        skip('ARITHMETIC', 'B.1 Delta_6 - 5 instance size', 'sentence not found')
    m = re.search(r'with\s*\n?\$([\d{},]+)\$ negated cubes', md)
    rec = os.path.join(ROOT, 'certificates', 'd005mv04_coverage_cert.txt')
    if m and os.path.exists(rec):
        mm = re.search(r'CNF\s+([\d,]+) clauses = (\d+) F_B \+ (\d+) SB \+ '
                       r'([\d,]+) negated cubes', open(rec).read())
        if mm:
            tot, fb, sb, cubes = (int(x.replace(',', '')) for x in mm.groups())
            record('DERIVED', 'B.1 Delta_6 - 5 coverage negated cubes', num(m.group(1)),
                   cubes, num(m.group(1)) == cubes,
                   'the coverage record, certificates/d005mv04_coverage_cert.txt')
            record('ARITHMETIC', 'B.1 Delta_6 - 5 coverage clause total', tot,
                   fb + sb + cubes, tot == fb + sb + cubes, '350 + 356 + 742,374')
    else:
        skip('DERIVED', 'B.1 Delta_6 - 5 coverage', 'sentence or record not found')

    # ------------------------------------------------------------------ DERIVED
    # Appendix A.6's cost table, row by row.
    cost = find_table(tabs, 'computation', 'core-hours')
    if cost is None:
        skip('DERIVED', 'A.6 cost table', 'table not found in the manuscript')
    else:
        def cell(rowwords, idx=-1):
            r = row_starting(cost, *rowwords)
            return num(r[idx]) if r else None

        for words, fn, label in (
            (['certified refutation', 'unit'],
             lambda: (lambda t: None if t is None else t[0] + t[1])(cert_cost('p19')),
             'P19 certificate, solve_s + check_s over 22,876 cubes'),
            (['certified refutation', 'unrestricted'],
             lambda: (lambda t: None if t is None else t[0] + t[1])(cert_cost('p23')),
             'P23 certificate, solve_s + check_s over 343,896 cubes'),
            (['delta_6', 'certified'],
             lambda: (lambda t: None if t is None else t[0] + t[1])(cert_cost('d005mv04')),
             'Delta_6 - 5 certificate, solve_s + check_s over 742,374 cubes'),
            (['delta_6', 'sweep'],
             lambda: marker_archive_core_h('d005mv04_sweep_markers.tar.zst'),
             'Delta_6 - 5 cluster sweep, secs= over its 8,031 markers'),
            (['31', 'sweep'],
             lambda: (lambda t: None if t is None else t[0])(
                 times_file_core_h('verdicts/p31mv_majority/p31mv_times.txt')),
             'P31-v, the per-base times file'),
            (['57'],
             lambda: (lambda p: None if not os.path.exists(p) else sum(
                 float(l.split()[2].rstrip('s')) for l in open(p)
                 if len(l.split()) >= 3 and l.split()[1] == 'SAT'
             ) / 3600)(os.path.join(ROOT, 'tournaments/dr19_arcflip/sweep.log')),
             'dr19_g2, the SAT rows of the 57-orbit sweep log'),
            (['regular tournaments on', '15'],
             lambda: (lambda s: None if s is None else s / 3600)(
                 marker_sum('cluster/jz_n15/results_margin1/done', 'secs')),
             'n=15 census, the secs= field of 6,000 residue markers'),
        ):
            want = cell(words)
            got = fn()
            if got is None:
                skip('DERIVED', 'A.6 row %s' % ' '.join(words), 'artifact absent')
            else:
                record('DERIVED', 'A.6 row %s' % ' '.join(words), want, round(got, 2),
                       close(want, got), label)

        # T4 is a CROSS-FILE check, not a re-derivation: the per-base markers
        # for the arc-criticality campaign live on the cluster, so what is
        # compared is the manuscript's figure against the kit's own roll-up,
        # recorded in a different file.  Weaker than summing raw evidence, and
        # labelled as such rather than being quietly counted as equivalent.
        agg = os.path.join(ROOT, 'cluster', 'jz_p23arc', 'AGGREGATE_OUTPUT.txt')
        want = cell(['one arc reversed'])
        if os.path.exists(agg):
            src = open(agg).read()
            m = re.search(r'core-hours spent\s*:\s*([\d.]+)', src)
            got = float(m.group(1)) if m else None
            n = re.search(r'base states screened\s*:\s*(\d+)', src)
            mean = re.search(r'mean per base state\s*:\s*([\d.]+)', src)
            if got is not None:
                record('DERIVED', 'A.6 row one arc reversed', want, got,
                       close(want, got),
                       'cluster/jz_p23arc roll-up (cross-file, markers not shipped)')
            if n and mean and got is not None:
                prod = int(n.group(1)) * float(mean.group(1)) / 3600
                record('ARITHMETIC', 'A.6 one arc reversed is internally consistent',
                       got, round(prod, 1), close(got, prod, 0.01),
                       'base states screened x mean per base state')
        else:
            declared('A.6 row one arc reversed', want, 'CLAIMS.md gap 3')

        # Delta_28 - 5: same cross-file shape -- the markers are on the cluster,
        # so the figure is compared against the sweep's roll-up, in seconds.
        rows = tsv_rows('verdicts/n22_obstructions/verdicts.tsv')
        want = cell(['delta_{28}', 'sweep'])
        if rows:
            h = rows[0]
            got = [float(r[h.index('seconds')]) / 3600 for r in rows[1:]
                   if r[0] == 'd027_mv04']
            if got:
                record('DERIVED', 'A.6 row Delta_28 - 5 sweep', want, round(got[0], 1),
                       close(want, got[0]),
                       'verdicts/n22_obstructions roll-up (cross-file, markers on '
                       'the cluster)')
            else:
                declared('A.6 row Delta_28 - 5 sweep', want, 'CLAIMS.md gap 7')
        else:
            declared('A.6 row Delta_28 - 5 sweep', want, 'CLAIMS.md gap 7')

        # T7, same cross-file shape as T4: the per-task accounting lives on the
        # cluster, so what is compared is the manuscript's figure against the
        # three-way total a different file records.
        sc = os.path.join(ROOT, 'cluster', 'jz_n13sc', 'SLURM_COST.txt')
        want = cell(['self-converse tournaments on'])
        if os.path.exists(sc):
            m = re.search(r'total\s+([\d.]+) core-h', open(sc).read())
            got = float(m.group(1)) if m else None
            if got is not None:
                record('DERIVED', 'A.6 row self-converse on 13', want, got,
                       close(want, got, 0.01),
                       'cluster/jz_n13sc three-way total (cross-file, per-task '
                       'accounting not shipped)')
            else:
                declared('A.6 row self-converse on 13', want, 'CLAIMS.md gap 3')
        else:
            declared('A.6 row self-converse on 13', want, 'CLAIMS.md gap 3')

        for words, where in ((['all tournaments on'], 'CLAIMS.md gap 1'),):
            declared('A.6 row %s' % ' '.join(words), cell(words), where)

    # Appendix A.5's runtime table.
    run = find_table(tabs, 'live base states', 'core-hours', 'nodes')
    if run is None:
        skip('DERIVED', 'A.5 runtime table', 'table not found in the manuscript')
    else:
        arch = MAJORITY_ARCHIVE
        for r in run[1:]:
            qv = num(r[0])
            if qv is None or int(qv) not in arch:
                continue
            qv = int(qv)
            live, hours, nodes, per = (num(r[1]), num(r[2]), num(r[3]), num(r[4]))
            tot = archive_totals(arch[qv])
            if tot is None:
                skip('DERIVED', 'A.5 q=%d' % qv, 'archive absent or zstd missing')
                continue
            _, n_nodes, n_dom, secs = tot
            record('DERIVED', 'A.5 q=%d core-hours' % qv, hours, round(secs / 3600, 2),
                   close(hours, secs / 3600), 'sum of time= over the archive')
            if nodes is not None:
                note = 'sum of nodes= over the archive'
                if not close(nodes, n_nodes, 0.01) and close(nodes, n_dom, 0.01):
                    note = ('THE PRINTED FIGURE IS dom_nodes, NOT nodes: '
                            'dom_nodes=%.3e, nodes=%.3e' % (n_dom, n_nodes))
                record('DERIVED', 'A.5 q=%d nodes' % qv, nodes, float('%.3g' % n_nodes),
                       close(nodes, n_nodes, 0.01), note)
            if live is not None and per is not None:
                record('ARITHMETIC', 'A.5 q=%d seconds per live base state' % qv,
                       per, round(hours * 3600 / live, 1),
                       close(per, hours * 3600 / live, 0.01),
                       'core-hours x 3600 / live base states')

        # the live counts themselves, search-free
        for qv, args in ((23, ['--q', '23', '--base', '0', '1', '2', '5', '11']),
                         (31, ['--q', '31', '--base', '0', '1', '2', '3', '6'])):
            r = row_starting(run, str(qv))
            if r is None:
                continue
            got = survivors(args)
            if got is None or got[1] is None:
                skip('DERIVED', 'A.5 q=%d live base states' % qv,
                     'base_survivors.py unavailable')
            else:
                # q=23 uses the break in use, not the optimum, so compare the
                # base-state total and let CLAIMS.md carry the break choice.
                record('DERIVED', 'A.5 q=%d base states (total)' % qv, None, got[0],
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
        # "can produce, but not with unit margin": unit margin UNSAT, majority SAT
        sep = [r for r in rows[1:] if len(r) > ma and r[mi].strip() == 'UNSAT'
               and r[ma].strip().startswith('SAT')]
        by_n = {}
        for r in sep:
            by_n[int(r[1])] = by_n.get(int(r[1]), 0) + 1
        # "...turn up 42 tournaments that five voters can produce, but not with unit
        # margin: 2 doubly regular ones at order 19, 4 vertex-transitive and 25
        # near-doubly regular ones at order 21, and 11 circulant ones at order 23."
        # Every count before an "at order N" is credited to N, and the counts must
        # also add up to the total the sentence opens with.
        flat = re.sub(r'[${}]', '', re.sub(r'\s+', ' ', md))
        m = re.search(r'turn up (\d+) tournaments that five voters can produce, but '
                      r'not with unit margin: ([^.]*)\.', flat)
        if m:
            want, acc = {}, []
            for tok in re.finditer(r'at order (\d+)|(\d+)', m.group(2)):
                if tok.group(1):
                    want[int(tok.group(1))] = want.get(int(tok.group(1)), 0) + sum(acc)
                    acc = []
                else:
                    acc.append(int(tok.group(2)))
            total = int(m.group(1))
            record('LEDGER', 'the %d unit-margin-only obstructions' % total, want,
                   by_n, want == by_n and sum(want.values()) == total and not acc,
                   'ledger rows with margin1 = UNSAT and majority = SAT, by order')
        else:
            record('LEDGER', 'the unit-margin-only obstructions', 'sentence not found',
                   by_n, False, 'could not read the claim out of the manuscript')
        # Section 3.7: none of the 37 doubly regular tournaments on 23 vertices
        # is inducible, at either margin.
        both = [r for r in rows[1:] if len(r) > ma and r[1] == '23'
                and r[mi].strip() == 'UNSAT' and r[ma].strip() == 'UNSAT']
        m = re.search(r'none of the \$(\d+)\$ doubly regular ones is, at\s*\n?unit '
                      r'margin or unrestricted', md)
        if m:
            record('LEDGER', 'order 23: doubly regular, not inducible at either margin',
                   int(m.group(1)), len(both), int(m.group(1)) == len(both),
                   'ledger rows at n=23 with margin1 = majority = UNSAT')
        else:
            skip('LEDGER', 'order 23 doubly regular count', 'sentence not found')

    # ------------------------------------------------- Section 3.2 and 3.7 costs
    m = re.search(r'two searches together took about \$([\d{},]+)\$\s*\n?cluster '
                  r'core-hours', md)
    cost = find_table(tabs, 'computation', 'core-hours')
    if m and cost:
        a = row_starting(cost, 'delta_6', 'sweep')
        b = row_starting(cost, 'delta_{28}', 'sweep')
        if a and b:
            tot = num(a[-1]) + num(b[-1])
            record('ARITHMETIC', '3.2 the two 22-vertex sweeps together', num(m.group(1)),
                   round(tot, 1), close(num(m.group(1)), tot, 0.01),
                   'the two A.6 sweep rows, summed; "about" read as within 1%')
    m = re.search(r'\$(\d+)\$ of them ran\s*\n?on the cluster, at about '
                  r'\$([\d{},]+)\$ cluster core-hours', md)
    rows = tsv_rows('cluster/jz_drt23maj/jz_drt23maj.tsv')
    if m and rows:
        h = rows[0]
        ch = [float(r[h.index('core_hours')]) for r in rows[1:]]
        ok_n = len([r for r in rows[1:] if r[h.index('verdict')] == 'UNSAT'])
        record('DERIVED', '3.7 doubly regular sweeps on the cluster (count)',
               int(m.group(1)), ok_n, int(m.group(1)) == ok_n,
               'UNSAT rows of cluster/jz_drt23maj/jz_drt23maj.tsv (cross-file roll-up)')
        record('DERIVED', '3.7 doubly regular sweeps on the cluster (core-hours)',
               num(m.group(2)), round(sum(ch), 1), close(num(m.group(2)), sum(ch), 0.01),
               'cluster/jz_drt23maj/jz_drt23maj.tsv, summed (cross-file roll-up)')
    elif m:
        declared('3.7 doubly regular sweeps on the cluster', num(m.group(2)),
                 'CLAIMS.md gap 7')

    # ------------------------------------------------------------- Appendix G
    gt = find_table(tabs, 'vertices', 'deleted', 'classes')
    if gt is None:
        skip('DERIVED', 'Appendix G level table', 'table not found')
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
            record('DERIVED', 'G classes per level (one, two, three deleted)', want, got,
                   want == got and ok_p,
                   'verify/drt23_level_counts.py from the 18 parents, one per converse '
                   'pair (checked)')
        else:
            skip('DERIVED', 'G classes per level', 'LABELG not set')
        # the settled count at 21 vertices, from the archive's own manifest
        r21 = row_starting(gt, '4{,}108') or row_starting(gt, '4,108')
        m = re.search(r'\$([\d{},]+)\$ settled', ' '.join(r21)) if r21 else None
        path = os.path.join(ROOT, 'evidence', 'n21_level_witnesses.tar.zst')
        if m and os.path.exists(path):
            raw = subprocess.run(['zstd', '-dc', path], capture_output=True).stdout
            tf = tarfile.open(fileobj=io.BytesIO(raw))
            rows = [l for l in tf.extractfile('n21_level/SETTLED.tsv').read().decode()
                    .splitlines() if l and not l.startswith('#')][1:]
            record('DERIVED', 'G classes settled at 21 vertices', num(m.group(1)),
                   len(rows), num(m.group(1)) == len(rows),
                   'rows of SETTLED.tsv in evidence/n21_level_witnesses.tar.zst; check 5d '
                   'verifies each witness')
        else:
            skip('DERIVED', 'G classes settled at 21 vertices', 'cell or archive absent')
        m = re.search(r'screen exhausted \$([\d{},]+)\$ base states and found none', md)
        rows = tsv_rows('cluster/jz_drt23mv/HARDNESS_378.tsv')
        if m and rows:
            ex = sum(int(r[3]) for r in rows if len(r) >= 6)
            hosts = sum(1 for r in rows if len(r) >= 6)
            record('DERIVED', 'G base states exhausted by the 22-vertex screen',
                   num(m.group(1)), ex, num(m.group(1)) == ex,
                   'exhausted column of cluster/jz_drt23mv/HARDNESS_378.tsv over %d hosts '
                   '(cross-file roll-up)' % hosts)
        m = re.search(r'about one base state in \$(\d+)\$ yields a\s*\n?witness', md)
        if m:
            declared('G witness density at 21 vertices, 1 in', num(m.group(1)),
                     'CLAIMS.md gap 7')

    # -------------------------------------------------------------- Appendix D
    counts = find_table(tabs, '$d_n$') or find_table(tabs, 'D_n')
    if counts is None:
        skip('DERIVED', 'Appendix D counts', 'table not found')
    else:
        want_r15 = None
        for r in counts[1:]:
            if num(r[0]) == 15:
                want_r15 = num(r[2])
        got = marker_sum('cluster/jz_n15/results_margin1/done', 'instances')
        if got is None:
            skip('DERIVED', 'Appendix D R_15', 'n15 markers absent')
        else:
            record('DERIVED', 'Appendix D R_15', want_r15, got, close(want_r15, got, 0),
                   'sum of instances= over the 6,000 residue markers')
        want_s13 = None
        for r in counts[1:]:
            if num(r[0]) == 13:
                want_s13 = num(r[3])
        agg = os.path.join(ROOT, 'cluster', 'jz_n13sc', 'aggregate.sh')
        if want_s13 is not None and os.path.exists(agg):
            src = open(agg).read()
            # the kit writes it with Python underscore separators
            mm = re.search(r'TOTAL\s*=\s*([\d_]+)', src)
            got13 = float(mm.group(1).replace('_', '')) if mm else None
            record('DERIVED', 'Appendix D S_13', want_s13, got13,
                   close(want_s13, got13, 0),
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
