# /// script
# requires-python = ">=3.11"
# dependencies = ["marimo", "matplotlib"]
# ///
"""Why Paley(23) is not the majority of five voters — a tutorial.

Self-contained: every witness and every tournament it needs is embedded below,
so nothing here reads a file from the repository and nothing reruns a search
that took hours. Open it in Molab or run `marimo edit paley23_five_voters.py`.
"""

import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Paley(23) is not the majority of five voters

    **The question.** Five people each rank $n$ candidates. For every pair,
    the candidate that more of them put first "wins" that pair. The wins form
    a *tournament* — a complete graph with every edge given a direction.

    Which tournaments can arise this way? Almost all cannot, by a counting
    argument, but that argument names no particular one. So:

    > $N(5)$ = the smallest $n$ such that **some** tournament on $n$
    > vertices is not the majority of any five rankings.

    Before the paper reproduced here, $N(5)$ was pinned only to
    $12 \le N(5) \le 38$. The paper narrows it to $13 \le N(5) \le 23$.
    This notebook explains the upper half — the part reproduced — and lets
    you re-run its verification steps in milliseconds.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The result, first

    ![the bound](https://raw.githubusercontent.com/Leonardini/TournamentsBeyond5Voters/main/reports/beyond-five-voters/images/fig1_bound.png)

    The upper bound moved from 38 to 23 because one specific 23-vertex
    tournament — the **Paley tournament** $P_{23}$ — was shown to be beyond
    five voters. Bachmeier et al. had tried exactly this instance with a SAT
    solver and reported it unresolved after six cumulative weeks.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What a Paley tournament is

    For a prime $q \equiv 3 \pmod 4$, put an arc $i \to j$ exactly when
    $j - i$ is a nonzero square mod $q$. Squares are closed under negation
    only when $q \equiv 1$, so for $q \equiv 3$ exactly one of $i \to j$ and
    $j \to i$ holds — which is what makes it a tournament at all.
    """)
    return


@app.cell
def _():
    def paley(q):
        """Arc set of the Paley tournament on q vertices: (i,j) in A iff i -> j."""
        qr = {(x * x) % q for x in range(1, q)}
        return {(i, j) for i in range(q) for j in range(q)
                if i != j and (j - i) % q in qr}

    def out_degrees(q):
        A = paley(q)
        return sorted({sum(1 for j in range(q) if (i, j) in A) for i in range(q)})

    # doubly regular: every vertex has the same out-degree, (q-1)/2
    {q: (out_degrees(q), (q - 1) // 2) for q in (7, 11, 19, 23, 31, 43)}
    return (paley,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The one lemma you can check by hand

    **3-cycle bound.** If $u \to v \to w \to u$ is a directed triangle, then
    across any $k$ rankings

    $$c(u\!\to\! v) + c(v\!\to\! w) + c(w\!\to\! u) \;\le\; 2k,$$

    because no single ranking can agree with all three arcs of a cycle.
    With $k = 5$ every arc needs support $\ge 3$, so no arc lying in a
    triangle can have support 5. That is why "margin $\le 3$" and plain
    majority coincide on these tournaments — a fact the reproduction leans
    on, and which you can confirm below.
    """)
    return


