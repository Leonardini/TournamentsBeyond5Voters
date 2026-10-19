# Every claim in the paper, and what in here establishes it

One row per statement the manuscript makes, with the artifact that carries the
verdict and the command that re-derives it. Each row has a stable **id**;
`tools/claims_index.py` turns this file into `claims.tsv` and `claims.json` for
a machine reader, and `tools/check_package.sh` fails if the two disagree or if
any path named below has gone missing, so the index cannot rot quietly as the
package changes.

The manuscript this indexes is `manuscript/Tournaments_not_inducible_by_five_voters_MSS.md`,
the version submitted to *Mathematical Social Sciences*, with its LaTeX source,
the built PDF and the highlights file beside it. Section numbers below are that
version's.

Bases are written as the manuscript writes them, **1-indexed**; the engine takes
them **0-indexed**, which is why `{1,2,3,6,12}` in the text is `--base 0 1 2 5 11`
on the command line. Same set, different convention, and it has caused confusion
before.

Two regimes recur. *Unit margin* (`--margin exact`, or `--max-margin 1`) asks
every arc to be carried exactly 3–2. *Unrestricted* majority (`--margin
majority`) asks only for at least 3 of 5. Unit margin is a restriction, so a
unit-margin witness is also an unrestricted one and an unrestricted refutation
is the stronger statement. **Only an unrestricted refutation bounds N(5).**

A third regime, `--max-margin 3`, appears in several runs and is *equal* to
unrestricted majority on every host here: by the 3-cycle bound of Section 3 an
arc lying in a directed triangle can never be unanimous, and
`verify/triangles_per_arc.py` checks that hypothesis host by host rather than
assuming it.

---

## 1. The bound: 13 ≤ N(5) ≤ 22

