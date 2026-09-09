# Handoff — the n=12 cover campaign

## What this proves, and why it is cheap

Every order-12 tournament is `L + v` for an order-11 `L`, and **every order-11
tournament is already known 5-inducible** (paper 1, all 903,753,248). Given a
5-voter profile realizing `L`, inserting `v` at slot `t_i` in each order makes
`v`'s out-neighbourhood the **majority of five suffixes** — so one profile
settles a whole family of extensions at once, indexed by `t` in `{0..11}^5`
(248,832 tuples against only 2^11 = 2,048 masks, a 121x surplus). Cross the
masks off; when all 2,048 are gone, every order-12 tournament extending `L` is
5-inducible.

This is **exact in both directions**. If `L+S` is 5-inducible by any profile at
all, restricting that profile to `L`'s vertices gives a profile realizing `L`
(deleting `v` never changes the relative order of survivors) with `v`'s
positions as the thresholds. So no realizable extension can escape *some*
profile of `L` — which is exactly why the engine must try more than one profile,
and why a single profile is not enough.

Why it beats covering order-12 classes by order-13 tournaments: there is **no
canonicalisation floor** (~2e11 canonicalisations) and **no indexing problem**
(no 1.4 TB bucket structure, no mixing hash). It is a complete case analysis,
not a cover, so the ~12x redundancy costs nothing and needs no de-duplication.
The enumeration is 9.04e8 order-11 classes rather than 1.54e11 order-12 ones.

## Validation already done

* **Two-sided known answer.** At k=3, n=7→8 with caps off, the uncovered masks
  reproduce the published 96 non-3-inducible order-8 tournaments on **456/456
  hosts**, totals **808 vs 808**, against an independent Python computation.
  Mask-level too: host 49 gives exactly {37, 53} both ways. This is
  `selftest.sh` T1 — run it on the cluster before the campaign.
* **All 1,223 regular order-11 tournaments** come out ALL at both margins. These
  were the a priori hardest hosts (densest hunting ground for non-realizability,
  tightest witness budget) and are in fact the easiest.
* **End-to-end from raw profiles.** Rebuilding the explicit 5-voter profile on
  12 elements by brute force over all 12^5 insertion tuples and recomputing the
  majority tournament from scratch matched `L+S` on 240/240 samples.
* **Regression.** With `--cover` absent the engine reproduces 1223 SAT / 0
  UNSAT, so the patch is additive and the validated path is untouched.

## The three tiers are a soundness mechanism, not tuning

1. **margin-1, capped** — settles 0-95% depending on the residue, NOT the ~99%
   claimed here before it was measured (see the pricing section). Margin-1 SAT implies majority SAT, so
   this settles **both** statements at once. It is also 44x faster than majority
   and yields 43x fewer incompletes; on the one regular host majority struggled
   with, margin-1 was 370x faster (0.10 s vs 37.0 s).
2. **margin-1, uncapped** — `--cover-skip` and `--per-base-nodes` can only
   *delay* coverage, so `ALL` under caps is a proof but `INCOMPLETE` under caps
   means only "the cap bit". Every capped incomplete is re-run automatically.
3. **majority** — for hosts that genuinely fail margin-1. Some order-12
   tournaments are majority-inducible but not margin-1 inducible (margin-1 is
   known to break by n=19), so a tier-2 failure is expected, not alarming.

**Only a tier-3 `INCOMPLETE` with `exhausted=1` is a candidate.** `exhausted=0`
means a cap or a time limit stopped the search and nothing may be concluded;
such residues are left unmarked and retried. This asymmetry is wired into the
scripts deliberately: a cap artifact misfiled as a negative would read as a
counterexample to N(5) >= 13, which is the worst failure mode available here.

## Sizing — UNSETTLED, measure before committing

Every local number was taken while an 11-core job held the laptop, and they are
inconsistent in exactly the way contention produces:

| measurement | implied ms/instance |
|---|---|
| engine-reported search time, 2,000 random hosts | 11.2 |
| wall clock, 2,000 random hosts | ~30 |
| wall clock, 100 random hosts | ~161 |

So the laptop range is 11–32 ms/instance (2,800–8,000 core-h) and the 100-host
figure is contention noise.

### MEASURED 2026-09-08 ON REAL RESIDUES — THE THREE FIGURES ABOVE DO NOT HOLD

Priced by running the production tier-1 command on hosts taken from actual
residues at `MOD=40000`, laptop, one core, nothing else contending:

