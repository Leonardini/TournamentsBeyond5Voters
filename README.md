# Tournaments not inducible by five voters — reproduction package

Code, tournaments, verdicts and certificates for the paper *Tournaments not
inducible by five voters*, which proves

> **13 ≤ N(5) ≤ 23**,

where N(k) is the least order at which some tournament is not the majority
tournament of any k linear orders. The upper bound comes from Paley(23); the
lower bound from an exhaustive case analysis at order 12.

**Start with [`CLAIMS.md`](CLAIMS.md).** It carries one row per statement the
paper makes, the artifact that holds the verdict, and the command that
re-derives it — and it ends with a plainly stated list of what this package
does *not* establish. [`REPRODUCE.md`](REPRODUCE.md) is the operational
companion: the exact command line for each published result.

```
tools/check_package.sh          # the acceptance gate; ~2 min, single-threaded
tools/check_package.sh --quick  # structural checks only, no solver needed
```

The gate is built to fail if the package is wrong rather than to confirm that
it is right. Every quantity is recomputed from the shipped bytes and compared
against a value recorded in a different file, and each positive check is paired
with a control that must fail: corrupt one cube's hash and the certificate root
must stop matching; apply the refutation audit to a witness search and it must
refuse to pass. A gate whose controls do not fire is not testing anything.

## What is here

| | |
|---|---|
| `engine/` | `kinduce.c`, the depth-first placement search, one translation unit, with its man page. `kcover.c` is the order-12 witness-extension engine. `versions/` keeps the 24 historical implementations that originally produced each result |
| `tournaments/` | the hosts as bit strings, plus the generators that build them and `deletion_classes.py`, which derives the deletion-class counts of §3.4 with nauty |
| `sat/` | the dissent-Boolean encoding, the cube tooling, the certification driver and the coverage check |
| `verify/` | witness verifiers that share no code with the search: they read the bit string and the ballots and recompute every arc's support |
| `certificates/` | the two machine-checked refutations — per-cube sha256 chains, published roots, and the verdict files that state their own scope |
| `verdicts/` | one verdict record per result, the consolidated ledger, and the witness documents |
| `evidence/` | chunk logs for every distributed sweep, compressed about 100×, plus the measurement JSON behind each configuration choice |
| `cluster/` | the two computations that did not run on the laptop: the order-12 census and the 15-vertex regular census |
| `manuscript/` | the paper the claims come from |
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

## Provenance

Every file here was copied from the working repository by
`tools/assemble_from_source.sh`, so the provenance of the package is one
readable list rather than a recollection. Re-running it is idempotent.
