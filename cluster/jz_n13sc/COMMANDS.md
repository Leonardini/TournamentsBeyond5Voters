# Self-converse tournaments on 13 vertices, margin 1

## What this is

A **hunt, not a census**. The cheapest open form of the margin-1 question is
*the smallest tournament that is not margin-1 5-inducible*. The record holder is
Paley(19); n=13 in general is unswept. **A single UNSAT here drops that from 19
to 13 and is the result** — so hits are printed the moment they occur.

Margin 1 first, because margin-1 SAT implies majority SAT: anything settled here
needs no majority run.

## Already done locally — do not redo

| | hosts | |
|---|---|---|
| regular (imbalance 0) | 11,237 | skipped: every regular tournament on n ≤ 13 is already known 5-inducible at **both** margins |
| imbalance bucket 4, in full | 116,765 | all SAT |
| imbalance bucket 8, in full | 581,515 | all SAT |
| every possibly-symmetric host | 319,270 | all SAT, across all buckets |
| **settled** | **1,026,306** | **zero UNSAT** |

The settled figure is NOT the sum of the four rows above: buckets 4 and 8 are listed
*in full*, so their 534 and 1,947 possibly-symmetric members are already inside those
counts and must not be added again with the 319,270. The naive sum, 1,028,787,
double-counts by exactly 2,481 — and is contradicted by this file's own remaining
figure, since 95,458,560 - 1,026,306 = 94,432,254 ("about 94.4 million") whereas
95,458,560 - 1,028,787 = 94,429,773. Verified against a live `prepare.sh` 2026-09-06.

`prepare.sh` reproduces the same partition, so those files can be skipped.
Remaining: about **94.4 million**, all provably rigid.

## What a clean result would mean

Colour refinement discretising is a *theorem* that Aut is trivial, so the
319,270 already swept are a genuine **superset** of every self-converse
tournament on 13 vertices with a non-trivial automorphism group. If an
obstruction exists here it therefore has **trivial Aut** — unlike Paley(19)
(|Aut| = 171) and unlike dr19_g2, the only two known. That is a reason to expect
this sweep to come back empty, and a reason the result is worth having anyway:
it would say the phenomenon requires symmetry.

## Steps

    # 0. build (seconds)
    KInduceDFS/jz_n13sc/build.sh

    # 1. fetch and partition -- ~7 GB unpacked, ~20 GB scratch with buckets
    N13_WORK=$SCRATCH/n13sc KInduceDFS/jz_n13sc/prepare.sh

    # 2. MEASURE THE RATE on a compute node before sizing anything
    N13_WORK=$SCRATCH/n13sc KInduceDFS/jz_n13sc/probe_rate.sh 20000

    # 3. submit
    N13_WORK=$SCRATCH/n13sc sbatch KInduceDFS/jz_n13sc/n13sc.slurm

    # 4. roll up, and resubmit until the count stops rising
    KInduceDFS/jz_n13sc/aggregate.sh KInduceDFS/jz_n13sc/results

`prepare.sh` refuses to proceed unless the listing has exactly 95,458,560 lines.

Environment: `N13_WORK`, `N13_OUT`, `N13_PER` (hosts per shard, default 200,000),
`N13_DEADLINE`.

## Cost

About 10 ms per host on the laptop, so roughly 265 core-h for the remainder —
but **the n=15 campaign measured this cluster at ≥ 4.3x slower** than the laptop
on a different engine, and that factor is a guess here. Run `probe_rate.sh` and
size the array from what it prints.

## Two things wired in rather than documented

**A shard is marked done only if instances-run equals instances-expected.** A
mismatch leaves it unmarked and prints a warning. This exists because a `xargs`
form used during development silently ran *zero* instances while still reporting
a summary — the count check is what caught it.

**ABORTED is not a verdict.** The per-host cap is 300 s; anything hitting it is
counted separately and must be re-run with a larger budget before it means
anything. Only `UNSAT` from a completed search is a hit.

## No symmetry break here

Self-converseness is an **anti**-automorphism — σ with u→v iff σ(v)→σ(u). It is
not an element of Aut(T) and licenses no vertex break. Colour refinement cannot
see it either, since refinement respects arc direction, which is why "rigid" in
this kit means Aut(T) = 1 rather than "no symmetry at all".

And `--toporb` is worthless at margin 1 (0.0007% of nodes) and is the one flag
that can silently discard profiles. Never pass it on a margin-1 run.
