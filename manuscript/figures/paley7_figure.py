"""Draw Figure 1 from the trace written by paley7_trace.py.

Visuals only: each panel is a self-contained tikzpicture carrying the diagram
and its labels, and nothing else.  The explanation belongs in the caption, not
in the picture.

Reads the trace JSON, asserts that the snapshots the figure shows are the ones
the search actually produced, and writes a standalone LaTeX document.  Nothing
is a hand-copied number: every order, slot tuple and domain comes out of the
trace, and every claim a panel makes is derived and checked first.

Usage:  python3 paley7_figure.py trace_maj.json paley7_alg1.tex
        python3 paley7_figure.py trace_maj.json --check ../<manuscript>.md
"""

import itertools
import json
import math
import sys

import paley7_trace as P

CANVAS = 18.6                # width of the whole figure, cm
LABEL_BASE = 1               # the manuscript numbers vertices from 1, the code from 0
CW, CH = 0.42, 0.36          # profile cell width and height, cm
VGAP = 0.10                  # gap between voter rows, cm
TW = 0.66                    # width of one slot tuple in a list, cm
ROWH = 0.32                  # line pitch in a tuple list, cm
LX = 0.78                    # indent of a domain's list past its $D(v)$ label, cm


def vl(v):
    """A vertex as the manuscript prints it.  Only ever for display: every
    comparison, domain key and shading test below stays on the code's own
    numbering, so the offset cannot leak into what the figure asserts."""
    return v + LABEL_BASE


def cyc(g, n):
    """A permutation in cycle form, on printed labels, fixed points dropped."""
    seen, out = set(), []
    for x in range(n):
        if x in seen or g[x] == x:
            continue
        c, y = [], x
        while y not in seen:
            seen.add(y)
            c.append(y)
            y = g[y]
        out.append(c)
    return "".join("(" + r"\,".join(str(vl(z)) for z in c) + ")" for c in out)


def tt(t):
    return r"\texttt{" + "".join(map(str, t)) + "}"


def tt_split(t, q):
    """A slot tuple with the positions that COINCIDE with q picked out.

    p_i = q_i is exactly the case in which the lift splits in two, so those
    digits are what the reader has to spot.
    """
    out = []
    for a, b in zip(t, q):
        out.append(r"\textcolor{okgreen}{%s}" % a if a == b else str(a))
    return r"\texttt{" + "".join(out) + "}"


def setnot(xs):
    return r"\{" + ",".join(str(vl(x)) for x in sorted(xs)) + r"\}"


# --------------------------------------------------------------------------
# pieces


def cells(row, x, y, shade=(), boxed=()):
    out = []
    for i, v in enumerate(row):
        fill = "basefill" if v in shade else "white"
        style = "cellnew" if v in boxed else "cell"
        out.append("  \\draw[%s, fill=%s] (%.3f,%.3f) rectangle ++(%.3f,%.3f);"
                   % (style, fill, x + i * CW, y, CW, CH))
        out.append("  \\node[lbl] at (%.3f,%.3f) {%s};"
                   % (x + i * CW + CW / 2, y + CH / 2, vl(v)))
    return out


def profile(orders, x, y, shade=(), boxed=(), names=None, ticks=False):
    """One row per voter, top-ranked leftmost.  Returns (lines, bottom y)."""
    out = []
    if ticks:
        for i in range(len(orders[0]) + 1):
            out.append("  \\draw[slottick] (%.3f,%.3f) -- ++(0,0.11);"
                       % (x + i * CW, y + 0.05))
            out.append("  \\node[slotnum] at (%.3f,%.3f) {%d};"
                       % (x + i * CW, y + 0.29, i))
    for i, o in enumerate(orders):
        yy = y - (i + 1) * CH - i * VGAP
        nm = names[i] if names else "$\\pi_{%d}$" % (i + 1)
        out.append("  \\node[vname] at (%.3f,%.3f) {%s};" % (x - 0.09, yy + CH / 2, nm))
        out += cells(o, x, yy, shade=shade, boxed=boxed)
    return out, y - len(orders) * CH - (len(orders) - 1) * VGAP


