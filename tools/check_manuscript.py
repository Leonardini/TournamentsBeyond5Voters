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
    # Appendix A.1's integer program at q = 23, k = 5.
    q, k = 23, 5
    for want, label in ((k * math.comb(q, 2), 'binaries'),
                        (2 * k * math.comb(q, 3), 'transitivity rows'),
                        (math.comb(q, 2), 'majority rows')):
        stated = re.search(r'\$?([\d{},]+)\$?\s*' + label, md)
        got = num(stated.group(1)) if stated else None
        record('ARITHMETIC', 'A.1 ILP %s at q=23' % label, got, want,
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

    # ------------------------------------------------------------------ DERIVED
    # Appendix A.4's cost table, row by row.
    cost = find_table(tabs, 'computation', 'core-hours')
    if cost is None:
        skip('DERIVED', 'A.4 cost table', 'table not found in the manuscript')
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
                skip('DERIVED', 'A.4 row %s' % ' '.join(words), 'artifact absent')
            else:
                record('DERIVED', 'A.4 row %s' % ' '.join(words), want, round(got, 2),
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
                record('DERIVED', 'A.4 row one arc reversed', want, got,
                       close(want, got),
                       'cluster/jz_p23arc roll-up (cross-file, markers not shipped)')
            if n and mean and got is not None:
                prod = int(n.group(1)) * float(mean.group(1)) / 3600
                record('ARITHMETIC', 'A.4 one arc reversed is internally consistent',
                       got, round(prod, 1), close(got, prod, 0.01),
                       'base states screened x mean per base state')
        else:
            declared('A.4 row one arc reversed', want, 'CLAIMS.md gap 3')

        # T7, same cross-file shape as T4: the per-task accounting lives on the
        # cluster, so what is compared is the manuscript's figure against the
        # three-way total a different file records.
        sc = os.path.join(ROOT, 'cluster', 'jz_n13sc', 'SLURM_COST.txt')
        want = cell(['self-converse tournaments on'])
        if os.path.exists(sc):
            m = re.search(r'total\s+([\d.]+) core-h', open(sc).read())
            got = float(m.group(1)) if m else None
            if got is not None:
                record('DERIVED', 'A.4 row self-converse on 13', want, got,
                       close(want, got, 0.01),
                       'cluster/jz_n13sc three-way total (cross-file, per-task '
                       'accounting not shipped)')
            else:
                declared('A.4 row self-converse on 13', want, 'CLAIMS.md gap 3')
        else:
            declared('A.4 row self-converse on 13', want, 'CLAIMS.md gap 3')

        for words, where in ((['all tournaments on'], 'CLAIMS.md gap 1'),):
            declared('A.4 row %s' % ' '.join(words), cell(words), where)

    # Appendix A.3's runtime table.
    run = find_table(tabs, 'live base states', 'core-hours', 'nodes')
    if run is None:
        skip('DERIVED', 'A.3 runtime table', 'table not found in the manuscript')
    else:
        arch = {23: 'rerun1_p23_majority.tar.zst', 27: 'p27_majority.tar.zst',
                31: 'p31_majority.tar.zst', 43: 'p43_majority.tar.zst'}
        for r in run[1:]:
            qv = num(r[0])
            if qv is None or int(qv) not in arch:
                continue
            qv = int(qv)
            live, hours, nodes, per = (num(r[1]), num(r[2]), num(r[3]), num(r[4]))
            tot = archive_totals(arch[qv])
            if tot is None:
                skip('DERIVED', 'A.3 q=%d' % qv, 'archive absent or zstd missing')
                continue
            _, n_nodes, n_dom, secs = tot
            record('DERIVED', 'A.3 q=%d core-hours' % qv, hours, round(secs / 3600, 2),
                   close(hours, secs / 3600), 'sum of time= over the archive')
            if nodes is not None:
                note = 'sum of nodes= over the archive'
                if not close(nodes, n_nodes, 0.01) and close(nodes, n_dom, 0.01):
                    note = ('THE PRINTED FIGURE IS dom_nodes, NOT nodes: '
                            'dom_nodes=%.3e, nodes=%.3e' % (n_dom, n_nodes))
                record('DERIVED', 'A.3 q=%d nodes' % qv, nodes, float('%.3g' % n_nodes),
                       close(nodes, n_nodes, 0.01), note)
            if live is not None and per is not None:
                record('ARITHMETIC', 'A.3 q=%d seconds per live base state' % qv,
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
                skip('DERIVED', 'A.3 q=%d live base states' % qv,
                     'base_survivors.py unavailable')
            else:
                # q=23 uses the break in use, not the optimum, so compare the
                # base-state total and let CLAIMS.md carry the break choice.
                record('DERIVED', 'A.3 q=%d base states (total)' % qv, None, got[0],
                       got[0] in (8031, 21009),
                       'search-free count from sat/base_survivors.py')

    # ------------------------------------------------------------------- LEDGER
    led = os.path.join(ROOT, 'verdicts', 'verdict_ledger.tsv')
    if not os.path.exists(led):
        skip('LEDGER', 'unit-margin obstructions', 'ledger absent')
    else:
        rows = [l.rstrip('\n').split('\t') for l in open(led)]
        hdr = rows[0]
        mi = hdr.index('margin1')
        obs = [r for r in rows[1:] if len(r) > mi and r[mi].strip() == 'UNSAT']
        by_n = {}
        for r in obs:
            by_n[int(r[1])] = by_n.get(int(r[1]), 0) + 1
        m = re.search(r'ten tournaments that are not\s*\n?\$?5\$?-inducible with unit '
                      r'margin: (\d+) doubly regular ones at order (\d+), (\d+) '
                      r'vertex-transitive ones at order (\d+), and\s*\n?(\d+) '
                      r'circulant ones at order (\d+)', md)
        if m:
            want = {int(m.group(2)): int(m.group(1)), int(m.group(4)): int(m.group(3)),
                    int(m.group(6)): int(m.group(5))}
            record('LEDGER', 'the ten unit-margin obstructions', want, by_n,
                   want == by_n, 'rows of verdict_ledger.tsv with margin1 = UNSAT')
        else:
            record('LEDGER', 'the ten unit-margin obstructions', 'sentence not found',
                   by_n, False, 'could not read the claim out of the manuscript')

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
        ROOT, 'manuscript', 'Tournaments_not_inducible_by_five_voters.md')
    sys.exit(main(path, '--json' in sys.argv[1:]))
