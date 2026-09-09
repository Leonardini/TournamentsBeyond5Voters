# JZ handoff: screen all regular tournaments on 15 vertices for 5-inducibility

**Goal.** Find a non-5-inducible regular tournament on 15 vertices, or prove
none exists. A hit gives **N(5) ≤ 15**, against the current bound of 23.

**Status of the surrounding claims** (verified 2026-09-02, not recalled):

| set | count | k=5 margin-1 | k=5 majority |
|---|---|---|---|
| regular n=9 | 15 | 15 SAT / 0 UNSAT | 15 / 0 |
| regular n=11 | 1,223 | 1,223 / 0 | 1,223 / 0 |
| regular n=13 | 1,495,297 | **1,495,297 / 0** (123 s) | **1,495,297 / 0** (189 s) |
| regular n=15 | **18,400,989,629** (OEIS A096368(7); was wrongly 12,007,554,066) | **this job, ~694 core-h at laptop rate** | stage 2 only |

n=9 and n=11 were re-run from scratch here; the majority column doubles as the
known-answer check, since `N(5) ≥ 12` is proven and therefore *every* n ≤ 11
tournament must come back SAT. Counts are OEIS A096368 and `gentourng`
reproduces them exactly (see `selftest.sh`).

n=13 was run to completion on the laptop on 2026-09-02 in 5.3 minutes total
(`screen_n13_regular.sh`, summaries in `../n13_regular_result.txt`) and is **not**
part of this handoff. Its alpha* pass had settled nothing, alpha* > 3/5 being
one-sided; this screen decided it.

## Why margin-1 first, and why that is not a compromise

margin-1 (`--margin exact`, every arc decided exactly 3–2) is a *restriction*
of unrestricted majority (every arc ≥ 3 of 5), so the margin-1 feasible set is
contained in the majority one. Hence

> margin-1 SAT ⟹ majority SAT.

Contrapositive: only a **margin-1 UNSAT** instance can possibly be majority
UNSAT. So stage 1 screens everything under margin-1 (cheaper per instance,
~110 µs vs ~220 µs) and stage 2 revisits only the survivors — which on all
evidence so far is the empty set. This costs about half of screening majority
directly and yields both results.

The n=9 exhaustive record confirms the containment numerically: 17,674
unrestricted-infeasible, 17,928 margin-1-infeasible, 254 margin-1-only, 0 in
the impossible direction — and 17,674 + 254 = 17,928 exactly.

## Cost, and how it was measured

Timings pooled over real generated instances on the laptop (1 core), fitting
`time = setup + N × marginal`:

| term | rate | full n=15 |
|---|---|---|
| generation (`gentourng -d7 -D7 15`) | 29.3 µs/instance | ~150 core-h |
| search (`kinduce20 --batch`) | 100.8 µs/instance | ~515 core-h |
| per-process setup | 17.6 s × 6000 residues | ~29 core-h |
| **total** | | **~694 core-h** (laptop rate) |

**CORRECTED 2026-09-03.** The rates above are re-measured on residue 0 of 6000
(3,205,018 instances: 94 s generation + 323 s search = 417 s), and the
INSTANCE TOTAL was wrong.  The true count is **OEIS A096368(7) =
18,400,989,629** -- 1.53x the 12,007,554,066 this kit was built on, which
appears in no term of that sequence.  (A096368 = 1, 1, 1, 3, 15, 1223,
1495297, 18400989629, ... by 2n+1 nodes; its n=13 term matches our own
exhaustive run, which anchors the offset.)  Cross-checked by sampling 20
residue classes: mean 3,230,598, sd 782,154, se 174,895, so 6000 x mean =
1.94e10, within 1 se of the OEIS figure (see residue_sizes.txt).  Sampling is
only a cross-check -- gentourng splits by INPUT chunk with no guarantee on
output-class sizes.  The method itself was validated first: at n=13, mod 8, the
eight residue counts sum to 1,495,297 exactly, so `res/mod` partitions the
output.  `gcc -O3
-march=native` buys 1.8% over `-O2` -- not worth rebuilding for.
Per-residue spread is 2.16M..5.02M, so per-task wall time must budget for the
FATTEST residue: 5.02M x 130.1 us = 653 s locally, and 10 residues per task at
a 4x JZ factor is ~7 h, over the old 6 h wall.  Raised to 20 h below.

