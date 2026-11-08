import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    IMG = ("https://raw.githubusercontent.com/Leonardini/Tournaments/main/"
           "reports/paley43-five-voters/images/")
    mo.md(
        rf"""
        # Can five voters produce any ranking?

        A tutorial walk through the central claim of
        [*Tournaments not inducible by three voters*](https://arxiv.org/abs/2607.26690)
        (Chindelevitch & Harutyunyan, arXiv 2607.26690) and its reproduction on a laptop.

        **The result, first.** A five-voter realization of the Paley tournament on 43 vertices
        would need two of its rankings to disagree in completely non-overlapping places. Among
        all 157 trillion available pairs, not one qualifies — the nearest miss still overlaps
        in 68 places.

        <img src="{IMG}fig1_level0_funnel.png" width="900" />

        Everything below explains what that means and re-derives the cheap parts live. Nothing
        in this notebook runs an expensive computation: the exhaustive screens were run
        separately (9 s and 11 s on 8 threads) and their results are quoted as data.
        """
    )
    return (IMG,)


@app.cell
def _(mo):
    mo.md(r"""
    ## The setup

    Give **m voters**, each a strict ranking of **n options**. For each pair of options,
    let the majority decide. The result assigns a direction to every pair — a
    **tournament**. Which tournaments can arise this way?

    Every tournament arises from *some* number of voters, so the sharp question is:

    > **N(k)** = the smallest number of options for which *some* tournament is **not**
    > the majority of k voters.

    Below N(k), k voters are universal. The paper brackets N(5) from both sides. This
    notebook follows the upper bound: an explicit 43-vertex tournament that five voters
    cannot produce, giving **N(5) ≤ 43**.

    ### Predictability, and the conjecture that fails

    Let *C* be the number of pairs and **MAS(T)** the largest number of pairs a single
    ranking can get right. Then

    $$\alpha^*(T) = \mathrm{MAS}(T)/C$$

    measures how nearly T is itself a ranking. A short count shows
    $\alpha^* \ge (k+1)/2k$ is **necessary** for k-inducibility. *Conjecture A* said it was
    also sufficient. The paper refutes that at k = 3 and at k = 5 — and Paley(43) is the
    k = 5 witness: it clears the threshold and still cannot be realized.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Build Paley(43) and check its constants

    Paley(q) for a prime $q \equiv 3 \pmod 4$: vertices $\mathbb{Z}_q$, and an arc
    $u \to v$ exactly when $v - u$ is a nonzero quadratic residue. Because $-1$ is a
    non-residue, exactly one of $u \to v$, $v \to u$ holds — so it really is a tournament.

    This is instant, and it is the same structural check the reproduction's
    `repro/verify_d0.c` performs.
    """)
    return


@app.cell
def _():
    def paley(q):
        """Adjacency matrix of the Paley tournament on q vertices."""
        res = {(x * x) % q for x in range(1, q)}
        return [[1 if (u != v and (v - u) % q in res) else 0 for v in range(q)]
                for u in range(q)]

    def stats(adj):
        """(arcs, out-degrees, cyclic triangles, triangles-per-arc) of a tournament."""
        n = len(adj)
        arcs = [(u, v) for u in range(n) for v in range(n) if adj[u][v]]
        outdeg = sorted({sum(row) for row in adj})
        tpa = [sum(1 for w in range(n) if adj[v][w] and adj[w][u]) for u, v in arcs]
        return len(arcs), outdeg, sum(tpa) // 3, sorted(set(tpa))

    P43 = paley(43)
    C43, deg43, T43, tpa43 = stats(P43)
    return C43, T43, deg43, paley, stats, tpa43


@app.cell
def _(C43, T43, deg43, mo, tpa43):
    mo.md(
        f"""
        | quantity | closed form | paper | computed here |
        |---|---|---|---|
        | arcs *C* | q(q−1)/2 | 903 | **{C43}** |
        | out-degrees | (q−1)/2 | 21 | **{deg43}** |
        | cyclic triangles *T* | (q³−q)/24 | 3311 | **{T43}** |
        | triangles per arc | (q+1)/4 | 11 | **{tpa43}** |

        A single value in the last row means Paley(43) is **doubly regular** — every arc lies
        in exactly the same number of directed triangles. That regularity is what makes the
        counting argument below so tight.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Why only a sliver of the 43! rankings can matter

    There are $43! \approx 6\times10^{52}$ possible voters, so a brute-force search is
    hopeless. Two facts cut it down to a finite check.

    ### Fact 1 — counting pins the top two voters

    Every arc must be forward in at least 3 of the 5 voters, so the five forward-counts
    sum to at least $3C$. Each is at most MAS. With MAS(Paley43) = 543 — certified by the
    paper's DP engine, and confirmed $\ge 543$ independently in this reproduction — the
    arithmetic is razor-thin.
    """)
    return


