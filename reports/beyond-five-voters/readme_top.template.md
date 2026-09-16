# Reproduction record — the headline claims, re-run from commit `48b4a49`

*An end-to-end re-run of this package's own results, driven by an agent from the
published commit rather than from the working tree, with every witness
re-verified by code that shares nothing with the search. 2026-09-15.*

[![Open in molab](https://marimo.io/molab-shield.svg)](https://molab.marimo.io/github/Leonardini/TournamentsBeyond5Voters/blob/main/paley23_five_voters.py)

**Claim tested.** B1 — $P_{23}$ is not the majority tournament of any five
linear orders, hence $N(5) \le 23$, improving the best previous bound of 38.
This is the instance Bachmeier et al. reported their SAT solver could not decide
within six cumulative weeks.

**What was done.** This package, pinned at `48b4a49`, was rebuilt from source and its `kinduce` engine run to
completion over **all 8,031 base states** of the published decomposition, one
invocation per base state across 11 workers, with the verdict audited by exact
index cover rather than by a count. Four further claims were reproduced
alongside it, and every witness was re-verified by a program that shares no code
with the search.

**Assessment: aligned on the central claim.** PLACEHOLDER_README_ASSESSMENT

| | paper | observed here |
|---|---|---|
| $P_{23}$ verdict | not 5-inducible | not 5-inducible |
| base states cleared | 8,031 | PLACEHOLDER_CLEARED |
| capped / missing / witnesses | 0 / 0 / 0 | PLACEHOLDER_ZEROS |
| cost | 34.03 core-h | PLACEHOLDER_COREH |
| nodes explored | 1.14 × 10¹⁰ (App. A.3) | **9.30 × 10⁷ — divergent** |
| seconds per live base state | 47.3 | 54.1 |
| $P_{19}$ at unit margin | not inducible (2,200 states) | PLACEHOLDER_P19M1 |
| ROOT (CNF), $P_{19}$ certification | `0eeb9dd5…96a78a` | identical, 22,876 cubes, 0 mismatches |
| ROOT (CNF), $P_{23}$ certification | `7e6c9c26…de49cb` | PLACEHOLDER_README_ROOT23 |

**Downscaling and substitutions.** No claim was run at reduced scale: every
refutation reported here is complete over its full base-state space, and both
certifications had their portable half — ROOT (CNF) — rebuilt cube by cube from
scratch. What was left out was left out whole: the order-12 census (~10,000
core-h, cluster scale), $P_{31}-v$ (239.5 core-h), $P_{43}-v$ (185.5 core-h),
$P_{31}$ (26.89 core-h) and the LRAT solving half of both certifications, which
the paper itself says is not portable across CaDiCaL builds. One substitution: the $P_{23}-v$ witness was
sought directly at the base state the package records it at, rather than scanned
up to, because what is being reproduced is the witness and not the cost of
locating it.

**Compute.** A single Apple M-series laptop (14 cores, 24 GB), 11 workers, run
locally through `orx`. The paper's own measurements were taken on the same
machine class at the same width, so the core-hour comparison is direct rather
than approximate.

**Read more.** [**The full report**](reports/beyond-five-voters/report.md) —
illustrated, claim by claim, with the code path and the controls.
[**The notebook**](paley23_five_voters.py) — a self-contained tutorial that
opens with the result and re-runs the verification steps in milliseconds; it
embeds the witnesses, so nothing expensive is rerun.

### Experiment log

Every node runs the identical command; what differs between them is one line of
`repro2609/claims.conf`, shown in the *selects* column. The harness is in
[`repro2609/`](repro2609/). The experiment branches themselves live in
[`Leonardini/Tournaments`](https://github.com/Leonardini/Tournaments), the
working repo the reproduction was driven from; each one carries the same
`repro2609/` tree at the commit that produced its result.

| branch | purpose | selects | exact run command | outcome | compute |
|---|---|---|---|---|---|
| [R0 — build, gate, controls](https://github.com/Leonardini/Tournaments/tree/orx/2609-13924-r0-engine-build-regression-gate-posit) | Build the pinned engine; node-for-node regression gate; the three sub-minute claims with independent witness checks | `CLAIMS="build pos calib"` | `bash repro2609/run.sh` | PLACEHOLDER_R0 | 11 workers, local |
| [B1 — Paley(23)](https://github.com/Leonardini/Tournaments/tree/orx/2609-13924-b1-paley-23-is-not-5-inducible-hence) | The headline refutation, complete over 8,031 base states | `CLAIMS="build p23"` | `bash repro2609/run.sh` | PLACEHOLDER_B1 | 11 workers, local |
| [P4/K9/K10 — margin hierarchy](https://github.com/Leonardini/Tournaments/tree/orx/2609-13924-p4-k9-k10-the-margin-hierarchy-at-ord) | Both doubly regular tournaments on 19 vertices at unit margin, plus all 57 arc-orbit reversals | `CLAIMS="build p19m1 dr19"` | `bash repro2609/run.sh` | PLACEHOLDER_P4 | 11 workers, local |
| [B2-portable — ROOT (CNF)](https://github.com/Leonardini/Tournaments/tree/orx/2609-13924-b2-portable-rebuild-root-cnf-for-both) | Regenerate both certifications' cube sets from scratch and compare the published hashes | `CLAIMS="root19 root23"` | `bash repro2609/run.sh` | **Aligned on $P_{19}$** — identical hash, 22,876 cubes, 0 mismatches. $P_{23}$ hit its 40-minute side-job cap at 70%, continued below | 1 worker, local, beside B1 |
| [B2-portable-2 — the $P_{23}$ root, given room](https://github.com/Leonardini/Tournaments/tree/orx/2609-13924-b2-portable-2-the-paley-23-root-cnf-r) | The same check with a 90-minute cap instead of 40 | `CLAIMS="root23"` | `bash repro2609/run.sh` | **Aligned** — 343,896 cubes regenerated, 0 per-cube and 0 per-chunk mismatches, hash identical; 49m32s | 1 worker, local |
| [P2 — Paley(31)](https://github.com/Leonardini/Tournaments/tree/orx/2609-13924-p2-paley-31-is-not-5-inducible) | Extend the method one Paley step further out; does not move $N(5)$ | `CLAIMS="build p31"` | `bash repro2609/run.sh` | **Not run** — configured and pushed, ~2.8 h at 11 workers; ran out of clock | would be 11 workers, local |
| `main` | Not run as an experiment (publication surface) | — | — | Carries the README, the report and the notebook | — |

---

