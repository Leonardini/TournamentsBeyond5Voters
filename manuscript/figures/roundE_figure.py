"""Draw Figure 2, the three-voter construction of Appendix E, on a worked example.

Everything in the picture is DERIVED from the tournament and then checked before
any TikZ is written: that the example is round and strongly connected, that the
out-degree blocks are intervals, that r is non-decreasing, that t_{n-1} < q, that
the keys are pairwise distinct, and -- the point of the appendix -- that every one
of the C(n,2) arcs is ranked correctly by exactly two of the three orders.  If any
of that fails the script raises rather than drawing a figure that asserts it.

The example is chosen, not general: out-degrees that are not all equal, so the
staircase has more than one step, and a repeated ceiling, so the tie-break in the
key is exercised rather than merely stated.

Usage:  python3 roundE_figure.py roundE.tex
        python3 roundE_figure.py --check ../<manuscript>.md
"""

import sys

# The example.  d[i] is the out-degree of v_i; the round rule is that the
# out-neighbours of v_i are the d[i] vertices that follow it in the cyclic order.
D = (2, 2, 2, 4, 4, 4, 3)
N = len(D)

CANVAS = 16.0                      # width of the whole figure, cm


# --------------------------------------------------------------- the tournament
def arc(i, j):
    """True iff v_i -> v_j, straight from the round rule."""
    return i != j and (j - i) % N <= D[i]


def check_tournament():
    """A round tournament, strongly connected, with the degrees we claim."""
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            assert arc(i, j) != arc(j, i), f"not a tournament at ({i},{j})"
        out = {j for j in range(N) if arc(i, j)}
        assert out == {(i + s) % N for s in range(1, D[i] + 1)}, \
            f"out-neighbourhood of v{i} is not the interval after it"
        assert len(out) == D[i]
    # local transitivity, the definition the appendix opens with, checked directly
    # rather than inferred from the construction
    for v in range(N):
        for nb in ({j for j in range(N) if arc(v, j)},
                   {j for j in range(N) if arc(j, v)}):
            for a in nb:
                for b in nb:
                    for c in nb:
                        if arc(a, b) and arc(b, c):
                            assert arc(a, c), f"N(v{v}) is not transitive"
    for fwd in (True, False):
        seen, stack = {0}, [0]
        while stack:
            u = stack.pop()
            for w in range(N):
                if (arc(u, w) if fwd else arc(w, u)) and w not in seen:
                    seen.add(w)
                    stack.append(w)
        assert len(seen) == N, "not strongly connected"


# ------------------------------------------------------------ the three orders
def derive():
    r = [i + D[i] for i in range(N)]
    assert all(r[i] <= r[i + 1] for i in range(N - 1)), "r is not non-decreasing"
    H = [i for i in range(N) if r[i] >= N]
    assert H and H == list(range(H[0], N)), "H is not a suffix"
    q = H[0]
    L = list(range(q))
    assert L, "L is empty, so the example is degenerate"
    t = {h: r[h] - N for h in H}
    assert all(t[H[a]] <= t[H[a + 1]] for a in range(len(H) - 1)), "ceilings not monotone"
    assert t[N - 1] < q, "back-targets reach into H"
    for h in H:                      # the back-targets are exactly v_0 ... v_{t_h}
        assert {l for l in L if arc(h, l)} == set(range(t[h] + 1))
    A = list(range(N))
    B = list(range(q, N)) + list(range(q))
    # key: the index for L, the ceiling plus a half for H; ties among equal
    # ceilings broken by larger index first, which decreasing-key order turns into
    # "the larger index comes first".
    key = {l: (l, 0) for l in L}
    key.update({h: (t[h] + 0.5, h) for h in H})
    assert len(set(key.values())) == N, "keys collide"
    C = sorted(range(N), key=lambda v: key[v], reverse=True)
    return r, q, L, H, t, A, B, C, key


def check_margin(A, B, C):
    """Every arc correct in exactly two of the three orders: the whole theorem."""
    pos = [{v: p for p, v in enumerate(o)} for o in (A, B, C)]
    for i in range(N):
        for j in range(i + 1, N):
            u, w = (i, j) if arc(i, j) else (j, i)
            s = sum(1 for p in pos if p[u] < p[w])
            assert s == 2, f"arc v{u} -> v{w} has support {s}, not 2"
    return True


# ------------------------------------------------------------------ the drawing
# Panel origins, and the width each panel is allowed.  Written here rather than
# sprinkled through the three functions so that a panel growing past its budget is
# a visible collision in ONE place -- the first draft ran panel (b)'s labels
# straight through panel (c).
PANEL = {"a": (1.90, 3.9), "b": (5.15, 4.6), "c": (10.35, 3.6)}


