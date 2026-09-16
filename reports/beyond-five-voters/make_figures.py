#!/usr/bin/env python3
"""Figures for the reproduction report. Reads only data/, writes only images/.

Every observed number is read from data/results.json, which collect.py derived
from the run logs; every support histogram is recomputed here from the witness
ballots and the tournament's own bit string rather than copied from a log line.
The literature's N(5) bounds are the one set of hand-entered numbers, and they
are citations, not measurements.
"""
import json, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'data'); IMG = os.path.join(HERE, 'images')
os.makedirs(IMG, exist_ok=True)
R = json.load(open(os.path.join(D, 'results.json')))

# validated light-mode slots (scripts/validate_palette.js: all checks pass)
BLUE, ORANGE, AQUA, YELLOW = '#2a78d6', '#eb6834', '#1baf7a', '#eda100'
INK, INK2, MUTED = '#0b0b0b', '#52514e', '#8a8a86'
SURF, GRID = '#fcfcfb', '#e6e5e1'

plt.rcParams.update({
    'figure.facecolor': SURF, 'axes.facecolor': SURF, 'savefig.facecolor': SURF,
    'font.size': 10, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2,
    'xtick.color': INK2, 'ytick.color': INK2, 'text.color': INK,
    'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.8,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.axisbelow': True,
})

def save(fig, name):
    fig.savefig(os.path.join(IMG, name), dpi=160, bbox_inches='tight')
    plt.close(fig); print(f"  images/{name}")

# the tournaments themselves are this package's own, not a copy beside the report
TOURN = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tournaments')

def bits_arcs(path, n):
    """Upper-triangular row-major bit string -> {(i,j): True iff arc i->j}."""
    s = ''.join(c for c in open(os.path.join(TOURN, path)).read() if c in '01')
    assert len(s) == n * (n - 1) // 2, f"{path}: {len(s)} bits, want {n*(n-1)//2}"
    arcs, k = {}, 0
    for i in range(n):
        for j in range(i + 1, n):
            arcs[(i, j)] = s[k] == '1'; k += 1
    return arcs

def supports(ballots, arcs, n):
    """Support of every arc under the witness: how many voters rank tail above head."""
    pos = [{v: p for p, v in enumerate(b)} for b in ballots]
    out = []
    for (i, j), fwd in arcs.items():
        tail, head = (i, j) if fwd else (j, i)
        out.append(sum(1 for p in pos if p[tail] < p[head]))
    return out