**The setup term is the whole design constraint.** `kinduce20` pays ~17.6 s
once per process building its per-mask base-state cache, then ~110 µs per
instance. Small shards therefore pay that setup over and over:

| MOD | instances/residue | min/residue | setup overhead | total |
|---|---|---|---|---|
| 100,000 | 120,076 | 0.6 | 544 core-h | 1,035 core-h |
| 20,000 | 600,378 | 1.8 | 109 core-h | 599 core-h |
| **6,000** | **2,001,259** | **5.2** | **33 core-h** | **523 core-h** |
| 1,000 | 12,007,554 | 29.7 | 5 core-h | 496 core-h |

MOD = 6000 buys 5-minute checkpoint granularity for 6% overhead. Do not raise
MOD without redoing this arithmetic — at 100,000 the job costs twice as much
and every extra hour is setup.

*A caution on measuring this yourself:* any timing run smaller than ~400k
instances is setup-dominated and will report a per-instance cost several times
the true marginal one. Five shards of ~18k instances each gave a nearly
constant 20 s regardless of instance count; dividing that through inflated the
estimate 8.7×.

## Shape

- `--array=0-599`, single-core tasks, `qos_cpu-t3`, `--time=06:00:00`.
- Each task strides through 10 of the 6000 residues: `RES = T, T+600, …`.
- ~52 min/task. With 100 tasks resident, ~5 h wall.
- **No `--mem`** — Jean-Zay rejects it; RAM follows `--cpus-per-task`. The
  engine needs ~2 MB, so one core is ample.
- No data transfer: instances are generated on the node. Only source needs to
  reach JZ (git), plus nauty, which `build.sh` fetches.

## Checkpointing

One marker file per completed residue, `results_margin1/done/r<res>`, written
**only after** the engine emits a summary. A resubmit skips finished residues,
so a wall-kill or cancel costs at most one residue (~5 min).

This is deliberate. The recurring failure mode on this project has been
end-only-save: whole campaigns (realize5_n18 job 811411, AlphaSweep n=13,
AlphaScreen n=39) burned their entire wall and wrote *nothing*, because output
came only at slice end. Per-residue markers make partial progress durable and
resume free.

## Files

| file | role |
|---|---|
| `build.sh` | compile `kinduce20`; fetch + build nauty `gentourng` if absent |
| `selftest.sh` | **mandatory** known-answer gate — counts and verdicts |
| `screen_residue.sh` | screen one residue; writes the done-marker and any UNSAT bits |
| `n15_margin1.slurm` | the array job |
| `aggregate.sh` | progress and results, safe mid-job |
| `COMMANDS.md` | the paste-able block, with what to send back at each step |

## What comes back

- **No UNSAT anywhere** ⟹ every regular tournament on 15 vertices is margin-1
  5-inducible, hence also majority 5-inducible. That closes n=15 regular as a
  route to improving N(5), and extends the regular ladder n=9, 11, 13, 15.
- **Any UNSAT** ⟹ a candidate. Send the `.bits` files back; they are one
  105-character line each. I verify them locally against an independent
  checker and run the majority confirmation. A confirmed majority UNSAT is
  **N(5) ≤ 15**.

## Scope limit, stated plainly

This screens *regular* tournaments only. Regularity is a heuristic bet — the
known obstructions (Paley) are regular, and `RESEARCH_LOG` records that
hardness tracks regular/Paley structure — but it is not a theorem that a
minimal non-5-inducible tournament must be regular. An all-clear therefore
bounds nothing about general n=15; it only rules out this family. The
`k_max` evidence in `Check3Majority/margin1_sat/FINDINGS.md` cuts the other
way and is worth remembering: the **self-converse** family breaks the regular
ceiling at every size (7 vs 5 at n=11), so if this comes back empty,
self-converse n=15 is the better next family, not a bigger regular sweep.