def tikz_wheel(q, x0):
    """Panel (a): the cyclic order, and two out-blocks, one of which wraps."""
    import math
    R = 1.22
    show = (1, 5)                    # one vertex of L, one of H: the wrap is the point
    assert show[0] < q <= show[1], "the highlighted pair must straddle q"
    out = [r"\begin{scope}[shift={(%.2f,0)}]" % x0]
    xy = {}
    for i in range(N):
        th = 90 - 360.0 * i / N      # clockwise, so the cyclic order reads clockwise
        xy[i] = (R * math.cos(math.radians(th)), R * math.sin(math.radians(th)))
    # NODES FIRST.  An arc drawn between bare coordinates ends at the centre of the
    # target, so the node drawn afterwards covers its arrowhead: the first draft had
    # seven arcs and no visible direction at all.  Referring to the nodes makes TikZ
    # stop each arc at the circle's boundary.
    for i in range(N):
        x, y = xy[i]
        fill = "black!12" if i >= q else "white"
        out.append(r"\node[circle,draw,inner sep=0.9pt,fill=%s,font=\tiny] (w%d) at (%.3f,%.3f) {$v_{%d}$};"
                   % (fill, i, x, y, i))
        out.append(r"\node[font=\tiny,text=black!55] at (%.3f,%.3f) {$%d$};" % (1.36 * x, 1.36 * y, D[i]))
    for k, i in enumerate(show):
        style = "thick" if k == 0 else "thick,densely dashed"
        for st in range(1, D[i] + 1):
            out.append(r"\draw[%s,->,>=stealth,black!65,shorten >=1pt] (w%d) to[bend left=10] (w%d);"
                       % (style, i, (i + st) % N))
    out.append(r"\node[font=\scriptsize] at (0,2.00) {\textbf{(a)} round, strongly connected};")
    out.append(r"\node[font=\tiny,text=black!55] at (0,-1.86) {outer number $=d_i$; two blocks shown};")
    out.append(r"\end{scope}")
    return out


def tikz_orders(q, L, H, t, A, B, x0):
    """Panel (b): the same cyclic order cut in two places, and what each cut breaks."""
    CW = 0.50
    nback = sum(t[h] + 1 for h in H)
    nfwd = len(L) * len(H) - nback
    out = [r"\begin{scope}[shift={(%.2f,0)}]" % x0]
    rows = (("A", A, 1.20, nback, "back arcs $H\\to L$", 0.72),
            ("B", B, -0.30, nfwd, "forward arcs $L\\to H$", -1.32))
    for name, order, y, cnt, what, ytext in rows:
        out.append(r"\node[font=\scriptsize] at (-0.62,%.2f) {$%s$};" % (y, name))
        for p, v in enumerate(order):
            fill = "black!12" if v >= q else "white"
            out.append(r"\node[draw,rounded corners=1pt,minimum width=%.2fcm,minimum height=0.32cm,"
                       r"inner sep=0pt,fill=%s,font=\tiny] (%s%d) at (%.3f,%.2f) {$v_{%d}$};"
                       % (CW, fill, name, p, p * CW, y, v))
        out.append(r"\node[font=\tiny,anchor=west] at (-0.62,%.2f) {fails its $%d$ %s};"
                   % (ytext, cnt, what))
    hmax = max(H)
    out.append(r"\draw[->,>=stealth,black!70] (A%d) to[bend right=34] (A%d);"
               % (A.index(hmax), A.index(t[hmax])))
    out.append(r"\node[font=\tiny,anchor=south] at (%.3f,%.2f) {$v_{%d}\!\to\!v_{%d}$};"
               % ((A.index(hmax) + A.index(t[hmax])) * CW / 2, 1.50, hmax, t[hmax]))
    # a forward arc L -> H really does exist: the back-targets of every h are a
    # proper subset of L, since t_{n-1} < q, so some L-H pair runs the other way.
    fwd = [(l, h) for l in L for h in H if arc(l, h)]
    assert fwd, "no forward L -> H arc, so the example cannot illustrate panel (b)"
    lmin, hfwd = fwd[0]
    out.append(r"\draw[->,>=stealth,black!70] (B%d) to[bend left=34] (B%d);"
               % (B.index(lmin), B.index(hfwd)))
    out.append(r"\node[font=\tiny,anchor=north] at (%.3f,%.2f) {$v_{%d}\!\to\!v_{%d}$};"
               % ((B.index(lmin) + B.index(hfwd)) * CW / 2, -0.80, lmin, hfwd))
    out.append(r"\node[font=\scriptsize,anchor=west] at (-0.62,2.00) "
               r"{\textbf{(b)} cut at $v_0$, then at $v_{q}$, $q=%d$};" % q)
    out.append(r"\node[font=\tiny,text=black!55,anchor=west] at (-0.62,-1.86) "
               r"{shaded $=H$};")
    out.append(r"\end{scope}")
    return out


