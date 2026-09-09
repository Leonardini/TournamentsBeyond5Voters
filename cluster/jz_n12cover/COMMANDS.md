# Commands — paste these, in this order

Run from the **repo root** unless a step says otherwise.

## 0. Build and self-test (login node, takes seconds)

    cd KInduceDFS/jz_n12cover && ./build.sh && ./selftest.sh && cd ../..

All three tests must pass. T1 is the important one: it reproduces the published
census of 96 non-3-inducible order-8 tournaments from scratch, two-sided.

## 1. Find the order-11 listing, or make one

There may already be a full order-11 collection on the cluster from the paper-1
census — look before regenerating:

    ls -la $WORK/jz_11 $SCRATCH/jz_11 2>/dev/null | head -30
    find $ALL_CCFRWORK -maxdepth 3 -name '*jz_11*' -o -maxdepth 3 -name '*n11*' 2>/dev/null | head
    head -2 <candidate-file> ; wc -l <candidate-file>

Wanted: one 55-character upper-triangular bit string per line, 903,753,248
lines. **Gate it before using it:**

    KInduceDFS/jz_n12cover/verify_listing.sh <file-or-shard-dir>

C1 checks the count, C2 the line shape, C3 that exactly 1,223 of them are
regular — a published invariant. A listing of the right size but a different
convention, or a partial run, would evaluate the wrong tournaments and come
back clean for the wrong reason. If C3 fails, do not use it.

If there is no usable listing, make one (0.8 core-h, ~51 GB):

    KInduceDFS/jz_n12cover/generate.sh $SCRATCH/n11_shards 45000

If the existing listing is a single large file rather than shards, split it:

    split -l 45000 -d -a 6 <file> $SCRATCH/n11_shards/sh_

## 2. Measure the actual rate ON A COMPUTE NODE — do not skip this

Grab one interactive core for 30 minutes and run:

    KInduceDFS/jz_n12cover/probe_rate.sh 4000

It runs the WHOLE pipeline -- generate, halve, cover, then decide the leftovers
one order-12 instance at a time -- and prints ms per screened host and the
projected core-hours over D_11/2, which is the number of hosts actually
evaluated once one of each converse pair is dropped. Measured on the laptop for
reference: 29 ms per screened host on a mid-stream residue (99.6% covered at
tier 1), 50 ms on residue 5000, and 251 ms on residue 0, whose hosts are the
near-transitive ones. Expect the projection to land between 3,700 and 8,000
laptop core-hours, and multiply by the measured cluster factor of 2.6-3.3. **Every figure in
HANDOFF.md was measured on a loaded laptop and spans 11–32 ms/instance; the
cluster factor is a guess carried over from a different engine at a different
n.** Size the array from what this prints, not from the defaults.

## 3. Submit

Sharded (preferred — even work units, retries do not regenerate):

    N12_LIST=$SCRATCH/n11_shards sbatch KInduceDFS/jz_n12cover/n12cover_shards.slurm

Inline generation (no listing on disk, uneven work units):

    sbatch KInduceDFS/jz_n12cover/n12cover.slurm

Environment variables: `N12_LIST`, `N12_OUT`, `N12_MOD`, `N12_DEADLINE`,
`COVER_SKIP`, `COVER_PBN`, `TIER2_TIME`, `TIER3_TIME`, `GENTOURNG`.

## 4. Check progress, and resubmit until complete

    KInduceDFS/jz_n12cover/aggregate.sh KInduceDFS/jz_n12cover/results

Resubmitting is the intended workflow: shards are marked done only on success,
so a resubmit picks up exactly what is left. Repeat step 3 until the done count
stops rising.

## 5. The two lines that matter

`aggregate.sh` prints **CANDIDATES** and, since 2026-09-08, a **census gate**:

    hosts generated : 903753248
      ALL 903753248 order-11 classes generated -- census gate PASSED
    converse halving: 903753248 generated, ... screened, factor 1.99xx

**Read the gate before the verdict.** `CANDIDATES 0` on its own is equally
consistent with a complete clean sweep and with a run that examined nothing --
that is exactly what happened on 2026-09-07, when 40,000 residues reported done
with zero instances. Only `generated == 903,753,248` distinguishes them.

Note `instances` is the count actually *evaluated*, which is about **half** of
`generated` because one host of each converse pair is dropped; do not read the
gate off that line.

If it is 0, every order-12 tournament reached so far is 5-inducible. If it is nonzero, look at
`results/candidates/<shard>.txt` — each `UNCOVERED` line names an order-12
tournament with no 5-voter realization, which would settle N(5) = 12.

Before believing any candidate, re-run it by hand with no limits at all:

    KInduceDFS/jz_n12cover/kcover --batch <host.bits> --n 11 --k 5 --inc \
        --cover --cover-skip 0 --margin majority --cover-dump

and check the line says `exhausted=1`. `exhausted=0` means a cap or the time
limit stopped the search and **nothing** may be concluded.

## The three tiers, as of 2026-09-08

Tier 1 is a coverage run: one `kcover` call settles all 2,048 one-vertex
extensions of a host at once, and on an ordinary residue it settles 95% of hosts
outright. Tiers 2 and 3 are **not** more coverage — that was the old design and
it could not terminate. Each mask tier 1 leaves uncovered is built into its own
order-12 tournament and decided directly by `kinduce`: margin 1 first (tier 2),
then majority for whatever comes back negative (tier 3). Only a *majority*
negative is a candidate counterexample.

Why: measured, tier 1 settles 0% of residue 0 — whose first host is the
transitive tournament, where all five voters agreeing can only reach the 12
suffix masks — and more coverage time does not help (174 s per host, still
1764–2000 of 2048). But one order-12 decision costs 14 ms, and that host's 284
leftovers all came back inducible in 4 seconds. Ordinary residues leave 0.8–1.3
masks per host, so the direct decisions add about 10% to the cover cost and the
pathological residues finish in minutes instead of never.

Both workers (`screen_residue.sh` and `eval_shard.sh`) source the pipeline from
`tiers.sh`, so they cannot drift apart; the selftest fails if either grows an
engine call of its own.

## If units keep coming back unresolved

An instance ran out of its budget, which is not a result. `TIER2_TIME` and
`TIER3_TIME` are now **per-instance decision caps** rather than per-host coverage
budgets, and the measured cost is 14 ms, so anything hitting even the default
120 s is worth looking at by hand before you simply raise it:

    TIER2_TIME=600 TIER3_TIME=3600 N12_LIST=$SCRATCH/n11_shards \
        sbatch KInduceDFS/jz_n12cover/n12cover_shards.slurm
