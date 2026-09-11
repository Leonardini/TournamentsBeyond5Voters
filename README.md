# Tournaments not inducible by five voters — reproduction package

Code, tournaments, verdicts and certificates for the paper *Tournaments not
inducible by five voters*, which proves

> **13 ≤ N(5) ≤ 23**,

where N(k) is the least order at which some tournament is not the majority
tournament of any k linear orders. The upper bound comes from Paley(23); the
lower bound from an exhaustive case analysis at order 12.

**Start with [`CLAIMS.md`](CLAIMS.md).** It carries one row per statement the
paper makes, each with a stable id, the artifact that holds the verdict, and the
command that re-derives it — and it ends with a plainly stated list of what this
package does *not* establish. [`REPRODUCE.md`](REPRODUCE.md) is the operational
companion: the exact command line for each published result.

```
tools/check_package.sh          # the acceptance gate; ~7 min, single-threaded
tools/check_package.sh --quick  # structural checks only, no solver needed
```

**If you are a program rather than a person**, read [`claims.json`](claims.json)
or [`claims.tsv`](claims.tsv). Both are *generated* from `CLAIMS.md` by
`tools/claims_index.py`, and the gate regenerates and diffs them, so a
hand-edited copy is a failure rather than a silent divergence. Each record
carries the claim id, its manuscript sections, its status (`established` or
`declared_gap`), and every artifact path, resolved against the package. The
declared gaps are in the same file, numbered as `CLAIMS.md` numbers them, so
"what does this package not establish" is a field lookup rather than a reading
exercise.

```
tools/claims_index.py --check   # CLAIMS.md == claims.tsv == claims.json, 0 missing paths
tools/check_manuscript.py       # re-derive every manuscript figure we can, from shipped bytes
tools/manifest.py --check       # MANIFEST.sha256 against the bytes on disk
python3 verify/appendix_e.py    # verify Appendix E's construction on 1,238 tournaments
engine/regression.sh            # the consolidated engine vs the versions that produced the results
```

Every one of those exits non-zero on failure.

The gate is built to fail if the package is wrong rather than to confirm that
it is right. Every quantity is recomputed from the shipped bytes and compared
against a value recorded in a different file, and each positive check is paired
with a control that must fail: corrupt one cube's hash and the certificate root
must stop matching; apply the refutation audit to a witness search and it must
refuse to pass; remove one base state from a sweep's record and the coverage
audit must notice. A gate whose controls do not fire is not testing anything.

**The gate currently reports one failure, and it is real.** Check 9 re-derives
every figure the manuscript prints that this package can re-derive, and Appendix
A.3's node count at $q = 27$ does not re-derive: the printed $1.14 \times 10^{8}$
is the run's `dom_nodes` counter where the rest of that column is `nodes`, whose
value is $6.22 \times 10^{9}$. The package holds the correct figure and the paper
does not. This is recorded under table 8 of `CLAIMS.md` rather than accommodated,
because a gate that is green against a wrong number is worse than one that is
red against it.

## What is here

| | |
|---|---|
| `engine/` | `kinduce.c`, the depth-first placement search, one translation unit, with its man page. `kcover.c` is the order-12 witness-extension engine. `versions/` keeps the 24 historical implementations that originally produced each result, and `versions/REGRESSION.md` records the consolidated engine agreeing with each of them node for node on the published command lines |
| `tournaments/` | the hosts as bit strings, plus the generators that build them and `deletion_classes.py`, which derives the deletion-class counts of §3.4 with nauty |
| `sat/` | the dissent-Boolean encoding, the cube tooling, the certification driver and the coverage check |
| `verify/` | checkers that share no code with the search: witness verifiers that read the bit string and the ballots and recompute every arc's support; `appendix_e.py`, which builds Appendix E's three orders from its own prose and checks them over every locally transitive tournament of order 3–14; `triangles_per_arc.py`, which tests the 3-cycle hypothesis that turns a `--max-margin 3` run into a majority verdict |
| `certificates/` | the two machine-checked refutations — per-cube sha256 chains, published roots, and the verdict files that state their own scope |
| `verdicts/` | one verdict record per result, the consolidated ledger, and the witness documents |
| `evidence/` | chunk logs for every distributed sweep, compressed about 100×, plus the measurement JSON behind each configuration choice |
| `cluster/` | the two computations that did not run on the laptop: the order-12 census and the 15-vertex regular census |
| `manuscript/` | the paper the claims come from, its LaTeX source, and `figures/` — the pipeline that draws Figure 1 from a real trace, by a second implementation of the search that refuses to emit one unless seven cross-checks pass |
| `notes_research_log.md` | the working notebook, kept for provenance |

