# Every claim in the paper, and what in here establishes it

One row per statement the manuscript makes, with the artifact that carries the
verdict and the command that re-derives it. `tools/check_package.sh` walks this
file and fails if any path named below has gone missing, so the index cannot
rot quietly as the package changes.

Bases are written as the manuscript writes them, **1-indexed**; the engine takes
them **0-indexed**, which is why `{1,2,3,6,12}` in the text is `--base 0 1 2 5 11`
on the command line. Same set, different convention, and it has caused confusion
before.

Two regimes recur. *Unit margin* (`--margin exact`, or `--max-margin 1`) asks
every arc to be carried exactly 3–2. *Unrestricted* majority (`--margin
majority`) asks only for at least 3 of 5. Unit margin is a restriction, so a
unit-margin witness is also an unrestricted one and an unrestricted refutation
is the stronger statement. **Only an unrestricted refutation bounds N(5).**

---

## 1. The bound: 13 ≤ N(5) ≤ 23

| § | claim | verdict artifact | re-derive |
|---|---|---|---|
| 3.1 | **Paley(23) is not 5-inducible**, hence N(5) ≤ 23. Complete over all 8,031 base states of `{1,2,3,6,12}` | `evidence/rerun1_p23_majority.tar.zst` (2,008 slices), `evidence/anchor2_p23_majority.tar.zst` (4,030 slices, a different base and anchor) | `REPRODUCE.md` § "N(5) ≤ 23", both anchors |
| 3.1 | Paley(23), **machine-checked** on both halves | `certificates/p23cert_d6/VERDICT.txt`, roots in `certificates/p23cert_d6/p23_cert.portable.txt` | `sat/certify_d6.py`; roots rebuilt by `sat/reroot.py` |
| C | **13 ≤ N(5)**: no order-12 tournament is 5-inducible | `cluster/jz_n12cover/` — **see gap 1** | `cluster/jz_n12cover/COMMANDS.md` |
| 3.3 | Paley(43) − v is not 5-inducible, so N(5) ≤ 43 is **re-derived by a second method** | `evidence/p43_majority.tar.zst`, `verdicts/p43_minus1v_VERDICT.txt` | `REPRODUCE.md` § "Paley(43) is not vertex-critical" |

The two Paley(23) refutations are independent in base and anchor, not merely
repeated runs. The cluster reproduction of the certificate is gap 3.

## 2. The rest of the Paley family

| § | claim | verdict artifact | re-derive |
|---|---|---|---|
| 3.1 | Paley(27) is not 5-inducible, 8,031 base states, 1.14e8 nodes | `evidence/p27_majority.tar.zst` | `REPRODUCE.md` § "Paley(27)" — needs the **GF(3³)** host, `tournaments/p27_paley.bits`; the Z/27 construction is not a tournament |
| 3.1 | Paley(31) is not 5-inducible, 21,009 base states, 3.43e9 nodes | `evidence/p31_majority.tar.zst`, `evidence/measurements/p31_result.json` | `REPRODUCE.md` § "Paley(31)" |
| 3.2 | Paley(19) **is** 5-inducible (recovers dim Q₁₉ = 5 of [1]) | `verdicts/WITNESSES_margin_hierarchy.md` | `kinduce --paley 19 --k 5 --max-margin 3 --order mrv --inc --base 0 1 2 3 5`, then `verify/verify_witness.py` |
| 3.2 | Paley(19) is **not** 5-inducible at unit margin, 2,200 base states of `{1,2,3,4,6}` | `verdicts/p19_margin1_VERDICT.txt`; certified in `certificates/p19cert_d6/` | `REPRODUCE.md` § "Paley(19)"; `sat/certify_p19_m1.py` |
| 3.2 | The witnesses are abundant, not delicate: ten workers hit at once from ten base states, support histogram 159 arcs at 3–2 and 12 at 4–1, none unanimous | `verdicts/WITNESSES_margin_hierarchy.md` | as above, `--max-margin 3` |
| 3.3 | Paley(43) is **not vertex-critical** | `verdicts/p43_minus1v_VERDICT.txt`, `evidence/p43_majority.tar.zst` | `REPRODUCE.md`; the two `--toporb` reps are the QR and non-QR cosets of the order-21 stabiliser |
| 3.1 | Paley(23) − v **is** 5-inducible, so n = 22 does not improve the bound | `evidence/n22_p23minusv.tar.zst`, `verdicts/WITNESSES_paley_minus_vertex.md` | `REPRODUCE.md` § "Paley(23) minus a vertex" |
| 3.1 | Paley(23), (27), (31) are **not vertex-critical at unit margin** | `verdicts/m1_family/VERDICTS.md` (cells `p23mv`, `p27mv`, `p31mv`), per-state times beside it | `REPRODUCE.md` § "The margin-1 family" |

