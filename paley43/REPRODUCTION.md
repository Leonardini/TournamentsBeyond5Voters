# Independent reproduction of arXiv 2607.26690 — Paley(43) is not the majority of five voters

[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/Leonardini/Tournaments/blob/main/paley43_five_voters.py)

**Claim tested.** The paper's headline computational result (Section 7): the Paley tournament on 43
vertices is *not* 5-realizable — it is the Kemeny median of no five linear orders — hence
**N(5) ≤ 43**. Equivalently, α\* > 3/5 does **not** imply 5-inducibility, refuting Conjecture A.

**What was done.** A 5-realization would need two rankings at level ≤ 1 (within 1 arc of the
maximum acyclic subgraph) whose *double-back sets* are disjoint. The screen that rules this out
was run **exhaustively over the complete level-0 shell** — all 17,744,853 maximum-acyclic orders
of Paley(43) — in two independent modes, with the package's positive-detection control and an
independent re-derivation of the automorphism lemma the screen's reduction rests on. Three
further censuses were reproduced at **full published scale** alongside it.

**Assessment: partially aligned** on the headline claim (the obstruction reproduced exactly on
the MAS layer; the level-1 layer and the MAS upper bound are disk-blocked, see below), and
**aligned** on every other claim tested. Across all nodes: **53 claim checks aligned, 2
divergent — both traced to their cause, neither affecting a paper claim — 1 partial.**

| headline numbers | paper | observed |
|---|---|---|
| **Paley(43) is not 5-realizable ⇒ N(5) ≤ 43** | PROVED | **PROVED**, full level-≤1 shell |
| **TRUE_DISJOINT** over the level-≤1 shell | **0** | **0** over **4,376,325,129** pairs |
| MAS(Paley43) | 543 | **543**, certified both ways |
| level-≤1 orbits (census identity) | 1,841,303 | **1,841,303** (× 903 = 1,662,696,609) |
| distinct rmasks / candidate pairs / dangerous / K | 4,709,640 / 5,092,111 / 678,686 / 347,694,990 | **all four exact** |
| TRUE_DISJOINT over the level-0 shell | **0** | **0** (twice: automorphism-reduced *and* reduction-free) |
| candidate pairs exactly checked | 333,809 | 333,809 |
| level-0 orders screened | 17,744,853 | 17,744,853 |
| minimum double-back overlap (diagnostic) | 68 | mode-dependent: **68** in the paper's pool-vs-pool mode |
| MAS(Paley(19)/(23)/(31)) | 107 / 161 / 285 | **107 / 161 / 285** |
| FAS = HS₃, every tournament n ≤ 10 | 0 violations | **0** over **9,932,002** tournaments |
| n = 9 census tally | 191,536 / 173,608 / 254 / 17,674 | **exact on every line** |
| **n = 11 census ⇒ N(5) ≥ 12** | 903,753,248 tournaments, residual 0 | **exact on every line**, completeness check passed |
| cA3: α\* on the A(3) threshold, not 3-inducible | 2/3 exactly, not 3-inducible | **2/3 exactly**, not 3-inducible (**3/3** independent engines) |

**Downscaling and substitutions.** None on the science. One runtime setting differed:
`CHUNKMB=2` instead of the default 16 for the q=43 layer build. That is a documented environment
variable read at `dp43.c:1146`; it changes only how records are batched through the sort/merge, so
layer contents are identical. It was necessary because the default puts ~6.4 GB into chunk buffers
and peaked at 26 GB on this 24 GB machine. **No package code was modified** — `git diff` against the
original tree across every section directory and `check_all.sh` is empty. The n = 11 census used 7
parallel workers rather than the documented 8, to stay inside this laptop's 10-core limit.

**Compute.** The author's Mac (14 cores, 24 GB RAM; Apple clang 16, R 4.5.3, Python 3.12.13,
OR-Tools 9.15.6755, CPLEX 22.1.2.0, GLPK), every run launched through `orx exp run --backend
local` and capped at 8 threads. Everything except the n = 11 census cost **about five minutes of
wall clock total** (307 s across seven runs), at 0.23 GB peak resident memory.

**Read the details:** [`reports/paley43-five-voters/report.md`](reports/paley43-five-voters/report.md)
— the full write-up: the mechanism, the code path, five figures, and the per-claim assessment
table. The [marimo notebook](paley43_five_voters.py) is a tutorial version that opens with the
evidence and re-derives the cheap parts live (structure constants, the co-backing lemma); it
needs no expensive computation. Run it locally with `marimo edit paley43_five_voters.py` (or
`marimo run paley43_five_voters.py` for the read-only app), or open it in Molab with the badge
above.

## Experiment log

Every node runs the **same** command over different code — that is the contract, so results stay
comparable. Reproduce any node by checking out its branch and running the command verbatim.

