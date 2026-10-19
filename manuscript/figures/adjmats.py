"""Appendix H of the MSS manuscript: the adjacency matrices of the three 22-vertex obstructions
Delta_1 - 10, Delta_6 - 5 and Delta_28 - 5 (his call, 2026-10-17 23:50, after Ararat's remark).

Each is rebuilt from its doubly regular parent (KInduceDFS/drt23/dNNN.bits, catalogue order, file
index NNN = i - 1) by deleting the catalogue vertex, and ASSERTED equal, arc for arc, to the host the
search refuted (KInduceDFS/jz_sweep1/hosts/dNNN_mvVV.bits, VV = v - 1).  Rows and columns list the
out-neighbours of the deleted vertex first, then its in-neighbours, each in increasing catalogue
label; entry 1 means the row vertex beats the column vertex.  Also asserted: both blocks induce
regular tournaments on 11 vertices, out-neighbours beat 6 in-neighbours, in-neighbours beat 5.
Writes figures/adjmats.md (pasted into the manuscript as Appendix H)."""
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]

def load(path):
    s = ''.join(c for c in open(path).read() if c in '01')
    n = round((1 + (1 + 8 * len(s)) ** 0.5) / 2); assert n * (n - 1) // 2 == len(s)
    A = [[0] * n for _ in range(n)]; k = 0
    for i in range(n):
        for j in range(i + 1, n): A[i][j], A[j][i] = (1, 0) if s[k] == '1' else (0, 1); k += 1
    return A

out = []
for i, v in ((1, 10), (6, 5), (28, 5)):
    D = load(ROOT / f'KInduceDFS/drt23/d{i - 1:03d}.bits'); assert len(D) == 23
    keep = [u for u in range(23) if u != v - 1]
    H = load(ROOT / f'KInduceDFS/jz_sweep1/hosts/d{i - 1:03d}_mv{v - 1:02d}.bits')
    assert all(H[a][b] == D[keep[a]][keep[b]] for a in range(22) for b in range(22)), (i, v)
    P = [u for u in keep if D[v - 1][u]]; M = [u for u in keep if D[u][v - 1]]
    assert len(P) == len(M) == 11
    assert all(sum(D[x][y] for y in P) == 5 for x in P) and all(sum(D[x][y] for y in M) == 5 for x in M)
    assert all(sum(D[x][y] for y in M) == 6 for x in P) and all(sum(D[y][x] for x in P) == 5 for y in M)
    order = P + M
    lab = lambda u: u + 1
    out.append(f"**$\\Delta_{{{i}}} - {v}$.** Out-neighbours of vertex ${v}$: "
               f"${', '.join(str(lab(u)) for u in P)}$; in-neighbours: ${', '.join(str(lab(u)) for u in M)}$.\n")
    out.append("```")
    for r in order:
        row = ''.join(str(D[r][c]) if r != c else '-' for c in order)
        out.append(f"{lab(r):>3} | {row[:11]} {row[11:]}")
    out.append("```\n")
(pathlib.Path(__file__).parent / 'adjmats.md').write_text('\n'.join(out))
print('\n'.join(out))
