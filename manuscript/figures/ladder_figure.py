"""Draw the figure of Delta_1 - 10 (code name d000_mv09): two copies of P_11 joined
by a ladder.

Everything the caption asserts is CHECKED against the host's bit string before any
TikZ is written: in the labels x_0..x_10, y_0..y_10 (indices mod 11),
  x_i -> x_j  iff  j - i in QR,          y_i -> y_j  iff  j - i in NQR,
  x_i -> y_j  iff  j - i in NQR,         y_j -> x_i  otherwise (j - i in QR or 0),
so every rung y_i -> x_i points from Y to X; and i -> i + 1 and i -> a i (a in QR),
applied to both sides, are automorphisms, generating a group of order 55, which is
all of Aut (checked by counting automorphisms with networkx).

The labelling: x_i = t^(-i)(0) and y_i = t^(-i)(19) in the host's 0-based vertex
names, where t is an order-11 automorphism; the script finds t itself.

Usage:  python3 ladder_figure.py ladder_d000.tex && pdflatex ladder_d000.tex
"""
import pathlib, sys
import networkx as nx
from networkx.algorithms.isomorphism import DiGraphMatcher

ROOT = pathlib.Path(__file__).resolve().parents[1]
P = 11
QR = {(a * a) % P for a in range(1, P)}
NQR = set(range(1, P)) - QR

# ------------------------------------------------------------------ the host
s = ''.join(c for c in open(ROOT / 'KInduceDFS/jz_sweep1/hosts/d000_mv09.bits').read() if c in '01')
n = 22
assert len(s) == n * (n - 1) // 2
A = [[0] * n for _ in range(n)]; k = 0
for i in range(n):
    for j in range(i + 1, n):
        A[i][j], A[j][i] = (1, 0) if s[k] == '1' else (0, 1); k += 1
G = nx.DiGraph((i, j) for i in range(n) for j in range(n) if A[i][j])
auts = [tuple(m[i] for i in range(n)) for m in DiGraphMatcher(G, G).isomorphisms_iter()]
assert len(auts) == 5 * P

ident = tuple(range(n))
def order(h):
    q, c = h, 1
    while q != ident: q, c = tuple(h[x] for x in q), c + 1
    return c
t = next(h for h in auts if order(h) == P)
X0, Y0 = 0, 19
xs, ys = [X0], [Y0]
for _ in range(P - 1): xs.append(t[xs[-1]]); ys.append(t[ys[-1]])
x = [xs[(-i) % P] for i in range(P)]           # x_i = t^(-i)(X0)
y = [ys[(-i) % P] for i in range(P)]
assert sorted(x + y) == list(range(n))

# ------------------------------------------------------------------ the claims
def arc(u, v): return A[u][v] == 1
for i in range(P):
    for j in range(P):
        d = (j - i) % P
        if i != j:
            assert arc(x[i], x[j]) == (d in QR), ('X', i, j)
            assert arc(y[i], y[j]) == (d in NQR), ('Y', i, j)
        assert arc(x[i], y[j]) == (d in NQR), ('XY', i, j)
assert all(arc(y[i], x[i]) for i in range(P)), 'rungs'
lab = {**{x[i]: ('x', i) for i in range(P)}, **{y[i]: ('y', i) for i in range(P)}}
inv = {v: u for u, v in lab.items()}
def is_aut(f):  # f acts on indices, both sides alike
    m = {inv[(side, i)]: inv[(side, f(i))] for side in 'xy' for i in range(P)}
    return all(arc(m[u], m[v]) == arc(u, v) for u in range(n) for v in range(n) if u != v)
assert is_aut(lambda i: (i + 1) % P)
assert all(is_aut(lambda i, a=a: (a * i) % P) for a in QR)
print(f"checked: 231 arcs follow the ladder rules; |Aut| = {len(auts)} = 11 x 5", file=sys.stderr)

# ------------------------------------------------------------------ the picture
GAP, DY, R = 4.2, 0.42, 0.11             # column gap, vertical step, vertex radius (cm)
DRAWN = [0, 1, 2, P - 3, P - 2, P - 1]   # rungs sketched, three at each end; the rest are dots
top = (P - 1) * DY / 2
def ypos(i): return top - i * DY
out = [r"\documentclass[border=2pt]{standalone}", r"\usepackage{amsmath,amssymb}",
       r"\usepackage{tikz}", r"\usetikzlibrary{arrows.meta}", r"\begin{document}",
       r"\begin{tikzpicture}[x=1cm,y=1cm]"]
bulge = top + 0.2                        # rails overhang the end vertices; semicircles join the rail ends
for side, cx, sgn, name in (('x', 0.0, -1, 'X'), ('y', GAP, 1, 'Y')):
    out.append(rf"\draw[black!65] ({cx},{bulge:.3f}) -- ({cx},{-bulge:.3f});")
    # semicircle outward, joining the rail's two ends
    start, end = 90, (270 if sgn < 0 else -90)
    out.append(rf"\draw[black!45] ({cx},{bulge:.3f}) arc[start angle={start},end angle={end},radius={bulge:.3f}];")
    out.append(rf"\node[font=\small] at ({cx + sgn * bulge * 0.62:.3f},0) {{$P_{{11}}$}};")
    out.append(rf"\node[font=\small] at ({cx},{bulge + 0.3:.3f}) {{${name}$}};")
    for i in range(P):
        out.append(rf"\fill[black] ({cx},{ypos(i):.3f}) circle[radius={R / 2:.3f}];")
        out.append(rf"\node[font=\scriptsize,anchor={'east' if sgn < 0 else 'west'}] at ({cx + sgn * 0.08:.3f},{ypos(i):.3f}) {{${side}_{{{i}}}$}};")
for i in DRAWN:
    out.append(rf"\draw[thick,-{{Stealth[length=2.2mm]}},black!75,shorten <=3pt,shorten >=3pt] ({GAP},{ypos(i):.3f}) -- (0,{ypos(i):.3f});")
mid = (ypos(2) + ypos(P - 3)) / 2       # halfway between the inner drawn rungs, drawn as three dots
for d in (-1, 0, 1):                     # so that they sit exactly on the centre line, unlike a \vdots glyph
    out.append(rf"\fill[black] ({GAP / 2},{mid + d * DY / 2:.3f}) circle[radius=0.035];")
out += [r"\end{tikzpicture}", r"\end{document}"]
pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'ladder_d000.tex').write_text('\n'.join(out) + '\n')