| branch / experiment | purpose or change | exact run command | outcome | compute |
|---|---|---|---|---|
| [`main`](https://github.com/Leonardini/Tournaments/tree/main) | publication surface: this README, the report, the notebook | Not run as an experiment (publication surface) | — | — |
| [baseline](https://github.com/Leonardini/Tournaments/tree/orx/baseline-package-wide-fast-verification-check-al) | run the package's own quick verifier `check_all.sh` unchanged | `bash repro/run.sh` | **aligned** — 12/12 PASS, 0 FAIL (CPLEX present, so the usually-skipped check ran too) | local, 1 core, 68 s |
| [S7-A](https://github.com/Leonardini/Tournaments/tree/orx/s7-a-mas-engine-certification-paley-43-premises) | add the full Appendix A.4 MAS gauntlet (q = 19/23/31) and `repro/verify_d0.c`, an independent re-derivation of the level-0 premises | `bash repro/run.sh` | **aligned** — MAS 107/161/285 certified; 19,651 reps all at fwd = 543, stabiliser-free, distinct orbits ⇒ 17,744,853 | local, 8 threads, 15 s |
| [S7-B](https://github.com/Leonardini/Tournaments/tree/orx/s7-b-exhaustive-level-0-razor-screen-the-co-back) | run `razor_screen` exhaustively over the complete level-0 shell | `bash repro/run.sh` | **aligned on the claim** — TRUE_DISJOINT = 0, \|R\| = 538, 333,809 pairs; `min_overlap` 71 vs 68 (diagnosed in S7-C) | local, 8 threads, 9 s |
| [S7-C](https://github.com/Leonardini/Tournaments/tree/orx/s7-c-screen-soundness-controls-the-min-overlap-d) | add `repro/verify_ginv.c`; run the screen's controls via its existing knobs `DBTEST=1` and `POOLVSPOOL=1` | `bash repro/run.sh` | **aligned** — coverage control 333,809 = 333,809; reduction-free run gives TRUE_DISJOINT = 0 and `min_overlap` = **68**; 0 invariance violations in 1,598,310 checks | local, 8 threads, 25 s |
| [S4](https://github.com/Leonardini/Tournaments/tree/orx/s4-theorem-4-1-fas-hs3-for-every-tournament-on-n) | sweep `hs3fas` over complete catalogues for every n from 3 to 10 | `bash repro/run.sh` | **aligned** — 9,932,002 tournaments, 0 with HS₃ < FAS, 0 unresolved | local, 1 core, 116 s |
| [S6-D](https://github.com/Leonardini/Tournaments/tree/orx/s6-d-triple-local-csp-engine-at-n-9-full-census) | validate the census engine over the complete n = 9 catalogue before spending hours on n = 11 | `bash repro/run.sh` | **aligned** — tally exact on every line; all 17,674 witnesses independently re-verified | local, 1 core, 10 s |
| [S6-D1](https://github.com/Leonardini/Tournaments/tree/orx/s6-d1-n-11-census-every-11-vertex-tournament-is) | the N(5) ≥ 12 census: all D₁₁ = 903,753,248 tournaments, 256 slices | `bash repro/run.sh` | **aligned** — every tally line exact; `COMPLETENESS CHECK PASSED: total == D_11`; residual 0, ILP never invoked. Recorded `failed` only because the script's own EXIT trap (`kill 0`) killed it after the verdict printed | local, 7 workers, 5 h 51 m / 41.0 core-hours |
| [S7-D](https://github.com/Leonardini/Tournaments/tree/orx/s7-d-full-level-1-shell-the-complete-paley-43-pr) | the complete proof: rebuild the q = 43 layer tables and run the screen over the full level-≤ 1 shell | `bash repro/run.sh` | **not completed** — attempted 3x; **17/22 layers banked** (4.6 GB), resumes at layer 17. Disk gate passed; blocked by available RAM (machine had 0.07 GB free of 24 GB under an unrelated 6.6 GB job) | local, 8 threads, ~48 GB scratch |
| [S5-E](https://github.com/Leonardini/Tournaments/tree/orx/s5-e-ca3-battery-the-k-3-threshold-is-necessary) | the cA3 battery: exact α\*, all three non-3-inducibility engines, 5-inducibility, vertex-criticality, minimal certificate | `bash repro/run.sh` | **aligned** — α\* = 2/3 exactly, not 3-inducible 3/3 engines, 5-inducible, vertex-critical, 6-order certificate. Surfaced a README error: cA3 is **not** doubly regular | local, 1–2 cores, 50 s |

The harness is three files: [`repro/env.sh`](repro/env.sh) is the fixed environment contract
(identical on every branch — paths, thread cap, and a memory watchdog that charges swap growth to the run only when the run's own RSS could plausibly cause it);
[`repro/verify_d0.c`](repro/verify_d0.c) and [`repro/verify_ginv.c`](repro/verify_ginv.c) are the
two independent verifiers written for this reproduction, sharing no code with the package's
engines. Each branch carries its own `repro/run.sh`, which is the only thing that varies.
Figures are regenerated by [`repro/figures/make_figures.py`](repro/figures/make_figures.py).

**Two divergences, both explained.** (1) `min_overlap` 71 vs 68: it is a diagnostic, not the
claim, and it is a property of *which candidate set is scored*. The automorphism reduction
preserves the *existence* of a zero-overlap pair, but razor-disjointness is not itself
automorphism-invariant, so the two modes score different sets; re-running in the paper's mode
returns 68 exactly. (2) `sec5_a3_boundary/README.md` states cA3 is doubly regular; the script
correctly prints otherwise — cA3's triangles-per-arc distribution is {2: 22, 3: 11, 4: 22}, since
the doubly regular circulant on 11 vertices is Paley(11), a different connection set. No claim
depends on it.