def domain_block(v, tups, x, y, perline, size, highlight=False, note=None):
    """One domain listed in full, with its size on the line below.

    Returns (lines, bottom y).  The size sits under the list rather than beside
    it, so it stays attached to its own domain even when the list wraps.
    """
    out = ["  \\node[key, anchor=west] at (%.3f,%.3f) {$D(%d)$};" % (x, y, vl(v))]
    body, rows = tuple_row(tups, x + LX, y, perline)
    out += body
    yb = y - rows * ROWH - 0.05                       # the line below the list,
    #                                                   with room for the frame
    out.append("  \\node[%s, anchor=west] at (%.3f,%.3f) {$|D(%d)|=%d$};"
               % ("keybox" if highlight else "keydim",
                  x + LX - (0.07 if highlight else 0.0), yb, vl(v), size))
    if note:
        out.append("  \\node[keyhi, anchor=west] at (%.3f,%.3f) {%s};"
                   % (x + LX + 1.65, yb, note))
    return out, yb


def tuple_row(tups, x, y, perline):
    """Slot tuples in monospace, wrapped one line per ROWH.

    Returns (lines, rows).  The caller advances the grid, so nothing lands on a
    half-line and a wrapped list cannot run into whatever comes next.
    """
    out = []
    for j, t in enumerate(tups):
        r, c = divmod(j, perline)
        out.append("  \\node[tup, anchor=west] at (%.3f,%.3f) {%s};"
                   % (x + c * TW, y - r * ROWH, tt(t)))
    return out, (len(tups) + perline - 1) // perline


def picture(lines):
    """Baseline at y=0, so panels set side by side line their titles up."""
    return ([r"\begin{tikzpicture}[x=1cm,y=1cm,baseline=0cm]"] + lines +
            [r"\end{tikzpicture}"])


def title(text, x=0.0, y=0.0):
    return ["  \\node[ttl] at (%.3f,%.3f) {%s};" % (x, y, text)]


def cross(x, y):
    return ["  \\node[bad] at (%.3f,%.3f) {$\\times$};" % (x, y)]


def tick(x, y):
    return ["  \\node[good] at (%.3f,%.3f) {$\\checkmark$};" % (x, y)]


# --------------------------------------------------------------------------
# panels


def panel_a(f):
    """The tournament: base bold, the inserted vertex's arcs to it dashed."""
    n, B, vstar, A = f["n"], f["B"], f["vstar"], f["A"]
    L = title(r"(a) the tournament $P_{%d}$" % n, -1.95, 0.0)
    R, cy = 1.62, -2.20
    for v in range(n):
        ang = math.radians(90 - 360.0 * v / n)
        L.append("  \\node[vtx] (v%d) at (%.3f,%.3f) {%d};"
                 % (v, R * math.cos(ang), cy + R * math.sin(ang), vl(v)))
    base_arcs = [(u, v) for u in B for v in B if A[u][v]]
    ins_arcs = [(vstar, v) for v in B if A[vstar][v]] + \
               [(u, vstar) for u in B if A[u][vstar]]
    hi = set(base_arcs) | set(ins_arcs)
    for u in range(n):
        for v in range(n):
            if A[u][v] and (u, v) not in hi:
                L.append("  \\draw[arc] (v%d) -- (v%d);" % (u, v))
    for u, v in ins_arcs:
        L.append("  \\draw[darc] (v%d) -- (v%d);" % (u, v))
    for u, v in base_arcs:
        L.append("  \\draw[barc] (v%d) -- (v%d);" % (u, v))
    for v in range(n):                       # redraw over the arc ends
        L.append("  \\node[vtx] at (v%d) {%d};" % (v, vl(v)))
    ly = cy - R - 0.42
    L.append("  \\draw[barc] (-1.95,%.3f) -- ++(0.60,0);" % ly)
    L.append("  \\node[key, anchor=west] at (-1.25,%.3f) {$T|_B$, $B=%s$};"
             % (ly, setnot(B)))
    L.append("  \\draw[darc] (-1.95,%.3f) -- ++(0.60,0);" % (ly - 0.34))
    L.append("  \\node[key, anchor=west] at (-1.25,%.3f) {arcs at $%d$};"
             % (ly - 0.34, vl(vstar)))
    return picture(L)


