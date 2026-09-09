# Margin-hierarchy witnesses, k = 5

**2026-09-03.**  The conjecture: the hierarchy
`margin<=1 subset margin<=3 subset unrestricted` is STRICT.  With `B_i` the
backward-arc set of voter `i`, support `= 5 - #{i : e in B_i}`, so margin<=3
says the `B_i` COVER every arc while no arc lies in more than two of them.

## First half: 5-inducible at margin<=3 but NOT at margin<=1 -- SETTLED, twice

Both hosts are margin-1 infeasible and have a verified margin<=3 witness.

| host | margin-1 | 3:2 arcs | 4:1 arcs | 5:0 arcs | slack used |
|---|---|---|---|---|---|
| Paley(19) | UNSAT (LRAT-verified, 22,876 cubes) | 159 | 12 | **0** | 12 of 22 |
| Paley(23) - v | UNSAT (complete sweep, `m1_family/p23mv`) | 208 | 23 | **0** | 23 of 57 |
| dr19_g2 | UNSAT (complete DFS sweep, 2200/2200, 0 capped, 2.70 core-h) | 160 | 11 | **0** | 11 of 27 |

Slack is `tLO*|E| - k*minFAS`; a 4:1 arc costs one unit of it and a 5:0 arc two.

Witnesses are ABUNDANT, not delicate: a shuffled 10-way sweep of Paley(19) at
`--max-margin 3` hit in all ten workers at once, from ten different base
states, with zero base states refuted.

Reproduce and check:

    ./kinduce24 --paley 19 --k 5 --max-margin 3 --order mrv --inc --base 0 1 2 3 5
    python3 verify_witness.py <log> 19 --majority

Paley(23)-v's witness is `n22_witness_slice.log` (found under `--margin
majority`; its support histogram happens to top out at 4:1, which is what makes
it a margin<=3 certificate).  Paley(19)'s is below.

## Second half: 5-inducible unrestricted but NOT at margin<=3 -- IMPOSSIBLE HERE

**2026-09-04.**  On every host in this project the second half CANNOT exist.  In
a 3-cycle u->v->w->u a linear order agrees with at most 2 of the 3 arcs, so
c(u,v)+c(v,w)+c(w,u) <= 2k = 10; majority forces each >= 3, so no support
exceeds 4.  An arc in ANY 3-cycle can therefore never be unanimous, and

        every arc in a 3-cycle   ==>   majority == margin<=3   (k=5).

And EVERY REGULAR tournament satisfies that: for u->v both N+(v) and N-(u) lie
in V\{u,v} (size n-2) with size (n-1)/2 each, so |N+(v) & N-(u)| >= 1.

That is why the 5:0 column below is 0 in every row -- it is forced, not luck --
and why `minfas_arc.c` fires nowhere in the Paley family: the target does not
exist there.  A separation REQUIRES an arc with N+(v) & N-(u) = empty, hence an
IRREGULAR host.  See RESEARCH_LOG.md 2026-09-04 08:30.

## Second half, original framing -- OPEN only off the regular families

Needs a tournament whose five near-optimal orders can never cover every arc.
`minfas_arc.c` screens for it soundly (`f(e) <= tLO*|E| - (k-1)*minFAS` is
necessary, `f(e)` = minFAS with arc `e` forced backward) but fires nowhere in
the Paley family and is asymptotically toothless -- see RESEARCH_LOG.md
2026-09-03 (late).

## Paley(19), margin<=3 witness

    RESULT: SAT, base state 1492, VERIFY bad_arcs=0 support_min=3 support_max=4 OK
    verify_witness.py: "all 171 arcs of Paley(19) at at least 3 of 5,
                        5 valid permutations -- witness is GENUINE"
    independent histogram: 171 arcs, 0 violations, 159 at 3:2, 12 at 4:1, 0 at 5:0

  voter 0: 9 7 12 13 18 10 16 8 14 0 17 4 15 1 5 2 6 11 3
  voter 1: 13 0 5 11 9 16 6 3 4 1 10 17 15 2 7 8 14 12 18
  voter 2: 1 17 18 5 3 14 12 4 10 2 8 9 6 15 0 7 16 13 11
  voter 3: 14 2 11 18 15 3 1 0 16 8 6 12 17 7 4 9 13 5 10
  voter 4: 6 10 7 4 11 8 15 5 12 16 2 13 17 3 0 9 14 1 18

## dr19_g2 -- the OTHER doubly-regular tournament on 19 vertices, margin<=3

There are exactly two DRTs on 19 vertices.  `dr19_g1` is Paley(19) relabelled
(explicit isomorphism found); `dr19_g2` is the genuinely different one, with
`|Aut| = 3` and SEVEN vertex orbits

    {0,2,18} {1,3,16} {4,5,14} {6,9,11} {7,10,17} {8} {12,13,15}

so `--top0` is UNSOUND on it and the correct break is `--toporb 0 1 4 6 7 8 12`.
Aut was computed explicitly (scratch backtracking search), which is what
discharges the caller-side obligation the engine prints and cannot check.

It is 5-inducible at margin<=3.  Found in **176 s on ONE core**:

    ./kinduce24 --bits dr19_g2.bits --n 19 --k 5 --max-margin 3 \
        --order mrv --inc --toporb 0 1 4 6 7 8 12
    python3 verify_witness_bits.py dr19_runs/WITNESS_g2_margin3.log dr19_g2.bits 19 5 --majority
    -> "VERIFIED: all 171 arcs at at least 3 of 5, 5 valid permutations -- GENUINE"

  voter 0: 0 6 7 15 1 13 2 11 3 4 18 9 10 16 5 17 14 8 12
  voter 1: 18 0 8 1 12 5 9 2 11 17 3 7 16 4 13 14 6 10 15
  voter 2: 14 4 6 10 17 3 12 5 7 2 8 18 11 16 13 15 0 9 1
  voter 3: 8 13 10 3 9 15 12 2 16 6 17 18 1 14 11 0 7 4 5
  voter 4: 16 5 14 15 4 11 9 7 17 1 12 13 18 10 0 2 8 6 3

Independent histogram: 171 arcs, 0 violations, 160 at 3:2, 11 at 4:1, 0 at 5:0.

How it sits against Paley(19) -- dr19_g2 is the LESS constrained of the two:

| host | minFAS | MAS/|E| | slack | 3:2 | 4:1 | 5:0 | margin<=3 cost (1 core) |
|---|---|---|---|---|---|---|---|
| Paley(19) | 64 | 0.6257 | 22 | 159 | 12 | 0 | -- |
| dr19_g2   | 63 | 0.6316 | 27 | 160 | 11 | 0 | 176 s |

Note slack does NOT bear on margin<=1: that rung forces every arc to exactly
3:2, so `#(4:1) + 2*#(5:0) = 0` satisfies the slack bound trivially in both.