| id | § | claim | verdict artifact | re-derive |
|---|---|---|---|---|
| B1 | 3.1 | **Paley(23) is not 5-inducible**, hence N(5) ≤ 23. Complete over all 8,031 base states of `{1,2,3,6,12}`, of which 2,591 survive the anchor | `evidence/rerun1_p23_majority.tar.zst` (2,008 slices, 34.03 core-h), `evidence/anchor2_p23_majority.tar.zst` (4,030 slices, a different base and anchor, 43.80 core-h) | `REPRODUCE.md` § "N(5) ≤ 23", both anchors |
| B2 | 3.1, B.1 | Paley(23), **machine-checked** on both halves | `certificates/p23cert_d6/VERDICT.txt`, roots in `certificates/p23cert_d6/p23_cert.portable.txt` and, bound to the host's adjacency, `certificates/p23cert_d6/p23_cert.v2.portable.txt` | `sat/certify_d6.py`; roots rebuilt by `sat/reroot.py`; `tools/check_package.sh` checks 3, 3c and 3d |
| B3 | C | **13 ≤ N(5)**: every order-12 tournament is 5-inducible. All 903,753,248 order-11 classes generated, 452,016,608 screened after the converse halving, **0 candidates** | `cluster/jz_n12cover/FINAL_ROLLUP.txt` — the verbatim roll-up of the completed run, 2026-09-12 | `cluster/jz_n12cover/COMMANDS.md`, rolled up by `cluster/jz_n12cover/aggregate.sh`, whose census gate exits non-zero on any mismatch |
| B4 | 3.5 | Paley(43) − v is not 5-inducible, so N(5) ≤ 43 is **re-derived by a second method** | `verdicts/p43mv_majority/p43mv_times.txt` (8,031 base states, exact cover, 185.54 core-h), `verdicts/p43_minus1v_VERDICT.txt` | `REPRODUCE.md` § "Paley(43) is not vertex-critical" |
| B5 | 3.2 | **Δ₆ − 5 is not 5-inducible**, hence N(5) ≤ 22. The host is `d005_mv04`, the doubly regular tournament `d005` on 23 vertices (line 6 of McKay's catalogue) with vertex 5 deleted (4, 0-based), the rest kept in order. Complete over all 8,031 base states of `{1,2,3,12,18}`, no symmetry break, 1,551.2 **cluster** core-hours | `evidence/d005mv04_sweep_markers.tar.zst` (8,031 markers, all UNSAT, capped=0, and the sweep's `VERDICT.txt` with its tree hash); host `tournaments/drt23_del/d005_mv04.bits` | `verify/sweep_cover_audit.py`, `tools/check_package.sh` check 8c; `REPRODUCE.md` § "N(5) <= 22" |
| B6 | 3.2, 3.4, B.1 | Δ₆ − 5, **machine-checked** on both halves: all 742,374 base states of the six-vertex base `{1,2,3,4,13,19}` UNSAT, each LRAT proof rechecked by `lrat-trim`, and the cube set proved exhaustive. 1,292.7 core-h; only Corollary 2.4 is human | `certificates/d005mv04cert_d6/VERDICT.txt`, `certificates/d005mv04cert_d6/d005mv04_cert.v2.portable.txt`, `certificates/d005mv04_coverage_cert.txt` | `sat/reroot.py`; `tools/check_package.sh` checks 3 and 3c |
| B7 | 3.2 | **Δ₂₈ − 5 is not 5-inducible** either: `d027_mv04`, `d027` less vertex 5, same base, complete, 1,537.7 cluster core-h. So the bound rests on two hosts from different parents | `verdicts/n22_obstructions/verdicts.tsv` and its README (the sweep's roll-up; the markers are still on the cluster, gap 7); host `tournaments/drt23_del/d027_mv04.bits` | `REPRODUCE.md` § "N(5) <= 22" |
| B8 | 3.2 | No two of the three are isomorphic or converse to each other; each has eleven vertices of out-degree 10 and eleven of 11 and every arc in at least five directed triangles. Δ₆ − 5 and Δ₂₈ − 5 have trivial automorphism group, and so do their parents `d005` and `d027`; Δ₁ − 10 has two vertex orbits | `verify/host_facts.py` | `tools/check_package.sh` check 8e, with Paley(23) as the control |
| B9 | 3.2, 3.3, G | All three are **vertex-critical**: every one-vertex deletion of each is 5-inducible. For Δ₁ − 10 the 22 deletions fall into two classes, one per vertex orbit | `evidence/n21_level_witnesses.tar.zst`, groups `all506` and `sample400` | `verify/critical_deletions.py`, matching each deletion to a witnessed class; `tools/check_package.sh` check 8d |
| B10 | 3.2 | **Δ₁ − 10 is not 5-inducible** either. The host is `d000_mv09`, `d000` (line 1 of McKay's catalogue) less vertex 10, two copies of P₁₁ joined by a ladder. Its automorphism group has order 55; an order-5 subgroup H fixes one vertex in each half and maps the base {x₁, x₃, x₄, x₅, x₉} onto itself, so the search keeps one base state per H-orbit (Corollary 2.5), 1,611 of 8,031, anchored on the two fixed vertices (Corollary 2.3). Every representative exhausted, none capped, 96.9 core-h on the laptop | `evidence/d000mv09_sweep_markers.tar.zst` (1,611 markers, the representatives, the run script and its verdict); host `tournaments/drt23_del/d000_mv09.bits` | `verify/quotient_sweep_audit.py`, which derives the group, the base, the 8,031 base states and the 1,611 representatives from the bits; `tools/check_package.sh` checks 8e and 8f |
| B11 | 3.3 | The 231 arcs of Δ₁ − 10 fall into five orbits under its automorphism group, of 55, 55, 55, 55 and 11 arcs, and reversing one of the 11, a rung y_i → x_i, leaves a 5-inducible tournament. Whether the arcs of the other four orbits are critical is open | `verdicts/d000mv09_rung/d000mv09_r01_15.log` (a majority witness for the reversal of the arc from vertex 1 to vertex 15, 0-based) | `verify/rung_reversal.py`; `tools/check_package.sh` check 8h |

The two Paley(23) refutations are independent in base and anchor, not merely
repeated runs. So are the two Δ₆ − 5 results, B5 and B6: one is the depth-first
engine on a five-vertex base, the other cube-and-conquer on a six-vertex base,
and they share no implementation. Bases are 1-indexed here as in the paper;
`d005_mv04`'s are `0 1 2 11 17` and `0 1 2 3 11 17` on the command line. `evidence/p43_majority.tar.zst` is the sweep of **Paley(43)
itself** (n = 43, 22.86 core-h), not of Paley(43) − v; the two were confused in
an earlier version of this file.

## 2. The rest of the Paley family

| id | § | claim | verdict artifact | re-derive |
|---|---|---|---|---|
| P1 | A.5 | Paley(27) is not 5-inducible, 8,031 base states, 2,537 live, 6.22 × 10⁹ nodes | `evidence/p27_majority.tar.zst` | `REPRODUCE.md` § "Paley(27)" — needs the **GF(3³)** host, `tournaments/p27_paley.bits`; the Z/27 construction is not a tournament |
| P2 | 3.1 | Paley(31) is not 5-inducible, 21,009 base states, 4,007 live, 3.43 × 10⁹ nodes | `evidence/p31_majority.tar.zst`, `evidence/measurements/p31_result.json` | `REPRODUCE.md` § "Paley(31)" |
| P3 | 3.4 | Paley(19) **is** 5-inducible (recovers dim Q₁₉ = 5 of [1]) | `verdicts/WITNESSES_margin_hierarchy.md` | `kinduce --paley 19 --k 5 --max-margin 3 --order mrv --inc --base 0 1 2 3 5`, then `verify/verify_witness.py` |
| P4 | 3.4 | Paley(19) is **not** 5-inducible at unit margin, 2,200 base states of `{1,2,3,4,6}` | `verdicts/p19_margin1_VERDICT.txt`; certified in `certificates/p19cert_d6/`, roots in `certificates/p19cert_d6/p19_cert.portable.txt` and `certificates/p19cert_d6/p19_cert.v2.portable.txt` | `REPRODUCE.md` § "Paley(19)"; `sat/certify_p19_m1.py` |
| P5 | 3.4 | The witnesses are abundant, not delicate: ten workers hit at once from ten base states, support histogram 159 arcs at 3–2 and 12 at 4–1, none unanimous | `verdicts/WITNESSES_margin_hierarchy.md` | as above, `--max-margin 3` |
| P6 | 3.3, G | Paley(23) − v **is** 5-inducible, so no 22-vertex obstruction comes from Paley(23) by deleting a vertex; the 22-vertex obstructions of B5 and B7 come from other doubly regular tournaments | `evidence/n22_p23minusv.tar.zst` (witness at base state 6,560), `verdicts/WITNESSES_paley_minus_vertex.md` | `REPRODUCE.md` § "Paley(23) minus a vertex" |
| P7 | 3.5 | **Paley(31) − v is not 5-inducible**, so Paley(31) is not vertex-critical. 8,031 base states of `{1,2,3,4,13}`, exact index cover, 0 capped | `verdicts/p31_minus1v_VERDICT.txt`, `verdicts/p31mv_majority/p31mv_times.txt` (one line per base state), `verdicts/p31mv_majority/README.md` | `REPRODUCE.md` § "Paley(31) is not vertex-critical" |
| P8 | 3.3 | Paley(23), (27), (31), (43) are **not vertex-critical at unit margin** | `verdicts/m1_family/VERDICTS.md` (cells `p23mv`, `p27mv`, `p31mv`, `p43mv`), per-state times beside it | `REPRODUCE.md` § "The margin-1 family" |

`verdicts/m1_family/VERDICTS.md` also records that the `p27` cell was abandoned
deliberately — Paley(27) is already refuted at majority and unit margin
restricts majority, so that cell is implied — and which arc cells are implied
rather than run. It says so in the table rather than leaving a gap to be
discovered.

**The break on P7 was turned on part-way through**, so 406 of the 8,031 base
states were searched with no break at all and 7,625 with `--toporb 0 2`. The
union is still a complete refutation, and the argument is in
`verdicts/p31mv_majority/README.md`: an exhaustive search of a base state is
strictly stronger than a broken one, so turning a sound break on later cannot
invalidate earlier work. Each line of the times file records which regime
produced it, so the mixture is visible in the record rather than implicit.

## 3. Criticality

Section 3.3's table has eight cells; this is one row per cell that carries a
verdict. "Not vertex-critical" also rules out arc-criticality, since
arc-criticality implies vertex-criticality.

| id | § | claim | verdict artifact |
|---|---|---|---|
| K1 | 3.3, 3.7 | q = 19, **unit margin: arc-critical**. Reversing any arc restores unit-margin inducibility; the reversal is unique up to isomorphism because Aut(P₁₉) is regular on arcs | `verdicts/WITNESSES_paley_arcrev.md` (§ "Paley(19), arc reversed"), host `tournaments/p19_arcrev.bits` |
| K2 | 3.3 | q = 19, unrestricted: 5-inducible, so criticality does not apply | P3 above |
| K3 | 3.3 | q = 23, unit margin: **not** vertex-critical | `verdicts/m1_family/VERDICTS.md` cell `p23mv` |
| K4 | 3.3 | q = 23, unit margin: not arc-critical either | `verdicts/m1_arcrev/VERDICT.md` |
| K5 | 3.3, 3.6 | q = 23, **unrestricted: arc-critical**. Reversing any single arc yields a 5-inducible tournament | `verdicts/p23_arc_critical_VERDICT.txt`, witness `verdicts/p23arc_witness/b1161.witness`; host `tournaments/p23_arcrev.bits` |
| K6 | 3.6 | Consequently Paley(23) is **vertex-critical** unrestricted | K5, plus the direct route in `evidence/n22_p23minusv.tar.zst` |
| K7 | 3.3, 3.5 | q = 31, both margins: **not vertex-critical** | P7 (unrestricted), P8 cell `p31mv` (unit) |
| K8 | 3.3, 3.5 | q = 43, both margins: **not vertex-critical** | B4 (unrestricted), P8 cell `p43mv` (unit) |
| K9 | 3.7 | The **second** doubly regular tournament on 19 vertices is arc-critical at unit margin: 57 orbits of size 3, 57 witnesses | `tournaments/dr19_arcflip/` (57 hosts, `manifest.tsv`, `sweep.log`, `sweep_run2.log`) |
| K10 | 3.7 | Both DRTs on 19 vertices are unit-margin obstructions and both are majority-inducible | `verdicts/WITNESSES_margin_hierarchy.md`, `verdicts/drt19_wit/`; `tournaments/dr19_g1.bits` is Paley(19) relabelled, `tournaments/dr19_g2.bits` the distinct one, \|Aut\| = 3, seven vertex orbits |
| K11 | 3.3 | The two 22-vertex obstructions are vertex-critical unrestricted; whether either is arc-critical is open | B9 |

K9's `sweep.log` is the complete record: 57 distinct orbit representatives, all
SAT, 3.5900 core-h. Its `tally: SAT=57 ABORTED=1` line refers to one *attempt* --
`g2_f13` hit a 400 s cap and was re-run at 1800 s, coming back SAT at 462 s in
the same log. A cap on a search for a WITNESS costs nothing but the retry: it can
only fail to find one, never wrongly report its absence. That is the opposite of
a cap in a refutation, which voids the verdict. `sweep_run2.log` re-runs 44 of
the 57 and is a confirmation, not extra coverage.

The witness for K5 is re-checked by `verify/verify_witness_bits.py`, which
shares no code with the search: it reads the bit string and the five ballots and
recomputes every arc's support. The scan was stopped at base state 1,161 once
the witness appeared, which is sound for a positive certificate and is the
opposite of what a refutation requires.

### The 21-vertex picture (§3.6, Appendix F)

| id | claim | verdict artifact |
|---|---|---|
| F1 | Each of the four unit-margin obstructions has \|Aut\| = 21 with trivial stabilisers, hence exactly ten arc orbits of size 21 | `tournaments/vt21_hosts/manifest.tsv`, `tournaments/vt21_arcflip/manifest.tsv` |
| F2 | The spectrum: h₁ `UUUUUUUUUU`, h₂ `USUSSUUSSU`, h₄ and h₅ all `S` — 15 of the 40 reversals stay obstructions | `verdicts/arcflip_spectrum.log` (final table), `tournaments/vt21_arcflip/out/*.exact.txt` per orbit; the first letter of h₂'s string additionally carries proofs, `certificates/h02f00cert_d6/VERDICT.txt` |
| F3 | So **arc-criticality at unit margin is carried by the arc, not the tournament**: h₂ is arc-semi-critical, 105 of 210 arcs each way | same |
| F4 | All 210 single-arc reversals of h₁ remain obstructions — 736 runs, none capped, tiling each range exactly | `verdicts/arcflip_spectrum.log`, `tournaments/vt21_arcflip/verdicts.tsv` |
| F5 | Every one of the 15 surviving reversals belongs to a host with **cyclic** automorphism group; all 20 orbits of the two with the nonabelian group of order 21 are inducible | `tournaments/vt21_hosts/manifest.tsv` (the group column), F2 |
| F6 | The four hosts and the 15 surviving reversals have **319 one-vertex deletions, 289 pairwise non-isomorphic**, and every one has an exhibited unit-margin witness | `verdicts/vt20_descent.log` (301 audited SAT, 0 UNSAT, 0 capped), witnesses in `verdicts/vt20_descent_shard/*.log`, counts derived by `tournaments/deletion_classes.py` |
| F7 | Hence nothing here descends to a unit-margin obstruction on 20 vertices | same |

**The leading `U` of h₂'s spectrum is now proof-carrying.** That letter says
`h02_f00` — h₂ with its orbit-00 arc `0 -> 1` reversed — is not 5-inducible at
unit margin, and it was established by the DFS engine like the rest of the row.
It has since been re-established by cube-and-conquer with both halves
machine-checked: 202,129 cubes all UNSAT with every LRAT proof independently
rechecked by `lrat-trim`, and the cube set proved exhaustive. 224.4 core-h.
`certificates/h02f00cert_d6/README.md` has the detail; the two engines share no
implementation, so this is a second method and not a rerun.

It is also the **shortest trust chain in the package**. Anchoring — Corollary 2.2 on
ordered pairs, or Corollary 2.3 on vertices — buys a reduction only when `Aut` has
few orbits, and `h02_f00` is rigid, so every orbit is a singleton and neither
lemma removes a single base state. All 202,129 ran, and only Corollary 2.4 (voters
lex-ordered) remains human, against an anchoring lemma *and* Corollary 2.4 for every
Paley certificate here. And because 21 is not a prime power, this host has no
`q`, which is what forced the certificate-block format described in
`certificates/CERT-v2.md`.

`tournaments/deletion_classes.py` derives 319 and 289 from the hosts by
canonicalising every deletion with nauty's `labelg` — 15 × 19 + 2 = 287 classes
from the reversals, plus h₄ − v and h₅ − v. It prints the reconciliation and is
worth running, because the raw file count (301) is neither of those numbers and
invites a wrong conclusion. Run it; it takes seconds.

## 4. The structured families (§3.7)

| id | claim | verdict artifact | re-derive |
|---|---|---|---|
| S1 | All **110** vertex-transitive tournaments on 21 vertices are 5-inducible — 106 at unit margin, the other four by exhibited majority witnesses. So that family holds no candidate below 23 | `verdicts/vt21_majority/`, `verdicts/vt21_margin1/`, `verdicts/verdict_ledger.tsv` | `tournaments/vt21_family.py`, `tournaments/vt21_all_reps.npy` |
| S2 | The closure survives one-arc perturbation: all **40** orbit representatives of the four obstructions are majority-inducible | `tournaments/vt21_arcflip/out/*.majority.txt` | — |
| S3 | Every regular tournament on at most **13** vertices is inducible at both margins (15, 1,223, 1,495,297 instances) | `verdicts/verdict_ledger.tsv`, `verdicts/n13_regular_result.txt`, re-run in `tools/check_package.sh` check 6 | `kinduce --batch <chunk> --n <n> --k 5 --margin exact --order mrv --inc` |
| S4 | Every regular tournament on **15** vertices is inducible at unit margin, all 18,400,989,629, none capped, residue counts summing to OEIS A096368(7) | `cluster/jz_n15/results_margin1/done/` — 6,000 residue markers, an exact cover of `r0..r5999` with none missing, extra or duplicated; re-checked by `tools/check_package.sh` check 5c | `cluster/jz_n15/aggregate.sh` |
| S5 | Every **self-converse** tournament on **13** vertices is inducible at unit margin — all S₁₃ = 95,458,560, 0 UNSAT, 0 aborted | the family splits three ways, each with its own record: **not provably rigid** (319,270) in `cluster/jz_n13sc/results_excluded/done/`, 77 chunks, all SAT, nothing capped; **regular** (11,237) by `verdicts/n13_regular_result.txt`; **rigid** (95,128,053) across all 488 shards, the cluster's 407 in `cluster/jz_n13sc/results/done/` and the laptop's 81 in `cluster/jz_n13sc/results_local/done/` | `cluster/jz_n13sc/aggregate.sh` reports the union as `COVERED IN FULL`; `cluster/jz_n13sc/prepare.sh` refuses to sweep unless the listing has exactly 95,458,560 lines |
| S6 | The three parts are exactly the family, with no gap and no overlap | `cluster/jz_n13sc/state/partition.tsv`, checked by `cluster/jz_n13sc/aggregate.sh` | the regular count is anchored from the other direction by `verify/selfconverse_regular_count.py`, which reaches 11,237 from `gentourng` and a converse test rather than from the catalogue |
| S7 | 3.7 | These sweeps and the families of Appendix G turn up **42** tournaments that are 5-inducible but not at unit margin: 2 doubly regular at order 19, 4 vertex-transitive and 25 near-doubly regular at order 21, and 11 circulant at order 23 | `verdicts/verdict_ledger.tsv`, the 42 rows with `margin1 = UNSAT` and `majority = SAT`; the 25 near-doubly regular ones are `verdicts/near_dr21/` (each host, its majority witness and `verdicts.tsv`) with their complete unit-margin searches in `evidence/near_dr21_unit_covers.tar.zst` | `tools/check_package.sh` check 9 reads the count off the ledger, and check 8g re-derives the 25 (near-doubly regular, witness verified, unit-margin search complete); `tournaments/near_dr21/` holds the scripts that built them and their representative lists |
| S8 | **Every locally transitive tournament is 5-inducible at unit margin**, by construction rather than search (Theorem E.1) | `verify/appendix_e.py` verifies Appendix E's own A, B, C at every cut point of every locally transitive tournament of order 3–14, and the non-strong case besides | `python3 verify/appendix_e.py` — 1,232 tournaments, 15,856 cut points, two controls, about 8 s |
| S9 | **Refuted conjecture:** triangle load does not decide unit-margin inducibility — among 23-vertex vertex-transitive tournaments with t = 4, three are obstructions and 36 are inducible | `verdicts/n23_tmin4/`, `tournaments/vt23/manifest.tsv` | `verify/triangles_per_arc.py` computes t; `tournaments/vt23_gen.py` builds the family |
| S10 | **Corrected 2026-10-15.** An earlier version of this file said every majority obstruction here has t ≥ 6. That no longer holds: the two 22-vertex obstructions have t = 5, which is the most any tournament on 22 vertices can have, and Paley(27) less two vertices (Appendix G) is a majority obstruction on 25 vertices with t = 5. The 37 doubly regular tournaments on 23 vertices have t = 6. So t ≥ 6 is not necessary for a majority obstruction | `verdicts/verdict_ledger.tsv` (its `tmin` column), `verdicts/n22_obstructions/README.md` (the ceiling at 22), `tournaments/descent_parents/p27_mv00_01.bits` | `verify/triangles_per_arc.py`, `verify/host_facts.py` |
| S11 | Order 23 is complete for both families: every vertex-transitive tournament on 23 vertices other than Paley(23) is 5-inducible, and none of the **37** doubly regular ones is, at unit margin or unrestricted. Up to converse the 37 are 19 classes, each settled by a complete search; 16 ran on the cluster at about 26,500 cluster core-hours together | `verdicts/verdict_ledger.tsv` (130 classes at n = 23); `cluster/jz_drt23maj/jz_drt23maj.tsv` (the 16, a roll-up; the markers are on the cluster, gap 7); `verdicts/drt23/drt23_maj.tsv` (d003 and d009, on the laptop); `verdicts/drt23/drt23_m1.tsv` (all 18 non-Paley classes at unit margin) | `tools/check_package.sh` check 9 re-adds the 16 and counts the 37 |

S8's verifier takes the family from its **definition** — every in- and
out-neighbourhood induces a transitive subtournament — not from the round
characterisation the appendix cites, so the equivalence is tested rather than
assumed. Orders 11 to 14 come from McKay's catalogue in
`tournaments/locally_transitive/`, and every line of that catalogue is put
through the same definition test, so the catalogue is checked here too.

## 5. The lemmas, which no certificate covers

| § | lemma | status |
|---|---|---|
| 3 | **3-cycle bound.** In a directed triangle the three supports sum to at most 2k, so with k = 5 no arc of a majority witness that lies in a triangle can be unanimous. Hence majority ≡ margin ≤ 3 on every host whose every arc lies in a triangle | proved in the paper; `verify/triangles_per_arc.py` checks the hypothesis host by host, and `--expect-paley-minus` asserts §3.5's stronger form, that every arc of P_q − v lies in at least (q−3)/4 triangles |
| 2.1 | (L1, Corollary 2.2) orbit anchoring loses no generality — licenses solving only the *live* cubes | human, proved in §2 |
| 2.1 | (L2, Corollary 2.4) the voters may be lex-ordered — licenses the lex chain in the coverage half | human, proved in §2 |

These are the trust boundary. The depth-first engine and the SAT pipeline share
these two lemmas and no code, so their agreement is evidence about the
implementations, not about the lemmas. `engine/kinduce.1`'s SOUNDNESS section
lists the obligations the program cannot check for itself, including that the
`--toporb` representatives really do meet every orbit — an orbit calculation
the caller owes and the engine trusts. Each verdict that used such a break says
how the obligation was discharged: see `verdicts/p43_minus1v_VERDICT.txt` and
`verdicts/p31_minus1v_VERDICT.txt`, both of which name the group order and the
orbit sizes from nauty.

## 6. The certificates (Appendix B)

All three are complete on the search half and the coverage half.

| | Paley(19), unit margin | Paley(23), unrestricted | Δ₆ − 5, unrestricted |
|---|---|---|---|
| base | `{1,2,3,4,5,12}`, 6 vertices | `{1,2,3,4,6,7}`, 6 vertices | `{1,2,3,4,12,18}` of Δ₆ − 5, 6 vertices |
| base states | 142,251 | 3,414,729 | 742,374 |
| live cubes | 22,876 | 343,896 | 742,374 (rigid host, no break) |
| instance | 855 vars, 12,255 clauses | — | 1,155 vars, 17,710 clauses |
| coverage instance | 143,032 clauses, 7.56 s | 3,415,435 clauses, UNSAT in 1,182.95 s, 2,097 MiB LRAT | 743,080 clauses, UNSAT in 82.81 s, 422 MiB LRAT |
| ROOT (CNF) | `0eeb9dd53956fec2…` | `7e6c9c26ac386e67…` | `f5ea8bf78c29405b…` |
| CERT (portable) | `8eb20a1d9e814aab…` | `ff60539e16abf2ec…` | `043a6488483235bb…` (CERT-v2; no v1 for a host with no q) |
| cost | 24.26 + 0.82 core-h | 228.28 + 7.73 core-h | 1,254.9 + 37.8 core-h |

The manuscript gives the Δ₆ − 5 base as `{1,2,3,4,13,19}` in the labelling of Δ₆;
the column above gives the same six vertices in Δ₆ − 5's own labelling, which is
`0 1 2 3 11 17` 0-indexed on the command line.

Every figure in that table re-derives from shipped bytes. The costs are the
column sums of `certificates/*/log/*.log`, which carry `solve_s` and `check_s`
per cube; `tools/check_package.sh` check 9 does the sum and compares against the
manuscript's Appendix A.6.

The LRAT proof bytes were **verified and discarded by design**: each proof was
checked by `lrat-trim`, hashed, and deleted, so peak storage is one proof per
worker rather than terabytes. What ships is the per-cube sha256 chain in
`certificates/*/log/`, and both published roots rebuild from it exactly —
`tools/check_package.sh` check 3 does that and check 3b corrupts one hash to
confirm the check would notice.

**The three levels, and which a third party must reproduce.**

* **ROOT (CNF)** is a sha256 chain over the CNF of every **cube**, in cube
  order. The search half only. Generated by this code from the tournament and
  the base, so it *must* reproduce anywhere.
* **`split_cover_cnf`** is the sha256 of the single **coverage** CNF file. It is
  not an ingredient of ROOT (CNF).
* **CERT (portable)** is the sha256 of a ten-line block naming q, k, the margin,
  the base, the two orbit representatives, the cube count, ROOT (CNF) **and**
  `split_cover_cnf`. **It is the only published value that commits to both
  halves at once.** The `.portable.txt` file *is* that block plus a trailing
  `CERT_PORTABLE=` line, so it audits itself: strip the last line, re-hash,
  compare — which is what check 3c does.
* **CERT (full)** additionally binds ROOT (proofs) and the coverage proof's
  hash. Not portable, and not meant to be.

**ROOT (proofs) and CERT (full) are not portable**: CaDiCaL is deterministic on
a fixed binary but its heuristics use floating-point scoring, so a different
build may emit a different, equally valid proof. **A mismatch there is not
evidence of an error.**

`certificates/p23cert_d6/VERDICT.txt` carries the full statement, including the
timing-free re-rooting that made ROOT (proofs) reproducible at all — the
original hashed record included wall-clock times, so it could not be reproduced
by anyone, this machine included. That file also records, in its own text, an
episode where the verdict script printed "coverage of the cube set: certified
separately" unconditionally, before the coverage check had been run for
Paley(23). It is left in rather than tidied away: a certificate that
misdescribes its own scope is the failure mode Appendix B.2 exists to guard
against, and no check caught it — re-reading the verdict against the log of what
had actually run did.

### 6a. The independent reproduction (§5.2)

| id | claim | verdict artifact |
|---|---|---|
| R1 | Both refutations were re-solved from scratch on the cluster, under a different compiler and CaDiCaL build, and **ROOT (CNF) matched bit for bit** | `cluster/jz_reproduce/slurm/recert_1829004.out` (p19, `PORTABLE ROOT MATCHES`), `cluster/jz_reproduce/slurm/recert_1919064.out` (p23) |
| R2 | At 70.9 and 567.6 cluster core-hours against the laptop's 25.1 and 236.0, i.e. 2.8× and 2.4× | the same two logs: `solve 68.1 + check 2.8` and `solve 542.0 + check 25.6` |
| R3 | Both coverage instances were rebuilt on the cluster to their committed CNF hashes and refuted again, and `CERT (portable)` was re-derived there by running the composition rather than inferring it | `cluster/jz_reproduce/slurm/cert_p19.out`, `cert_p23.out` |
| R4 | The four earlier attempts failed for reasons that say nothing about the result | `cluster/jz_reproduce/slurm/recert_{1827897,1828524,1829003,1843769}.out`, and `cluster/jz_reproduce/COMMANDS.md` says which failed how |

`cluster/jz_reproduce/COMMANDS.md` states per value what has and has not been
reproduced elsewhere, because "the certificate reproduces" is four different
claims and they did not all happen. **CERT (portable) has never been computed on
a second machine** — it is determined by the two hashes that did match, but
determined is not run, and binding the two halves by inference is the exact
failure `sat/certroot.py` was written to end.

## 7. The method comparison (Appendix A)

| id | § | claim | artifact |
|---|---|---|---|
| M1 | A.3 | Integer programming does not reach these instances; at q = 23 the program has 1,265 binaries, 17,710 transitivity rows and 253 majority rows | `evidence/measurements/`; the three sizes are 5·C(23,2), 10·C(23,3) and C(23,2), checked arithmetically by `tools/check_manuscript.py` |
| M2 | A.3 | SAT alone does not either. The dissent-Boolean encoding cuts CaDiCaL conflicts 26–42× against the order-variable family (2,399 / 1,491 / 57 on doubly regular tests), and with a sound symmetry break on top neither 19-vertex instance still returns a verdict | `sat/cube_sat.py` (the three encodings), `evidence/measurements/` |
| M3 | A.2 | The exact domain rule beats the capped one on decision quality alone: 992,378 nodes capped against 294,964 exact, identical verdicts, on a 29-instance Paley(19) benchmark | `evidence/measurements/`, `sat/leaf_bench.py` |
| M4 | B.1 | LRAT over DRAT on measurement: 0.295 s vs 1.043 s per leaf end to end, 29× in checking alone | `sat/leaf_bench.py` |
| M5 | A.4 | Choosing the base: four cheap proxies each inverted when measured, so only live-count × measured s/state is the objective. At q = 31 the class with 4,007 live states beat the class with 2,537 | `evidence/measurements/probe2_results.json`, `probe3_results.json`, `price31.json`, `evidence/README.md`; the class ranking re-derives from `python3 sat/base_survivors.py --q 31 --classes` |
| M6 | A.5 | The cluster runs 2–5× slower per core than the laptop, over six independent experiments | `evidence/measurements/price43_series.json`, `cluster/jz_reproduce/` (R2 above contributes two of the six) |
| M7 | A.4 | Incremental refinement is worth about 110× in wall time, against a factor of a few for the dynamic order | `evidence/measurements/` |

`evidence/README.md` is worth reading for M5: it records that the Paley(27)
price came in 32% high through sampling noise rather than bias, with the
bootstrap that established which it was, and why the right estimator is a
cost-weighted paired ratio against a completed run.

## 8. The cost and node tables (Appendix A.5 and A.6)

**Every figure in both tables that can be re-derived from shipped bytes is
re-derived, by `tools/check_cost_table.py`, and compared against the number the
manuscript prints.** This is the check most likely to catch a stale figure, and
it caught one (see the note below the table).

| id | table row | figure | re-derives from |
|---|---|---|---|
| T1 | A.6 P₁₉ certified refutation, unit | 25.1 core-h | `certificates/p19cert_d6/log/*.log`, columns `solve_s + check_s` → 25.08 |
| T2 | A.6 P₂₃ certified refutation, unrestricted | 236.0 core-h | `certificates/p23cert_d6/log/*.log` → 236.00 |
| T3 | A.6 P₃₁ − v sweep, unrestricted | 239.5 core-h | `verdicts/p31mv_majority/p31mv_times.txt` → 239.53 |
| T4 | A.6 P₂₃ one arc reversed, unrestricted | 210.4 core-h | `cluster/jz_p23arc/AGGREGATE_OUTPUT.txt` — 1,035 base states screened at a 731.8 s mean; the product is 210.4 core-h. The per-base markers are on the cluster, so this is a cross-file check against the kit's own roll-up, not a re-derivation from raw evidence |
| T5 | A.6 second DRT on 19, all 57 arc reversals, unit | 3.59 core-h | `tournaments/dr19_arcflip/sweep.log` → 3.5900 |
| T6 | A.6 regular tournaments on 15, unit | 3,106 core-h | `cluster/jz_n15/results_margin1/done/`, `secs=` field → 3,106.0 |
| T7 | A.6 self-converse on 13, unit | 1,310 core-h | `cluster/jz_n13sc/SLURM_COST.txt` — 1,261.7 cluster + 46.8 laptop + 1.0 laptop = 1,309.5, agreeing to 99.96%. **Sum Elapsed, not CPUTimeRAW**: the accounting reports AllocCPUS = 2 for a single-threaded task, so CPUTimeRAW is exactly double |
| T8 | A.6 all tournaments on 12, unit | ≈ 10,000 core-h | `cluster/jz_n12cover/FINAL_ROLLUP.txt` — 36,268,412 core-seconds = **10,074.6 core-h**, measured, summed from the per-residue markers by `aggregate.sh` |
| T9 | A.5 the four full Paley sweeps: core-hours 34.03, 31.04, 26.89, 22.87 | | the `time=` fields of `evidence/{rerun1_p23,p27,p31,p43}_majority.tar.zst` → 34.03, 31.04, 26.89, 22.86 |
| T10 | A.5 live base states 2,591, 2,537, 4,007, 2,537 | | `python3 sat/base_survivors.py`, search-free, and `--selfcheck` reproduces 8,031 / 2,591 / 16,118 / 2,200 |
| T11 | A.5 seconds per live base state 47.3, 44.0, 24.2, 32.5 | | T9 × 3600 ÷ T10, arithmetic |
| T12 | A.5 node counts | | the `nodes=` fields of the same four archives → 1.14e10, **6.22e9**, 3.43e9, 1.43e9 |
| T13 | A.5 P₄₃ − v takes 185.5 core-h | | `verdicts/p43mv_majority/p43mv_times.txt` → 185.54 |
| T14 | A.6 Δ₆ − 5 certified refutation, unrestricted | 1,292.7 core-h | `certificates/d005mv04cert_d6/log/*.log`, columns `solve_s + check_s` → 1,292.68 |
| T15 | A.6 Δ₆ − 5 sweep (cluster), unrestricted | 1,551.2 cluster core-h | the `secs=` fields of the 8,031 markers in `evidence/d005mv04_sweep_markers.tar.zst` → 1,551.19 |
| T16 | A.6 Δ₂₈ − 5 sweep (cluster), unrestricted | 1,537.7 cluster core-h | `verdicts/n22_obstructions/verdicts.tsv`, 5,535,720 s. The markers are on the cluster, so this is a cross-file check against the sweep's roll-up (gap 7) |

**T12 was a discrepancy with an earlier draft, CORRECTED 2026-09-11.** Appendix A.3
(now A.5) used to print 1.14 × 10⁸ for the q = 27 node count: the archive's `dom_nodes`
counter, not its `nodes` counter, while the q = 31 and q = 43 cells of the same
column were `nodes` and did match. The shipped manuscript now prints the true
6.22 × 10⁹, so the column falls monotonically in q (1.14e10, 6.22e9, 3.44e9,
1.43e9) while the work per node rises monotonically (10.8, 18.0, 28.2, 57.4 µs) —
the opposite of the mechanism the surrounding paragraph describes, and still
supporting its conclusion that the runtime falls in q. `tools/check_manuscript.py`
re-derives every cell of this column by summing `nodes=` over the archive, and
names the swap explicitly if a `nodes` cell ever matches `dom_nodes` instead, so
the check is on the counter and not on the one value that was once wrong.

## 9. Exact enumeration counts (Appendix D)

| id | count | value | anchored by |
|---|---|---|---|
| D1 | D₁₁ | 903,753,248 | OEIS A000568; `cluster/jz_n12cover/aggregate.sh` requires its generation to reach exactly this and fails otherwise |
| D2 | D₁₂ | 154,108,311,168 | OEIS A000568 |
| D3 | R₁₁ | 1,223 | regenerated from `gentourng` by `tools/check_package.sh` check 6, compared against OEIS A096368 |
| D4 | R₁₃ | 1,495,297 | `verdicts/n13_regular_result.txt` |
| D5 | R₁₅ | 18,400,989,629 | the 6,000 `instances=` fields of `cluster/jz_n15/results_margin1/done/` sum to it; check 5c |
| D6 | S₁₁ | 279,968 | OEIS A002785; `cluster/jz_n12cover/aggregate.sh` uses it to derive the exact converse-halving target (D₁₁ + S₁₁)/2 = 452,016,608 and exits non-zero if the kept count differs |
| D7 | S₁₂ | 1,492,288 | OEIS A002785 |
| D8 | S₁₃ | 95,458,560 | OEIS A002785; `cluster/jz_n13sc/aggregate.sh` reconciles 11,237 + 319,270 + 95,128,053 against it exactly, and `prepare.sh` refuses to sweep unless the listing has that many lines |

The partition in D8 is worth stating, because the middle class is easy to get
backwards:

```
completeness: 11,237 regular (excluded) + 319,270 symmetric (swept)
              + 95,128,053 rigid = 95,458,560
matches the 95,458,560 total EXACTLY -- no gap, no overlap
```

The 11,237 excluded ones are the *regular* self-converse tournaments, already
settled by the order-13 regular sweep. The 319,270 are the hosts **not provably
rigid** — the label `symmetric` in the roll-up's output is loose, because colour
refinement failing to discretise does not show that Aut is non-trivial, it only
fails to show that Aut is trivial. The implication runs one way: discretising
*is* a proof of triviality, so the 319,270 are a provable superset of every
order-13 self-converse tournament with non-trivial Aut, and an obstruction
surviving the rigid sweep would necessarily be rigid — unlike both obstructions
known at order 19. Getting this backwards would turn a sound argument into a
claim about 319,270 tournaments that nothing established.

`cluster/jz_n13sc/state/jz_counts.tsv` holds the per-bucket rigid counts, and
they are identical on both machines. That is what makes a sweep split across two
machines auditable at all: the two halves agree on what the universe *is* before
either reports a verdict about it.

## 11. Below 22 vertices (Appendix G and Question 1)

| id | § | claim | verdict artifact | re-derive |
|---|---|---|---|---|
| G1 | G | Below the 36 doubly regular tournaments on 23 vertices other than Paley(23), up to isomorphism and converse, there are **378** classes at 22 vertices, **4,108** at 21 and **28,724** at 20 | `tournaments/drt23_del/PARENTS18.txt` (one per converse pair), `tournaments/drt23_del/HOSTS_level2.tsv`, `tournaments/drt23_del/HOSTS_level3.tsv` | `verify/drt23_level_counts.py` from the parents' bits, which also checks the 18 are one per pair and that each level file holds one host per class; `tools/check_package.sh` checks 8d and 9 |
| G2 | G | At 22 vertices all 378 were screened at up to 50 base states each: 13,863 base states searched to the end, no witness | `cluster/jz_drt23mv/HARDNESS_378.tsv` (per-host roll-up; the markers are on the cluster, gap 7) | check 9 re-adds the exhausted column |
| G3 | G | At 21 vertices **1,173** classes are settled, all 5-inducible: all 506 two-vertex deletions of Δ₆ and Δ₂₈, a stratified random sample of 400, all 53 classes below Δ₁₁, and every class deleting vertex 5 and one other (283). The other 2,935 are open | `evidence/n21_level_witnesses.tar.zst` (its SETTLED.tsv gives each class's group and where its witness was banked; one witness per class) | `verify/verify_descent_witnesses.py --selftest`, which rebuilds each host from its name; `tools/check_package.sh` check 8d |
| G4 | G, 4.2 | At 20 vertices all **28,724** classes are 5-inducible, so every tournament on 19 vertices or fewer below the 36 is too | `evidence/n20_descent_witnesses.tar.zst` (a witness for each, plus the 19,836 hosts of the two lineages in G6) | the same verifier; check 8d also requires the witnessed names to equal the rows of `HOSTS_level3.tsv` |
| G5 | G | At 21 vertices about one base state in 110 yields a witness, so a host there costs a few dozen cluster core-hours to settle; at 22 a proof costs about 1,500 | the screen's per-host markers are in the working repository's archive of the cluster run, not here (gap 7) | — |
| G6 | G | Paley(27) less two vertices and the circulant on 25 vertices with six triangles on every arc are not 5-inducible, and every 21-vertex subtournament of either is | `evidence/p27mv0001_sweep_markers.tar.zst` (complete cover, 8,031 states, 523.4 laptop core-h); the circulant's complete sweep is on the cluster (gap 7); `evidence/n21_other_lineages_witnesses.tar.zst` (208 and 506 witnesses with the level files); parents in `tournaments/descent_parents/` | `verify/sweep_cover_audit.py`; `verify/level_coverage.py`, which finds 150 and 286 classes up to isomorphism and converse and every one witnessed; checks 8c and 8d |
| Q1 | 4.2 | **Question 1** (is N(5) = 22?) is open. G3 and G4 are the evidence the paper cites for it | — | — |

`d005_mv09_11` carries a witness its screening kit rejected
(`evidence/descent_n21_witnesses.tar.zst`, `results/witness/d005_mv09_11.BADWITNESS.log`).
The kit marks a witness that way whenever its checker exits non-zero, and that
happened here for a reason outside the witness: the rejected file verifies
against the rebuilt host. The class is settled by a second witness, banked
separately, which is the one in `n21_level_witnesses.tar.zst`. The verifier
reports such files and never counts them.

## 10. The engine itself

| id | claim | artifact |
|---|---|---|
| E1 | `engine/kinduce.c` is a **consolidation**; no published number was produced by it. Each result names its original version in `REPRODUCE.md` | `engine/versions/` holds the 24 historical sources |
| E2 | The consolidated engine agrees with each of those versions **node for node** on the published command lines | `engine/versions/REGRESSION.md`, produced by `engine/regression.sh` |
| E3 | Figure 1 is drawn from a real trace by a second, independent implementation of the search, which refuses to emit one unless seven cross-checks pass | `manuscript/figures/README.md`, `paley7_trace.py`, `paley7_figure.py`; the caption's numbers are checked against the trace by `paley7_figure.py --check` |

E2 compares the *whole* RESULT line except `time=` — nodes, sols, base_states,
dom_calls, dom_nodes, mrv_fails, top0_fails, bound_fails, fas_fails and
refine_tuples — because verdicts would agree under any correct implementation,
while those counters pin the tie-breaking, the variable order and the domain
refinement.

---

# Gaps — what this package does not establish

Stated plainly, because a reproduction package that overstates its coverage is
worse than one with a short list of holes.

**Gap 1 — Appendix C (13 ≤ N(5)) was incomplete, CLOSED 2026-09-12.** The order-12
census was still running on the cluster when this package was first assembled, and
Appendix C's three quantities were projections from a partial roll-up. It has now
finished and passed its gate, and all three are measurements. The verbatim
roll-up is `cluster/jz_n12cover/FINAL_ROLLUP.txt`: all 903,753,248 order-11
classes generated, 452,016,608 screened after the converse halving, phase 1
complete on 99.4747% of hosts, 4,317,084 leftover extensions of which every one
was 5-inducible at unit margin, phase 3 never invoked, **`CANDIDATES: 0`**, and
10,074.6 core-hours. Appendix C's 99.5%, its "about one extension in 200,000"
(the measured rate is one in 214,434) and its ≈10,000 core-hours all stand as
written.

The gate is not a formality and it caught a real loss. An earlier complete pass
reported 40,000/40,000 residues but kept 443,771,294, which is 8,105,330 *below*
D₁₁/2. `mktemp -d` obeys `$TMPDIR`, a small node-local filesystem shared by every
array task on the node; under that pressure the generator's pipe hit ENOSPC, 52
residues were truncated and 46 produced nothing, and each still wrote its `done`
marker. 15,690,562 hosts had never been screened. The kit now exports
`TMPDIR="$WORK"` so a child tool picks the per-job scratch, and asserts on both
sides of the filter that it received what the generator emitted and wrote what it
kept; `filter_log_check.sh` reconciles those tallies from the SLURM logs at no
compute cost, which is what named the 87 residues, and `rescreen.slurm` redid
them. `selftest.sh` T12 drives all three census-gate verdicts on synthetic
markers.

What makes the gate trustworthy is that its first test uses no published
constant. Keeping `L` iff `canon(L) ≤ canon(L̄)` decides a converse pair by
comparing the same two canonical forms in opposite order, so exactly one member
survives — two if self-converse, never zero — hence kept ≥ D₁₁/2 for any correct
run, whatever S₁₁ is. S₁₁ is then *measured* as 2·kept − D₁₁ = 279,968, and
A002785(11) is an asserted cross-check on that measurement rather than an input
to it. Only D₁₁ = 903,753,248 (A000568) is taken from outside, and it is checked
against the generator's own count.

**Gap 2 — the cluster's coverage runs left no artifact (claim R3), CLOSED 2026-09-12.**
Both instances have now run `run.sh <inst> all` to completion in a single batch
allocation, and the logs are shipped: `cluster/jz_reproduce/slurm/cert_p19.out`
and `cert_p23.out`. So `CERT (portable)` — the value that binds the search half
to the coverage half — is the product of a composition that was actually **run**
on a second machine, on inputs both computed in that same run.

Until now it was only an *inference*: `CERT (portable)` is a sha256 whose only
non-constant inputs are `search_root_cnf` and `split_cover_cnf`, and both had
matched, so the value was determined. True, but unearned — and binding the two
halves by inference rather than by running the composition is precisely the
failure `certroot.py` was written to end.

The p23 run is worth reading for how thin the distinction looks in a log.
`run.sh` prints `NOTE: search_root_cnf was READ FROM <conf>` whenever the root
came from the conf instead of the current run. An earlier attempt printed
`CERT (portable) matches the recorded value` with its root stage SIGKILLed at
cube 200 of 343,896 on a login node — the reassuring line, with half the
certificate merely re-hashed from a recorded number. That log is kept as
`cert_p23_loginkill.out` for exactly that reason. The closing run carries no such
NOTE: 343,896 cubes regenerated with **0 mismatches per cube and per chunk**,
`ROOT (CNF)` identical, the coverage CNF solved fresh to UNSAT with
`CHECK=VERIFIED` and its sha256 asserted against `COVER_CNF_SHA` rather than
eyeballed, 4 h 54 m of wall on 4 cores.

**One value did not reproduce, and must not.** `CERT (full)` commits to LRAT
proof bytes, which depend on the solver build; §5.2 claims portability only for
`CERT (portable)`. What is stronger than promised is that `ROOT (proofs)` matched
byte-for-byte on both instances, so the entire p23 difference comes from
`split_cover_proof`, for which the conf deliberately records no expectation.

**Gap 3 — the two Appendix A.4 cost figures with no artifact, CLOSED 2026-09-11.** Both Appendix A.4 figures that had no artifact
now have one. Row T4, Paley(23) with one arc reversed at 210.4 core-hours, is in
`cluster/jz_p23arc/AGGREGATE_OUTPUT.txt`; note what that file says about its own
`missing indices: 6996` line, since the scan stopped at the witness, which is
sound for a positive certificate and would void a refutation. Row T7, the
order-13 self-converse census at 1,310 core-hours, is in
`cluster/jz_n13sc/SLURM_COST.txt`, which also records the trap that would have
overstated it by 93%: the scheduler reports `AllocCPUS = 2` for a task that asks
for one CPU, because it counts both hyperthreads of the physical core that
`--hint=nomultithread` reserves, so `CPUTimeRAW` is exactly twice the worker time
Appendix A.4 means.

Neither is a re-derivation from raw per-task evidence — those records stay on the
cluster — so both are cross-file checks against a roll-up written by a different
program, which is the same standard the rest of this file uses and is weaker than
summing shipped bytes. `tools/check_manuscript.py` labels them that way.

**Gap 4 — `evidence/arcrev/` is not what its name suggests.** Those 24 logs are
the witness-distance scan that priced the arc-criticality question, not the
sweep that answered it. The answer is K5's witness.

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

**Gap 7 — results whose per-state records are still on the cluster.** Four
computations behind the 22-vertex results finished on the cluster, and what ships
is the campaign's own roll-up rather than its markers: the sweep of Δ₂₈ − 5
(B7, T16; `verdicts/n22_obstructions/verdicts.tsv`), the 16 doubly regular
tournaments on 23 vertices at unrestricted margin (S11;
`cluster/jz_drt23maj/jz_drt23maj.tsv`), the 378-host screen at 22 vertices (G2;
`cluster/jz_drt23mv/HARDNESS_378.tsv`) and the sweep of the circulant on 25
vertices (G6). Each roll-up was written by the campaign's aggregator, which
reports UNSAT only for an exact, uncapped tiling of the base states, so these
are cross-file checks of the same standard as gap 3, weaker than re-adding raw
markers. The witness density of G5 comes from screen markers that are archived
in the working repository and are too large to ship. Bringing the cluster
markers back as `.tar.zst` archives, as was done for Δ₆ − 5
(`evidence/d005mv04_sweep_markers.tar.zst`), would close this gap.

**Not a gap, but read §5.2 before comparing numbers.** Verdicts replicate under
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