@app.cell
def _(paley):
    def min_triangles_per_arc(q):
        A = paley(q)
        return min(sum(1 for w in range(q) if (v, w) in A and (w, u) in A)
                   for (u, v) in A)

    # every arc sits in at least (q-3)/4 triangles, so none can be unanimous
    {q: (min_triangles_per_arc(q), (q - 3) // 4) for q in (19, 23, 31, 43)}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Evidence 1 — the witness for $P_{19}$, re-checked here

    $P_{19}$ **is** five-voter inducible. The search reproduced that in 164
    seconds; the five ballots it returned are embedded below. Checking a
    witness is trivial compared with finding one, so the cell recomputes
    every arc's support from scratch — this is a genuine verification, not a
    replay of a logged number.
    """)
    return


@app.cell
def _():
    # the witness the reproduction's search returned for P19 (margin <= 3)
    P19_WITNESS = [
        [18, 0, 16, 1, 6, 12, 4, 10, 2, 11, 3, 8, 17, 9, 15, 7, 13, 5, 14],
        [7, 8, 14, 12, 4, 13, 0, 11, 9, 1, 18, 5, 10, 6, 15, 16, 17, 2, 3],
        [16, 13, 17, 14, 2, 18, 6, 15, 3, 10, 0, 4, 1, 7, 5, 11, 8, 12, 9],
        [8, 15, 5, 2, 9, 6, 13, 11, 3, 1, 12, 10, 0, 7, 17, 18, 16, 14, 4],
        [17, 5, 3, 9, 7, 4, 10, 14, 11, 15, 12, 16, 1, 2, 18, 8, 0, 6, 13],
    ]

    def supports(ballots, arcs):
        """For each arc, how many ballots rank its tail above its head."""
        pos = [{v: p for p, v in enumerate(b)} for b in ballots]
        return {(u, v): sum(1 for p in pos if p[u] < p[v]) for (u, v) in arcs}

    return P19_WITNESS, supports


@app.cell
def _(P19_WITNESS, paley, supports):
    _sup = supports(P19_WITNESS, paley(19))
    _hist = {s: sum(1 for c in _sup.values() if c == s) for s in (0, 1, 2, 3, 4, 5)}
    _verdict = ("GENUINE WITNESS" if min(_sup.values()) >= 3
                else "not a witness — some arc is not carried")
    {"support histogram": {k: v for k, v in _hist.items() if v},
     "arcs": len(_sup), "verdict": _verdict}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Every arc lands on 3–2 or 4–1, none on 5–0 — exactly what the 3-cycle
    bound forces. $P_{19}$ is inducible, but **not** if you insist every arc
    be carried 3–2; that refutation needed 2,200 subproblems and is
    reproduced separately. So unit margin is strictly weaker than plain
    majority, which is one of the paper's contributions.

    ## Evidence 2 — the negative control

    This is the check that would catch a broken verifier. Reversing any one
    arc of $P_{23}$ makes it inducible (so $P_{23}$ is *arc-critical*). The
    witness below was found for $P_{23}$ with arc $(0,1)$ reversed. It must

    - carry **all 253** arcs of the reversed tournament, and
    - fail against the **unreversed** $P_{23}$ on **exactly one** arc.

    A verifier that said "valid" to both would be broken, and one that said
    "invalid" to both would be useless.
    """)
    return


@app.cell
def _():
    # the witness for P23 with arc (0,1) reversed, at base state 1161
    P23ARC_WITNESS = [
        [0, 18, 4, 13, 22, 8, 3, 17, 12, 7, 21, 16, 2, 11, 20, 6, 1, 15, 10, 19, 5, 14, 9],
        [0, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 1, 19, 2, 20, 3, 21, 4, 22, 5],
        [16, 20, 1, 5, 9, 13, 17, 21, 2, 6, 10, 14, 18, 22, 3, 7, 11, 15, 19, 0, 4, 8, 12],
        [19, 12, 22, 2, 5, 15, 18, 8, 11, 21, 1, 14, 4, 7, 17, 10, 20, 13, 0, 3, 16, 6, 9],
        [3, 19, 14, 9, 4, 20, 15, 10, 5, 21, 16, 11, 6, 22, 1, 17, 12, 7, 0, 2, 18, 13, 8],
    ]
    return (P23ARC_WITNESS,)


@app.cell
def _(P23ARC_WITNESS, paley, supports):
    _p23 = paley(23)
    _rev = {(1, 0) if a == (0, 1) else a for a in _p23}   # flip the single arc

    def _report(arcs, label):
        s = supports(P23ARC_WITNESS, arcs)
        bad = [a for a, c in s.items() if c < 3]
        return {"host": label, "arcs": len(s), "carried": len(s) - len(bad),
                "failing arcs": bad}

    [_report(_rev, "P23 with (0,1) reversed — must pass"),
     _report(_p23, "unreversed P23 — must fail on exactly (0,1)")]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Why $P_{23}$ was the hard one

    The previous paper refuted $P_{43}$ with no search at all, using a
    quantity called the *slack*. Small slack pins the five voters close to
    the best possible ranking, and at $q = 43$ that left only ~1.8 million
    cases. But slack is not monotone in $q$:

    | $q$ | 7 | 11 | 19 | **23** | 31 | 43 |
    |---|---|---|---|---|---|---|
    | slack$_5$ | 7 | 10 | 22 | **46** | 30 | 6 |

    $q = 23$ is a local *maximum*, so that argument is useless exactly where
    the bound would improve most. What replaced it is a bespoke depth-first
    search: fix how the five voters rank a 5-vertex **base** (8,031 ways up
    to relabelling), then insert the remaining vertices one at a time,
    always choosing the vertex with the fewest options left and refining the
    option sets incrementally instead of recomputing them.

    ![where the cost lives](https://raw.githubusercontent.com/Leonardini/TournamentsBeyond5Voters/main/reports/beyond-five-voters/images/fig2_cost_concentration.png)

    A refutation is only as good as its coverage, which is why the
    reproduction audits the **exact index cover** of the 8,031 subproblems
    rather than counting them: a subproblem that was cut off leaves no
    marker, so a gap cannot be cancelled by a duplicate.
    """)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Optional: run the algorithm yourself

    Below is Algorithm 1 of the paper in forty lines — the same shape as the C
    engine that settled $P_{23}$, minus the incremental domain refinement that
    makes it fast. It shares no code with that engine, so a witness it returns
    is an independent confirmation rather than a replay.

    Small cases only: a slot tuple costs $(|S|+1)^k$, so $q = 11$ at $k = 5$ is
    about the ceiling for Python in a browser.
    """)
    return


@app.cell
def _(mo):
    q_pick = mo.ui.dropdown({"7": 7, "11": 11}, value="7", label="Paley(q)")
    k_pick = mo.ui.dropdown({"3": 3, "5": 5}, value="3", label="voters k")
    mo.hstack([q_pick, k_pick], justify="start")
    return k_pick, q_pick


@app.cell
def _(paley):
    import itertools
    import time

    def search(q, k, node_cap=400_000):
        """Insert one vertex at a time into k partial orders, always taking the
        vertex with the fewest legal insertions left (the MRV rule), and
        backtrack as soon as some unplaced vertex has none."""
        A = paley(q)
        need = (k + 1) // 2
        nodes = [0]

        def domain(v, orders, placed):
            """Slot tuples for v that get every arc between v and placed right."""
            out = []
            for slots in itertools.product(*(range(len(o) + 1) for o in orders)):
                for u in placed:
                    c = sum(1 for i, o in enumerate(orders) if slots[i] <= o.index(u))
                    tail = v if (v, u) in A else u
                    if (c if tail == v else k - c) < need:
                        break
                else:
                    out.append(slots)
            return out

        def dfs(orders, placed):
            nodes[0] += 1
            if nodes[0] > node_cap:
                raise RuntimeError("node cap")
            if len(placed) == q:
                return [list(o) for o in orders]
            doms = {v: domain(v, orders, placed) for v in range(q) if v not in placed}
            if any(not d for d in doms.values()):
                return None
            v = min(doms, key=lambda x: len(doms[x]))
            for slots in doms[v]:
                nxt = [o[:i] + [v] + o[i:] for o, i in zip(orders, slots)]
                if (got := dfs(nxt, placed | {v})):
                    return got
            return None

        t0 = time.time()
        try:
            w = dfs([[0] for _ in range(k)], {0})
        except RuntimeError:
            return None, nodes[0], time.time() - t0, "hit the node cap"
        return w, nodes[0], time.time() - t0, "ran to completion"
    return (search,)


@app.cell
def _(k_pick, paley, q_pick, search, supports):
    _w, _n, _t, _note = search(q_pick.value, k_pick.value)
    if _w:
        _s = supports(_w, paley(q_pick.value))
        _lo, _hi = min(_s.values()), max(_s.values())
        _out = {"verdict": "inducible — witness below", "nodes": _n,
                "seconds": round(_t, 2), "support range": [_lo, _hi],
                "margin": "unit — every arc at the narrowest majority"
                          if _hi == (k_pick.value + 1) // 2 else "mixed",
                "witness": _w}
    else:
        _out = {"verdict": f"no witness ({_note})", "nodes": _n,
                "seconds": round(_t, 2)}
    _out
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What was reproduced, and what was not

    | | |
    |---|---|
    | $P_{23}$ is not 5-inducible, so $N(5) \le 23$ | reproduced, complete over all 8,031 subproblems |
    | $P_{19}$ inducible but not at unit margin | reproduced, both halves |
    | $P_{23}$ arc-critical | reproduced; the witness found is byte-identical to the published one |
    | ROOT (CNF) of the certified refutations | rebuilt from scratch and compared |
    | $13 \le N(5)$ (the order-12 census) | not attempted — ~10,000 core-hours, cluster scale |
    | $P_{31} - v$, $P_{43} - v$ not vertex-critical | not attempted — 185–240 core-hours each |

    The full write-up, with the per-claim table and the compute costs, is in
    [`reports/beyond-five-voters/report.md`](https://github.com/Leonardini/TournamentsBeyond5Voters/blob/main/reports/beyond-five-voters/report.md).
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


if __name__ == "__main__":
    app.run()