def tikz_keys(L, H, t, C, x0):
    """Panel (c): the keys, and C read off them from the right."""
    UX = 1.05                        # cm per unit of key
    out = [r"\begin{scope}[shift={(%.2f,0)}]" % x0]
    right = (max(t.values()) + 0.5) * UX + 0.45
    out.append(r"\draw[black!45] (-0.35,0) -- (%.2f,0);" % right)
    for l in L:
        out.append(r"\draw[black!45] (%.3f,-0.07) -- (%.3f,0.07);" % (l * UX, l * UX))
        out.append(r"\node[font=\tiny,text=black!55,anchor=north] at (%.3f,-0.09) {$%d$};" % (l * UX, l))
        out.append(r"\node[draw,circle,inner sep=0.9pt,fill=white,font=\tiny] at (%.3f,0.40) {$v_{%d}$};"
                   % (l * UX, l))
    lanes = {}
    for h in sorted(H, reverse=True):   # larger index drawn HIGHER, because that is
                                        # the one C lists first among equal ceilings
        lane = lanes.get(t[h], 0)
        lanes[t[h]] = lane + 1
        y = -0.58 - 0.42 * lane
        out.append(r"\draw[black!30,densely dotted] (%.3f,-0.07) -- (%.3f,%.2f);"
                   % ((t[h] + 0.5) * UX, (t[h] + 0.5) * UX, y + 0.16))
        out.append(r"\node[draw,circle,inner sep=0.9pt,fill=black!12,font=\tiny] at (%.3f,%.2f) {$v_{%d}$};"
                   % ((t[h] + 0.5) * UX, y, h))
    out.append(r"\draw[->,>=stealth,black!70] (%.2f,1.30) -- (-0.20,1.30);" % right)
    out.append(r"\node[font=\tiny,text=black!55,anchor=south] at (%.2f,1.36) {decreasing key};" % (right / 2))
    out.append(r"\node[font=\tiny,anchor=west] at (-0.35,0.86) {$\mathrm{key}(v_l)=l$};")
    out.append(r"\node[font=\tiny,anchor=west] at (-0.35,-1.45) "
               r"{$\mathrm{key}(v_h)=t_h+\tfrac12$; equal $t_h$ stack, larger $h$ first};")
    out.append(r"\node[font=\scriptsize,anchor=west] at (-0.35,2.00) {\textbf{(c)} the keys give $C$};")
    out.append(r"\node[font=\tiny,anchor=west] at (-0.35,-1.86) {$C=(%s)$};"
               % ",".join("v_{%d}" % v for v in C))
    out.append(r"\end{scope}")
    return out


def build(path):
    check_tournament()
    r, q, L, H, t, A, B, C, key = derive()
    check_margin(A, B, C)
    body = (tikz_wheel(q, PANEL["a"][0])
            + tikz_orders(q, L, H, t, A, B, PANEL["b"][0])
            + tikz_keys(L, H, t, C, PANEL["c"][0]))
    doc = ([r"\documentclass[varwidth=%.1fcm, border=2pt]{standalone}" % CANVAS,
            r"\usepackage{amsmath,amssymb}",
            r"\usepackage{tikz}",
            r"\usetikzlibrary{arrows.meta}",
            r"\begin{document}",
            r"\begin{tikzpicture}[x=1cm,y=1cm]"]
           + body
           + [r"\end{tikzpicture}", r"\end{document}"])
    with open(path, "w") as fh:
        fh.write("\n".join(doc) + "\n")
    return r, q, L, H, t, A, B, C


def check_caption(md):
    """Fail unless the manuscript's caption quotes what the figure actually shows."""
    check_tournament()
    r, q, L, H, t, A, B, C, key = derive()
    check_margin(A, B, C)
    text = open(md).read()
    want = {"the out-degree sequence": "(%s)" % ", ".join(str(x) for x in D),
            "the value of q": "q = %d" % q,
            "the third order": "(%s)" % ", ".join("v_{%d}" % v for v in C)}
    # v_{6} and v_6 are the same vertex; the caption may write either, so compare
    # on a form that cannot depend on which.
    def norm(x):
        return x.replace(" ", "").replace("{", "").replace("}", "")
    bad = [k for k, v in want.items() if norm(v) not in norm(text)]
    for k, v in want.items():
        print(("  ok   " if k not in bad else "  MISS ") + f"{k}: {v}")
    return not bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(0 if check_caption(sys.argv[sys.argv.index("--check") + 1]) else 1)
    out = sys.argv[1] if len(sys.argv) > 1 else "roundE.tex"
    r, q, L, H, t, A, B, C = build(out)
    print(f"d = {D}")
    print(f"r = {r}   q = {q}   L = {sorted(L)}   H = {sorted(H)}")
    print("t = " + ", ".join(f"t_{h}={t[h]}" for h in sorted(H)))
    print("A = " + " ".join(f"v{v}" for v in A))
    print("B = " + " ".join(f"v{v}" for v in B))
    print("C = " + " ".join(f"v{v}" for v in C))
    print(f"every one of the {N*(N-1)//2} arcs has support exactly 2")
    print(f"wrote {out}")