def panel_b(f):
    """The forced base state, and every unplaced vertex's domain in full."""
    B, k, vstar, dom0 = f["B"], f["k"], f["vstar"], f["dom0"]
    L = title(r"(b) the base state, forced", 0.0, 0.0)
    body, y = profile(f["base_state"], 0.45, -0.86, shade=set(B), ticks=True)
    L += body
    L.append("  \\node[key, anchor=west] at (2.10,%.3f) {the only one};"
             % ((y - 0.86) / 2 - 0.10))
    assert len(P.base_states(f["A"], B, k, f["regime"])) == 1, \
        "panel (b) says the base state is the only one, and it is not"
    y -= 0.54
    L.append("  \\node[key, anchor=west] at (0,%.3f) {options, as slot "
             "triples:};" % y)
    y -= 0.42
    for v in f["unplaced"]:
        body, y = domain_block(v, dom0[v], 0, y, 6, len(dom0[v]),
                               highlight=(v == vstar),
                               note=("fewest, so $v^{*}=%d$" % vl(vstar))
                                    if v == vstar else None)
        L += body
        y -= ROWH + 0.14
    return picture(L)


def panel_c(f):
    """The two ways an insertion gets rejected."""
    vstar, B = f["vstar"], f["B"]
    u, v = f["unanimous"]
    L = title(r"(c) two rejected insertions of $%d$" % vl(vstar), 0.0, 0.0)
    y = -0.30
    for q, orders, tag in ((f["q_bad"], f["ord_bad"],
                            r"breaks Lemma 2.1: no voter can still lead with "
                            r"$(%s)$ or $(%s)$"
                            % (",".join(str(vl(z)) for z in f["reps"][0]),
                               ",".join(str(vl(z)) for z in f["reps"][1]))),
                           (f["q_empty"], f["ord_empty"],
                            r"$D(%d\mid B\cup\{%d\})=\varnothing$; and it makes "
                            r"$%d\to%d$ unanimous"
                            % (vl(f["empty_at"]), vl(vstar), vl(u), vl(v)))):
        L.append("  \\node[key, anchor=west] at (0,%.3f) {put $%d$ at %s:};"
                 % (y - 0.14, vl(vstar), tt(q)))
        body, y2 = profile(orders, 0.50, y - 0.40, shade=set(B), boxed={vstar})
        L += body
        mid = (y - 0.40 + y2) / 2
        L += cross(2.55, mid)
        L.append("  \\node[key, anchor=west, text width=3.45cm] at (2.85,%.3f) {%s};"
                 % (mid, tag))
        y = min(y2, mid - 0.55) - 0.50
    return picture(L)


def panel_d(f):
    """The surviving insertion, and everyone else's options before and after."""
    vstar, B = f["vstar"], f["B"]
    L = title(r"(d) an insertion of $%d$ that survives" % vl(vstar), 0.0, 0.0)
    L.append("  \\node[key, anchor=west] at (0,-0.44) {put $%d$ at "
             "\\textcolor{okgreen}{%s}:};" % (vl(vstar), tt(f["q_good"])))
    body, y = profile(f["ord_good"], 0.50, -0.70, shade=set(B), boxed={vstar})
    L += body
    mid = (-0.70 + y) / 2
    L += tick(2.55, mid)
    L.append("  \\node[key, anchor=west, text width=3.45cm] at (2.85,%.3f) "
             "{$\\pi_1$ still leads with $(%s)$, and nothing has run out of room};"
             % (mid, ",".join(str(vl(z)) for z in f["reps"][0])))
    y = min(y, mid - 0.50) - 0.58
    L.append("  \\node[key, anchor=west] at (0,%.3f) {what that leaves of (b)'s "
             "options:};" % y)
    y -= 0.42
    for v in f["unplaced"]:
        if v == vstar:
            continue
        before, after = f["dom0"][v], f["after"][v]
        body, y = domain_block(v, after, 0, y, 5, len(after))
        L += body
        L.append("  \\node[keygood, anchor=west] at (%.3f,%.3f) {was $%d$};"
                 % (LX + 1.65, y, len(before)))
        y -= ROWH + 0.14
    return picture(L)