`verdicts/m1_family/VERDICTS.md` also records that the `p27` cell was abandoned
deliberately — Paley(27) is already refuted at majority and unit margin
restricts majority, so that cell is implied — and which arc cells are implied
rather than run. It says so in the table rather than leaving a gap to be
discovered.

## 3. Criticality

| § | claim | verdict artifact | re-derive |
|---|---|---|---|
| 3.4 | **Paley(23) is arc-critical**: reversing any arc gives a 5-inducible tournament. Witness at base state 1,161 of `T^e`; the scan was then stopped, which is sound for a positive certificate | `verdicts/WITNESSES_paley_arcrev.md`, `evidence/arcrev/` | host `tournaments/p23_arcrev.bits`; witness re-checked by `verify/verify_witness_bits.py` |
| 3.4 | Consequently Paley(23) is **vertex-critical** | as above, plus the direct route in `evidence/n22_p23minusv.tar.zst` | arc-criticality ⇒ vertex-criticality (§3.3) |
| 3.4 | Paley(23) is **not** vertex-critical at unit margin | `verdicts/m1_family/VERDICTS.md` cell `p23mv` | — |
| 3.4 | Paley(23) is not arc-critical at unit margin either | `verdicts/m1_arcrev/VERDICT.md` | — |
| 3.5 | The **second** doubly regular tournament on 19 vertices is arc-critical at unit margin: 57 orbits of size 3, 57 witnesses, none capped | `tournaments/dr19_arcflip/` (57 hosts, plus `tournaments/dr19_arcflip/manifest.tsv`, `tournaments/dr19_arcflip/sweep.log` and `tournaments/dr19_arcflip/sweep_run2.log`) | `REPRODUCE.md` § "The second doubly regular tournament on 19 vertices" |
| 3.5 | Both DRTs on 19 vertices are unit-margin obstructions and both are majority-inducible | `verdicts/WITNESSES_margin_hierarchy.md`, `verdicts/drt19_wit/` | `tournaments/dr19_g1.bits` is Paley(19) relabelled; `tournaments/dr19_g2.bits` is the distinct one, \|Aut\| = 3, seven vertex orbits |

### The 21-vertex picture (§3.4)

| claim | verdict artifact |
|---|---|
| Each of the four unit-margin obstructions has \|Aut\| = 21 with trivial stabilisers, hence exactly ten arc orbits of size 21 | `tournaments/vt21_hosts/manifest.tsv`, `tournaments/vt21_arcflip/manifest.tsv` |
| The spectrum: h₁ `UUUUUUUUUU`, h₂ `USUSSUUSSU`, h₄ and h₅ all `S` — 15 reversals stay obstructions | `verdicts/arcflip_spectrum.log` (final table), `tournaments/vt21_arcflip/out/*.exact.txt` per orbit |
| So **arc-criticality at unit margin is carried by the arc, not the tournament**: h₂ is arc-semi-critical, 105 of 210 arcs each way | same |
| All 210 single-arc reversals of h₁ remain obstructions — 736 runs, none capped, tiling each range exactly | `verdicts/arcflip_spectrum.log`, `tournaments/vt21_arcflip/verdicts.tsv` |
| The four hosts and the 15 surviving reversals have **319 one-vertex deletions, 289 pairwise non-isomorphic**, and every one has an exhibited unit-margin witness | `verdicts/vt20_descent.log` (301 audited SAT, 0 UNSAT, 0 capped), witnesses in `verdicts/vt20_descent_shard/*.log`, counts derived by `tournaments/deletion_classes.py` |
| Hence nothing here descends to a unit-margin obstruction on 20 vertices | same |

`tournaments/deletion_classes.py` derives 319 and 289 from the hosts by canonicalising every
deletion with nauty's `labelg` — 15 × 19 + 2 = 287 classes from the reversals,
plus h₄ − v and h₅ − v. It prints the reconciliation and is worth running,
because the raw file count (301) is neither of those numbers and invites a
wrong conclusion. Run it; it takes seconds.

## 4. The structured families (§3.5)