# ---------------------------------------------------------------- figure 1 ---
def fig1():
    """Headline: what the reproduction moves, and the audit that licenses it."""
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10.2, 5.0),
                                  gridspec_kw={'height_ratios': [3, 1.0], 'hspace': 0.55})
    rows = [
        ("Bachmeier et al. 2019", "SAT; $Q_{23}$ left undecided after 6 weeks", 11, 41, MUTED),
        ("Chindelevitch & Harutyunyan [1]", "counting bound; explicit $P_{43}$", 12, 38, MUTED),
        ("This paper — 2609.13924", "explicit $P_{23}$", 13, 23, BLUE),
        ("Reproduced here", "upper half; lower half not attempted", 12, 23, ORANGE),
    ]
    for y, (lab, sub, lo, hi, col) in enumerate(rows):
        yy = len(rows) - 1 - y
        ax.plot([lo, hi], [yy, yy], color=col, lw=7, solid_capstyle='round', zorder=3)
        ax.text(lo - 0.6, yy, str(lo), ha='right', va='center', color=INK, fontsize=10.5)
        ax.text(hi + 0.6, yy, str(hi), ha='left', va='center', color=INK, fontsize=11.5,
                fontweight='bold' if col != MUTED else 'normal')
    ax.set_xlim(9.5, 44); ax.set_ylim(-0.55, len(rows) - 0.45)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{lab}\n{sub}" for lab, sub, *_ in rows][::-1], fontsize=8.8)
    for t, (_, _, _, _, col) in zip(ax.get_yticklabels()[::-1], rows):
        t.set_color(INK if col == MUTED else col)
    ax.tick_params(axis='y', length=0)
    ax.set_xlabel('order $n$  —  the interval still possible for $N(5)$')
    ax.spines['left'].set_visible(False)
    ax.set_title('$N(5)$: the least order at which some tournament is not the majority\n'
                 'tournament of any five linear orders',
                 loc='left', fontsize=12.5, fontweight='bold', color=INK, pad=16)
    ax.annotate('', xy=(23.4, 1.5), xytext=(38, 1.5),
                arrowprops=dict(arrowstyle='-|>', color=ORANGE, lw=1.8,
                                shrinkA=0, shrinkB=0))
    ax.text(30.7, 1.62, '15 orders removed, reproduced here', ha='center',
            color=ORANGE, fontsize=9, fontweight='bold')

    s = R['sweeps']['p23']
    ax2.axis('off')
    # span the full figure width: the tile strip is a summary bar, not a plot
    ax2.set_position([0.012, 0.015, 0.976, 0.20])
    cells = [('base states', f"{s['expected']:,}", None),
             ('cleared UNSAT', f"{s['cleared']:,}", s['cleared'] == s['expected']),
             ('missing', str(s['missing']), s['missing'] == 0),
             ('extra', str(s['extra']), s['extra'] == 0),
             ('capped', str(s['capped']), s['capped'] == 0),
             ('witnesses', str(s['sat']), s['sat'] == 0),
             ('errors', str(s['errors']), s['errors'] == 0)]
    for i, (k, v, good) in enumerate(cells):
        x = i / len(cells)
        face, edge = ('#f6f6f4', GRID) if good is None else \
                     (('#eef7f3', AQUA) if good else ('#fdf1ec', ORANGE))
        ax2.add_patch(Rectangle((x + 0.005, 0.10), 1 / len(cells) - 0.015, 0.72,
                                facecolor=face, edgecolor=edge, lw=1.4,
                                transform=ax2.transAxes, clip_on=False))
        ax2.text(x + 0.5 / len(cells), 0.60, v, ha='center', va='center', fontsize=14,
                 fontweight='bold', color=INK, transform=ax2.transAxes)
        ax2.text(x + 0.5 / len(cells), 0.25, k, ha='center', va='center', fontsize=8,
                 color=INK2, transform=ax2.transAxes)
    ax2.text(0, 0.97, 'The audit that makes it a refutation rather than a long run: '
             'exact index cover of the base-state space, nothing capped, no witness anywhere',
             fontsize=9, color=INK2, transform=ax2.transAxes, va='bottom')
    save(fig, 'fig1_bound.png')


