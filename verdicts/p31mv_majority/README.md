# Is Paley(31) vertex-critical?  The P31−v majority sweep

## The question, stated exactly

Let $T = \mathrm{Paley}(31) - v$ on $n = 30$ vertices. Decide whether there are
$k = 5$ linear orders $\pi_1,\dots,\pi_5$ of $V(T)$ with

$$c(a,b) = \#\{\, i : a \prec_{\pi_i} b \,\} \;\ge\; 3 \qquad
\text{for every arc } a \to b \text{ of } T .$$

* **SAT** ⟹ Paley(31) **is vertex-critical**: a 31-vertex tournament that is not
  5-inducible, every one-vertex deletion of which is. The arc question — is it
  *arc*-critical? — then opens.
* **UNSAT** ⟹ Paley(31) is not vertex-critical, as Paley(43) is not, and the
  monotone criticality ladder across $q$ breaks at 31 rather than later.

Paley(31) itself is not 5-inducible: settled 2026-09-03, 5253/5253 chunks UNSAT,
0 capped, coverage $[0,21009)$ with no gaps, 26.89 core-h.

## Why this is the interesting rung

| $q$ | margin-1 arc-crit | margin-1 vertex-crit | majority arc-crit | majority vertex-crit |
|---|---|---|---|---|
| 19 | **YES** | YES | (implied YES) | YES |
| 23 | NO | NO | **YES** | YES |
| 27 | NO | NO | ? | ? |
| 31 | (implied NO) | NO | ? | **this sweep** |
| 43 | (implied NO) | NO | (implied NO) | **NO** |

Criticality holds at 19 and 23 and fails at 43, so 27 and 31 are where the
transition sits. Leonid's conjecture is a smooth degradation, with 27 and 31
vertex-critical but not arc-critical.

## Three facts that make one run enough

1. **One run settles all 31 deletions.** $|\mathrm{Aut}(\mathrm{Paley}(31))| =
   465 = \binom{31}{2}$ (nauty), so Aut is regular on arcs and in particular
   vertex-transitive; all one-vertex deletions are isomorphic.
2. **`--max-margin 3` is a majority verdict.** 3-cycle bound, checked on *this*
   host by `../p43m2v_majority/verify_host.py`-style recomputation: every arc of
   `p31_minus1v.bits` lies in at least **7** cyclic triangles and **0** arcs lie
   in none, so no arc can reach support 5.
3. **Margin 1 is already refuted** (`../m1_family` cell `p31mv`: 2200/2200 base
   states, exact coverage, no witness, 2.21 core-h). Majority is the only live
   rung, so this sweep is the whole remaining question.

## What we deliberately give up

$|\mathrm{Aut}(\mathrm{Paley}(31)-v)| = 15$ exactly (nauty; $=(q-1)/2$, the
stabiliser of the deleted vertex), splitting the 30 survivors into two orbits of
size 15 and licensing a two-rep `--toporb` break worth about **20%** at this
margin. **It is not used.** An unsound break loses witnesses, and a witness is
the outcome this sweep exists to find; 20% of wall time is a cheaper price than
a wrong answer.

## The prior, measured rather than asserted

A 39-draw witness probe on Paley(27)−v and Paley(31)−v found nothing
(`../p27p31_probe`). That is only evidence if the protocol has power, so the
identical protocol was run on hosts *known* to be majority 5-inducible
(`../calibration`): the n=21 vertex-transitive hosts h01 and h02, which are
margin-1 obstructions but majority-SAT — the closest available analogue.
**h01: 3 of 30 base states yielded a witness inside 90 s; h02: 5 of 5.** Pooled,
8 of 35 = 23%. So a null of 0 in 39 has probability $0.9^{39} = 0.016$ at h01's
rate and $4\times10^{-5}$ at the pooled rate. Mild-to-strong evidence that
**UNSAT** is the likely verdict here — which is exactly why it is worth a
complete sweep rather than another probe.

## Adding `--toporb 0 2` part-way through, and why the mixture is still complete

The break is applied from 2026-09-09 09:2x onward; the base states settled before
that were searched **without** it. The union is still a complete refutation:

Let $W$ be any witness. `--toporb 0 2` is sound here (Aut(P31−v) has exactly two
vertex orbits, of size 15 each — the QR and non-QR cosets of $\mathrm{Stab}(0)$ —
and new labels 0 and 2 are old labels 1 and 3, one in each), so some
$g \in \mathrm{Aut}$ carries $W$ to a witness $W' = gW$ in which some voter ranks
0 or 2 first. $W'$ lies in exactly one base state $B$, because the base states
partition the profile space. Two cases, and both are covered:

* $B$ was settled **without** the break — then $B$ was searched exhaustively, so
  it contains no witness at all, contradicting $W' \in B$;
* $B$ is searched **with** the break — then $W'$ satisfies the break by
  construction, so it is inside the searched region.

Either way a witness cannot hide, so the mixed sweep refutes exactly what an
unbroken one would. Note the direction that matters: an *exhaustive* search of a
base state is strictly stronger than a broken one, so earlier work is never
invalidated by turning a sound break on later — only the reverse would be a
problem.

Markers record which regime produced them (`brk=` field), so the mixture is
visible in the record rather than implicit.

**What it does NOT do:** it does not reduce the 8,031 base states — measured, the
engine reports the same count with and without it. Base-state elimination would
need a `--toppair`-style break, and that is impossible here for any valid rep
set: pruning requires every rep to sit inside the base, a 5-base offers only
$5\times4 = 20$ ordered pairs, and $\mathrm{Aut}(P31-v)$ has **58** orbits on
ordered pairs ($30 \cdot 29 / 15$, the action being free). For Paley(31) itself
$|\mathrm{Aut}| = 465 = \#\text{arcs}$ gives just 2 orbits, which is why the
3.17× break exists there — deleting a vertex divides $|\mathrm{Aut}|$ by $q$ and
multiplies the orbit count by about $q$, destroying precisely the
arc-transitivity the base-state break relies on.

## Snapshotting and resuming

The per-base markers in `done/` are resumption state and untracked. The tracked
record is the times file, written and rebuilt by the SHARED tools (one copy, so
this kit and its sibling cannot drift):

    bash KInduceDFS/sweep_snapshot.sh p31mv_majority    # done/ -> the times file
    bash KInduceDFS/sweep_rehydrate.sh p31mv_majority   # the times file -> done/

Verified byte-for-byte round trip on every recorded state. Snapshot before
pausing, swapping, or compacting a session.
