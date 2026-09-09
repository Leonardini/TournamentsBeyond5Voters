# Independent reproduction on the cluster

## Why

On 2026-09-05 several things in the certification workflow changed: a dead
constant removed from `cubes.py`, a stale label fixed in `cover_check.py`,
wall-clock timings removed from the hashed records, a streaming path added to
`cover_check.py`, and an unearned coverage claim removed from the verdict
template. Each was validated locally — but local validation of a local change is
weak evidence. Different hardware and a different compiler is the real test.

## One driver, instance as data

Everything that differs between campaigns — size, margin, base, arc/non,
expected roots, cost — lives in `instances/<name>.conf`. Nothing in the scripts
knows about Paley(19) or Paley(23) specifically, so **adding Paley(27) or
Paley(31) is a new conf file and nothing else**.

    run.sh <instance> <stage>

| stage | what it does | needs a solver? |
|---|---|---|
| `root` | regenerate every cube CNF, assert ROOT (CNF) | **no** |
| `coverage` | build and solve the split-half CNF, assert UNSAT + verified | yes |
| `cert` | bind split + search into the two combined roots | no |
| `recertify` | full re-solve of every cube (see `SOLVE_CORE_H`) | yes |
| `all` | root, coverage, cert | yes |

Every expected value is **asserted**, not printed for a human to compare. An
empty expectation in the conf means "record what you observe" — never "assume it
passed". `p23.conf` deliberately leaves `COVER_CLAUSES` empty because that half
had not completed when the kit was written.

## Tier 1 — cheap (~1 core-h, no cube solving)

    KInduceDFS/jz_reproduce/check.sh          # every instance
    KInduceDFS/jz_reproduce/check.sh p19      # just one

ROOT (CNF) commits to the CNF *files*, which this repository's Python generates,
so regenerating and hashing them involves **no solving at all** — the check costs
minutes rather than the hundreds of core-hours the original runs took, and needs
only Python. That is the check that would catch a real encoding change. If the
toolchain isn't built yet, the `root` stage still works.

## Tier 2 — full re-certification (the gold standard)

    INSTANCE=p19 sbatch KInduceDFS/jz_reproduce/recertify.slurm    # ~24 core-h
    INSTANCE=p23 sbatch KInduceDFS/jz_reproduce/recertify.slurm    # ~228 core-h

Re-derives each verdict from scratch and compares ROOT (CNF), exiting non-zero on
mismatch. It does **not** compare ROOT (proofs): a different cadical build may
emit a different, equally valid proof, so a difference there is expected.

**A SAT cube would be a witness and a major result.** The run stops and keeps the
instance as `STOP_SAT`. Do not dismiss it as a porting artifact.

## Tier 3 — a different solver (strongest)

The method is solver-agnostic; cadical is our choice, not a dependency of the
argument. Any solver emitting DRAT/LRAT can produce the proofs, and any checker
can verify them. Running a sample of cubes under a *different* solver — kissat,
say — tests the result rather than the build: same CNFs, same ROOT (CNF),
different search, different proofs, same verdict.

Point `CAD` in `certify_d6.py` at the other solver and use `--sample N --seed S`
(a uniform sample; `--limit` is a prefix and cube difficulty is heavily skewed,
so it would mislead).

Stronger still on the checking side: `cake_lpr` is formally verified in HOL4,
where `lrat-trim` is merely a different program by a different author.

## What can and cannot be reproduced elsewhere

| | reproducible off the original machine? |
|---|---|
| **ROOT (CNF)**, both campaigns | **yes** — and needs no solver |
| Coverage certificate | **yes** — fresh proof; its CNF hash must match, its proof hash will not |
| **CERT (portable)** | **yes** — built from the two above |
| Known-answer selftests | **yes** |
| **ROOT (proofs)**, **CERT (full)** | **no, by design** — they commit to LRAT bytes |

## Toolchain

    git clone https://github.com/arminbiere/cadical && cd cadical && ./configure && make
    git clone https://github.com/arminbiere/lrat-trim && cd lrat-trim && ./configure && make

`certify_d6.py` and `cover_check.py` expect them at
`~/Downloads/DownloadedSoftware/{cadical/build/cadical,lrat-trim/lrat-trim}`;
edit `CAD`/`LT` at the top of each, or symlink.

**`lrat-trim` exits 20 on success, not 0.** Anything wrapping it must test for
`s VERIFIED` in the output, not the exit code.

## Memory

`cover_check.py` must be run with `--stream` on anything the size of Paley(23).
The in-memory path holds every clause as Python lists — ~9 GB for 3,414,729
negated cubes at 75 literals — and was killed at 8.99 GB. Streaming ran the
Paley(19) instance in 39 MB of Python; cadical's own footprint on the Paley(23)
instance is the part still to be measured, so watch it rather than assume.

Note the coverage instance is **much larger than the search instance**: the
`--arc`/`--non` filter reduces the search half to the live cubes, but coverage
must consider *all* base states — 3,414,729 for Paley(23) against 343,896 live.

## Known gap

The Paley(23) **split half was still running when this kit was written**. The
search half (all 343,896 cubes UNSAT) is done and verified. Until coverage
passes somewhere, that refutation rests on the enumeration being exhaustive by
construction, which is an argument rather than a machine-checked certificate —
and `p23.conf` has no `CERT_PORTABLE` recorded for exactly that reason.