def panel_e(f):
    """REFINE: lift each parent tuple, then filter by the one new arc."""
    CASE = {"keep": r"$=$", "shift": r"$+1$",
            "split": r"\textcolor{okgreen}{\textbf{split}}"}
    grouped = {}
    for a in f["arrows"]:
        grouped.setdefault(tuple(a["src"]), []).append(a)
    q = f["q_good"]
    L = title(r"(e) refining $D(%d)$" % vl(f["wdet"]), 0.0, 0.0)
    L.append("  \\node[key, anchor=west] at (0,-0.40) {past "
             "\\textcolor{okgreen}{%s}:};" % tt(q))
    L += ["  \\node[hdr, anchor=west] at (0,-0.86) {tuple};",
          "  \\node[hdr, anchor=west] at (0.86,-0.86) {per voter};",
          "  \\node[hdr, anchor=west] at (3.40,-0.86) {lift};",
          "  \\node[hdr, anchor=west] at (4.24,-0.86) {$c_{%d}(%d)$};"
          % (vl(f["wdet"]), vl(f["vstar"]))]
    y = -1.36
    for src, lifts in grouped.items():
        L.append("  \\node[tup, anchor=west] at (0,%.3f) {%s};"
                 % (y, tt_split(src, q)))
        L.append("  \\node[key, anchor=west] at (0.86,%.3f) {%s};"
                 % (y, ", ".join(CASE[c] for c in lifts[0]["cases"])))
        for j, a in enumerate(lifts):
            ty = y - j * ROWH
            L.append("  \\draw[lift] (2.72,%.3f) -- (3.30,%.3f);" % (y, ty))
            L.append("  \\node[%s, anchor=west] at (3.40,%.3f) {%s};"
                     % ("tup" if a["kept"] else "tupdead", ty, tt(a["dst"])))
            L.append("  \\node[%s, anchor=west] at (4.24,%.3f) {$%d$};"
                     % ("key" if a["kept"] else "keydead", ty, a["support"]))
            L += (tick(4.78, ty) if a["kept"] else cross(4.78, ty))
        y -= ROWH * len(lifts) + 0.10
    return picture(L)