@app.cell
def _(C43):
    MAS43 = 543                       # certified by dp43.c; >= 543 re-derived in S7-A
    need = 3 * C43                    # every arc forward in >= 3 of 5 voters
    have = 5 * MAS43                  # the most five voters can supply
    slack = have - need
    forced_level = slack // 4         # f2 >= MAS - floor(slack/4)
    alpha43 = MAS43 / C43
    return MAS43, alpha43, forced_level, have, need, slack


@app.cell
def _(C43, MAS43, alpha43, forced_level, have, mo, need, slack):
    mo.md(
        f"""
        - required: every arc forward in ≥ 3 of 5 voters ⇒ total ≥ 3C = **{need:,}**
        - available: 5 voters, each ≤ MAS = {MAS43} ⇒ total ≤ **{have:,}**
        - **slack = {slack} arcs**, spread over five voters

        Order the voters by forward-count $f_1 \\ge \\dots \\ge f_5$. Then
        $4f_2 \\ge 3C - f_1 \\ge {need:,} - {MAS43} = {need - MAS43:,}$, so $f_2 \\ge 541.5$,
        hence $f_2 \\ge 542$: **both top voters sit at level ≤ {forced_level}** (within
        {forced_level} of the maximum). That shell is finite.

        And the density test does *not* save Paley(43) — it passes it:

        $$\\alpha^* = \\frac{{{MAS43}}}{{{C43}}} = \\frac{{181}}{{301}} = {alpha43:.9f}
        \\;>\\; 0.6 = \\tfrac35 .$$

        It clears the necessary condition by 2/1505 and is still not 5-inducible. That is the
        refutation of Conjecture A at k = 5: the real obstruction is global, and no
        single-density parameter can see it.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Fact 2 — the co-backing lemma

    Call a 3-cycle **double-backed** by a voter if that voter gets 2 of its 3 arcs wrong
    (a ranking restricted to a 3-cycle always gets 1 or 2 wrong — it can never get all
    three right). The lemma:

    > In any 5-voter realization, every cyclic triangle is double-backed by **at most one**
    > voter.

    The proof is three lines of counting, and it is small enough to verify exhaustively
    here over all $6^5 = 7776$ ways five voters can order one triangle.
    """)
    return


@app.cell
def _():
    from itertools import permutations, product

    def cobacking_check():
        """Over all 6^5 ways five voters can order one 3-cycle a->b->c->a:
        whenever every arc is forward in >= 3 voters, how many voters double-back?"""
        cyc = [(0, 1), (1, 2), (2, 0)]                 # the three arcs
        orders = list(permutations(range(3)))          # the 6 rankings of {a,b,c}

        def backed(order, arc):
            pos = {v: i for i, v in enumerate(order)}
            return pos[arc[1]] < pos[arc[0]]           # head ranked before tail => wrong

        worst = 0
        realizable = 0
        for profile in product(orders, repeat=5):
            if all(sum(not backed(o, a) for o in profile) >= 3 for a in cyc):
                realizable += 1
                d = sum(1 for o in profile if sum(backed(o, a) for a in cyc) == 2)
                worst = max(worst, d)
        return realizable, worst

    n_realizable, max_double_backers = cobacking_check()
    return max_double_backers, n_realizable