| claim | verdict artifact | re-derive |
|---|---|---|
| All **110** vertex-transitive tournaments on 21 vertices are 5-inducible — 106 at unit margin, the other four by exhibited majority witnesses. So that family holds no candidate below 23 | `verdicts/vt21_majority/`, `verdicts/vt21_margin1/`, `verdicts/verdict_ledger.tsv` | `tournaments/vt21_family.py`, `tournaments/vt21_all_reps.npy` |
| The closure survives one-arc perturbation: all **40** orbit representatives of the four obstructions are majority-inducible | `tournaments/vt21_arcflip/out/*.majority.txt` | — |
| Every regular tournament on at most **13** vertices is inducible at both margins (15, 1,223, 1,495,297 instances) | `verdicts/verdict_ledger.tsv`, and re-run in `tools/check_package.sh` check 6 | `kinduce --batch <chunk> --n <n> --k 5 --margin exact --order mrv --inc` |
| Every regular tournament on **15** vertices is inducible at unit margin, all 18,400,989,629, none capped, residue counts summing to OEIS A096368(7) | **gap 2 — no verdict artifact in this package** | `cluster/jz_n15/` |
| Every **self-converse** tournament on **13** vertices is inducible at unit margin — all $S_{13}$ = 95,458,560, 0 UNSAT, 0 aborted | the family splits three ways, each with its own record: **not provably rigid** (319,270) in `cluster/jz_n13sc/results_excluded/done/` — 77 chunks, all SAT, nothing capped; **regular** (11,237) by `verdicts/n13_regular_result.txt`, which clears all 1,495,297 regular order-13 tournaments at margin 1; **rigid** (95,128,053) across 488 shards, of which `cluster/jz_n13sc/results_local/done/` holds 81 — **the other 407 are gap 2** | `cluster/jz_n13sc/sweep_excluded.sh` then `cluster/jz_n13sc/report_excluded.sh`; `cluster/jz_n13sc/prepare.sh` refuses to sweep unless the listing has exactly 95,458,560 lines |
| The three parts are exactly the family, with no gap and no overlap | `cluster/jz_n13sc/state/partition.tsv` (per-bucket, and the per-bucket rigid counts are identical on both machines), checked by `cluster/jz_n13sc/aggregate.sh` | the regular count is anchored by `cluster/jz_n13sc/selfconverse_regular_n13.log`, produced by `verify/selfconverse_regular_count.py` from the **other** direction |
| **Refuted conjecture:** triangle load does not decide unit-margin inducibility — among 23-vertex vertex-transitive tournaments with t = 4, three are obstructions and 36 are inducible | `verdicts/n23_tmin4/`, `tournaments/vt23/manifest.tsv` | `verify/tri_per_arc.py` computes t; `tournaments/vt23_gen.py` builds the family |
| The unrestricted form survives: every majority obstruction we have has t ≥ 6 | `verdicts/verdict_ledger.tsv` | `verify/tri_per_arc.py` |
| Appendix D's exact enumeration counts $D_n$, $R_n$, $S_n$ | `verdicts/verdict_ledger.tsv` for our own sweeps; the $R_n$ column is OEIS A096368 and `gentourng` reproduces it | `tools/check_package.sh` check 6 regenerates $R_9$ and $R_{11}$ and compares against the published values |

## 5. The lemmas, which no certificate covers

| § | lemma | status |
|---|---|---|
| 3.3 | **3-cycle bound.** In a directed triangle the three supports sum to at most 2k, so with k = 5 no arc of a majority witness that lies in a triangle can be unanimous. Hence majority ≡ margin ≤ 3 on every regular tournament | proved in the paper; `verify/tri_ceiling.py` checks the hypothesis on a given host |
| 2.1 | (L1) orbit anchoring loses no generality — licenses solving only the *live* cubes | human, proved in §2 |
| 2.3 | (L2) the voters may be lex-ordered — licenses the lex chain in the coverage half | human, proved in §2 |

These are the trust boundary. The depth-first engine and the SAT pipeline share
these two lemmas and no code, so their agreement is evidence about the
implementations, not about the lemmas. `engine/kinduce.1`'s SOUNDNESS section
lists the obligations the program cannot check for itself, including that the
`--toporb` representatives really do meet every orbit — an orbit calculation
the caller owes and the engine trusts.

## 6. The certificates (Appendix B)

Both are complete on the search half and the coverage half.