| residue | hosts | tier-1 `ALL` | ms/host |
|---|---|---|---|
| 0 | 50 | **0 (0%)** | 240 |
| 1 | 20 | 1 (5%) | 245 |
| 1000 | 20 | 19 (95%) | 103 |
| 5000 | 20 | 16 (80%) | 165 |

Two things follow, and both are blockers.

**"Tier 1 settles ~99%" is false, and the settle rate is a property of the
residue, not a constant.** It is 95% where the hosts are unstructured and 0% on
the first residues, whose hosts sit at the top of gentourng's generation tree.
The per-host cost is 100–250 ms, three to twenty times the table above, which
alone multiplies the 2,800–8,000 core-h estimate by an order of magnitude.

**Worse: the hard hosts are not settled by ANY tier.** Tier 2 (margin-1,
`--cover-skip 0 --time 120`) on three residue-0 hosts:

    COVER 0 covered=1764/2048 ... INCOMPLETE exhausted=0 nodes=262144 time=173.889
    COVER 1 covered=1956/2048 ... INCOMPLETE exhausted=0 nodes=262144 time=173.629
    COVER 2 covered=2000/2048 ... INCOMPLETE exhausted=0 nodes=262144 time=174.816

`nodes=262144` is 2^18 in all three, so tier 2 stops on an internal NODE cap
before its time budget, overruns to 174 s, and returns nothing decidable. Those
hosts then go to tier 3 at 600 s each. Since a residue with any unresolved host
is deliberately left unmarked, **a residue like 0 can never be marked done, no
matter how many times the array is resubmitted** — it would consume 1,242 x
(174 + 600) s = 267 core-h and finish exactly where it started.

**What is actually needed before this route runs again.** The covering claim is
per order-12 CLASS, not per host: every order-12 tournament is reached from all
12 of its one-vertex deletions, so a mask that resists at one host only matters
if it resists at all twelve. The pipeline currently demands that EVERY host
cover all 2,048 of its masks, which is far stronger than the theorem needs and
is what makes the structured hosts fatal. Deciding stubborn (host, mask) pairs
by canonicalising the order-12 class and attacking it from its easiest deletion
is the fix, and it is a redesign, not a parameter change. The n=15 campaign measured the cluster at **>= 4.3x
slower than this laptop**, but that was a different engine at a different n and
is a guess here. Run `probe_rate.sh` on a compute node.

**Residue sizes are very uneven and MOD saturates.** gentourng splits by input
chunk: res=7 gives 8,957 instances, res=1234 gives 164,154 (an 18x spread), and
mod=40000 and mod=200000 give identical counts — past some granularity it stops
subdividing and a larger MOD only manufactures empty residues. Sample sizes
before choosing MOD.

## Engine flags

    --cover              settle all 2^n extensions of each host in one search
    --cover-skip N       geometric skip after unproductive profiles (0 = off)
    --per-base-nodes N   abandon a base state after N nodes (0 = off)
    --cover-dump         print the UNCOVERED masks (the prize, for candidates)
    --margin exact       margin-1 (primary pass); --margin majority for tier 3

`--cover-skip` and `--per-base-nodes` are the speedups: naive 778 ms/host ->
42.6 with skip -> 8.4 with base diversity (majority) -> 4.5 (margin-1), on the
regular hosts. Both are one-directional — they can only delay coverage, never
claim it.

## How `--cover` works inside the engine

The DFS already computes, at each node, the domain `D(v | S)` of insertion
tuples for an unplaced vertex — with `U_i(p_i)` the suffix after slot `p_i`, the
support is `c_v(u) = #{i : u in U_i(p_i)}`, carried in three bit-planes by a
ripple adder. Normally the leaf tests that support against the target's required
arcs. Drop that requirement and `geq(b0,b1,b2,tHI) & placed` **is** the mask. So
cover mode is a leaf variant of `dom_rec` plus a 2^n accumulator, and needs no
threshold grid and no cross-off list of its own.

## Open

* Sizing, per above.
* The ~0.65% of random hosts that tier 1 leaves incomplete: on the sample these
  were all cap artifacts, resolved at tier 2. The genuine margin-1 failure rate
  at n=12 is unmeasured, and it sets the tier-3 load.
* A correction worth knowing: `D_11 x 2^11` is **not** exactly `12 x D_12`.
  Automorphisms inflate it by `Sum_v |Aut(T-v)|/|Aut(T)|` — at n=7→8 the totals
  are 58,368 vs 55,040 and the uncovered counts 808 vs 768 (+5%). The true
  order-12 ratio is 12.01. Nothing in this kit depends on it, but an earlier
  design that resolved deferred masks by counting multiplicities would have
  broken silently.
