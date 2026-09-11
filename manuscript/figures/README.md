# Figures

## Figure 1 --- Algorithm 1 worked through on $P_7$ with $k = 3$

Three files, in the order they run:

    python3 paley7_trace.py --base 0 1 3 --regime majority --json trace_maj.json
    python3 paley7_figure.py trace_maj.json paley7_alg1.tex
    pdflatex paley7_alg1.tex

`paley7_trace.py` is a second, independent implementation of the placement
search of Appendix A.2, written to be read rather than to be fast, which dumps
the state of every node it visits. It refuses to produce a trace unless seven
cross-checks pass, and they are the point of it:

| | what it pins |
|---|---|
| T1 | base-state and witness counts agree with `KInduceDFS/kinduce` on the same instance, at both margin regimes |
| T2 | the witness set contains the profile Shepardson and Tovey publish, and is a single orbit under $\mathrm{Aut}(P_7) \times S_k$ --- their uniqueness claim, which they assert without proof |
| T3 | at every node, the incrementally refined domain equals the domain recomputed from scratch |
| T4 | every arc of every witness has support exactly $(k+1)/2$ even when the search runs at majority |
| T5 | imposing Lemma 2.1 during the search only ever removes nodes, and leaves one witness |
| T6 | the witness set does not depend on the decomposition: all 91 bases of order 3, 4 and 5 return the same profiles |
| T7 | the witness is one order's orbit under an automorphism of order $k$, so its stabiliser has order $k$ and there are $|\mathrm{Aut}|/k$ witnesses |

`paley7_figure.py` draws the panels and nothing else: no number in the picture
is hand-copied, and it asserts that the snapshots it draws are the ones the
trace actually contains before emitting any TikZ.

The caption lives in the manuscript, so its numbers cannot be checked by
compiling the figure. They are checked separately:

    python3 paley7_figure.py trace_maj.json --check ../Tournaments_not_inducible_by_five_voters.md

which fails unless every quantity the caption quotes matches the trace.

`show_trace.py trace_maj.json` prints a trace in a readable form, node by node.

Build products that do not belong in git: `paley7_alg1.aux`, `paley7_alg1.log`,
and any `fig_preview*.png` from `pdftoppm`.

## Is Paley(7) the smallest instance that exercises all of Algorithm 1?

`smallest_instance.py` tests the claim the caption makes, over every tournament
on at most 7 vertices, every base of order 3 to n-1, and both margin regimes.
It first pins down what "every part" means -- eleven of them, listed in the
module docstring -- since the claim cannot be checked until that is fixed.