| | Paley(19), unit margin | Paley(23), unrestricted |
|---|---|---|
| base | `{1,2,3,4,5,12}`, 6 vertices | `{1,2,3,4,6,7}`, 6 vertices |
| base states | 142,251 | 3,414,729 |
| live cubes | 22,876 | 343,896 |
| coverage instance | — | 3,415,435 clauses, UNSAT in 1,182.95 s, 2,097 MiB LRAT |
| ROOT (CNF) | `certificates/p19cert_d6/p19_cert.portable.txt` | `7e6c9c26ac386e67…` |
| combined | — | `ff60539e16abf2ec…` |
| cost | 24.3 + 0.8 core-h | 228.3 + 7.7 core-h |

The LRAT proof bytes were **verified and discarded by design**: each proof was
checked by `lrat-trim`, hashed, and deleted, so peak storage is one proof per
worker rather than terabytes. What ships is the per-cube sha256 chain in
`certificates/*/log/`, and both published roots rebuild from it exactly —
`tools/check_package.sh` check 3 does that and check 3b corrupts one hash to
confirm the check would notice.

**Which hashes a third party must reproduce.** ROOT (CNF) commits to the CNF of
every cube in cube order; it is generated by this code from the tournament and
the base and *must* reproduce anywhere. ROOT (proofs) additionally commits to
the proof bytes, which are not portable: CaDiCaL is deterministic on a fixed
binary but its heuristics use floating-point scoring, so a different build may
emit a different, equally valid proof. **A mismatch there is not evidence of an
error.** `certificates/p23cert_d6/VERDICT.txt` carries the full statement, including the
timing-free re-rooting that made ROOT (proofs) reproducible at all — the
original hashed record included wall-clock times, so it could not be reproduced
by anyone, this machine included.

That file also records, in its own text, an episode where the verdict script
printed "coverage of the cube set: certified separately" unconditionally, before
the coverage check had been run for Paley(23). It is left in rather than
tidied away: a certificate that misdescribes its own scope is the failure mode
Appendix B.2 exists to guard against, and no check caught it — re-reading the
verdict against the log of what had actually run did.

## 7. The method comparison (Appendix A)

| § | claim | artifact |
|---|---|---|
| A.1 | Integer programming does not reach these instances | `evidence/measurements/` |
| A.2 | SAT alone does not either. The dissent-Boolean encoding cuts CaDiCaL conflicts 26–42× against the order-variable family (2,399 / 1,491 / 57 on doubly regular tests), and with a sound symmetry break on top neither 19-vertex instance still returns a verdict | `sat/cube_sat.py` (the three encodings), `evidence/measurements/` |
| A.3 | The exact domain rule beats the capped one on decision quality alone: 992,378 nodes capped against 294,964 exact, identical verdicts, on a 29-instance Paley(19) benchmark | `evidence/measurements/`, `sat/leaf_bench.py` |
| B.1 | LRAT over DRAT on measurement: 0.295 s vs 1.043 s per leaf end to end, 29× in checking alone | `sat/leaf_bench.py` |
| A.4 | Choosing the decomposition: four cheap proxies each inverted when measured, so only bases × measured s/base is the objective | `evidence/measurements/probe2_results.json`, `evidence/measurements/probe3_results.json`, `evidence/measurements/price31.json`, `evidence/README.md` |
| A.5 | The cluster runs 2.6–3.3× slower per core than the laptop | `evidence/measurements/price43_series.json`, `cluster/jz_reproduce/` |

`evidence/README.md` is worth reading for A.4: it records that the Paley(27)
price came in 32% high through sampling noise rather than bias, with the
bootstrap that established which it was, and why the right estimator is a
cost-weighted paired ratio against a completed run.

---

# Gaps — what this package does not establish

Stated plainly, because a reproduction package that overstates its coverage is
worse than one with a short list of holes.

**Gap 1 — Appendix C (13 ≤ N(5)) is not yet complete.** The order-12 census was
still running on the cluster when this package was assembled, and the manuscript
carries three `PLACEHOLDER` markers for the phase-1 share, the phase-2 extension
count and the total cost. `grep -c PLACEHOLDER manuscript/*.md` returning
nonzero means the appendix is not ready. What is here is the kit that ran, the
aggregation and its self-test; the verdict markers are not.

**Gap 2 — the n = 15 regular census has no verdict artifact.** §3.5's claim over
all 18,400,989,629 regular tournaments on 15 vertices, and the 3,106 core-hour
row of the cost table, rest on an aggregate reported from the cluster;
`cluster/jz_n15/results_margin1/{done,unsat}/` are empty here. The `done/`
markers are the completeness certificate for that sweep — a marker is written
only on a finished residue, so their index cover is what makes the claim
exhaustive — and they have not been brought back. **This is the largest single
computation in the paper and the one with the least evidence in hand.**