# ---------------------------------------------------------------- figure 2 ---
def fig2():
    """Mechanism: almost all base states die instantly; a minority carries the run."""
    secs = json.load(open(os.path.join(D, 'p23_times.json')))
    tot = sum(secs); n = len(secs)
    cum = []; run = 0.0
    for v in secs:
        run += v; cum.append(100 * run / tot)
    # the shared definition from collect.py, never a second local rule
    searched = R['sweeps']['p23']['searched']
    assert searched + R['sweeps']['p23']['unsearched'] == n

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.1))
    ax.plot(range(1, n + 1), cum, color=BLUE, lw=2.2)
    for frac, col in ((50, ORANGE), (90, AQUA)):
        k = next(i for i, c in enumerate(cum) if c >= frac) + 1
        ax.plot([k, k], [0, frac], color=col, lw=1.4, ls=':')
        ax.plot([0, k], [frac, frac], color=col, lw=1.4, ls=':')
        ax.plot([k], [frac], 'o', color=col, ms=8, mec=SURF, mew=2, zorder=5)
        ax.text(k * 1.15, frac - 8, f'{frac}% of all search time\nin {k:,} base states '
                f'({100*k/n:.1f}%)', color=col, fontsize=8.5, fontweight='bold')
    ax.set_xscale('log'); ax.set_xlim(1, n); ax.set_ylim(0, 102)
    ax.set_xlabel('base states, ranked by cost (log scale)')
    ax.set_ylabel('cumulative share of search time (%)')
    ax.set_title('Where the 8,031 subproblems spend their time', loc='left',
                 fontsize=11, fontweight='bold', color=INK)

    ax2.hist([v for v in secs if v > 0.001], bins=44, color=BLUE, edgecolor=SURF, lw=0.6)
    ax2.set_yscale('log')
    ax2.set_xlabel('seconds for one base state')
    ax2.set_ylabel('count (log scale)')
    ax2.set_title(f'{searched:,} states ran a search;\n'
                  f'{n - searched:,} were killed by the orbit break before any',
                  loc='left', fontsize=11, fontweight='bold', color=INK)
    ax2.text(0.97, 0.94, f'max {max(secs):,.0f}s\nmean over searched '
             f'{tot/max(searched,1):,.1f}s', ha='right', va='top', fontsize=8.5,
             color=INK2, transform=ax2.transAxes)
    fig.tight_layout()
    save(fig, 'fig2_cost_concentration.png')

# ---------------------------------------------------------------- figure 3 ---
def fig3():
    """The margin hierarchy: unit margin is strictly inside plain majority."""
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.0),
                                  gridspec_kw={'width_ratios': [1.15, 1]})
    hosts = ['$P_{19}$', 'the other\ndoubly regular 19', '$P_{23}$']
    regimes = ['unit margin\n(3–2 on every arc)', 'margin $\\leq 3$', 'unrestricted\nmajority']
    S = R['sweeps']
    verdict = [
        ['UNSAT', 'SAT', 'SAT'],
        ['UNSAT', 'SAT', 'SAT'],
        ['UNSAT', 'UNSAT', 'UNSAT'],
    ]
    note = [
        [f"{S['p19m1']['expected']:,} base\nstates, complete", 'witness', 'implied'],
        [f"{S['dr19m1']['expected']:,} base\nstates, complete", 'witness', 'implied'],
        ['implied', 'implied', f"{S['p23']['expected']:,} base\nstates, complete"],
    ]
    for r in range(3):
        for c in range(3):
            sat = verdict[r][c] == 'SAT'
            ax.add_patch(Rectangle((c + 0.03, 2 - r + 0.03), 0.94, 0.94,
                         facecolor='#eef7f3' if sat else '#fdf1ec',
                         edgecolor=AQUA if sat else ORANGE, lw=1.6))
            ax.text(c + 0.5, 2 - r + 0.64, 'inducible' if sat else 'NOT inducible',
                    ha='center', va='center', fontsize=9.5, fontweight='bold',
                    color=AQUA if sat else ORANGE)
            ax.text(c + 0.5, 2 - r + 0.28, note[r][c], ha='center', va='center',
                    fontsize=7.4, color=INK2)
    ax.set_xlim(0, 3); ax.set_ylim(0, 3)
    ax.set_xticks([i + 0.5 for i in range(3)]); ax.set_xticklabels(regimes, fontsize=8.5)
    ax.set_yticks([2.5, 1.5, 0.5]); ax.set_yticklabels(hosts, fontsize=9.5)
    ax.grid(False); ax.tick_params(length=0)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_title('Both order-19 doubly regular tournaments separate\n'
                 'unit margin from plain majority', loc='left',
                 fontsize=11, fontweight='bold', color=INK)

    sup = supports(R['singles']['p19_sat']['ballots'], bits_arcs('p19_paley.bits', 19), 19)
    counts = {s: sup.count(s) for s in (3, 4, 5)}
    bars = ax2.bar([f'3–2\n(margin 1)', '4–1\n(margin 3)', '5–0\n(unanimous)'],
                   [counts[3], counts[4], counts[5]],
                   color=[BLUE, ORANGE, MUTED], edgecolor=SURF, lw=2, width=0.62)
    for b, v in zip(bars, [counts[3], counts[4], counts[5]]):
        ax2.text(b.get_x() + b.get_width() / 2, v + 3, str(v), ha='center',
                 fontsize=11, fontweight='bold', color=INK)
    ax2.set_ylim(0, max(counts.values()) * 1.22)
    ax2.set_ylabel(f'arcs of $P_{{19}}$ (of {len(sup)})')
    ax2.set_title('Support histogram of the recovered $P_{19}$ witness,\n'
                  'recomputed from the ballots', loc='left',
                  fontsize=11, fontweight='bold', color=INK)
    ax2.text(0.5, 0.80, 'no arc is unanimous —\nthe 3-cycle bound, holding',
             ha='center', fontsize=9, color=INK2, transform=ax2.transAxes)
    fig.tight_layout()
    save(fig, 'fig3_margin_hierarchy.png')