@app.cell
def _(max_double_backers, mo, n_realizable):
    mo.md(
        f"""
        Of the 7,776 profiles, **{n_realizable:,}** realize the triangle by majority, and
        across all of them the largest number of voters that double-back is
        **{max_double_backers}** — the lemma, verified exhaustively.

        So in a realization the five voters' **double-back sets are pairwise disjoint**. Combined
        with Fact 1:

        > If Paley(43) were 5-realizable, there would be **two rankings at level ≤ 1 whose
        > double-back sets are disjoint.**

        Showing no such pair exists is the whole computation — and it is what Figure 1 shows.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## How the exhaustive check is made tractable

    The level-0 shell alone holds 17,744,853 maximum-acyclic rankings — about
    $1.57\times10^{14}$ pairs. Two devices, both proved sound in the paper's §6, bring that
    to seconds. Neither can hide a disjoint pair.

    **The razor.** Fix a 24-vertex window $W = \{0,\dots,23\}$ and let $R$ be the 3-cycles
    lying wholly inside it (|R| = 538). Then $\mathrm{rmask}(O) = \mathrm{DB}(O)\cap R$
    depends only on how $O$ orders $W$, so the shell collapses to 124,406 distinct rmasks.
    If two rmasks overlap the full double-back sets certainly overlap — so only
    *razor-disjoint* pairs are candidates.

    **The automorphism reduction.** $|\mathrm{DB}(\sigma O_1)\cap \mathrm{DB}(\sigma O_2)|$
    is invariant under $G = \{x \mapsto ax+b : a \text{ a quadratic residue}\}$, of order
    903, so testing orbit representatives against the pool suffices — a factor 903 off one
    side.

    Both were re-checked in the reproduction: the invariance lemma over **all 903 σ**
    (0 violations in 1,598,310 checks), and G's action on the 3311 triangles giving 5
    orbits of sizes 903, 903, 903, 301, 301 with 602 triangles carrying a nontrivial
    stabiliser — the paper's figures exactly.
    """)
    return


@app.cell
def _(IMG, mo):
    mo.md(
        f"""
        ## What the reproduction observed

        <img src="{IMG}fig3_modes.png" width="900" />

        | quantity | paper (App. A.4) | observed | |
        |---|---|---|---|
        | razor triangles \\|R\\| | 538 | 538 | aligned |
        | level-0 orders screened | 17,744,853 | 17,744,853 | aligned |
        | candidate pairs exactly checked | 333,809 | 333,809 | aligned |
        | **TRUE_DISJOINT** | **0** | **0** | **aligned** |
        | minimum overlap | 68 | 71 → **68** | see note |

        **The one divergence, and its resolution.** `min_overlap` — how close the nearest
        candidate came to disjointness — first read 71. It is a diagnostic, not the claim, and
        it depends on *which candidate set is scored*. The automorphism reduction preserves the
        **existence** of a zero-overlap pair, but razor-disjointness is itself not
        G-invariant: σ permutes cyclic triangles without preserving which ones lie inside W.
        Re-running in the reduction-free `POOLVSPOOL` mode the paper used — 328,864,989
        full-pool pairs — returned **TRUE_DISJOINT = 0** and **min_overlap = 68**, the published
        figure exactly.

        **The control that makes a zero meaningful.** A screen reporting zero is worthless if
        it never looked. Restricting the double-back set to the razor triangles makes every
        candidate disjoint by construction, so reported seeds must equal candidates examined —
        and they did: 333,809 = 333,809.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## The k = 3 twin, and a small correction

    The same phenomenon appears one level down, where everything is certifiable by hand.
    **cA3** is the $\mathbb{Z}_{11}$ circulant with connection set $\{1,2,3,4,6\}$. It has
    $\alpha^* = 2/3$ **exactly** — sitting precisely *on* the A(3) threshold — and is still
    not 3-inducible. The reproduction confirmed that unanimously with three independent
    engines: OR-Tools CP-SAT (infeasible, proven), a CPLEX ILP, and a solver-free search
    over all 11! = 39,916,800 backward masks. It *is* 5-inducible, and vertex-critical:
    deleting any single vertex makes it 3-inducible.

    One documentation slip surfaced. The package's §5 README says cA3 is doubly regular;
    the script itself says otherwise, and the script is right:
    """)
    return


@app.cell
def _(paley, stats):
    from collections import Counter

    CA3_ROWS = ["01111100000", "00110100011", "00011100110", "00001110011",
                "01000011101", "00001001111", "11100101000", "11110000010",
                "11010011000", "10001010101", "10100011100"]
    CA3 = [[int(c) for c in r] for r in CA3_ROWS]

    def tpa_distribution(adj):
        n = len(adj)
        vals = [sum(1 for w in range(n) if adj[v][w] and adj[w][u])
                for u in range(n) for v in range(n) if adj[u][v]]
        return dict(sorted(Counter(vals).items()))

    ca3_dist = tpa_distribution(CA3)
    p11_dist = tpa_distribution(paley(11))
    _c, _d, ca3_tri, _t = stats(CA3)
    return ca3_dist, ca3_tri, p11_dist