The order-13 self-converse census has the same shape, and its own aggregate
says so out loud. Run it on what is here and it reports

```
completeness: 11,237 regular (excluded) + 319,270 symmetric (swept)
              + 95,128,053 rigid = 95,458,560
matches the 95,458,560 total EXACTLY -- no gap, no overlap
==> INCOMPLETE: 81 of 488 shards, 15,238,214 of 95,128,053 hosts;
    407 shards / 79,889,839 hosts still to sweep
```

The partition is exact and is worth reading twice. The 11,237 excluded ones are
the *regular* self-converse tournaments, already settled by the order-13 regular
sweep. The 319,270 are the hosts **not provably rigid** — the label `symmetric`
in the roll-up's output and the `sym/` directory name are both loose, because
colour refinement failing to discretise does not show that Aut is non-trivial,
it only fails to show that Aut is trivial. The implication runs one way:
discretising *is* a proof of triviality, so the 319,270 are a provable superset
of every order-13 self-converse tournament with non-trivial Aut, and an
obstruction surviving the rigid sweep would necessarily be rigid — unlike both
obstructions known at order 19. Getting this backwards would turn a sound
argument into a claim about 319,270 tournaments that nothing established.

What is missing is the cluster's 407 shards. The 81 run on the laptop are here
in full — 15,238,214 hosts, 0 UNSAT, 0 aborted — and
`cluster/jz_n13sc/state/jz_counts.tsv` holds the per-bucket rigid counts that
both machines must match line for line, which is what makes a split sweep
auditable at all. The sweep did complete; its cluster half's markers were not
brought back, and until they are, this package's own roll-up reports the family
as 16.02% swept. The paper's cost row is a `PLACEHOLDER` for the related
reason: the laptop half measured 46.8 core-hours for that 16.02%, and adding a
laptop rate to a cluster rate is precisely the error that table's note warns
about.

**Gap 3 — the cluster reproduction of the Paley(23) certificate is not
recorded here.** §5.2 rests the independent-implementation claim partly on the
cluster regenerating the same cube set and matching ROOT (CNF) bit for bit. The
Paley(19) instance did this (job 1829004, `PORTABLE ROOT MATCHES`); the
Paley(23) recertification was still running. `cluster/jz_reproduce/` holds the
kit and the Paley(19) log.

**Gap 4 — `versions/REGRESSION.md` is missing.** `REPRODUCE.md` closes by citing
it for the node-for-node agreement of the consolidated engine against each of
the 25 historical versions. The file does not exist. The 24 historical sources
are here, so the comparison can be run, but it is not recorded. Note also that
`engine/kinduce.c` is the consolidated engine, *not* the binary that originally
produced any published result; each result names its original version in
`REPRODUCE.md`, and the two agreeing is exactly what the absent file was meant
to document.

**Gap 5 — two coverage proofs are too large to ship and are not here.**
`cover_p19_d6.cnf` (34 MB), its DRAT (383 MB) and its LRAT (222 MB) exceed
GitHub's per-file limit and are regenerable from `sat/cover_check.py`; the
verification output is preserved in `certificates/p19_coverage_cert.txt`.

**Gap 6 — external tools are not vendored.** Versions used:

| tool | version | role |
|---|---|---|
| CaDiCaL | 2.0.0 | solves each cube, emits LRAT |
| `lrat-trim` | 0.2.0 | independently rechecks each LRAT proof |
| `drat-trim` | — | checks the coverage DRAT |
| nauty | 2.8.6 | `gentourng` generates the catalogues, `labelg` canonicalises |

`tools/check_package.sh` resolves each through a ladder of locations and fails
loudly naming everything it tried, rather than silently measuring nothing.
Set `SOFTWARE_DIR`, or `GENTOURNG`/`LABELG` individually, if yours live
elsewhere.

**Not a gap, but read §5.3 before comparing numbers.** Verdicts replicate under
any correct implementation — that is the paper's claim. Node counts replicate
exactly, but only with the binary, the vertex numbering, the base, the base-state
set and the margin regime all held fixed; the engine prints all but the numbering
in a header on every run, so a run log is a self-describing fingerprint, and the
numbering is the reason tournaments ship as bit strings rather than being rebuilt
from their constructions. **Two of the four 21-vertex tournaments are not in the
canonical labelling a fresh enumeration produces.** Wall-clock and core-hours
replicate only in order of magnitude.

One practical note: `lrat-trim` signals success with `s VERIFIED` and **exit
code 20**, following the SAT-solver convention, not exit code 0.