## Building

```sh
cc -O3 -march=native -o kinduce engine/kinduce.c
man ./engine/kinduce.1
```

No dependencies for the search. The SAT route needs CaDiCaL 2.0.0 and
`lrat-trim` 0.2.0, the coverage check needs `drat-trim`, and the catalogue
sweeps need nauty 2.8.6 (`gentourng`, `labelg`). These are not vendored;
`tools/check_package.sh` resolves each through a ladder of locations and fails
loudly naming everything it tried, rather than silently measuring nothing.

`man ./engine/kinduce.1` has a SOUNDNESS section listing the obligations the
program cannot check for itself. The one that matters in practice: when you
pass `--toporb`, you are asserting that your representatives meet every vertex
orbit. That is an orbit calculation the caller owes, and the engine trusts it.

## Reading the verdicts

A refutation is only as good as the union of its slices, so the audit is on the
**index cover**, not the count — a missing index and a duplicated one cancel in
a count:

```sh
ls done | sort -n > /tmp/got.txt
seq 0 8030   > /tmp/want.txt
comm -13 /tmp/got.txt /tmp/want.txt | wc -l    # missing: must be 0
comm -23 /tmp/got.txt /tmp/want.txt | wc -l    # extra:   must be 0
```

and no `SLICE` line may report a nonzero `capped` count: **a run that hit a cap
is not a verdict.** The drivers write a marker only on `RESULT UNSAT`, which is
what makes the exact index cover a completeness certificate — a capped or
aborted state leaves no marker behind.

Positive results are the other way round. A witness search stops at its first
witness and never visits the remaining slices, so partial coverage there is
success rather than incompleteness. Do not apply the refutation checklist to
one; the gate's fourth control exists because that mistake is easy to make.

## What replicates, and what does not

*Verdicts* replicate under any correct implementation. That is the claim the
paper makes.

*Node counts* replicate exactly, but only with five things held fixed, each of
which can differ silently between two people running what they believe is the
same computation: the binary (or at least identical tie-breaking, since ties
are common), the vertex numbering, the base, the resulting base-state set, and
the margin regime. The engine prints all but the numbering in a header on every
run, so a run log is a self-describing fingerprint. The numbering is why
tournaments ship here as bit strings rather than being rebuilt from their
constructions — **two of the four 21-vertex tournaments are not in the
canonical labelling a fresh enumeration produces.**

*Wall-clock and core-hours* replicate only in order of magnitude. The cluster
we used runs 2.6–3.3× slower per core than the laptop, measured three
independent ways, so core-hours are comparable within our own runs and not
across machines.

Of the two published certificate roots, only **ROOT (CNF)** is portable: it
commits to the CNF of every cube in cube order, is generated by this code from
the tournament and the base, and must reproduce anywhere. **ROOT (proofs)**
additionally commits to the LRAT proof bytes, which are not portable — CaDiCaL
is deterministic on a fixed binary, but its heuristics use floating-point
scoring, so a different build may search differently and emit a different,
equally valid proof. **A mismatch there is not evidence of an error.**

The proof bytes themselves were verified and discarded by design: each was
checked by `lrat-trim`, hashed, and deleted, so peak storage was one proof per
worker rather than terabytes. That makes this artifact weaker than one that
publishes its proofs, and §5.3 of the paper says so. The trade is deliberate at
this scale — regenerating either certificate from nothing costs 25 or 236
core-hours, three orders of magnitude below what re-validating a published
proof of the Boolean Pythagorean triples kind costs.

One practical note: `lrat-trim` signals success with `s VERIFIED` and **exit
code 20**, following the SAT-solver convention, not exit code 0.

## Provenance and integrity

Every file here was copied from the working repository by
`tools/assemble_from_source.sh`, so the provenance of the package is one
readable list rather than a recollection. Re-running it is idempotent.

`MANIFEST.sha256` hashes every shipped file. `tools/manifest.py --check`
verifies it and reports CHANGED, MISSING and UNTRACKED separately, because they
mean different things: a changed file is a corruption or an edit, a missing one
is an incomplete copy, an untracked one is usually a build product.

## Licence and citation

CC BY 4.0; see [`LICENSE`](LICENSE), which also names the four external tools
that are used but not vendored and the source of the redistributed tournament
catalogues. [`CITATION.cff`](CITATION.cff) carries the preferred citation —
please cite the paper rather than the repository alone.