@app.cell
def _(ca3_dist, ca3_tri, mo, p11_dist):
    mo.md(
        f"""
        | tournament on 11 vertices | connection set | triangles per arc | doubly regular? |
        |---|---|---|---|
        | **cA3** | {{1,2,3,4,6}} | **{ca3_dist}** | **no** |
        | Paley(11) | {{1,3,4,5,9}} (the residues) | {p11_dist} | yes |

        cA3 *cannot* be doubly regular: on 11 vertices the doubly regular circulant is
        Paley(11), built from the quadratic residues, and cA3 is a different circulant. Its
        {ca3_tri} cyclic triangles follow from regularity alone. No claim in the paper depends
        on this — it is an error in one "What to expect" line of the reproducibility package,
        caught by running it.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Optional: the density threshold across Paley tournaments

    Bounded interactive aside — **not** part of the reproduction evidence. The MAS values
    below are the certified ones (q = 7…31 were re-certified in this reproduction, q = 43
    is the paper's). Nothing is recomputed; move the slider to see how the threshold
    behaves.
    """)
    return


@app.cell
def _(mo):
    q_pick = mo.ui.slider(
        steps=[7, 11, 19, 23, 31, 43], value=43, label="Paley(q), q ≡ 3 mod 4:", show_value=True
    )
    q_pick
    return (q_pick,)


@app.cell
def _(mo, q_pick):
    KNOWN_MAS = {7: 14, 11: 35, 19: 107, 23: 161, 31: 285, 43: 543}
    _q = q_pick.value
    _C = _q * (_q - 1) // 2
    _mas = KNOWN_MAS[_q]
    _a = _mas / _C
    _slack5 = 5 * _mas - 3 * _C
    _src = "re-certified in this reproduction" if _q <= 31 else "the paper's certified value"
    mo.md(
        f"""
        **Paley({_q})** — C = {_C}, MAS = {_mas} ({_src})

        - $\\alpha^* = {_mas}/{_C} = {_a:.6f}$ versus the 5-voter threshold $3/5 = 0.6$
          → **{"clears it" if _a > 0.6 else "fails it, so 5 voters are ruled out by density alone"}**
        - realization slack $5\\,\\mathrm{{MAS}} - 3C = {_slack5}$
          {"→ tiny, so the top two voters are pinned near the maximum" if 0 < _slack5 <= 12 else ""}

        {"At q = 43 the slack is just 6 arcs — that thin margin is exactly what turns the question into a finite screen." if _q == 43 else ""}
        """
    )
    return


@app.cell
def _(IMG, mo):
    mo.md(
        f"""
        ## Everything else that was reproduced

        <img src="{IMG}fig5_scale.png" width="900" />

        Beyond the Paley(43) line, three further censuses reproduced at full published scale on
        the same laptop:

        - **§4, Theorem 4.1** — minimum feedback arc set equals minimum 3-cycle hitting set for
          every tournament on n ≤ 10: **9,932,002** tournaments, **0** violations, **0**
          unresolved, 110 s.
        - **§6, n = 9** — the triple-local CSP tally matched on every line (191,536 / 173,608 /
          254 / 17,674), and all 17,674 non-3-inducible tournaments were shown margin-1
          5-inducible with every witness independently re-verified.
        - **§6, n = 11** — the N(5) ≥ 12 census over all 903,753,248 tournaments.

        **What a complete reproduction still needs:** about 15 GB more free disk. The full
        level-≤ 1 shell needs ~48 GB of scratch for the q = 43 layer tables; the laptop had 43
        GB free, so the screen was run exhaustively on level 0 (17.7 M rankings) rather than
        level ≤ 1 (1.66 B). That also leaves the MAS ≤ 543 direction resting on the paper's
        certification, while MAS ≥ 543 was re-derived here independently.

        ---

        **Read next:** the full write-up in
        [`reports/paley43-five-voters/report.md`](https://github.com/Leonardini/Tournaments/blob/main/reports/paley43-five-voters/report.md),
        the proof in
        [`paley43/PALEY43_NONREALIZABLE.md`](https://github.com/Leonardini/TournamentsBeyond5Voters/blob/main/paley43/PALEY43_NONREALIZABLE.md),
        and the paper itself at [arXiv 2607.26690](https://arxiv.org/abs/2607.26690).
        """
    )
    return


if __name__ == "__main__":
    app.run()