## dr19_g2 at margin<=1: UNSAT -- BOTH DRTs on 19 vertices fail this rung

    ./kinduce24 --bits dr19_g2.bits --n 19 --k 5 --max-margin 1 \
        --order mrv --inc --toporb 0 1 4 6 7 8 12
    SLICE cleared=2200 capped=0 of [0,2200)  => SLICE EXHAUSTED, no witness
    RESULT UNSAT nodes=3499129111 sols=0 time=9716.956s     (2.70 h, ONE core)

Complete: every base state cleared, NOTHING capped, and the 10 h `--time` cap
was never approached. Log `dr19_runs/g2_m1.log`.

So on 19 vertices the margin-1 obstruction is not a Paley accident -- it is
shared by BOTH doubly-regular tournaments, which are non-isomorphic.

**This kills a tempting inference.** dr19_g2 is the LESS constrained host --
minFAS 63 vs 64, slack 27 vs 22 -- so one might expect it to clear a rung
Paley(19) cannot. It does not. The reason is structural: margin<=1 forces every
arc to exactly 3:2, so `#(4:1) + 2*#(5:0) = 0` and the slack bound
`<= tLO*|E| - k*minFAS` is satisfied with room to spare in BOTH cases. Slack
is simply not the binding constraint on this rung. Do not argue from minFAS or
slack to margin-1 feasibility.

SOUNDNESS: NO HUMAN LEMMA REMAINS.  The break was dropped entirely and the
sweep rerun as a plain complete search:

    ./kinduce24 --bits dr19_g2.bits --n 19 --k 5 --max-margin 1 --order mrv --inc
    SLICE cleared=2200 capped=0 of [0,2200)
    RESULT UNSAT nodes=3499152400 sols=0 top0_fails=0 time=9712.114s

This run carries NO caller-discharged assumption -- no orbit lemma, nothing the
engine cannot check -- so it stands alone as the refutation.  The two agree:

| run | nodes | time | top0_fails |
|---|---|---|---|
| `--toporb 0 1 4 6 7 8 12` | 3,499,129,111 | 9716.96 s | 135,947 |
| no break at all           | 3,499,152,400 | 9712.11 s | 0 |

**The orbit break is worthless at margin 1** -- 23,289 nodes out of 3.5e9
(0.0007%) and no measurable time.  It fired 135,947 times, but the subtrees it
cut were already dead: without it those nodes simply fail on MRV instead
(mrv_fails +214,717).  The margin<=1 constraint prunes so hard by itself that
Aut-breaking adds nothing.

PRACTICAL RULE: on a margin<=1 sweep, do NOT pass --toporb.  It buys nothing
measurable and it is the only step that can silently discard profiles if the
representative set is wrong.  Save it for the looser rungs, where the search
is wide enough for it to pay.