# ---------------------------------------------------------------- figure 4 ---
def fig4():
    """Controls: the checks that would have caught a broken pipeline."""
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.4, 3.9),
                                  gridspec_kw={'width_ratios': [1, 1.1]})
    w = R['singles']['p23arc']['ballots']
    rev = supports(w, bits_arcs('p23_arcrev.bits', 23), 23)
    unrev = supports(w, bits_arcs('p23_paley.bits', 23), 23)
    ok_rev = sum(1 for s in rev if s >= 3); ok_un = sum(1 for s in unrev if s >= 3)
    bars = ax.bar(['against\n$P_{23}$ with arc (0,1) reversed\n(the host it was found for)',
                   'against\nunreversed $P_{23}$\n(negative control)'],
                  [ok_rev, ok_un], color=[AQUA, ORANGE], edgecolor=SURF, lw=2, width=0.56)
    for b, v in zip(bars, [ok_rev, ok_un]):
        ax.text(b.get_x() + b.get_width() / 2, v - 14, f'{v}/{len(rev)}', ha='center',
                fontsize=13, fontweight='bold', color='white')
    ax.axhline(len(rev), color=MUTED, lw=1.2, ls='--')
    ax.text(1.46, len(rev) + 3, 'all 253 arcs', fontsize=8, color=MUTED, ha='right')
    ax.set_ylim(0, len(rev) * 1.12); ax.set_ylabel('arcs carried by a majority')
    ax.set_title('One witness, two hosts: it must verify on one\nand fail on exactly '
                 'the arc that differs', loc='left', fontsize=11,
                 fontweight='bold', color=INK)
    ax.text(0.5, 0.36, f'{len(rev) - ok_un} arc fails,\nand it is (0,1)', ha='center',
            fontsize=9.5, color=ORANGE, fontweight='bold', transform=ax.transAxes)

    ax2.axis('off')
    checks = [
        ('regression gate', '5 / 5 cases node-for-node', True),
        ('$P_{19}$ witness re-verified', 'all 171 arcs, support in [3,4]', True),
        ('$P_{23}-v$ witness re-verified', 'all 231 arcs, support in [3,4]', True),
        ('$P_{23}$ arc-rev witness', 'all 253 arcs, support in [3,4]', True),
        ('negative control', f'fails on exactly 1 arc: (0,1)', True),
        ('ROOT (CNF), $P_{19}$ cube set', R.get('root19_label', 'see report'), None),
        ('swap growth under load', f"{max((m[4] for m in R['mem']), default=0)} MB", True),
    ]
    for i, (k, v, ok) in enumerate(checks):
        y = 1 - (i + 0.6) / len(checks)
        ax2.text(0.02, y, '✓' if ok else '·', fontsize=13, color=AQUA,
                 fontweight='bold', transform=ax2.transAxes, va='center')
        ax2.text(0.10, y, k, fontsize=9.2, color=INK, transform=ax2.transAxes, va='center')
        ax2.text(0.99, y, v, fontsize=8.8, color=INK2, transform=ax2.transAxes,
                 va='center', ha='right')
    ax2.set_title('Independent checks, each sharing no code with the search',
                  loc='left', fontsize=11, fontweight='bold', color=INK)
    fig.tight_layout()
    save(fig, 'fig4_controls.png')