def panel_f(f):
    """The completed profile, labelled by the automorphism that generates it."""
    n, k = f["n"], f["k"]
    names = ["$\\pi$"] + ["$g^{%d}\\pi$" % i if i > 1 else "$g\\pi$"
                          for i in range(1, k)]
    L = title(r"(f) the completed profile", 0.0, 0.0)
    px = 0.78                                   # room for the widest row label
    body, y = profile(f["witness"], px, -0.34, shade=set(f["B"]), names=names)
    L += body
    lx = px - 0.70                              # the labels' own left edge
    L.append("  \\node[key, anchor=west] at (%.3f,%.3f) {$g = %s$, of order $%d$};"
             % (lx, y - 0.36, f["gcyc"], k))
    L.append("  \\node[key, anchor=west] at (%.3f,%.3f) {every arc at support $%d$};"
             % (lx, y - 0.68, (k + 1) // 2))
    return picture(L)


# --------------------------------------------------------------------------
# the facts, all derived and checked


def facts_from(trace):
    A, k, B = trace["arcs"], trace["k"], trace["base"]
    n = len(A)
    f = {"A": A, "k": k, "B": B, "n": n, "regime": trace["regime"],
         "reps": [tuple(r) for r in trace["reps"]]}

    root = next(r for r in trace["trace"] if r["kind"] == "node" and not r["path"])
    f["base_state"] = [list(o) for o in root["orders"]]
    f["vstar"] = root["vstar"]
    f["dom0"] = {int(v): [tuple(p) for p in d] for v, d in root["dom"].items()}
    f["keys"] = {int(v): kk for v, kk in root["keys"].items()}
    kids = {tuple(c["slot"]): c for c in root["children"]}

    assert len(P.base_states(A, B, k, f["regime"])) == 1, \
        "panel (b) says the base state is forced, and it is not"
    assert f["vstar"] == min(f["dom0"], key=lambda v: (len(f["dom0"][v]), v)), \
        "panel (b) marks the MRV choice, and it is not the minimum"

    pruned = [s for s, c in kids.items() if c["status"] == "anchor"]
    empties = [s for s, c in kids.items() if c["status"] == "empty"]
    alive = [s for s, c in kids.items() if c["status"] == "descend"]
    assert len(pruned) == 1 and len(empties) == 1, \
        "panel (c) shows one prune of each kind; the trace has %d and %d" \
        % (len(pruned), len(empties))
    f["q_bad"], f["q_empty"] = pruned[0], empties[0]

    f["witness"] = [list(o) for o in trace["witnesses"][0]]
    wpath = next(r["path"] for r in trace["trace"] if r["kind"] == "witness")
    f["q_good"] = tuple(wpath[0][1])
    assert f["q_good"] in alive, "the witness path does not start at a live child"

    bs = [tuple(o) for o in f["base_state"]]
    for tag, q in (("bad", f["q_bad"]), ("empty", f["q_empty"]), ("good", f["q_good"])):
        f["ord_" + tag] = [list(o) for o in P.insert(bs, f["vstar"], q)]

    f["after"] = {int(v): [tuple(p) for p in d]
                  for v, d in kids[f["q_good"]]["dom"].items()}
    f["empty_at"] = kids[f["q_empty"]]["empty_at"]
    f["unplaced"] = sorted(f["dom0"])

    # the tuple only the unrestricted margin admits, and the arc it makes unanimous
    unit = set(P.domain_fresh(A, bs, set(B), f["vstar"], k, "unit"))
    assert f["q_empty"] not in unit, \
        "panel (c) calls the empty-domain tuple margin-specific, and it is not"
    orders = [tuple(o) for o in f["ord_empty"]]
    unan = [(u, v) for u, v in itertools.permutations(sorted(set(B) | {f["vstar"]}), 2)
            if A[u][v] and P.support(orders, u, v) == k]
    assert len(unan) == 1, "expected one unanimous arc, found %d" % len(unan)
    f["unanimous"] = unan[0]
    f["tri"] = P.triangles_through(A, *f["unanimous"])

    # panel (e): the shortest lift diagram that still shows all three cases
    arrows = kids[f["q_good"]]["arrows"]
    cand = [int(w) for w in arrows
            if {c for a in arrows[w] for c in a["cases"]} == {"keep", "shift", "split"}]
    assert cand, "no unplaced vertex exhibits all three REFINE cases here"
    f["wdet"] = min(cand, key=lambda w: len(arrows[str(w)]))
    f["arrows"] = arrows[str(f["wdet"])]
    # panel (f): the witness is one order's orbit under an automorphism of order k
    group = P.automorphisms(A)
    f["aut"] = len(group)
    free = P.Search(A, k, f["regime"], B, reps=None, check_fresh=False)
    free.run()
    f["n_witness_free"] = len(free.witnesses)
    assert P.orbit_count(free.witnesses, group) == 1, \
        "panel (f) claims a single orbit, and there is more than one"
    g, seed = P.affine_generator(A, group, [tuple(o) for o in f["witness"]], k)
    assert g is not None, "panel (f) claims the witness is one order's orbit"
    f["gdesc"] = P.describe_affine(g, n)      # the caption quotes the affine form
    f["gcyc"] = cyc(g, n)                     # the panel shows it on the labels
    cur, rows = list(seed), []
    for _ in range(k):
        rows.append(list(cur))
        cur = [g[x] for x in cur]
    assert rows == f["witness"], \
        "panel (f) labels the rows pi, g pi, g^2 pi, and they are not in that order"
    f["nodes_free"], f["nodes_anch"] = free.nodes, trace["nodes"]
    return f


PREAMBLE = [
    r"\documentclass[varwidth=%.1fcm, border=2pt]{standalone}" % CANVAS,
    r"\usepackage{tikz}",
    r"\usepackage{amsmath,amssymb}",
    r"\usetikzlibrary{arrows.meta,shapes.misc}",
    r"\definecolor{vertfill}{HTML}{F5A623}",
    r"\definecolor{lbltext}{HTML}{1F3B73}",
    r"\definecolor{arcgray}{HTML}{C6C6C6}",
    r"\definecolor{hired}{HTML}{B03030}",
    r"\definecolor{basefill}{HTML}{ECECEC}",
    r"\definecolor{okgreen}{HTML}{2E6B34}",
    r"\tikzset{",
    r"  vtx/.style={circle, draw=lbltext, fill=vertfill, inner sep=0pt,"
    r" minimum size=5.4mm, font=\scriptsize\bfseries, text=lbltext},",
    r"  arc/.style={-{Stealth[length=1.4mm]}, draw=arcgray, line width=0.4pt},",
    r"  barc/.style={-{Stealth[length=2.0mm]}, draw=black, line width=1.3pt},",
    r"  darc/.style={-{Stealth[length=1.8mm]}, draw=hired, line width=0.9pt,"
    r" dash pattern=on 1.7pt off 1.3pt},",
    r"  cell/.style={draw=lbltext!45, line width=0.3pt},",
    r"  cellnew/.style={draw=hired, line width=1.0pt},",
    r"  lbl/.style={font=\small, text=lbltext, inner sep=0pt},",
    r"  vname/.style={font=\small, text=lbltext, anchor=east, inner sep=0pt},",
    r"  slottick/.style={draw=lbltext!55, line width=0.3pt},",
    r"  slotnum/.style={font=\tiny, text=lbltext!75, inner sep=0pt},",
    r"  tup/.style={font=\small, inner sep=0pt, anchor=west},",
    r"  tupdead/.style={font=\small, text=black!35, inner sep=1pt,"
    r" anchor=west, strike out, draw=black!35},",
    r"  key/.style={font=\small, inner sep=0pt, align=left},",
    r"  keyhi/.style={font=\small, text=hired, inner sep=0pt},",
    r"  keygood/.style={font=\small, text=okgreen, inner sep=0pt},",
    r"  keydead/.style={font=\small, text=black!40, inner sep=0pt},",
    r"  keydim/.style={font=\small, text=black!55, inner sep=0pt},",
    r"  hdr/.style={font=\small\itshape, text=black!65, inner sep=0pt},",
    r"  ttl/.style={font=\bfseries, text=lbltext, anchor=west, inner sep=0pt},",
    r"  bad/.style={font=\small, text=hired, inner sep=0pt},",
    r"  good/.style={font=\small, text=okgreen, inner sep=0pt},",
    r"  lift/.style={-{Stealth[length=1.3mm]}, draw=black!50, line width=0.4pt},",
    r"  keybox/.style={key, draw=hired, line width=0.7pt, rounded corners=1.5pt,"
    r" inner xsep=2pt, inner ysep=1.2pt},",
    r"}",
    r"\newsavebox{\pnlA}\newsavebox{\pnlB}\newsavebox{\pnlC}",
    r"\newsavebox{\pnlD}\newsavebox{\pnlE}\newsavebox{\pnlF}",
    r"\newlength{\pnlone}\newlength{\pnltwo}\newlength{\pnlthree}",
    r"\newlength{\pnlgap}\newlength{\pnlcanvas}",
    r"\setlength{\pnlcanvas}{%.1fcm}" % CANVAS,
    # a column is as wide as the wider of the two panels standing in it
    r"\newcommand{\pnlcol}[3]{\setlength{#1}{\wd#2}%",
    r"  \ifdim\wd#3>#1\relax\setlength{#1}{\wd#3}\fi}",
    r"\begin{document}",
]


def savebox(name, lines):
    """A panel stashed in a box, so LaTeX can measure it before placing it."""
    return (["\\sbox{\\%s}{%%" % name] + lines[:-1] +
            [lines[-1] + "%", "}%"])


def build(trace, out_path):
    """Six panels in a 3 x 2 grid whose columns LaTeX measures for itself.

    Each column is as wide as the wider of its two panels and the slack is
    split evenly between the two gaps, so (b) starts exactly where (e) does and
    (c) where (f) does, whatever the panels turn out to measure.  Setting the
    gaps by hand is what kept coming unstuck: any edit to a panel moved the
    column it sits in.
    """
    f = facts_from(trace)
    L = list(PREAMBLE)
    for name, lines in (("pnlA", panel_a(f)), ("pnlB", panel_b(f)),
                        ("pnlC", panel_c(f)), ("pnlD", panel_d(f)),
                        ("pnlE", panel_e(f)), ("pnlF", panel_f(f))):
        L += savebox(name, lines)
    L += [r"\pnlcol{\pnlone}{\pnlA}{\pnlD}",
          r"\pnlcol{\pnltwo}{\pnlB}{\pnlE}",
          r"\pnlcol{\pnlthree}{\pnlC}{\pnlF}",
          r"\setlength{\pnlgap}{\pnlcanvas}",
          r"\addtolength{\pnlgap}{-\pnlone}",
          r"\addtolength{\pnlgap}{-\pnltwo}",
          r"\addtolength{\pnlgap}{-\pnlthree}",
          r"\setlength{\pnlgap}{0.5\pnlgap}",
          # overlapping panels are the one failure this layout can still have,
          # so say so loudly rather than shipping a figure that reads wrong
          r"\ifdim\pnlgap<0pt\relax\errmessage{the panels are wider than "
          r"the \the\pnlcanvas\space canvas: \the\pnlone, \the\pnltwo, "
          r"\the\pnlthree}\fi",
          r"\makebox[\pnlone][l]{\usebox{\pnlA}}\hspace{\pnlgap}%",
          r"\makebox[\pnltwo][l]{\usebox{\pnlB}}\hspace{\pnlgap}%",
          r"\usebox{\pnlC}",
          r"\par\bigskip",
          r"\makebox[\pnlone][l]{\usebox{\pnlD}}\hspace{\pnlgap}%",
          r"\makebox[\pnltwo][l]{\usebox{\pnlE}}\hspace{\pnlgap}%",
          r"\usebox{\pnlF}",
          r"\end{document}"]
    open(out_path, "w").write("\n".join(L) + "\n")
    return f


def caption_tokens(f):
    """Every quantity the caption quotes, as it must appear in the manuscript.

    The caption explains a picture that carries no prose of its own, so its
    numbers are the ones most likely to go stale.  This turns that from a silent
    wrong answer into a hard error.  The list shrank when the caption did: it
    checks what the caption SAYS, and must not force it to say more.
    """
    B, k = f["B"], f["k"]
    return {
        "the base": setnot(B),
        "slots per voter": "%d^{%d} = %d" % (len(B) + 1, k, (len(B) + 1) ** k),
        "support": "support exactly $%d$" % ((k + 1) // 2),
        "witnesses": "all $%d$ witnesses" % f["n_witness_free"],
        "|Aut|": "of order $%d$" % f["aut"],
        "generator": "x \\mapsto %s" % f["gdesc"],
    }


def check_caption(f, path):
    """Fail loudly if the manuscript's Figure 1 caption has drifted."""
    text = open(path).read()
    i = text.find(r"\caption{Algorithm 1 on")
    assert i >= 0, "no Figure 1 caption found in " + path
    cap = " ".join(text[i:text.find(r"\end{figure}", i)].split())
    bad = [name for name, tok in caption_tokens(f).items()
           if " ".join(tok.split()) not in cap]
    assert not bad, "the caption does not state, or misstates: " + ", ".join(bad)
    print("caption checks out against the trace (%d quantities)"
          % len(caption_tokens(f)))


if __name__ == "__main__":
    trace = json.load(open(sys.argv[1]))
    if sys.argv[2] == "--check":
        check_caption(facts_from(trace), sys.argv[3])
    else:
        build(trace, sys.argv[2])
        print("wrote", sys.argv[2])
