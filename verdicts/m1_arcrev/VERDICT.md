# Paley(23) is NOT arc-critical at margin 1

**2026-09-03.**  Complete refutation, laptop, 8 cores, ~40 min wall.

## Statement

`Paley(23)` with any one arc reversed is **not margin-1 5-inducible**.  Since
all single-arc reversals of `Paley(q)` are isomorphic for prime `q` (`Aut` is
regular on arcs; verified constructively for all 253 arcs, see
`../WITNESSES_paley_arcrev.md`), one host settles them all.  And `Paley(23)`
itself is not margin-1 5-inducible either -- immediate, since margin-1 is a
restriction of majority and majority is already refuted.  So the reversal
repairs nothing at margin 1.

**This is the opposite of `Paley(19)`, which IS margin-1 arc-critical.**

## What it does NOT settle

Nothing about MAJORITY.  `minFAS(Paley(23)^e) = 91`, so

    total dissents >= 5 x 91 = 455,   budget = 2 x 253 = 506,   slack = 51

and up to 51 of the 253 arcs may sit above 3:2 in a majority witness.  Majority
therefore does not collapse to margin-1 here, and the majority question --
is `Paley(23)` arc-critical at all -- remains open, at a measured 500 core-h
for the blind scan.

## Evidence

    host      p23_arcrev.bits  (Paley(23) with the arc (0,1) reversed)
    engine    kinduce24 --bits p23_arcrev.bits --n 23 --k 5 --margin exact
              --order mrv --inc --pool-mb 512 --base 0 1 2 6 15
    base      {0,1,2,6,15}, mask 918, 2200 base states -- EXACTLY the base the
              auto-selector picks; naming it is bit-identical (654,513 nodes on
              base state 1852 either way) and skips a 12 s per-process scan of
              all C(23,5) = 33,649 subsets.

    coverage  2200 done-markers, all distinct, [0,2200) with no gaps and no
              duplicates; 0 leftover logs (a base state that produced no RESULT
              is never marked done); 0 witnesses.
    cost      2.79 core-h of search (mean 4.56 s per base state, sd 1.11,
              range 1.76-8.47); ~7 core-h wall including per-process setup.

## Known-answer gate

The same binary and the same configuration, pointed at `p19_arcrev.bits`,
returns **SAT** in 444.6 s with `VERIFY bad_arcs=0 support_min=3 support_max=3
OK` -- the established `Paley(19)` margin-1 arc-reversal witness.  So the
pipeline finds a witness of exactly this shape when one exists.