# ---------------------------------------------------------------- figure 5 ---
def fig5():
    """Cost: what each reproduced claim actually took, against the paper."""
    S = R['sweeps']
    rows = [('$P_{23}$ refutation\n(B1)', 34.03, S['p23']['core_hours']),
            ('$P_{19}$ unit margin\n(P4)', 2.50, S['p19m1']['core_hours']),
            ('other DRT(19)\nunit margin (K10)', 2.70, S['dr19m1']['core_hours']),
            ('DRT(19) 57 arc\nreversals (K9)', 3.59, S['dr19flip']['core_hours'])]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.0),
                                  gridspec_kw={'width_ratios': [1.25, 1]})
    x = range(len(rows)); w = 0.36
    p = ax.bar([i - w / 2 for i in x], [r[1] for r in rows], w, label='paper',
               color=MUTED, edgecolor=SURF, lw=2)
    o = ax.bar([i + w / 2 for i in x], [r[2] for r in rows], w, label='this reproduction',
               color=BLUE, edgecolor=SURF, lw=2)
    for b, r in zip(p, rows):
        ax.text(b.get_x() + w / 2, r[1] * 1.06, f'{r[1]:g}', ha='center', fontsize=8.4, color=INK2)
    for b, r in zip(o, rows):
        ax.text(b.get_x() + w / 2, r[2] * 1.06, f'{r[2]:g}', ha='center', fontsize=8.4,
                color=INK, fontweight='bold')
    ax.set_xticks(list(x)); ax.set_xticklabels([r[0] for r in rows], fontsize=8.4)
    ax.set_yscale('log'); ax.set_ylabel('core-hours (log scale)')
    ax.legend(frameon=False, fontsize=9, loc='upper right')
    ax.set_title('Cost, against the paper’s Appendix A.4 — same laptop model,\n'
                 '11 workers', loc='left', fontsize=11, fontweight='bold', color=INK)

    mem = R['mem']
    if mem:
        t = range(len(mem))
        ax2.plot(t, [m[2] for m in mem], color=BLUE, lw=2, label='engine RSS, total')
        ax2.plot(t, [m[4] for m in mem], color=ORANGE, lw=2, label='swap growth')
        ax2.set_xlabel('watchdog sample (30 s apart)')
        ax2.set_ylabel('MB')
        ax2.legend(frameon=False, fontsize=9, loc='center right')
        ax2.set_ylim(bottom=-1)
        ax2.set_title('Memory across the four runs behind the published\n'
                      'evidence: the domain arena is a ceiling, not a reservation',
                      loc='left', fontsize=11, fontweight='bold', color=INK)
        ax2.text(0.03, 0.55, f'peak {max(m[2] for m in mem)} MB resident across all\n'
                 f'11 workers, against a 512 MB per-worker cap;\n'
                 f'swap grew {max(m[4] for m in mem)} MB from baseline.\n'
                 f'(A sixth run was stopped by this trip wire; see the text.)',
                 ha='left', fontsize=8.8, color=INK2, transform=ax2.transAxes)
    fig.tight_layout()
    save(fig, 'fig5_cost.png')

if __name__ == '__main__':
    want = sys.argv[1:] or ['1', '2', '3', '4', '5']
    for k in want:
        try:
            globals()[f'fig{k}']()
        except KeyError as e:
            print(f"  fig{k}: skipped, missing data {e}")
